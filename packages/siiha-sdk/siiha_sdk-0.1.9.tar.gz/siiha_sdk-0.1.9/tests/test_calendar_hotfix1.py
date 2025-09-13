# -*- coding: utf-8 -*-
import datetime
import pytz
from dateutil.parser import isoparse

import siiha_sdk.calendar as cal
from siiha_sdk.calendar import parse_event

TZZ = pytz.timezone("Asia/Taipei")

def iso(dt: datetime.datetime) -> str:
    if dt.tzinfo is None:
        dt = TZZ.localize(dt)
    else:
        dt = dt.astimezone(TZZ)
    return dt.replace(second=0, microsecond=0).isoformat()

def test_setup_now():
    # 固定 now：2025-09-13 15:00 +08
    cal.NOW_PROVIDER = TZZ.localize(datetime.datetime(2025, 9, 13, 15, 0, 0))
    assert True

def dur_minutes(a, b):
    if not (a and b): return None
    return int((isoparse(b) - isoparse(a)).total_seconds() // 60)

def test_04_tomorrow_10pm():
    ev = parse_event("tomorrow 10PM", tz="Asia/Taipei")
    assert ev["start"] == iso(datetime.datetime(2025, 9, 14, 22, 0))
    assert ev["end"]   == iso(datetime.datetime(2025, 9, 14, 23, 0))
    assert ev["title"] == "Meeting"

def test_05_tomorrow_1000():
    ev = parse_event("tomorrow 10:00", tz="Asia/Taipei")
    assert ev["start"] == iso(datetime.datetime(2025, 9, 14, 10, 0))
    assert ev["end"]   == iso(datetime.datetime(2025, 9, 14, 11, 0))
    assert ev["title"] == "Meeting"

def test_18_today_3pm_ch_mix():
    ev = parse_event("今天 3pm 會議 with a@b.com，地點: 公司", tz="Asia/Taipei")
    assert ev["start"] == iso(datetime.datetime(2025, 9, 13, 15, 0))
    assert ev["end"]   == iso(datetime.datetime(2025, 9, 13, 16, 0))
    assert ev["title"] == "Meeting"
    assert ev["location"] == "公司"
    assert ev["attendees"] == ["a@b.com"]

def test_19_in_2_days_10am():
    ev = parse_event("in 2 days 10AM", tz="Asia/Taipei")
    assert ev["start"] == iso(datetime.datetime(2025, 9, 15, 10, 0))
    assert ev["end"]   == iso(datetime.datetime(2025, 9, 15, 11, 0))
    assert ev["title"] == "in 2 days" or ev["title"] == "Meeting"

def test_35_next_month_5th_3pm_title_meeting():
    ev = parse_event("下個月五號下午三點", tz="Asia/Taipei")
    # 依 2025-09-13，下一個月 = 2025-10，五號 15:00
    assert ev["start"] == iso(datetime.datetime(2025, 10, 5, 15, 0))
    assert ev["end"]   == iso(datetime.datetime(2025, 10, 5, 16, 0))
    assert ev["title"] == "Meeting"

def test_45_next_tuesday_10am():
    ev = parse_event("next Tuesday 10AM", tz="Asia/Taipei")
    # 2025-09-13 是週六，下一週的週二 = 2025-09-16
    assert ev["start"] == iso(datetime.datetime(2025, 9, 16, 10, 0))
    assert ev["end"]   == iso(datetime.datetime(2025, 9, 16, 11, 0))

def test_46_next_tue_1000():
    ev = parse_event("next Tue 10:00", tz="Asia/Taipei")
    assert ev["start"] == iso(datetime.datetime(2025, 9, 16, 10, 0))
    assert ev["end"]   == iso(datetime.datetime(2025, 9, 16, 11, 0))

def test_47_next_tue_at_10():
    ev = parse_event("next Tue at 10", tz="Asia/Taipei")
    assert ev["start"] == iso(datetime.datetime(2025, 9, 16, 10, 0))
    assert ev["end"]   == iso(datetime.datetime(2025, 9, 16, 11, 0))

def test_48_this_sat_at_5_for_45mins():
    ev = parse_event("this Saturday at 5 for 45 mins", tz="Asia/Taipei")
    # 2025-09-13 為週六，this Saturday 定義為下一個週六（避免落到今天）
    assert ev["start"] == iso(datetime.datetime(2025, 9, 20, 5, 0))
    assert ev["end"]   == iso(datetime.datetime(2025, 9, 20, 5, 45))

def test_49_this_sat_5am_duration_45():
    ev = parse_event("this Saturday 5AM, duration: 45 minutes", tz="Asia/Taipei")
    assert ev["start"] == iso(datetime.datetime(2025, 9, 20, 5, 0))
    assert ev["end"]   == iso(datetime.datetime(2025, 9, 20, 5, 45))
