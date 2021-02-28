from datetime import date, datetime
from typing import Tuple

import pytest

from timesheetbot.services.report import get_report_dates, get_longest_frame_category

cases = (
    (
        (datetime(2021, 2, 2, 15, 30), datetime(2021, 2, 2, 16, 30)),
        (datetime(2021, 2, 2),),
    ),
    (
        (datetime(2021, 2, 2, 15, 30), datetime(2021, 2, 5, 16, 30)),
        (datetime(2021, 2, 2), datetime(2021, 2, 3), datetime(2021, 2, 4), datetime(2021, 2, 5)),
    ),
    (
        (datetime(2021, 2, 2, 15, 30), datetime(2021, 2, 3, 9)),
        (datetime(2021, 2, 2), datetime(2021, 2, 3)),
    )
)


@pytest.mark.parametrize('time_ranges, expected_dates', cases)
def test_report_dates(time_ranges: Tuple[datetime, datetime], expected_dates: Tuple[date]):
    assert tuple(get_report_dates(time_ranges)) == expected_dates


cases = (
    (
        activities1 := (
            (datetime(2021, 2, 2), None, None),
            (datetime(2021, 2, 2, 15, 10), datetime(2021, 2, 2, 15, 40), 'foo'),
            (datetime(2021, 2, 2, 15, 40), datetime(2021, 2, 2, 16, 10), 'bar'),
            (datetime(2021, 2, 2, 16, 10), datetime(2021, 2, 2, 16, 20), 'bar'),
            (datetime(2021, 2, 2, 16, 20), datetime(2021, 2, 2, 17), 'bar'),
        ),
        (datetime(2021, 2, 2, 10), datetime(2021, 2, 2, 11)),
        '',
    ),
    (
        activities1,
        (datetime(2021, 2, 2, 15, 00), datetime(2021, 2, 2, 15, 10)),
        '',
    ),
    (
        activities1,
        (datetime(2021, 2, 2, 17), datetime(2021, 2, 2, 18)),
        '',
    ),
    (
        activities1,
        (datetime(2021, 2, 2, 15), datetime(2021, 2, 2, 15, 30)),
        'foo',
    ),
    (
        activities1,
        (datetime(2021, 2, 2, 15, 10), datetime(2021, 2, 2, 16, 10)),
        'foo',
    ),
    (
        activities1,
        (datetime(2021, 2, 2, 15, 30), datetime(2021, 2, 2, 16)),
        'bar',
    ),
    (
        activities1,
        (datetime(2021, 2, 2, 15, 10), datetime(2021, 2, 2, 16, 20)),
        'bar',
    ),
)


@pytest.mark.parametrize('activities, time_frame, expected_category_name', cases)
def test_category(activities: tuple, time_frame: Tuple[datetime, datetime], expected_category_name: str):
    assert get_longest_frame_category(activities, time_frame) == expected_category_name
