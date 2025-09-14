from time import time
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from django.conf import settings

def get_utc_now():
    return datetime.now(timezone.utc)

def get_kst_now():
    return get_utc_now() + timedelta(hours=9)


def exp_hours(hours):
    return get_utc_now() + timedelta(hours=int(hours))

def exp_days(days):
    return get_utc_now() + timedelta(days=int(days))

def current_time():
    return int(time() * 1000)

def get_delete_date():
    return get_utc_now() + relativedelta(months=+int(settings.DELETE_MONTH))