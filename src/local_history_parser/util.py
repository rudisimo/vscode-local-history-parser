import datetime
import logging
import warnings

from itertools import filterfalse
from itertools import tee
from typing import Any, Callable, Dict, Iterable, List, Tuple


LOG_LEVELS = [
    logging.ERROR,
    logging.WARN,
    logging.INFO,
    logging.DEBUG,
]


def setup_logging(verbosity: int) -> None:
    """
    Configure default logging facility.
    """
    logging_level = LOG_LEVELS[verbosity] if -1 < verbosity < len(LOG_LEVELS) else logging.DEBUG
    logging.basicConfig(level=logging_level)
    logging.captureWarnings(True)


def partition(predicate: Callable[[Any], bool], iterable: Iterable[Any]) -> Tuple[Iterable[Any], Iterable[Any]]:
    """
    Use a predicate to partition entries into false entries and true entries.

    Stolen from: https://docs.python.org/3/library/itertools.html#itertools-recipes
    """

    iter_false, iter_true = tee(iterable)
    return filterfalse(predicate, iter_false), filter(predicate, iter_true)


def dict_factory(data: List[Tuple[str, Any]]) -> Dict[str, Any]:
    """
    Factory function to convert complex dataclass fields into a dictionary.
    """

    def convert(obj: Any):
        return obj

    return dict((k, convert(v)) for k, v in data)


def relative_datetime_factory(input: str) -> datetime.datetime:
    """
    Factory function to convert relative datetime strings into datetime object.
    """
    now = datetime.datetime.utcnow()
    units = dict(days=0, seconds=0)
    mappings = [
        ("second", "seconds", 1),
        ("minute", "seconds", 60),
        ("hour", "seconds", 3600),
        ("day", "days", 1),
        ("week", "days", 7),
        ("month", "days", 30),
        ("year", "days", 365),
    ]

    try:
        value, unit = input.lower().split()[:-1]
        units = {u: int(value) * c for (m, u, c) in mappings if unit.startswith(m)}
        now -= datetime.timedelta(**units)
    except Exception as err:
        warnings.warn(
            f"Failed to parse datetime string: {input}\n{err}",
            UserWarning,
        )
    finally:
        return now
