from datetime import date

from dateutil.relativedelta import relativedelta


def calculate_age(date_of_birth: date, today: date | None = None) -> relativedelta:
    if today is None:
        today = date.today()
    return relativedelta(today, date_of_birth)
