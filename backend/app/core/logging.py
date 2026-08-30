from __future__ import annotations
import json
import logging
import re
class SensitiveFilter(logging.Filter):
    _pattern = re.compile(r"(?i)(password|token|authorization|api[_-]?key|prompt)(\s*[:=]\s*)[^\s]+")
    def filter(self, record):
        record.msg = self._pattern.sub(r"\1=***", str(record.getMessage()))
        record.args = ()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({"level":record.levelname,"logger":record.name,"message":record.getMessage()}, ensure_ascii=False)
def configure_logging(level=logging.INFO):
    root=logging.getLogger(); root.handlers.clear(); h=logging.StreamHandler(); h.addFilter(SensitiveFilter()); h.setFormatter(JsonFormatter()); root.addHandler(h); root.setLevel(level)
def get_logger(name):
    logger = logging.getLogger(name)
    if not any(isinstance(f, SensitiveFilter) for f in logger.filters):
        logger.addFilter(SensitiveFilter())
    return logger





