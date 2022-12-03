from __future__ import annotations

import json
import re
import warnings
from contextlib import contextmanager
from dataclasses import InitVar, dataclass, field
from datetime import datetime
from enum import IntEnum, auto
from pathlib import Path
from sys import stdout
from typing import Any, Callable, Iterator, List, Mapping, Optional, TextIO
from urllib.parse import urlparse

from .model import ExtendedDataclass
from .util import relative_datetime_factory


def build_record_filter(
    regex: Optional[str],
) -> Callable[[HistoryRecord], bool]:
    """
    Create a history record filter function.
    """

    # Create path filter
    regex_filter = None
    if regex is not None:
        regex_filter = re.compile(regex, flags=re.I)

    # Create filter predicate function
    def predicate(record: HistoryRecord) -> bool:
        if regex_filter is not None:
            return bool(regex_filter.search(str(record.target_file)))
        return True

    return predicate


def build_snapshot_filter(
    since: Optional[str], until: Optional[str]
) -> Callable[[HistorySnapshot], bool]:
    """
    Create a history snapshot filter function.
    """

    # Create since date filter
    since_filter = None
    if since is not None:
        since_filter = relative_datetime_factory(since)

    # Create until-date filter
    until_filter = None
    if until is not None:
        until_filter = relative_datetime_factory(until)

    # Create filter predicate function
    def predicate(snapshot: HistorySnapshot) -> bool:
        if since_filter is not None and until_filter is not None:
            return since_filter < snapshot.created_on < until_filter
        elif since_filter is not None:
            return since_filter < snapshot.created_on
        elif until_filter is not None:
            return snapshot.created_on < until_filter
        return True

    return predicate


class HistorySortOrder(IntEnum):
    NEWEST = auto()
    OLDEST = auto()


@dataclass
class HistorySnapshot(ExtendedDataclass):
    path: InitVar[Path]

    # Input properties (JSON)
    id: str = field(repr=False)
    timestamp: int = field(repr=False)
    source: Optional[str] = field(default=None, repr=False)

    # Public properties
    created_on: datetime = field(init=False, hash=False, compare=False)
    source_file: Path = field(init=False, repr=False, hash=False, compare=False)

    def __post_init__(self, path: Path) -> None:
        self.created_on = datetime.utcfromtimestamp(self.timestamp / 1000)
        self.source_file = path / self.id


@dataclass
class HistoryRecord(ExtendedDataclass):
    path: InitVar[Path]

    # Input properties (JSON)
    version: int = field()
    resource: str = field()
    entries: List[Mapping[str, Any]] = field(default_factory=list, repr=False)

    # Public properties
    source_file: Path = field(init=False, repr=False, hash=False, compare=False)
    target_file: Path = field(init=False, repr=False, hash=False, compare=False)
    snapshots: List[HistorySnapshot] = field(
        init=False, repr=False, hash=False, compare=False, default_factory=list
    )

    def __post_init__(self, path: Path) -> None:
        self.source_file = path
        self.target_file = Path(urlparse(self.resource).path)
        self.snapshots = [
            HistorySnapshot.from_dict(d, path=path.parent) for d in self.entries
        ]

    def __len__(self) -> int:
        return len(self.snapshots)

    @contextmanager
    def filter(
        self, fn: Callable[[HistorySnapshot], bool], *, order: HistorySortOrder
    ) -> Iterator[List[HistorySnapshot]]:
        matched = filter(fn, self.snapshots)
        reverse_order = False if order == HistorySortOrder.OLDEST else True
        try:
            yield list(
                sorted(matched, key=lambda o: o.timestamp, reverse=reverse_order)
            )
        finally:
            pass


class HistoryStreamer:
    writer: TextIO
    records: List[HistoryRecord] = list()
    records_written: int = 0

    def __init__(self, path: Path, out: Optional[TextIO]) -> None:
        self.writer = stdout if out is None else out
        for history_file in path.glob("**/entries.json"):
            with history_file.open(mode="r") as fp:
                try:
                    history_contents = json.load(fp)
                    history_record = HistoryRecord.from_dict(
                        history_contents, path=history_file
                    )
                    self.records.append(history_record)
                except Exception:
                    warnings.warn(
                        f"Failed to parse local history file: {history_file}",
                        UserWarning,
                    )

    def __len__(self) -> int:
        return len(self.records)

    def write(self, data: str) -> None:
        self.writer.write(f"{data}\n")
        self.records_written += 1

    @contextmanager
    def filter(
        self, fn: Callable[[HistoryRecord], bool]
    ) -> Iterator[List[HistoryRecord]]:
        matched = filter(fn, self.records)
        try:
            yield list(sorted(matched, key=lambda o: str(o.target_file)))
        finally:
            pass
