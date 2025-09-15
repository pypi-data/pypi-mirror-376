import datetime
import isoweek
import pytz

''' weeks start on mondays '''
def first_date_of_week(any_datetime):
  year, iso_week, iso_weekday = any_datetime.isocalendar()
  return any_datetime - datetime.timedelta(days=(iso_weekday-1))

def last_date_of_week(any_datetime):
  year, iso_week, iso_weekday = any_datetime.isocalendar()
  return first_date_of_week(any_datetime) + datetime.timedelta(days=6) # last date is 6 days after the first date

def is_leap_day(date):
  return date.month == 2 and date.day == 29

def is_in_leap_week(date):
  return isoweek.Week.withdate(date).week == 53

def is_in_week_prior_leap_week(date):
  same_day_next_week = date + datetime.timedelta(days=7)
  return is_in_leap_week(same_day_next_week)

def has_leap_week(year: int):
  return isoweek.Week(year, 53).week == 53

def last_year(date):
  return isoweek.Week.withdate(date).year - 1

def days_since_same_date_last_year(date):
  return 7 * 53 if is_in_leap_week(date) or has_leap_week(last_year(date)) else 7 * 52

def comp_yearwise(datetime_or_date, n_years):
    dt : datetime.datetime = safe_datetime(datetime_or_date)
    comp_days = 0
    dt_week = isoweek.Week.withdate(dt)
    while n_years >= 1:
        if n_years==1 and comp_days == 0:
            weeks = 52
        else:
            weeks = isoweek.Week.last_week_of_year(dt_week.year - n_years).week
        comp_days += weeks*7
        n_years = n_years-1
    comp_date = dt - datetime.timedelta(days=comp_days)
    return comp_date

def days_between(datetime_or_date_a, datetime_or_date_b):

    dt_a : datetime.datetime = safe_datetime(datetime_or_date_a)
    dt_b : datetime.datetime = safe_datetime(datetime_or_date_b)

    delta = dt_a - dt_b
    
    return delta.days

def safe_datetime(datetime_or_date):
    if type(datetime_or_date) == datetime.date:
        return datetime.datetime.combine(datetime_or_date, datetime.datetime.min.time())
    elif type(datetime_or_date) == datetime.datetime:
        return datetime_or_date
    else:
        raise TypeError
    
def get_l4w_days(today: datetime.date):
    """Allows for only showing MTD sales where there are not enough days to show L4W
    
    Specifically we do not want to look in 2022 when showing 2023 W1-W4 Sales. Assumes
    dates are inclusive.

    Params:
        today (datetime.date): date to consider

    Returns:
        l4w_days (int): how many days to go back.
    """
    if today.month == 1 and today.day < 28:
        return today.day - 1
    else:
        return 27

def timestamp_to_datetimetz(timestamp: float, to_tzinfo: str='UTC', timezone_aware=False) -> datetime.datetime:
    """Convert a timestamp into a datetime object with a specific timezone applied.
    
    Params:

        timestamp (float): Timestamp in seconds

        to_tzinfo (str): To timezone in tzinfo eg America/New_York. Default/None is UTC.

        timezone_aware (bool): Include timezone info in returned datetime object

    Returns:
        A datetime object of the converted date. 
    """
    
    from_tz = pytz.UTC
    to_tz = pytz.timezone(to_tzinfo)

    out_ts = datetime.datetime.fromtimestamp(timestamp, tz=from_tz)

    out_ts = out_ts.astimezone(to_tz)

    if timezone_aware:
        return out_ts
    
    return out_ts.replace(tzinfo=None)

def chunk_days(start_date: datetime.date, end_date: datetime.date, days: int):
    """ Returns an iterable of datetime.date objects based on a start_date, end_date and chunk days interval

    Params:
      start_date (datetime.date): Starting interval
      end_date (datetime.date): The ending interval
      days (int): The amount of days
    
    """
    timedelta_curr_days = datetime.timedelta(days=days)

    _curr_start = start_date

    if days < 1:
        raise ValueError("Days must be greater than 0.")
    
    if not all([isinstance(start_date, datetime.date), isinstance(end_date, datetime.date)]):
        raise ValueError("start_date and end_date must be of type datetime.date")

    while True:
        _curr_end = _curr_start + timedelta_curr_days

        if start_date == end_date:
           yield (start_date, end_date)
           break

        if _curr_end > end_date:
            yield (_curr_start, end_date)
            break

        if _curr_start < end_date:
            yield (_curr_start, _curr_end)
            _curr_start = _curr_start + timedelta_curr_days
