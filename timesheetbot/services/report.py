import itertools
from datetime import datetime, timedelta, date, time
from io import BytesIO
from math import ceil
from typing import Tuple, List, Generator

from openpyxl import Workbook

from timesheetbot import utils

DEFAULT_TIME_STEP_MINUTES = 30
TIME_INITIAL_ROW = 2
DATE_INITIAL_COL = 2


def generate_report(
    time_range: Tuple[datetime, datetime],
    activities: List[tuple],
    time_step_minutes: int = DEFAULT_TIME_STEP_MINUTES,
) -> BytesIO:
    wb = Workbook(iso_dates=True)
    wb['Sheet'].title = 'Timesheet'
    ws = wb['Timesheet']
    actvts = prepare_activities(time_range, activities)

    times = get_report_times(time_step_minutes)
    for row, time_val in enumerate(times, TIME_INITIAL_ROW):
        ws.cell(column=1, row=row, value=str(time_val))

    for col, (date_val, activity_gr) in enumerate(
        itertools.groupby(actvts, key=lambda a: a[-3].date()), DATE_INITIAL_COL
    ):
        # TODO fix +1 date for week (other periods ?)
        wb['Timesheet'].cell(column=col, row=1, value=str(date_val))

        # TODO fill in activities
        # for row, time_val in enumerate(times, TIME_INITIAL_ROW):
        #     ws.cell(column=col, row=row, value=str(time_val))

    return _report_to_virt_file(wb)


def prepare_activities(time_range, activities) -> tuple:
    # statistic time frame
    dates = tuple((datetime.combine(date_val, time()), None, None) for date_val in get_report_dates(time_range))

    def prepare_activity(activity: tuple) -> tuple:
        return *activity[:-3], *map(utils.parse_datetime, activity[-3:-1]), activity[-1]
    # merge time frame with activities
    activities = sorted(dates + tuple(map(prepare_activity, activities)), key=lambda a: a[-3].date())

    return tuple(activities)


def get_report_dates(time_range: Tuple[datetime, datetime]) -> Generator[date, None, None]:
    assert time_range[0] < time_range[1]
    d0, d1 = map(datetime.date, time_range)
    days_cnt = ceil((d1 - d0) / timedelta(1)) + 1
    for delta_days in range(days_cnt):
        yield d0 + timedelta(delta_days)


def get_report_times(time_step_minutes: int) -> Tuple[time, ...]:
    report_row_cnt = ceil(timedelta(1) / timedelta(minutes=time_step_minutes))
    time_step = timedelta(minutes=time_step_minutes)

    # todo: tests, accumulate
    time_value = datetime.utcfromtimestamp(0)
    times = [time_value.time()]
    for row in range(report_row_cnt):
        time_value += time_step
        times.append(time_value.time())

    return tuple(times)


def _report_to_virt_file(wb: Workbook):
    virtual_wb = BytesIO()
    wb.save(virtual_wb)
    virtual_wb.seek(0)
    return virtual_wb
