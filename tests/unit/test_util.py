from datetime import datetime
from datetime import timedelta
from typing import Any

import pytest

from local_history_parser.util import datetime as module_datetime
from local_history_parser.util import relative_datetime_factory


FAKE_DATETIME = datetime(1999, 12, 31, 23, 59, 59, 999999)


@pytest.fixture
def mock_datetime(monkeypatch: pytest.MonkeyPatch):
    class patched_datetime:
        @classmethod
        def utcnow(cls):
            return FAKE_DATETIME

    monkeypatch.setattr(module_datetime, "datetime", patched_datetime)


@pytest.mark.parametrize(
    "input_datetime,expected_timedelta",
    [
        pytest.param("0 minutes ago", timedelta(), id="0s-ago"),
        pytest.param("1 second ago", timedelta(seconds=1), id="1s-ago"),
        pytest.param("1 hour ago", timedelta(hours=1), id="1h-ago"),
        pytest.param("3 days ago", timedelta(days=3), id="3d-ago"),
        pytest.param("1 month ago", timedelta(days=30), id="1m-ago"),
        pytest.param("1 year ago", timedelta(days=365), id="1y-ago"),
        pytest.param("10 years ago", timedelta(days=3650), id="10y-ago"),
    ],
)
def test_relative_datetime_factory(input_datetime: str, expected_timedelta: timedelta, mock_datetime: Any):
    patched_datetime = relative_datetime_factory(input=input_datetime)
    expected_datetime = FAKE_DATETIME - expected_timedelta
    assert patched_datetime == expected_datetime
