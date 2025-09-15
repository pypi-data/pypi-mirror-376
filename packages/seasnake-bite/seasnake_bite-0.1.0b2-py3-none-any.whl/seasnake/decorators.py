import functools
import logging

from .capture import TraceManager
from .dispatcher import TraceDispatcher
from .log_to_puml import tracelog_to_puml
from .observers import get_trace_observer


def trace_log(_func=None, *, max_depth=3):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = TraceManager(dispatcher=TraceDispatcher(), max_depth=max_depth)
            tracer.dispatcher.register(get_trace_observer())
            tracer.start()
            try:
                return func(*args, **kwargs)
            finally:
                tracer.stop()

        return wrapper

    return decorator if _func is None else decorator(_func)


def sequence_puml(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        # Flush the trace logger's handlers to ensure all events are written
        try:
            observer = get_trace_observer()
            for handler in getattr(observer.logger, "handlers", []):
                try:
                    handler.flush()
                except Exception:
                    pass
        except Exception:
            # In case observer/logger isn't available, fall back silently
            pass
        try:
            tracelog_to_puml(
                log_file="trace.log", output_puml_file="trace_diagram.puml"
            )
        except Exception as e:
            logging.warning(f"Failed to generate PUML: {e}")
        return result

    return wrapper


def snakebite(_func=None, *, max_depth=3):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = TraceManager(dispatcher=TraceDispatcher(), max_depth=max_depth)
            observer = get_trace_observer()
            tracer.dispatcher.register(observer)
            tracer.start()
            try:
                return func(*args, **kwargs)
            finally:
                # Ensure tracing is stopped before generating PUML
                tracer.stop()
                # Flush the trace logger so all events are on disk
                try:
                    for handler in getattr(observer.logger, "handlers", []):
                        try:
                            handler.flush()
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    tracelog_to_puml(
                        log_file="trace.log", output_puml_file="trace_diagram.puml"
                    )
                except Exception as e:
                    logging.warning(f"Failed to generate PUML: {e}")

        return wrapper

    return decorator if _func is None else decorator(_func)
