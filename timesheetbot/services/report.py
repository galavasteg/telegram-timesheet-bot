from openpyxl import Workbook

TIME_HOURS_BOUND = (6, 0)


def create_report_book() -> Workbook:
    report = Workbook(iso_dates=True)
    # TODO:
    return report


def fill_report(report: Workbook):
    """TODO"""


def generate_report():
    report = create_report_book()
    fill_report(report)
    return report
