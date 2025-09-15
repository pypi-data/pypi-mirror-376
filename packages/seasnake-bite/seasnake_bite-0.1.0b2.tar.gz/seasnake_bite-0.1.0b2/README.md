# sea-snake
sea-snake is a small Python library generating PlantUML sequence diagrams. 
Decorate any function with `snakebite` to record a call stack and produce both a `trace.log` and a `trace_diagram.puml` file.

## Installation

```bash
pip install seasnake-bite
```

## Quick start

```python
from seasnake import snakebite

@snakebite(max_depth=2)
def greet(name: str) -> None:
    print(f"Hello, {name}!")

if __name__ == "__main__":
    greet("Slytherin")
```

Running the script will create `trace.log` and `trace_diagram.puml` in the
current directory, capturing the call sequence.

## Filtering & Options

- include_prefixes / ignore_prefixes: focus tracing on your modules and filter noise. Example: `@snakebite(include_prefixes=("myapp."), ignore_prefixes=("myapp.vendor",))`.
- log_lines: generic per-line logs are off by default. Enable with `log_lines=True` only when debugging.
- sample_lines: when `log_lines=True`, you can reduce volume with `sample_lines=N` to log every Nth execution line.
- max_depth: limit call depth recorded from the decorated entrypoint.

These options are applied consistently during capture and when parsing the log to produce the diagram.

## Logging behavior

- The trace logger writes to `trace.log`. Console logging is opt-in; by default, sea-snake avoids printing to stdout/stderr.
- PUML generation (`trace_diagram.puml`) runs after tracing stops, and the logger is flushed to ensure no events are missed.

## Coverage & Test Interop

sea-snake uses Python tracing APIs and is designed to coexist with coverage/debuggers. If you use coverage in tests and encounter empty logs in subprocesses, open an issue with a minimal repro. The library chains existing tracers where safe and restores them after completion.

## Known Limitations

- Async functions: the decorator isn’t async-aware yet; wrap a sync entrypoint or await inside a traced sync wrapper.
- If/elif/else rendering: control-flow isn’t yet modeled as a single alt/else chain.
- Exceptions: exception events aren’t captured/rendered in diagrams yet.
- Participant names: not quoted/aliased; unusual characters may render oddly.
- Threads: tracer installs for new threads; no per-thread lanes/toggle in diagrams yet.
- Coverage interop: chaining preserves coverage in main pytest; subprocess coverage can affect performance.
- Performance: generic line logs are off by default; enable with `log_lines=True`, and consider `sample_lines=N` for large traces.
- Multiprocessing: separate processes write separate logs; consider per-process file paths if needed.

## Explore further

Run the test suite to see additional examples:

```bash
pytest
```

More information on contributing and project structure can be found in the
[CONTRIBUTING.md](CONTRIBUTING.md) and the `tests/` directory.

Disclaimer: This software is provided “as is” without warranty of any kind. Use at your own risk. The authors and contributors are not liable for any claim, damages, or other liability arising from use of this project. See the LICENSE file for details.
