import datetime


def build_dates(start_date):
    date_list = []
    offset = 0
    while len(date_list) < 6:
        delta = datetime.timedelta(days=offset)
        next_date = start_date + delta
        date_list.append(next_date)
        offset += 1
    return date_list


def get_sunday_date(date_obj):
    days = datetime.timedelta(days=6)
    return date_obj + days
