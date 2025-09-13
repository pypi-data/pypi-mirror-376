# This script runs a QB program and captures high-level timing information about different parts of the system.
# The output is a JSON file containing timing information that can be used to analyze performance.

import argparse
import os
import json

from relationalai.clients.snowflake import Resources as snowflake_api
from relationalai.early_access.lqp.executor import LQPExecutor
from relationalai.early_access.builder import builder
from relationalai.clients.use_index_poller import UseIndexPoller as index_poller

from enum import Enum

import time

# Categories that spans can belong to
class SpanCategory(Enum):
    DATA_PREP = "Data Preparation"
    QB_COMPILE = "QB Compilation"
    EXEC = "RAICode Execution"
    SNOWFLAKE = "Snowflake Requests"
    RESULTS = "Result Processing"
    OTHER = "Other"
    UNKNOWN = "Unknown"

# Contextual information that describes an instrumented method. These are used to create spans.
#
# To better distinguish important spans, we have an `is_core` flag to indicate "core methods".
# Core methods represent high-level concepts that make sense to be reasoned about in isolation.
#
# Core methods must be mutually exclusive. This means that they should not overlap in time with one another,
# and should represent distinct concepts.
# For example, `exec_rai_app` and `process_results` are core methods since they are distinct high-level concepts
# that aid with understanding the overall time breakdown and do not overlap with one another.
# On the other hand, `exec_snowflake` is not a core method since it overlaps with other core methods and
# is tricky to reason about in isolation without knowing /what/ was being executed.
#
# Ideally, the sum of all core methods should equal the total time of the root span.
#
# Additionally, we have a `count_for_cat` flag to indicate whether this method should count towards the time of
# its category. This prevents duplicate counting for overlapping methods in the same category.
class TimeMarker:
    def __init__(self, name, category: SpanCategory, is_core=False, count_for_cat=False):
        self.name = name
        self.category = category
        self.is_core = is_core
        self.count_for_cat = count_for_cat

# Time span for a specific operation.
class TimeSpan:
    def __init__(self, id: str, marker: TimeMarker, parent_id, tags={}):
        self.id = id
        self.marker = marker
        self.parent_id = parent_id
        self.tags = tags

        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = time.time()

    def end(self):
        self.end_time = time.time()

    def duration(self):
        assert self.start_time is not None, "Span has not started yet"
        assert self.end_time is not None, "Span has not ended yet"
        return self.end_time - self.start_time

# Context for the benchmarking. Keeps track of active spans and finished spans.
class BenchmarkContext:
    def __init__(self):
        self.current_spans = []
        self.finished_spans = []
        self.span_id_counter = 0
        self.print_logs = True
        self.gap_size = 0.0
        self.last_end_time = 0

    def start_span(self, marker: TimeMarker):
        parent_id = self.current_spans[-1].id if self.current_spans else None
        span_id = f"span_{self.span_id_counter}"
        self.span_id_counter += 1

        new_span = TimeSpan(span_id, marker, parent_id)
        new_span.start()
        self.current_spans.append(new_span)

        if new_span.marker.is_core:
            assert new_span.start_time is not None, "Span has not started yet"
            last_end_diff = new_span.start_time - self.last_end_time
            self.gap_size += last_end_diff
            if last_end_diff > 0.01:
                print(f"\tWarning: Gap of {last_end_diff:.4f} seconds before start of span `{new_span.id}` ({new_span.marker.name})")

        return new_span

    def end_span(self):
        assert self.current_spans, "No active span to end"
        span = self.current_spans.pop()
        span.end()
        self.finished_spans.append(span)
        if span.marker.is_core:
            self.last_end_time = span.end_time

        if self.print_logs:
            duration = span.duration()
            print(f"Span {span.id} ({span.marker.name}) ended, duration: {duration:.4f} seconds")
        return span

BENCHMARK_CTX = BenchmarkContext()

# Wrapper for instrumenting a method.
# If more fine-grained control is needed, consider monkey-patching manually with spans instead.
# E.g. if you want to add tags or have more complex logic.
class InstrumentedMethod:
    def __init__(self, module, method_name, category, is_core=False, count_for_cat=False, alias=None):
        self.module = module
        self.method_name = method_name

        marker_name = alias if alias else method_name
        self.marker = TimeMarker(marker_name, category, is_core, count_for_cat)

        self.original_method = getattr(module, method_name)
        self.new_method = self._create_instrumented_method()

    def _create_instrumented_method(self):
        def instrumented_method(*args, **kwargs):
            global BENCHMARK_CTX
            BENCHMARK_CTX.start_span(self.marker)
            result = self.original_method(*args, **kwargs)
            BENCHMARK_CTX.end_span()
            return result
        return instrumented_method

    def apply(self):
        setattr(self.module, self.method_name, self.new_method)

    def restore(self):
        setattr(self.module, self.method_name, self.original_method)

# List of all methods to track.
INSTRUMENTED_METHODS = [
    # Core methods. They must be mutually exclusive, high-level concepts, and ideally sum up to the total time.
    InstrumentedMethod(LQPExecutor, "prepare_data", SpanCategory.DATA_PREP, is_core=True, count_for_cat=True),
    InstrumentedMethod(LQPExecutor, "compile_lqp", SpanCategory.QB_COMPILE, is_core=True, count_for_cat=True),
    InstrumentedMethod(snowflake_api, "_exec_rai_app", SpanCategory.EXEC, is_core=True, count_for_cat=True, alias="exec_rai_app"),
    InstrumentedMethod(snowflake_api, "_fetch_exec_async_artifacts", SpanCategory.RESULTS, is_core=True, count_for_cat=True, alias="fetch_artifacts"),
    InstrumentedMethod(LQPExecutor, "_process_results", SpanCategory.RESULTS, is_core=True, count_for_cat=True, alias="process_results"),

    # Other trackers, these should also be on the high-level side but can overlap
    InstrumentedMethod(LQPExecutor, "execute", SpanCategory.EXEC, alias="execute_lqp"),
    InstrumentedMethod(snowflake_api, "_exec", SpanCategory.SNOWFLAKE, count_for_cat=True, alias="exec_snowflake"),
    InstrumentedMethod(index_poller, "_poll_loop", SpanCategory.DATA_PREP, alias="poll_index"),
]

def _make_unknown_span(parent_id, parent_duration, known_children_duration):
    unknown_duration = parent_duration - known_children_duration
    if unknown_duration <= 0.01:
        return None
    return {
        "name": "Unknown",
        "duration": unknown_duration,
        "category": SpanCategory.UNKNOWN.value,
        "parent": parent_id,
        "tags": {},
        "is_core": True,
        "children": [],
        "total_percent": (unknown_duration / parent_duration) * 100,
        "parent_percent": (unknown_duration / parent_duration) * 100,
    }

def _make_task_times_dict(spans, root_span):
    total_duration = root_span.duration()
    task_times = dict()
    for span in spans:
        if span.marker.name not in task_times:
            task_times[span.marker.name] = {"duration": 0.0, "category": span.marker.category.value}
        task_times[span.marker.name]["duration"] += span.duration()

    # Add total percent to each
    for v in task_times.values():
        v["percent"] = (v["duration"] / total_duration) * 100
    return task_times

def _make_spans_dict(spans, root_span):
    spans_dict = dict()
    for span in spans:
        spans_dict[span.id] = {
            "name": span.marker.name,
            "duration": span.duration(),
            "category": span.marker.category.value,
            "parent": span.parent_id,
            "tags": span.tags,
            "is_core": span.marker.is_core,

            # To be filled later
            "children": [],
        }

    # Fill in children
    for span in spans:
        if span.parent_id:
            spans_dict[span.parent_id]["children"].append(span.id)

    # Add total_percent and parent_percent
    total_duration = root_span.duration()
    for span in spans:
        span_info = spans_dict[span.id]
        span_info["total_percent"] = (span_info["duration"] / total_duration) * 100
        if span.parent_id:
            parent_duration = spans_dict[span.parent_id]["duration"]
            span_info["parent_percent"] = (span_info["duration"] / parent_duration) * 100
        else:
            # Root span has no parent
            span_info["parent_percent"] = 100.0

    # Add "Unknown" spans for when sum of children < parent
    for span in spans:
        children = spans_dict[span.id]["children"]
        if not children:
            continue
        known_children_duration = sum(spans_dict[child_id]["duration"] for child_id in children)
        unknown_span = _make_unknown_span(span.id, spans_dict[span.id]["duration"], known_children_duration)
        if unknown_span:
            unknown_id = f"{span.id}_unknown"
            spans_dict[unknown_id] = unknown_span
            spans_dict[span.id]["children"].append(unknown_id)

    return spans_dict

def _make_core_times_dict(spans, root_span):
    core_times = dict()
    total_duration = root_span.duration()
    for span in spans:
        if span.marker.is_core:
            if span.marker.name not in core_times:
                core_times[span.marker.name] = {
                    "duration": 0.0,
                }
            core_times[span.marker.name]["duration"] += span.duration()
    for v in core_times.values():
        v["total_percent"] = (v["duration"] / total_duration) * 100
    return core_times

def _make_category_times_dict(spans, root_span):
    category_times = dict()
    for span in spans:
        if span.marker.count_for_cat:
            cat_name = span.marker.category.value
            if cat_name not in category_times:
                category_times[cat_name] = {
                    "duration": 0.0,
                }
            category_times[cat_name]["duration"] += span.duration()
    return category_times

def main():
    parser = argparse.ArgumentParser(description="Extract LQP requests to run locally")
    parser.add_argument("--program", type=str, help="Path to the QB program to run", required=True)
    parser.add_argument("--outdir", type=str, help="Path to the output directory", required=True)

    args = parser.parse_args()
    program = args.program
    outdir = args.outdir

    if not os.path.isfile(program):
        raise ValueError(f"Program path {program} is not a file")
    if not os.path.isdir(outdir):
        raise ValueError(f"Output path {outdir} is not a directory")

    benchmark_lqp(program, outdir)

def _run_instrumented_qb(qb_prog_path: str):
    global BENCHMARK_CTX
    global INSTRUMENTED_METHODS

    # Run the QB program with instrumentation
    for method in INSTRUMENTED_METHODS:
        method.apply()

    # Special marker for the root span
    e2e_marker = TimeMarker("e2e", SpanCategory.OTHER)
    root_span = BENCHMARK_CTX.start_span(e2e_marker)
    BENCHMARK_CTX.last_end_time = root_span.start_time
    with builder.with_overrides(**{
        'dry_run': False,
        'reasoner.rule.use_lqp': True,
    }):
        with open(qb_prog_path) as f:
            # Compile with the correct filename
            code = compile(f.read(), qb_prog_path, "exec")
            exec(code)
    root_span = BENCHMARK_CTX.end_span()
    assert root_span.marker == e2e_marker, "Mismatched root span"
    for method in INSTRUMENTED_METHODS:
        method.restore()
    spans = BENCHMARK_CTX.finished_spans
    return spans, root_span

def benchmark_lqp(qb_prog_path: str, outdir: str):
    global BENCHMARK_CTX
    spans, root_span = _run_instrumented_qb(qb_prog_path)

    print(f"Total benchmark time: {root_span.duration():.4f} seconds")
    print(f"\tMissing time not tracked by core methods: {BENCHMARK_CTX.gap_size:.4f} seconds")

    # Write results to file
    final_json_dict = dict()
    final_json_dict["spans"] = _make_spans_dict(spans, root_span)
    final_json_dict["task_times"] = _make_task_times_dict(spans, root_span)
    final_json_dict["core_times"] = _make_core_times_dict(spans, root_span)
    final_json_dict["category_times"] = _make_category_times_dict(spans, root_span)

    final_json = json.dumps(final_json_dict, default=str)
    out_path = os.path.join(outdir, "benchmark_results.json")
    with open(out_path, "w") as f:
        f.write(final_json)

    print(f"Wrote benchmark results to {out_path}")

if __name__ == "__main__":
    main()
