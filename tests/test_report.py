from datetime import date, datetime
from typing import Tuple

import pytest

from timesheetbot.services.report import get_report_dates


cases = (
    (
        (datetime(2021, 2, 2, 15, 30), datetime(2021, 2, 2, 16, 30)),
        (date(2021, 2, 2),),
    ),
    (
        (datetime(2021, 2, 2, 15, 30), datetime(2021, 2, 5, 16, 30)),
        (date(2021, 2, 2), date(2021, 2, 3), date(2021, 2, 4), date(2021, 2, 5)),
    ),
    (
        (datetime(2021, 2, 2, 15, 30), datetime(2021, 2, 3, 9)),
        (date(2021, 2, 2), date(2021, 2, 3)),
    )
)


@pytest.mark.parametrize('time_ranges, expected_dates', cases)
def test_report_dates(time_ranges: Tuple[datetime, datetime], expected_dates: Tuple[date]):
    assert tuple(get_report_dates(time_ranges)) == expected_dates
