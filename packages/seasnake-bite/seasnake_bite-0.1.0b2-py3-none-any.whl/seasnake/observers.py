# observers.py
from .logging_config import setup_trace_logger

_trace_observer = None
_session_id = None


def get_trace_observer():
    global _trace_observer, _session_id
    if _trace_observer is None:
        import uuid

        _session_id = str(uuid.uuid4())
        logger = setup_trace_logger("trace_logger", session_id=_session_id)
        _trace_observer = SeaSnakeObserver(logger)
    return _trace_observer


class TraceObserver:
    def on_event(self, event_type, payload):
        raise NotImplementedError


class SeaSnakeObserver(TraceObserver):
    def __init__(self, logger):
        self.logger = logger

    def on_event(self, event_type, payload):
        self.logger.info(f"{event_type}: {payload['detail']}")
