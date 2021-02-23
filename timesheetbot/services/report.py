from datetime import datetime, timedelta
from io import BytesIO
from math import ceil
from typing import Tuple

from openpyxl import Workbook

DEFAULT_TIME_STEP_MINUTES = 30

REPORT_TIME_STEP = timedelta(minutes=DEFAULT_TIME_STEP_MINUTES)
TIME_STEP_INITIAL_ROW = 2


def generate_report(
    date_range: Tuple[datetime, datetime],
    report_time_step_minutes: int = DEFAULT_TIME_STEP_MINUTES,
) -> BytesIO:
    wb = create_report_book(report_time_step_minutes)
    fill_report(wb, date_range)

    virtual_wb = BytesIO()
    wb.save(virtual_wb)
    virtual_wb.seek(0)
    return virtual_wb


def create_report_book(time_step_minutes: int = DEFAULT_TIME_STEP_MINUTES) -> Workbook:
    report_row_cnt = ceil(timedelta(1) / timedelta(minutes=time_step_minutes))
    wb = Workbook(iso_dates=True)
    wb.save('tmp/report.xlsx')
    ws = wb['Sheet']

    time_value, row = datetime.utcfromtimestamp(0), TIME_STEP_INITIAL_ROW
    ws.cell(column=1, row=row, value=str(time_value.time()))
    for row in range(row + 1, report_row_cnt + TIME_STEP_INITIAL_ROW + 1):
        time_value += REPORT_TIME_STEP
        ws.cell(column=1, row=row, value=str(time_value.time()))

    return wb


def fill_report(wb: Workbook, date_range: Tuple[datetime, datetime]):
    wb['Sheet'].title = 'Timesheet'
    # TODO


