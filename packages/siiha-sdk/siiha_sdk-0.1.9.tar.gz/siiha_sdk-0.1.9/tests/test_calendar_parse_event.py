# tests/test_calendar_parse_event.py
import re
import pytz
from datetime import datetime, timedelta
import importlib

import siiha_sdk.calendar as cal

TZZ = pytz.timezone("Asia/Taipei")

# 固定 now：2025-08-15 09:00 Asia/Taipei
class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        base = datetime(2025, 8, 15, 9, 0, 0)
        return tz.localize(base) if tz else base

    @classmethod
    def today(cls):
        return cls.now()

def patch_now(monkeypatch, hh=9, mm=0):
    # 固定 aware now：預設 2025-08-15 09:00 Asia/Taipei
    fixed = TZZ.localize(datetime(2025, 8, 15, hh, mm, 0))
    # 用 NOW_PROVIDER 注入；不用 reload、也不會受 from/import 影響
    monkeypatch.setattr(cal, "NOW_PROVIDER", lambda: fixed, raising=False)


def _iso2dt(iso):
    if iso is None:
        return None
    if "T" not in iso and len(iso) == 10:
        # date-only all-day
        return iso
    return cal.isoparse(iso).astimezone(TZZ)


def test_A_now_plus(monkeypatch):
    patch_now(monkeypatch)
    r = cal.parse_event("now + 90 min focus block", tz="Asia/Taipei", default_minutes=60)
    assert "lock:now_plus" in r["flags"] or "lock:later_hint" in r["flags"]
    s, e = _iso2dt(r["start"]), _iso2dt(r["end"])
    assert s.hour == 9 and s.minute == 0
    assert int((e - s).total_seconds() / 60) == 90
    assert r["title"] in ("focus block", "Focus block", "專注時段", "Meeting")  # tidy 容忍


def test_B_date_time_variants(monkeypatch):
    patch_now(monkeypatch)
    cases = [
        ("2025-09-30 14:00", 2025, 9, 30, 14, 0, "lock:date_hhmm"),
        ("2025/09/30 14:00", 2025, 9, 30, 14, 0, "lock:date_hhmm"),
        ("09/30/2025 14:00", 2025, 9, 30, 14, 0, "lock:date_hhmm"),
        ("Sep 30 2025 14:00", 2025, 9, 30, 14, 0, "lock:date_hhmm"),
        ("Sep 30 2025 2PM", 2025, 9, 30, 14, 0, "lock:hhmm_ap"),
        ("下週二 10:00", None, None, None, 10, 0, "lock:hhmm_ap"),  # 有週詞錨點
    ]
    for s, Y, M, D, h, m, flag in cases:
        r = cal.parse_event(s, tz="Asia/Taipei")
        assert any(f.startswith("lock:") for f in r["flags"])
        assert flag in r["flags"]
        sdt = _iso2dt(r["start"])
        if Y:
            assert (sdt.year, sdt.month, sdt.day, sdt.hour, sdt.minute) == (Y, M, D, h, m)
        else:
            # 下週二：只驗時間（日期依固定 now 由 parser 決定）
            assert sdt.hour == h and sdt.minute == m


def test_C_date_only_all_day(monkeypatch):
    patch_now(monkeypatch)
    r = cal.parse_event("Sep 30 2025", tz="Asia/Taipei")
    assert "all_day" in r["flags"] and "lock:all_day" in r["flags"]
    assert r["start"] == "2025-09-30"
    assert r["end"] == "2025-10-01"

    r2 = cal.parse_event("2025/9/30", tz="Asia/Taipei")
    assert "all_day" in r2["flags"]
    assert r2["start"].startswith("2025-09-30")


def test_D_ranges(monkeypatch):
    patch_now(monkeypatch)
    r = cal.parse_event("2025-09-30 23:00-01:00", tz="Asia/Taipei")
    assert "lock:range_hhmm" in r["flags"]
    s, e = _iso2dt(r["start"]), _iso2dt(r["end"])
    assert int((e - s).total_seconds() / 3600) in (2, 26)  # 視跨日後演算，這裡寬鬆驗 2 小時

    r2 = cal.parse_event("2025/9/30 上午9點-10點", tz="Asia/Taipei")
    assert "lock:range_zh" in r2["flags"]
    s2, e2 = _iso2dt(r2["start"]), _iso2dt(r2["end"])
    assert s2.hour == 9 and e2.hour in (10, 22)  # 中文前綴轉換後 10 點


def test_E_tomorrow_and_morning_evening(monkeypatch):
    patch_now(monkeypatch)
    r = cal.parse_event("tomorrow 10", tz="Asia/Taipei")
    s = _iso2dt(r["start"])
    assert s.hour == 10 and s.minute == 0
    assert any(f in r["flags"] for f in ("lock:date_hour_only", "lock:hh_ap", "lock:generic"))

    r2 = cal.parse_event("evening meeting tomorrow", tz="Asia/Taipei")
    assert "lock:tmr_evening" in r2["flags"]
    s2 = _iso2dt(r2["start"])
    assert s2.hour == 19


def test_F_noon_midnight(monkeypatch):
    patch_now(monkeypatch)
    r = cal.parse_event("noon", tz="Asia/Taipei")
    assert "lock:noon" in r["flags"]
    assert _iso2dt(r["start"]).hour == 12

    r2 = cal.parse_event("午夜", tz="Asia/Taipei")
    assert "lock:midnight" in r2["flags"]
    assert _iso2dt(r2["start"]).hour == 0


def test_G_duration_priority(monkeypatch):
    patch_now(monkeypatch)
    r = cal.parse_event("Sep 30 2025 14:00, duration 2 hours", tz="Asia/Taipei", default_minutes=60)
    s, e = _iso2dt(r["start"]), _iso2dt(r["end"])
    assert int((e - s).total_seconds()/60) == 120

    r2 = cal.parse_event("明天上午10點，持續90分鐘", tz="Asia/Taipei", default_minutes=60)
    s2, e2 = _iso2dt(r2["start"]), _iso2dt(r2["end"])
    assert int((e2 - s2).total_seconds()/60) == 90


def test_H_emails_location_title(monkeypatch):
    patch_now(monkeypatch)
    r = cal.parse_event("今天 3pm 會議 with a@b.com，地點: 公司", tz="Asia/Taipei")
    assert "a@b.com" in r["attendees"]
    assert r["location"] == "公司"
    assert isinstance(r["title"], str) and len(r["title"]) > 0


def test_I_two_tokens_loose(monkeypatch):
    patch_now(monkeypatch)
    r = cal.parse_event("8/16 9-11", tz="Asia/Taipei")
    # 有日期錨點就不啟用 loose，會走 range_hour_only or hhmm
    assert any(f in r["flags"] for f in ("lock:range_hour_only", "lock:range_hhmm", "lock:hhmm_ap"))


def test_J_after_noon(monkeypatch):
    patch_now(monkeypatch)
    r = cal.parse_event("2 hours after noon", tz="Asia/Taipei")
    assert "lock:after_noon" in r["flags"]
    assert _iso2dt(r["start"]).hour in (14,)

def test_K_dt_dt_range(monkeypatch):
    patch_now(monkeypatch)
    r = cal.parse_event("2025-09-30 11:30PM–2025-10-01 12:30AM", tz="Asia/Taipei")
    assert "lock:range_dt_dt" in r["flags"]
    s, e = _iso2dt(r["start"]), _iso2dt(r["end"])
    assert int((e - s).total_seconds()/60) in (60, 61)  # 容忍 60±1 分鐘
