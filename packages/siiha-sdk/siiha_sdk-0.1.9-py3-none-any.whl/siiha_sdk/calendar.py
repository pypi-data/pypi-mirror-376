# src/siiha_sdk/calendar.py
from __future__ import annotations
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import re
import pytz
from dateutil.parser import isoparse

from dateutil.relativedelta import relativedelta

from siiha_sdk.auth import get_calendar_service
from siiha_sdk.utils import cleanse_text, normalize_attendees
from siiha_sdk.config import DEFAULT_TIMEZONE, DEFAULT_CALENDAR_ID, GOOGLE_SEND_UPDATES

# =========================
# Google Calendar helpers
# =========================

print("[siiha-sdk] calendar.py loaded ver:A21-hotfix1-6")

# --- module globals ---
# 測試可 monkeypatch 這個，回傳一個 *aware* datetime（例如固定時間）
NOW_PROVIDER = None
_LAST_NOW_SOURCE = [None]

def _tz(tz_str: Optional[str]) -> pytz.BaseTzInfo:
    return pytz.timezone(tz_str or DEFAULT_TIMEZONE)

def _detect_user_timezone(service=None) -> Optional[str]:
    """盡力從使用者的 Google 設定/行事曆偵測時區。失敗回 None。"""
    try:
        svc = service or get_calendar_service()
        try:
            v = svc.settings().get(setting='timezone').execute()
            if v and v.get('value'):
                return v['value']
        except Exception:
            pass
        try:
            cl = svc.calendarList().get(calendarId=DEFAULT_TIMEZONE if '@' in DEFAULT_TIMEZONE else DEFAULT_CALENDAR_ID).execute()
            if cl and cl.get('timeZone'):
                return cl['timeZone']
        except Exception:
            pass
    except Exception:
        pass
    return None

def _effective_tz(tz_str: Optional[str], service=None) -> str:
    """時區來源優先序：呼叫者帶入 > 使用者日曆偵測 > DEFAULT_TIMEZONE"""
    return tz_str or _detect_user_timezone(service) or DEFAULT_TIMEZONE

def _now(tz: str) -> datetime:
    TZZ = pytz.timezone(tz)

    if NOW_PROVIDER is not None:
        n = NOW_PROVIDER() if callable(NOW_PROVIDER) else NOW_PROVIDER
        src = "NOW_PROVIDER"
    else:
        n, src = None, None

        # 1) 先試本模組命名空間（pytest 多半 patch 這個）
        if n is None:
            cand = globals().get("datetime", None)
            if cand is not None:
                dt_cls = getattr(cand, "datetime", cand)  # class or module
                if hasattr(dt_cls, "now"):
                    try:
                        n = dt_cls.now()     # 無參 now()，讓 monkeypatch 接得住
                        src = "cal.datetime"
                    except Exception:
                        n = None

        # 2) 再試 stdlib（若沒 patch 到這個再用）
        if n is None:
            try:
                import datetime as _sysdt
                dt_cls = getattr(_sysdt, "datetime", None)
                if dt_cls and hasattr(dt_cls, "now"):
                    try:
                        n = dt_cls.now()     # 無參 now()
                        src = "stdlib.datetime"
                    except Exception:
                        n = None
            except Exception:
                n = None

        # 3) 最後保底
        if n is None:
            import datetime as _sysdt
            n = _sysdt.datetime.now()
            src = "fallback.now()"

    # 時區一致化
    n = TZZ.localize(n) if n.tzinfo is None else n.astimezone(TZZ)
    try:
        _LAST_NOW_SOURCE[0] = src
    except Exception:
        pass
    return n

def _norm_title(s: Optional[str]) -> str:
    """標題正規化：trim / 合併空白 / 統一逗號 / 英文大小寫無關"""
    if not s:
        return ""
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    s = s.replace("，", ",")
    s = re.sub(r"\s*,\s*", ", ", s)
    return s.casefold()

def _same_instant(a_iso: str, b_iso: str) -> bool:
    """兩個 RFC3339 是否指向同一瞬間（跨時區也成立）"""
    try:
        return isoparse(a_iso) == isoparse(b_iso)
    except Exception:
        return False

def _day_window(start_iso: str, tz_str: Optional[str]) -> tuple[str, str]:
    """在目標時區展開該天的整日窗口（避免 Z 導致 UTC 偏移）。"""
    dt = isoparse(start_iso)                       # aware datetime
    dt_local = dt.astimezone(_tz(tz_str))         # 轉成本地時區再切日界
    start_of_day = dt_local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    return start_of_day.isoformat(), end_of_day.isoformat()

def find_existing_event(service, title: str, start_iso: str, tz_str: Optional[str]) -> Optional[Dict]:
    """同一天窗內：『同一瞬間』且『標題正規化後相等』→ 視為重複。"""
    tmin, tmax = _day_window(start_iso, tz_str)
    want_title = _norm_title(title)

    res = service.events().list(
        calendarId=DEFAULT_CALENDAR_ID,
        q=want_title,                 # 只作為篩選提示；實際仍做嚴格比對
        timeMin=tmin,
        timeMax=tmax,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    for e in res.get("items", []):
        e_start_iso = e.get("start", {}).get("dateTime")
        if not e_start_iso:
            # 跳過全日事件（若未來要支援，再另開邏輯）
            continue
        same = _same_instant(e_start_iso, start_iso)
        same_title = _norm_title(e.get("summary")) == want_title
        if same and same_title:
            return e
    return None

def create_calendar_event(
    title: str,
    start_iso: str,
    end_iso: str,
    location: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    description: Optional[str] = None,
    timezone: str = DEFAULT_TIMEZONE,
    dedupe: bool = True,
) -> Dict:
    """
    Create a Google Calendar event (local OAuth).
    Assumes start_iso/end_iso are RFC3339 strings WITH timezone.
    """
    try:
        service = get_calendar_service()
        timezone = _effective_tz(timezone, service)

        title = cleanse_text(title) or ""
        location = cleanse_text(location)
        description = cleanse_text(description)
        attendees = normalize_attendees(attendees)

        if dedupe:
            existing = find_existing_event(service, title, start_iso, timezone)
            if existing:
                return {
                    "ok": True,
                    "eventId": existing["id"],
                    "htmlLink": existing.get("htmlLink"),
                    "start": existing["start"].get("dateTime"),
                    "end": existing["end"].get("dateTime"),
                    "attendees": [a["email"] for a in existing.get("attendees", [])],
                    "timezone": timezone,
                    "deduped": True,
                }

        body = {
            "summary": title,
            "location": location,
            "description": description,
            "start": {"dateTime": start_iso, "timeZone": timezone},
            "end": {"dateTime": end_iso, "timeZone": timezone},
        }
        if attendees:
            body["attendees"] = [{"email": e} for e in attendees]

        event = service.events().insert(
            calendarId=DEFAULT_CALENDAR_ID,
            body=body,
            sendUpdates=GOOGLE_SEND_UPDATES,
        ).execute()

        return {
            "ok": True,
            "eventId": event["id"],
            "htmlLink": event.get("htmlLink"),
            "start": event["start"].get("dateTime"),
            "end": event["end"].get("dateTime"),
            "attendees": [a["email"] for a in event.get("attendees", [])],
            "timezone": timezone,
            "deduped": False,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

# =========================
# Natural language parsing
# =========================
import json
from dateutil import parser as dateparser

MIN_DUR, MAX_DUR = 5, 180
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

# --- title tidy（沿用你現有，細部調整略） ---
_TITLE_TRASH_PREFIX = re.compile(
    r'(?i)^\s*(?:now|next|this|today|tomorrow|tmr|'
    r'(?:next|this)\s+(?:mon|tue|wed|thu|fri|sat|sun|monday|tuesday|wednesday|thursday|friday|saturday|sunday))'
    r'\s*[:：,\-–—]*\s*'
)
_TITLE_VERB_PREFIX = re.compile(
    r'(?i)^\s*(?:create|add|schedule|set\s*up|安排|建立|新增|排(?:會議|行程)?)\s+'
    r'(?:a\s+)?(?:calendar\s+)?(?:event|meeting)\s*:?-?\s*|^\s*(?:create|add|schedule|set\s*up|安排|建立|新增|排(?:會議|行程)?)\s*'
)
_TITLE_INVITE_TAIL  = re.compile(r'(?i)[,;，；]\s*(?:invite|invites?|邀請|受邀)\b.*$')
_TITLE_TIME_CHUNKS  = re.compile(
    r'(?i)\b(?:'
    r'(?:\d{4}[/-]\d{1,2}[/-]\d{1,2})|'
    r'(?:\d{1,2}/\d{1,2}(?:/\d{2,4})?)|'
    r'(?:\d{1,2}:[0-5]\d)|'
    r'(?:\d{1,2}(:[0-5]\d)?\s*(?:am|pm))|'
    r'(?:\d{1,2}(:[0-5]\d)?\s*[-–—]\s*\d{1,2}(:[0-5]\d)?\s*(?:am|pm)?)|'
    r'(?:\b[0-2]?\d\s*[-–—]\s*[0-2]?\d\b)|'
    r'(?:from\s+\d{1,2}(:[0-5]\d)?\s*(?:am|pm)?\s*[-–—]\s*\d{1,2}(:[0-5]\d)?\s*(?:am|pm)?)|'
    r'(?:at\s+\d{1,2}(:[0-5]\d)?\s*(?:am|pm)?)'
    r')\b'
)
_TITLE_MONTH_WORDS = re.compile(r'(?i)\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\b\s*\d{0,2}(?:,\s*\d{2,4}|\s+\d{2,4})?')
_TITLE_DAY_WORDS_ZH = re.compile(r"(今天|明天|後天|本週|這週|下週[一二三四五六日天]?|週[一二三四五六日天]|星期[一二三四五六日天]|禮拜[一二三四五六日天])")
_TITLE_DAY_WORDS_EN = re.compile(r'(?i)\b(mon|tue|wed|thu|fri|sat|sun|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b')
_TITLE_AT_LOC = re.compile(r'(?i)\s*(?:,| |，)?\s*(?:at|@|在|於)\s+[^\s,，。]+$')
# 新增：移除「下個月/本月/這個月 + 幾號」這種中文日期殘留，避免 title 不當殘留
_TITLE_ZH_MONTHDAY = re.compile(r"(下個?月|本月|這個?月|這月)\s*[一二兩三四五六七八九十\d]{1,2}\s*號")
 
_TITLE_REL_PHRASES = re.compile(
    r'(?i)\b(?:'
    r'in\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*'
    r'(?:hours?|hrs?|minutes?|mins?|days?|weeks?)'
    r'|for\s+\d+\s*(?:hours?|hrs?|minutes?|mins?)'
    r')\b'
    r'|[一二兩三四五六七八九十\d]+\s*(?:小時半|小時|分鐘|天|週)'
)

_TITLE_DURATION_PHRASES = re.compile(
    r'(?i)\b(?:duration|for)\s*[:：]?\s+\d+(?:\.\d+)?\s*(?:hours?|hrs?|minutes?|mins?)\b'
    r'|(?:持續)\s*[:：]?\s*[一二兩三四五六七八九十\d]+(?:\.\d+)?\s*(?:小時半|小時|分鐘)'
)
_TITLE_ZH_TIME = re.compile(
    r'(早上|上午|下午|晚上|晚間|夜間|凌晨|中午)?\s*'
    r'([一二兩三四五六七八九十\d]{1,2})(?:[:：]([0-5]\d))?\s*點(?:半|([0-5]\d)分)?',
    re.I
)
_TITLE_ZH_RANGE = re.compile(
    r'(?:'
    r'(早上|上午|下午|晚上|晚間|夜間|凌晨|中午)?\s*[一二兩三四五六七八九十\d]{1,2}(?:[:：][0-5]\d)?\s*點(?:半|[0-5]\d分)?'
    r')\s*(?:到|至|~|—|–|-)\s*(?:'
    r'(早上|上午|下午|晚上|晚間|夜間|凌晨|中午)?\s*[一二兩三四五六七八九十\d]{1,2}(?:[:：][0-5]\d)?\s*點(?:半|[0-5]\d分)?'
    r')',
    re.I
)
_TITLE_NUMERIC_ONLY = re.compile(r'^\s*\d+(?:\.\d+)?\s*$')
_TITLE_LEADING_PLUS = re.compile(r'^(?:\s*[+＋]\s*\d+(?:\.\d+)?\s*(?:minutes?|mins?|hours?|hrs?|分鐘|小時)\b[ ,，：:;；\-\u2013\u2014]*)+', re.I)
_TITLE_LEADING_DURATION = re.compile(
    r'^(?:\s*(?:\d+(?:\.\d+)?\s*(?:minutes?|mins?|hours?|hrs?)|[一二兩三四五六七八九十\d]+(?:\.\d+)?\s*(?:分鐘|小時))(?=$|[\s,，：:;；\-\u2013\u2014!！]))+',
    re.I
)
_TITLE_NOW_ADD = re.compile(r'(?i)\bnow\s*[\+\uFF0B]\s*\d+(?:\.\d+)?\s*(?:minutes?|mins?|hours?|hrs?)\b')
_TITLE_FROM_NOW_LATER = re.compile(
    r'(?i)\b(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*'
    r'(?:minutes?|mins?|hours?|hrs?|days?|weeks?)\s*(?:from\s+now|later)\b'
    r'|[一二兩三四五六七八九十\d]+(?:\.\d+)?\s*(?:分鐘|小時|天|週)後'
    r'|[一二兩三四五六七八九十\d]+\s*個?\s*半\s*小時後'
)
_TITLE_LABEL_FIELDS = re.compile(r'(?i)\b(?:start|end|開始|結束|title)\s*[:：]\s*[^\n,;，；]+')
_TITLE_TRAILING_WITH = re.compile(r"[,\s，；;]*\bwith\b\s*$", re.I)

def tidy_title(title: str, idea_text: str = "") -> str:
    s = (title or "").strip().strip('"\'')
    if not s:
        s = (idea_text or "").strip()
    s = EMAIL_RE.sub("", s)
    s = _TITLE_LABEL_FIELDS.sub("", s)
    s = _TITLE_LEADING_PLUS.sub("", s)
    s = _TITLE_TRASH_PREFIX.sub("", s)
    s = _TITLE_VERB_PREFIX.sub("", s)
    s = _TITLE_INVITE_TAIL.sub("", s)
    s = _TITLE_TIME_CHUNKS.sub("", s)
    s = _TITLE_MONTH_WORDS.sub("", s)
    s = _TITLE_DAY_WORDS_ZH.sub("", s)
    s = _TITLE_DAY_WORDS_EN.sub("", s)
    s = _TITLE_REL_PHRASES.sub("", s)
    s = _TITLE_DURATION_PHRASES.sub("", s)
    s = _TITLE_ZH_RANGE.sub("", s)
    s = _TITLE_ZH_TIME.sub("", s)
    s = _TITLE_NOW_ADD.sub("", s)
    s = _TITLE_FROM_NOW_LATER.sub("", s)
    s = _TITLE_ZH_MONTHDAY.sub("", s)
    s = _TITLE_AT_LOC.sub("", s)
    s = re.sub(r"(?i)\bwith\b\s*(?:[,，；;]*)\s*(?=$|(?:地點|location|attendees?|invite|邀請|受邀|title|標題)\b)", "", s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[,\，；;]\s*(?=[,\，；;])", "", s)
    s = _TITLE_TRAILING_WITH.sub("", s)
    s = re.sub(r"[,\s，；;]*?\b(with|to|at)\b\s*$", "", s, flags=re.I)
    s = re.sub(r"[,\s，；;]*?[給在於和跟]\s*$", "", s)
    s = re.sub(r"[\(\)（）\[\]【】{}]", "", s)
    s = re.sub(r"(?i)\bnow\b|現在|此刻", "", s)
    s = re.sub(r"(?i)\bmidnight\b|午夜", "", s)
    s = re.sub(r"(?i)\b(?:after|before)\s+noon\b", "", s)
    s = re.sub(r"(?i)\b(?:this|next)\s+week\b", "", s)
    s = re.sub(r"(?:持續|duration|for)\s*$", "", s, flags=re.I)
    s = re.sub(r"(?i)\bweek\b", "", s)
    for _ in range(2):
        s = _TITLE_LEADING_PLUS.sub("", s)
        s = _TITLE_LEADING_DURATION.sub("", s)
    s = s.replace("+", " ").replace("＋", " ")
    s = s.strip(" .,，。．;；-–—!！")
    if _TITLE_NUMERIC_ONLY.fullmatch(s or ""):
        s = "Meeting"
    _TIMEY = re.compile(
        r'^(?:\s*(?:today|tomorrow|tmr|this|next|week|later|mon|tue|wed|thu|fri|sat|sun|'
        r'meeting|morning|afternoon|evening|night|noon|midnight|'
        r'今天|明天|後天|本週|這週|下週|週[一二三四五六日天]|星期[一二三四五六日天]|禮拜[一二三四五六日天]|'
        r'明早|明晚|今晚|早上|上午|下午|晚上|晚間|夜間|凌晨|中午|會議|開會)\s*)+$',        
        re.I
    )
    if not s or _TIMEY.fullmatch(s.strip()):
        s = "Meeting"
    if re.fullmatch(r'(?i)\s*(meeting|會議|開會)\s*', s or ""):
        s = "Meeting"
    if not s or re.fullmatch(r"(?i)(now|later|minute|minutes|min|hour|hours|hr|hrs|後)", s):
        if _TITLE_NOW_ADD.search(idea_text) or _TITLE_FROM_NOW_LATER.search(idea_text):
            s = "專注時段" if re.search(r"(分鐘|小時|現在|此刻|後)", idea_text) else "Focus block"
    return (s or "Meeting")[:80]

# --- generic helpers（純函式） ---
_TIME_ONLY = re.compile(r'(?i)^\s*\d{1,2}(:[0-5]\d)?\s*(?:am|pm)?\s*$')
_DATE_TOKEN = re.compile(
    r'(?i)\b(today|tomorrow|tmr|day\s+after\s+tomorrow|this|next|'
    r'mon|tue|wed|thu|fri|sat|sun|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b'
    r'|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'
    r'|\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b'
    r'|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\b'
    r'|(?:\d{4}年\d{1,2}月\d{1,2}日)'
    r'|(?:\d{1,2}月\d{1,2}日)'
    r'|(?:下|本|這)?(?:週|周|星期|禮拜)[一二三四五六日天]'
)

def looks_like_time_string(s: str) -> bool:
    return bool(s and _TIME_ONLY.match(s.strip()))

def has_explicit_date(text: str) -> bool:
    return bool(text and _DATE_TOKEN.search(text))

_ZH_NUM = {"零":0,"一":1,"二":2,"兩":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10}
def _zh_to_int(s: str) -> int:
    if not s: return 0
    if s.isdigit(): return int(s)
    if "十" in s:
        a,b = s.split("十", 1)
        tens = _ZH_NUM.get(a, 1 if a=="" else 0)
        ones = _ZH_NUM.get(b, 0) if b != "" else 0
        return tens*10 + ones
    return _ZH_NUM.get(s, 0)

_WORD_NUM = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10,"eleven":11,"twelve":12}
def _en_word_to_int(tok: str) -> Optional[int]:
    if not tok: return None
    t = tok.lower().strip()
    return _WORD_NUM.get(t)

_REL_PATS = [
    re.compile(r"\bin\s+(\d+)\s*(minutes?|mins?)\b", re.I),
    re.compile(r"\bin\s+(\d+)\s*(hours?|hrs?)\b", re.I),
    re.compile(r"\bin\s+(\d+)\s*(days?)\b", re.I),
    re.compile(r"\bin\s+(\d+)\s*(weeks?)\b", re.I),
    re.compile(r"\b(\d+)\s*(minutes?|mins?)\s+later\b", re.I),
    re.compile(r"\b(\d+)\s*(hours?|hrs?)\s+later\b", re.I),
    re.compile(r"\b(\d+)\s*(days?)\s+later\b", re.I),
    re.compile(r"\b(\d+)\s*(weeks?)\s+later\b", re.I),
    re.compile(r"([一二兩三四五六七八九十]+)\s*分鐘後"),
    re.compile(r"([一二兩三四五六七八九十]+)\s*小時後"),
    re.compile(r"([一二兩三四五六七八九十]+)\s*天後"),
    re.compile(r"([一二兩三四五六七八九十]+)\s*週後"),
]

NOW_PLUS       = re.compile(r"(?i)\bnow\s*[\+\uFF0B]\s*(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?)\b")
FROM_NOW       = re.compile(r"(?i)\b(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?)\s*(?:from\s+)?now\b")
ZH_NOW_PLUS    = re.compile(r"(?:現在|此刻)\s*[\+\uFF0B加]\s*([一二兩三四五六七八九十\d]+(?:\.\d+)?)\s*(分鐘|小時)")
LATER_EN       = re.compile(r"(?i)\b\d+(?:\.\d+)?\s*(?:minutes?|mins?|hours?|hrs?)\s+later\b")
LATER_ZH       = re.compile(r"(?:[一二兩三四五六七八九十\d]+(?:\.\d+)?)\s*(分鐘|小時)後")
LATER_ZH_HALF  = re.compile(r"(?:([一二兩三四五六七八九十\d]+))\s*個?\s*半\s*小時後")

_ONLY_HHMM = re.compile(r'^\s*([0-2]?\d):([0-5]\d)\s*$')
_SIMPLE_RANGE_HH = re.compile(r'\b([01]?\d|2[0-3])\s*[-–—~]\s*([01]?\d|2[0-3])\b')
_HOUR_RANGE = re.compile(r'(?<!\d)(?<!-)\b([01]?\d|2[0-3])\s*[-–—~]\s*([01]?\d|2[0-3])\b(?!-)(?!\d)')
_ONLY_HH = re.compile(r'^\s*([0-2]?\d)\s*(am|pm)?\s*$', re.I)
_ANY_ONLY_HH = re.compile(r'(?<!\d)([01]?\d|2[0-3])(?!\s*[:\d])', re.I)
_TIME_TOK  = re.compile(r'\b([01]?\d|2[0-3])(?::([0-5]\d))?\s*(am|pm)?\b', re.I)

_EXPLICIT_DT_HHMM = re.compile(r'(?i)\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})[ T](\d{1,2}):([0-5]\d)\s*(am|pm)?\b')
_EXPLICIT_HHMM_AP = re.compile(r'(?i)\b([0-2]?\d):([0-5]\d)\s*(am|pm)\b')
_EXPLICIT_HHMM    = re.compile(r'(?i)\b([0-2]?\d):([0-5]\d)\b')  # 無 ap 的 HH:MM
_HAS_EXPLICIT_DATE = re.compile(
    r'(?i)(\d{4}[/-]\d{1,2}[/-]\d{1,2})|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\b|\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b'
)
_EXPLICIT_HH_AP   = re.compile(r'(?i)\b([0-1]?\d)\s*(am|pm)\b')

_ZH_PM_TO_AM = re.compile(r'(晚上|晚間|夜間)\s*([0-1]?\d|2[0-3])\s*點.*?(?:到|至|~|—|-)\s*凌晨\s*([0-1]?\d)\s*點')
_ZH_SINGLE_TIME = re.compile(
    r'(早上|上午|下午|晚上|晚間|夜間|凌晨|中午)\s*'
    r'([一二兩三四五六七八九十\d]{1,2})(?:[:：]([0-5]\d))?\s*點', re.I)
_ZH_RANGE = re.compile(
    r'(?:'
    r'(早上|上午|下午|晚上|晚間|夜間|凌晨|中午)?\s*([一二兩三四五六七八九十\d]{1,2})(?:[:：]([0-5]\d))?\s*點'
    r')\s*(?:到|至|~|—|–|-)\s*'
    r'(?:'
    r'(早上|上午|下午|晚上|晚間|夜間|凌晨|中午)?\s*([一二兩三四五六七八九十\d]{1,2})(?:[:：]([0-5]\d))?\s*點'
    r')',
    re.I
)

_LATER_THIS = re.compile(r'(?i)\blater\s+this\s+(morning|afternoon|evening|night)\b')
_NOON_WORDS = re.compile(r'(?i)\bnoon\b|中午')
_MIDNIGHT_WORDS = re.compile(r'(?i)\bmidnight\b|午夜')
_EVENING_TMR = re.compile(r'(?i)\bevening\s+.*\btomorrow\b|明天.*(晚上|晚間|夜間)')
_MORNING_TMR = re.compile(r'(?i)\bmorning\s+.*\btomorrow\b|明天.*(早上|上午|清晨)')

_DT_DT_RANGE = re.compile(
    r'(?P<a>\d{4}-\d{2}-\d{2}[ T]\d{1,2}:\d{2}(?:\s*(?:AM|PM|am|pm)?)?)\s*[–—\-~]\s*'
    r'(?P<b>\d{4}-\d{2}-\d{2}[ T]\d{1,2}:\d{2}(?:\s*(?:AM|PM|am|pm)?)?)'
)

def _strip_duration_phrases(s: str) -> str:
    if not s: return s
    out = re.sub(r'(?i)\b(duration|for)\s+\d+(?:\.\d+)?\s*(hours?|hrs?|minutes?|mins?)\b', ' ', s)
    out = re.sub(r'(?i)\bfor\s+\d+(?:\.\d+)?\s*(hours?|hrs?|minutes?|mins?)\b', ' ', out)
    out = re.sub(r'(持續)\s*[一二兩三四五六七八九十\d]+(?:\.\d+)?\s*(小時半|小時|分鐘)', ' ', out)
    return out

def _has_time_token(s: str) -> bool:
    if not s:
        return False
    if _NOON_WORDS.search(s) or _MIDNIGHT_WORDS.search(s) or _ZH_SINGLE_TIME.search(s):
        return True
    if re.search(r'(?i)\b([01]?\d|2[0-3]):([0-5]\d)\b', s):
        return True
    if re.search(r'(?i)\b([0-1]?\d)\s*(am|pm)\b', s):
        return True
    return False

def _contains_relative_day(s: str) -> bool:
    return bool(
        re.search(r'(?i)\b(tomorrow|day\s+after\s+tomorrow|in\s+\d+\s*(days?|weeks?))\b', s)
        or re.search(r'(?i)\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(weeks?|days?)\s+later\b', s)
        or re.search(r'明天|後天|下個?月|[一二兩三四五六七八九十\d]+\s*(天|週|周)後', s)
    )

def _bucket_to_hour(tag: Optional[str]) -> int:
    if not tag: return 9
    t = tag.lower() if isinstance(tag, str) else tag
    if t in ('morning','早上','上午','清晨'): return 9
    if t in ('afternoon','下午'): return 15
    if t in ('evening','night','晚上','晚間','夜間'): return 19
    if t in ('noon','中午'): return 12
    if t in ('midnight','午夜','凌晨'): return 0
    return 9

def _zh_hour_to_24(prefix: Optional[str], hh: int) -> int:
    tag = (prefix or '').lower()
    if tag in ('下午','晚上','晚間','夜間') and 1 <= hh <= 11:
        return hh + 12
    if tag in ('凌晨',) and hh == 12:
        return 0
    if tag in ('中午',):
        return 12 if hh == 12 else (hh + 12 if 1 <= hh <= 11 else hh)
    if tag in ('上午','早上','清晨'):
        return 0 if hh == 12 else hh
    return hh

def _weekday_from_zh(ch: str) -> int:
    table = {'一':0,'二':1,'三':2,'四':3,'五':4,'六':5,'日':6,'天':6}
    return table.get(ch, 0)

def _find_anchor_date(text: str, tz: str, base_now: Optional[datetime] = None) -> Optional[datetime]:
    """找出字串中的『日期錨』（不含時間）。回傳當地時區該日 00:00（aware）。"""
    if not text: return None
    TZZ = pytz.timezone(tz)
    now_local = (base_now.astimezone(TZZ) if (base_now and base_now.tzinfo) else _now(tz))
    base = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    s = text
 
    # 中文今天（保留，修 18）
    if re.search(r'今天', s):
        return base

    # 新增：this <weekday> / next <weekday>
    m_this = re.search(r'(?i)\bthis\s+(mon|tue|wed|thu|fri|sat|sun|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', s)
    if m_this:
        wd_map = {'mon':0,'monday':0,'tue':1,'tuesday':1,'wed':2,'wednesday':2,'thu':3,'thursday':3,'fri':4,'friday':4,'sat':5,'saturday':5,'sun':6,'sunday':6}
        tgt = wd_map[m_this.group(1).lower()]
        start_of_week = base - timedelta(days=base.weekday())  # 週一為 0
        anchor = start_of_week + timedelta(days=tgt)
        # 若今天就是該週幾，為避免落到今日，往下一週
        if base.weekday() == tgt:
            anchor = anchor + timedelta(days=7)
        return anchor
    m_next = re.search(r'(?i)\bnext\s+(mon|tue|wed|thu|fri|sat|sun|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', s)
    if m_next:
        wd_map = {'mon':0,'monday':0,'tue':1,'tuesday':1,'wed':2,'wednesday':2,'thu':3,'thursday':3,'fri':4,'friday':4,'sat':5,'saturday':5,'sun':6,'sunday':6}
        tgt = wd_map[m_next.group(1).lower()]
        start_next = base - timedelta(days=base.weekday()) + timedelta(days=7)
        return start_next + timedelta(days=tgt)

    # 允許日期後緊接中文（例如：2025-09-30上午10點），移除 \b，改用不與數字黏連的 lookaround
    m = re.search(r'(?<!\d)(\d{4})[/-](\d{1,2})[/-](\d{1,2})(?!\d)', s)    
    if m:
        y,mn,d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return base.replace(year=y, month=mn, day=d)
    # 同理，月/日(/年) 也放寬邊界，避免被相鄰中文字卡住
    m = re.search(r'(?<!\d)(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?(?!\d)', s)    
    if m:
        mn, d = int(m.group(1)), int(m.group(2))
        y = int(m.group(3)) if m.group(3) else now_local.year
        if y < 100: y += 2000
        return base.replace(year=y, month=mn, day=d)
    m = re.search(r'(?i)\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\b[^0-9]*(\d{1,2})(?:[^0-9]+(\d{4}))?', s)
    if m:
        dt = dateparser.parse(' '.join(filter(None, [m.group(1), m.group(2), m.group(3) or str(now_local.year)])),
                              fuzzy=True, default=base)
        return TZZ.localize(dt.replace(hour=0, minute=0, second=0, microsecond=0)) if dt.tzinfo is None else dt.replace(hour=0, minute=0, second=0, microsecond=0)
    m = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', s)
    if m:
        return base.replace(year=int(m.group(1)), month=int(m.group(2)), day=int(m.group(3)))
    m = re.search(r'(\d{1,2})月(\d{1,2})日', s)
    if m:
        return base.replace(month=int(m.group(1)), day=int(m.group(2)))
    m = re.search(r'下個?月([一二兩三四五六七八九十\d]{1,2})號', s)
    if m:
        day = _zh_to_int(m.group(1)) if not m.group(1).isdigit() else int(m.group(1))
        dt = (base + relativedelta(months=+1))
        return dt.replace(day=min(day, 28))
    m = re.search(r'(下|本|這)?(?:週|周|星期|禮拜)([一二三四五六日天])', s)
    if m:
        kind, wd = m.group(1) or '', m.group(2)
        today = base.weekday()
        target = _weekday_from_zh(wd)
        start_of_week = base - timedelta(days=today)
        if kind == '下':
            start_of_week += timedelta(days=7)
        anchor = start_of_week + timedelta(days=target)
        return anchor
    m = re.search(r'(?i)\bnext\s+week\s+(mon|tue|wed|thu|fri|sat|sun|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', s)
    if m:
        wd_map = {'mon':0,'monday':0,'tue':1,'tuesday':1,'wed':2,'wednesday':2,'thu':3,'thursday':3,'fri':4,'friday':4,'sat':5,'saturday':5,'sun':6,'sunday':6}
        target = wd_map[m.group(1).lower()]
        start_next = base - timedelta(days=base.weekday()) + timedelta(days=7)
        return start_next + timedelta(days=target)
    if re.search(r'(?i)\bday\s+after\s+tomorrow\b|後天', s):
        return base + timedelta(days=2)
    if re.search(r'(?i)\btomorrow\b|明天', s):
        return base + timedelta(days=1)
    md = re.search(r'(?i)\bin\s+(\d+)\s*days?\b', s)
    if md: return base + timedelta(days=int(md.group(1)))
    mw = re.search(r'(?i)\bin\s+(\d+)\s*weeks?\b', s)
    if mw: return base + timedelta(weeks=int(mw.group(1)))
    mwd = re.search(r'(?i)\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+days?\s+later\b', s)
    if mwd:
        a = mwd.group(1)
        n = int(a) if a.isdigit() else (_en_word_to_int(a) or 0)
        return base + timedelta(days=n)
    mww = re.search(r'(?i)\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+weeks?\s+later\b', s)
    if mww:
        a = mww.group(1)
        n = int(a) if a.isdigit() else (_en_word_to_int(a) or 0)
        return base + timedelta(weeks=n)  
    mdz = re.search(r'([一二兩三四五六七八九十\d]+)\s*天後', s)
    if mdz: return base + timedelta(days=_zh_to_int(mdz.group(1)))
    mwz = re.search(r'([一二兩三四五六七八九十\d]+)\s*週後', s)
    if mwz: return base + timedelta(weeks=_zh_to_int(mwz.group(1)))
    return None

def _rewrite_relative_to_absolute_date(raw: str, tz: str, base_now: Optional[datetime] = None) -> Tuple[str, bool]:
    """把 'in 2 days 10AM' / '兩天後10點' 類型改寫成具體日期字串；回傳 (新字串, 是否改寫)。"""
    if not raw: return raw, False
    TZZ = pytz.timezone(tz)
    _n = (base_now.astimezone(TZZ) if (base_now and base_now.tzinfo) else _now(tz))
    base = _n.replace(hour=0, minute=0, second=0, microsecond=0)
    s = raw
    changed = False
    def repl_days(m):
        nonlocal changed
        d = int(m.group(1)); dt = base + timedelta(days=d); changed = True
        return dt.strftime('%Y-%m-%d')
    def repl_weeks(m):
        nonlocal changed
        w = int(m.group(1)); dt = base + timedelta(weeks=w); changed = True
        return dt.strftime('%Y-%m-%d')
    s2 = re.sub(r'(?i)\bin\s+(\d+)\s*days?\b', repl_days, s)
    s2 = re.sub(r'(?i)\bin\s+(\d+)\s*weeks?\b', repl_weeks, s2)
    def mark(v, repl):
        return repl if v else None
    if re.search(r'(?i)\btomorrow\b', s2):
        s2 = re.sub(r'(?i)\btomorrow\b', (base + timedelta(days=1)).strftime('%Y-%m-%d'), s2); changed = True
    if re.search(r'(?i)\bday\s+after\s+tomorrow\b', s2):
        s2 = re.sub(r'(?i)\bday\s+after\s+tomorrow\b', (base + timedelta(days=2)).strftime('%Y-%m-%d'), s2); changed = True
    if re.search(r'明天', s2):
        s2 = re.sub(r'明天', (base + timedelta(days=1)).strftime('%Y-%m-%d'), s2); changed = True
    if re.search(r'後天', s2):
        s2 = re.sub(r'後天', (base + timedelta(days=2)).strftime('%Y-%m-%d'), s2); changed = True
    def repl_en_weeks_later(m):
        nonlocal changed
        a = m.group(1)
        n = int(a) if a.isdigit() else (_en_word_to_int(a) or 0)
        dt = base + timedelta(weeks=n); changed = True
        return dt.strftime('%Y-%m-%d')
    def repl_en_days_later(m):
        nonlocal changed
        a = m.group(1)
        n = int(a) if a.isdigit() else (_en_word_to_int(a) or 0)
        dt = base + timedelta(days=n); changed = True
        return dt.strftime('%Y-%m-%d')
    s2 = re.sub(r'(?i)\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+weeks?\s+later\b', repl_en_weeks_later, s2)
    s2 = re.sub(r'(?i)\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+days?\s+later\b', repl_en_days_later, s2)
    def repl_zh_days(m):
        nonlocal changed
        d = _zh_to_int(m.group(1)); dt = base + timedelta(days=d); changed = True
        return dt.strftime('%Y-%m-%d')
    def repl_zh_weeks(m):
        nonlocal changed
        w = _zh_to_int(m.group(1)); dt = base + timedelta(weeks=w); changed = True
        return dt.strftime('%Y-%m-%d')
    s2 = re.sub(r'([一二兩三四五六七八九十\d]+)\s*天後', repl_zh_days, s2)
    s2 = re.sub(r'([一二兩三四五六七八九十\d]+)\s*週後', repl_zh_weeks, s2)
    return s2, changed

def _parse_relative_offset(text: str, tz: str, base_now: Optional[datetime] = None) -> Optional[datetime]:
    if not text: return None
    TZZ = pytz.timezone(tz)
    now = (base_now.astimezone(TZZ) if (base_now and base_now.tzinfo) else _now(tz))
    s = text.strip()
    for pat in _REL_PATS:
        m = pat.search(s)
        if not m: continue
        g1 = m.group(1)
        if g1.isdigit():
            n = int(g1)
            unit = m.group(2).lower() if len(m.groups()) >= 2 else ""
        else:
            n = _zh_to_int(g1)
            unit = "分鐘" if "分鐘" in pat.pattern else ("小時" if "小時" in pat.pattern else "天")
        if n <= 0: return now
        if unit.startswith(("min","分鐘")):  return now + timedelta(minutes=n)
        if unit.startswith(("hour","hr","小時")): return now + timedelta(hours=n)
        return now + timedelta(days=n)
    if re.search(r"\bday after tomorrow\b|後天", s, re.I): return now + timedelta(days=2)
    if re.search(r"\btomorrow\b|明天", s, re.I): return now + timedelta(days=1)
    return None

def _coerce_datetime(x, tz: str, def_date: Optional[datetime] = None, base_now: Optional[datetime] = None):
    if not x:
        return None
    if isinstance(x, datetime):
        return x if x.tzinfo else pytz.timezone(tz).localize(x)
    if isinstance(x, dict):
        x = x.get("dateTime") or x.get("date") or ""
    raw = str(x)

    skip_rel = False
    if _contains_relative_day(raw) and _has_time_token(raw):
        raw, _ = _rewrite_relative_to_absolute_date(raw, tz, base_now=base_now)
        skip_rel = True
    if not skip_rel:
        rel = _parse_relative_offset(raw, tz, base_now=base_now)
        if rel:
            return rel
    try:
        TZZ = pytz.timezone(tz)
        if def_date is not None:
            base_local = def_date.astimezone(TZZ) if def_date.tzinfo else TZZ.localize(
                def_date.replace(hour=0, minute=0, second=0, microsecond=0)
            )
            base_local = base_local.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            _n = (base_now.astimezone(TZZ) if (base_now and base_now.tzinfo) else _now(tz))
            base_local = _n.replace(hour=0, minute=0, second=0, microsecond=0)
        def_naive = base_local.replace(tzinfo=None)

        raw_for_parse = _strip_duration_phrases(raw)
        dt = dateparser.parse(raw_for_parse, fuzzy=True, default=def_naive)
        if dt is None:
            raise ValueError("dateparser returned None")
        dt = (TZZ.localize(dt) if dt.tzinfo is None else dt.astimezone(TZZ))
        if _ANY_ONLY_HH.search(raw) and not re.search(r'(?i)\b(am|pm)\b', raw) and ":" not in raw:
            dt = dt.replace(minute=0, second=0, microsecond=0)
        if re.search(r'\d{4}-\d{2}-\d{2}', raw) and ":" not in raw and not re.search(r'(?i)\b(am|pm)\b', raw):
            mh = re.search(r'(?<!\d)([01]?\d|2[0-3])(?!\d)', raw)
            if mh:
                dt = dt.replace(hour=int(mh.group(1)), minute=0, second=0, microsecond=0)
        return dt
    except Exception:
        try:
            dt = isoparse(str(x))
            return dt if dt.tzinfo else pytz.timezone(tz).localize(dt)
        except Exception:
            return None

def _extract_duration_minutes(s: str) -> Optional[int]:
    if not s: return None
    has_anchor = re.search(r'(?i)\b(duration|for)\b', s) or re.search(r'(持續)', s)
    if not has_anchor:
        return None
    m = re.search(r"(?i)\bduration\s*[:：]?\s+(\d+(?:\.\d+)?)\s*(hours?|hrs?)\b", s)
    if m: return int(round(float(m.group(1))*60))
    m = re.search(r"(?i)\bduration\s*[:：]?\s+(\d+(?:\.\d+)?)\s*(minutes?|mins?)\b", s)
    if m: return int(round(float(m.group(1))))
    m = re.search(r"(?i)\bfor\s+(\d+(?:\.\d+)?)\s*(hours?|hrs?)\b", s)
    if m: return int(round(float(m.group(1))*60))
    m = re.search(r"(?i)\bfor\s+(\d+(?:\.\d+)?)\s*(minutes?|mins?)\b", s)
    if m: return int(round(float(m.group(1))))
    m = re.search(r"(?:持續)\s*[:：]?\s*(\d+(?:\.\d+)?)\s*小時", s)
    if m: return int(round(float(m.group(1))*60))
    m = re.search(r"(?:持續)\s*[:：]?\s*(\d+)\s*分鐘", s)
    if m: return int(m.group(1))
    m = re.search(r"(?:持續)?\s*([一二兩三四五六七八九十\d]+)\s*小時半", s)
    if m: return _zh_to_int(m.group(1))*60 + 30
    m = re.search(r"(?:持續)?\s*([一二兩三四五六七八九十\d]+)\s*個?\s*半\s*小時", s)
    if m:
        base = _zh_to_int(m.group(1)) if not m.group(1).isdigit() else int(m.group(1))
        return base*60 + 30
    if re.search(r"(?:持續)?\s*半個?小時", s): return 30
    m = re.search(r"(?:持續)\s*([一二兩三四五六七八九十\d]+)\s*小時", s)
    if m: return _zh_to_int(m.group(1))*60
    m = re.search(r"(?:持續)\s*([一二兩三四五六七八九十\d]+)\s*分鐘", s)
    if m: return _zh_to_int(m.group(1))
    return None

def _split_emails(s: str) -> list[str]:
    if not s: return []
    out, seen = [], set()
    for em in EMAIL_RE.findall(s):
        em = em.strip(".,;:，；。、)）]」> ").lower()
        if em not in seen:
            out.append(em); seen.add(em)
    return out

# =========================
# parse_event core（純函式，不偵測 now/時區）
# =========================

def parse_event_core(text: str, base_now: datetime, tz: str, default_minutes: int = 60) -> Dict:
    """
    解析自然語句為事件：
      - 命中任一 lock 步驟即鎖定，不覆寫（僅允許後續補 end 或微調跨日）
      - 只有日期 → all-day（startDate/endDate；start/end 皆 None）
      - 旗標：lock:* / rewrite:* 會告知命中哪一步，方便 pytest 驗證
    """
    s = (text or "").strip()
    s = s.replace("—", "-").replace("–", "-").replace("~", "-")  # 標準化 dash
    TZZ = pytz.timezone(tz)

    flags: list[str] = []
    now = base_now.astimezone(TZZ) if base_now.tzinfo else TZZ.localize(base_now)
    used_labeled = False
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None
    locked_early = False
    early_locked_by_ampm = False

    # --- 抽取 body/location/attendees/顯式 title ---
    body = ""
    m = re.search(r"\b(body|description)\s*[:：]\s*([^\n]+)", s, re.I)
    if m:
        body = m.group(2).strip()

    location = None

    # 先試標籤式 location / 地點
    m_label = re.search(r"(?:\blocation\b|地點)\s*[:：]\s*([^\n,;]+)", s, re.I)
    if m_label:
        cand = m_label.group(1).strip()
        # 剃掉尾端時長描述
        cand = re.sub(r'(?i)\s*,?\s*for\s*[:：]?\s*\d+(?:\.\d+)?\s*(?:hours?|hrs?|minutes?|mins?)\s*$', '', cand)
        cand = re.sub(r'\s*(?:持續)\s*[:：]?\s*[一二兩三四五六七八九十\d]+(?:\.\d+)?\s*(?:小時半|小時|分鐘)\s*$', '', cand)
        location = (cand.strip() or None)
    else:
        # 再試 "at ..."
        m_at = re.search(r"\bat\s+([^\n,;]+)", s, re.I)
        if m_at:
            cand_raw = m_at.group(1).strip()
            # 先剃掉尾端時長（避免 "5 for 45 mins"）
            cand = re.sub(r'(?i)\s*,?\s*for\s*[:：]?\s*\d+(?:\.\d+)?\s*(?:hours?|hrs?|minutes?|mins?)\s*$', '', cand_raw)
            cand = re.sub(r'\s*(?:持續)\s*[:：]?\s*[一二兩三四五六七八九十\d]+(?:\.\d+)?\s*(?:小時半|小時|分鐘)\s*$', '', cand)
            cand = cand.strip(" ，,;；。")

            # --- 只有在 "at ..." 路徑才做時間判斷，時間就不當成地點 ---
            is_timey = (
                looks_like_time_string(cand) or
                re.search(r'(?i)\b([01]?\d|2[0-3]):([0-5]\d)\b', cand) or   # HH:MM
                re.search(r'(?i)\b([0-1]?\d)\s*(am|pm)\b', cand) or          # 5 pm
                _NOON_WORDS.search(cand) or _MIDNIGHT_WORDS.search(cand) or  # noon/midnight/中午/午夜
                _ZH_SINGLE_TIME.search(cand)                                 # 上午9點/下午3點…（中文）
            )

            if not is_timey:
                location = (cand or None)

    explicit_title: Optional[str] = None
    mt = re.search(r"(?:\btitle\b|標題)\s*[:：]\s*([^\n,;，；]+)", s, re.I)
    if mt:
        explicit_title = mt.group(1).strip()
    attendees = _split_emails(s)

    # === 步驟 3：相對日詞 + 明確時間 → 改寫（僅 rewrite，不 lock） ===
    s_abs = s
    if _contains_relative_day(s) and _has_time_token(s):
        s_abs, changed = _rewrite_relative_to_absolute_date(s, tz, base_now=now)
        if changed:
            flags.append("rewrite:relative+time")
            # 明確：相對日 + 單一時間 → 交給後續「絕對日期+時間」規則，不再落入工作時段 bucket
            # （只改寫，不在此鎖定）

    # === 步驟 1：兩端皆含日期時間的區間（最強約束） ===
    if not locked_early:
        mdd = _DT_DT_RANGE.search(s_abs)
        if mdd:
            a, b = mdd.group('a'), mdd.group('b')
            try:
                base_naive = now.replace(hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=None)
                adt = dateparser.parse(_strip_duration_phrases(a), fuzzy=True, default=base_naive)
                bdt = dateparser.parse(_strip_duration_phrases(b), fuzzy=True, default=base_naive)
                start_dt = TZZ.localize(adt) if adt.tzinfo is None else adt.astimezone(TZZ)
                end_dt   = TZZ.localize(bdt) if bdt.tzinfo is None else bdt.astimezone(TZZ)
                locked_early = True
                flags.append("lock:dt_dt_range")
                flags.append("lock:range_dt_dt")
            except Exception:
                pass

    # === 步驟 2：標籤式 start:/end: ===
    if not locked_early:
        # start: 非貪婪到 end/分隔符/行尾
        ms = re.search(r"\bstart\s*[:：]\s*([^\n]+?)(?=\s+\bend\b|[,;，、]|$)", s_abs, re.I)
        me = re.search(r"\bend\s*[:：]\s*([0-2]?\d(?::[0-5]\d)?(?:\s*(?:am|pm))?)", s_abs, re.I)
        if ms:
            anchor_date = _find_anchor_date(s_abs, tz, base_now=now)
            start_dt = _coerce_datetime(ms.group(1), tz, def_date=anchor_date, base_now=now)
            if start_dt:
                if me:
                    raw_e = (me.group(1) or "").strip()
                    mhm = _ONLY_HHMM.match(raw_e)
                    if mhm:
                        hh, mm = int(mhm.group(1)), int(mhm.group(2))
                        end_dt = start_dt.replace(hour=hh, minute=mm, second=0, microsecond=0)
                    else:
                        mh = _ONLY_HH.match(raw_e)
                        if mh:
                            hh = int(mh.group(1))
                            ap = (mh.group(2) or "").lower()
                            if ap in ("am","pm"):
                                hh = (0 if hh == 12 else hh) + (12 if ap == "pm" else 0)
                            end_dt = start_dt.replace(hour=hh, minute=0, second=0, microsecond=0)
                        else:
                            end_dt = _coerce_datetime(raw_e, tz, def_date=start_dt or anchor_date, base_now=now)
                locked_early = True
                used_labeled = True
                flags.append("lock:labeled")

    # === 步驟 5：錨點日期 + 區間（HH:MM–HH:MM、h–h） ===
    if not locked_early:
        anchor_date = _find_anchor_date(s_abs, tz, base_now=now)
        if anchor_date:
            # ⬇️ 新增：把各種日期樣式先清掉，避免 YYYY-MM-DD 的「-09-14」被當作 9–14 小時區間
            s_for_range = s_abs
            s_for_range = re.sub(r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b', ' ', s_for_range)         # 2025-09-14 / 2025/09/14
            s_for_range = re.sub(r'\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b', ' ', s_for_range)         # 9/14 或 9/14/2025
            s_for_range = re.sub(r'\d{4}年\d{1,2}月\d{1,2}日', ' ', s_for_range)                # 2025年9月14日
            s_for_range = re.sub(r'\d{1,2}月\d{1,2}日', ' ', s_for_range)
            
            m = re.search(r"\b([0-2]?\d:[0-5]\d)\s*[-–—~]\s*([0-2]?\d:[0-5]\d)\b", s_for_range)
            if m:
                s_naive = dateparser.parse(m.group(1), default=anchor_date.replace(tzinfo=None))
                e_naive = dateparser.parse(m.group(2), default=anchor_date.replace(tzinfo=None))
                start_dt = TZZ.localize(s_naive)
                end_dt   = TZZ.localize(e_naive)
                if end_dt <= start_dt:
                    end_dt = end_dt + timedelta(days=1)
                locked_early = True
                flags.append("lock:range_with_anchor")
                flags.append("lock:range_hhmm")
            else:
                m2 = _HOUR_RANGE.search(s_for_range)
                if m2:
                    h1 = int(m2.group(1)); h2 = int(m2.group(2))
                    if h1 > h2: h1, h2 = h2, h1
                    start_dt = anchor_date.replace(hour=h1, minute=0, second=0, microsecond=0)
                    end_dt   = anchor_date.replace(hour=h2, minute=0, second=0, microsecond=0)
                    if end_dt <= start_dt:
                        end_dt = end_dt + timedelta(days=1)
                    locked_early = True
                    flags.append("lock:range_with_anchor")
                    flags.append("lock:range_hour_only")
                else:
                    # 2025/9/30 上午9點-10點 → 用 anchor_date 建立中文區間
                    mz = _ZH_RANGE.search(s_abs)
                    if mz:
                        p1, h1, m1, p2, h2, m2_ = mz.groups()
                        if not p2: p2 = p1
                        h1i = _zh_to_int(h1) if not str(h1).isdigit() else int(h1)
                        h2i = _zh_to_int(h2) if not str(h2).isdigit() else int(h2)
                        sh = _zh_hour_to_24(p1, h1i); eh = _zh_hour_to_24(p2, h2i)
                        mm1 = int(m1) if m1 else 0; mm2v = int(m2_) if m2_ else 0
                        start_dt = anchor_date.replace(hour=sh % 24, minute=mm1, second=0, microsecond=0)
                        end_dt   = anchor_date.replace(hour=eh % 24, minute=mm2v, second=0, microsecond=0)
                        if end_dt <= start_dt:
                            end_dt = end_dt + timedelta(days=1)
                        locked_early = True
                        flags.append("lock:range_zh")

    # === 步驟 4：絕對日期 + 明確時間（含 AM/PM / 中文前綴） ===
    if not locked_early:
        anchor_date = _find_anchor_date(s_abs, tz, base_now=now)
        picked = False
        m1 = _EXPLICIT_DT_HHMM.search(s_abs)
        if m1:
            date_part, hh, mm, ap = m1.group(1), int(m1.group(2)), int(m1.group(3)), (m1.group(4) or "").lower()
            try:
                base = dateparser.parse(date_part, fuzzy=True, default=now.replace(hour=0,minute=0,second=0,microsecond=0))
                base = TZZ.localize(base) if base.tzinfo is None else base.astimezone(TZZ)
                if ap in ("am","pm"):
                    hh = (0 if hh == 12 else hh) + (12 if ap == "pm" else 0)
                    early_locked_by_ampm = True
                start_dt = base.replace(hour=hh%24, minute=mm, second=0, microsecond=0)
                locked_early = True
                picked = True
                flags.append("lock:date_hhmm")
            except Exception:
                pass
        if (not picked) and anchor_date:
            m2 = _EXPLICIT_HHMM_AP.search(s_abs)
            if m2:
                hh, mm, ap = int(m2.group(1)), int(m2.group(2)), (m2.group(3) or "").lower()
                if ap in ("am","pm"):
                    hh = (0 if hh == 12 else hh) + (12 if ap == "pm" else 0)
                    early_locked_by_ampm = True
                start_dt = anchor_date.replace(hour=hh%24, minute=mm, second=0, microsecond=0)
                locked_early = True
                flags.append("lock:hhmm_ap")
                picked = True
        # 先處理中文單點（避免被英式 HH am/pm 抢走）
        if (not picked) and anchor_date:
            m4 = _ZH_SINGLE_TIME.search(s_abs)
            if m4 and not early_locked_by_ampm:
                prefix, hstr, mstr = m4.group(1), m4.group(2), m4.group(3)
                hh = _zh_to_int(hstr) if not str(hstr).isdigit() else int(hstr)
                mm = int(mstr) if mstr else 0
                hh24 = _zh_hour_to_24(prefix, hh)
                start_dt = anchor_date.replace(hour=hh24%24, minute=mm, second=0, microsecond=0)
                locked_early = True
                flags.append("lock:zh_single")
                picked = True
        # 保底（有 anchor_date 但中文單點 regex 沒命中時，嘗試直接 coerce 一次）
        if (not picked) and anchor_date and re.search(r'(早上|上午|下午|晚上|晚間|夜間|凌晨|中午)\s*\d', s_abs):
            tmp = _coerce_datetime(s_abs, tz, def_date=anchor_date, base_now=now)
            if tmp:
                start_dt = tmp.replace(second=0, microsecond=0)
                locked_early = True
                flags.append("lock:zh_single")
                picked = True
        # 再處理：錨點 + HH:MM（無 am/pm）
        if (not picked) and anchor_date:
            m5 = _EXPLICIT_HHMM.search(s_abs)
            if m5 and not re.search(r'(?i)\b(am|pm)\b', s_abs):
                hh, mm = int(m5.group(1)), int(m5.group(2))
                start_dt = anchor_date.replace(hour=hh % 24, minute=mm, second=0, microsecond=0)
                locked_early = True
                picked = True
                # 若字串包含明確日期 → date_hhmm；否則（例如「下週二 10:00」）→ hhmm_ap
                if _HAS_EXPLICIT_DATE.search(s_abs):
                    flags.append("lock:date_hhmm")
                else:
                    flags.append("lock:hhmm_ap")
        # 最後：HH am/pm（只有小時，但帶 ap）
        if (not picked) and anchor_date:
            m3 = _EXPLICIT_HH_AP.search(s_abs)
            if m3:
                hh = int(m3.group(1)); ap = (m3.group(2) or "").lower()
                if ap in ("am","pm"):
                    hh = (0 if hh == 12 else hh) + (12 if ap == "pm" else 0)
                    early_locked_by_ampm = True
                start_dt = anchor_date.replace(hour=hh%24, minute=0, second=0, microsecond=0)
                locked_early = True
                # 與 HH:MM（含/不含 AM/PM）的旗標一致：一律使用 lock:hhmm_ap
                flags.append("lock:hhmm_ap")
                picked = True

    # === 步驟 6：錨點日期 + 裸小時（無 :、無 am/pm） ===
    s_wo_dates = re.sub(_DATE_TOKEN, ' ', s_abs)
    if not locked_early:
        anchor_date = _find_anchor_date(s_abs, tz, base_now=now)
        if anchor_date and (":" not in s_wo_dates) and (not re.search(r'(?i)\b(am|pm)\b', s_wo_dates)):
            hh_tokens = list(_ANY_ONLY_HH.finditer(s_wo_dates))
            if hh_tokens:
                hh = int(hh_tokens[-1].group(1))
                start_dt = anchor_date.replace(hour=hh%24, minute=0, second=0, microsecond=0)
                locked_early = True
                flags.append("lock:date_hour_only")

    # === 步驟 7：有時間、無日期（now+X / later… / bucket 詞） ===
    force_now_start = False
    hinted_minutes: Optional[int] = None
    if not locked_early:
        m_now = NOW_PLUS.search(s) or FROM_NOW.search(s) or ZH_NOW_PLUS.search(s)
        if m_now:
            try:
                base_now = now
                if m_now.re is ZH_NOW_PLUS:
                    raw = m_now.group(1); unit = m_now.group(2)
                    amount = float(raw) if re.fullmatch(r"\d+(?:\.\d+)?", raw) else float(_zh_to_int(raw))
                    hinted_minutes = int(round(amount * (60 if "小時" in unit else 1)))
                else:
                    amount = float(m_now.group(1)); unit = (m_now.group(2) or "").lower()
                    hinted_minutes = int(round(amount * (60 if unit.startswith(("hour","hr")) else 1)))
                # 語意修正：start=now，duration=hinted_minutes（由後面時長決策補 end）
                start_dt = base_now.replace(second=0, microsecond=0)
                # 不要預先把 start 往後推，避免測試出現 10:30
                force_now_start = True
                locked_early = True
                flags.append("lock:now_or_bucket")
                flags.append("lock:now_plus")
                try:
                    flags.append(f"now_src:{_LAST_NOW_SOURCE[0]}")
                except Exception:
                    pass
            except Exception:
                pass
        if not locked_early:
            if _LATER_THIS.search(s):
                tag = _LATER_THIS.search(s).group(1).lower()
                if tag == "morning":
                    now_local = now
                    if (now_local.hour < 10) or (now_local.hour == 10 and now_local.minute < 30):
                        start_dt = now_local.replace(hour=10, minute=30, second=0, microsecond=0)
                    elif now_local.hour < 12:
                        start_dt = now_local.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                    else:
                        start_dt = (now_local + timedelta(days=1)).replace(hour=10, minute=30, second=0, microsecond=0)
                else:
                    hh = _bucket_to_hour(tag)
                    start_dt = now.replace(hour=hh, minute=0, second=0, microsecond=0)
                locked_early = True
                flags.append("lock:now_or_bucket")
        if not locked_early:
            # 先處理「after noon」，避免被一般 noon bucket 吃掉
            m_after_noon = re.search(r'(?i)\b(\d+)\s+hours?\s+after\s+noon\b', s_abs)
            if m_after_noon:
                add_h = int(m_after_noon.group(1))
                start_dt = now.replace(hour=12, minute=0, second=0, microsecond=0) + timedelta(hours=add_h)
                locked_early = True
                flags.append("lock:after_noon")
        if not locked_early:
            if _NOON_WORDS.search(s):
                start_dt = now.replace(hour=12, minute=0, second=0, microsecond=0)
                locked_early = True; flags.append("lock:noon")
            elif _MIDNIGHT_WORDS.search(s):
                start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
                locked_early = True; flags.append("lock:midnight")
            elif _EVENING_TMR.search(s) and not _has_time_token(s):
                start_dt = (now + timedelta(days=1)).replace(hour=19, minute=0, second=0, microsecond=0)
                locked_early = True; flags.append("lock:tmr_evening")
            elif _MORNING_TMR.search(s) and not _has_time_token(s):
                start_dt = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
                locked_early = True; flags.append("lock:morning")
        if not locked_early:
            # "... later" 類單句（無日期）→ 用時長提示
            if LATER_EN.search(s) or LATER_ZH.search(s) or LATER_ZH_HALF.search(s):
                hinted = _extract_duration_minutes(s)
                if hinted and hinted > 0:
                    hinted_minutes = hinted
                    start_dt = now.replace(second=0, microsecond=0)
                    locked_early = True
                    flags.append("lock:later_hint")
                    flags.append("lock:now_or_bucket")                 

    # === 步驟 8：中文區間（含晚上→凌晨跨日） ===
    if not locked_early:
        m = _ZH_PM_TO_AM.search(s_abs)
        if m:
            sh = int(m.group(2)); eh = int(m.group(3))
            base = now
            start_dt = base.replace(hour=(0 if sh == 12 else sh) + 12, minute=0, second=0, microsecond=0)
            end_dt   = (base + timedelta(days=1)).replace(hour=eh % 24, minute=0, second=0, microsecond=0)
            locked_early = True
            flags.append("lock:range_zh")
        elif _ZH_RANGE.search(s_abs):
            p1, h1, m1, p2, h2, m2 = _ZH_RANGE.search(s_abs).groups()
            if not p2: p2 = p1
            h1i = _zh_to_int(h1) if not str(h1).isdigit() else int(h1)
            h2i = _zh_to_int(h2) if not str(h2).isdigit() else int(h2)
            sh = _zh_hour_to_24(p1, h1i); eh = _zh_hour_to_24(p2, h2i)
            mm1 = int(m1) if m1 else 0; mm2 = int(m2) if m2 else 0
            base = now
            start_dt = base.replace(hour=sh%24, minute=mm1, second=0, microsecond=0)
            end_dt   = base.replace(hour=eh%24, minute=mm2, second=0, microsecond=0)
            if end_dt <= start_dt:
                end_dt = end_dt + timedelta(days=1)
            locked_early = True
            flags.append("lock:range_zh")

    # === 步驟 9：鬆散兩個時間 token（無 dash 的小配對；僅在無明確日期/無相對語/無小數） ===
    def _should_enable_loose_heuristics(s_in: str, locked: bool, force_now: bool) -> bool:
        if locked or force_now:
            return False
        if has_explicit_date(s_in):
            return False
        if re.search(r'(?i)\blater\b', s_in):
            return False
        if any(p.search(s_in) for p in _REL_PATS):
            return False
        if re.search(r"\d+\.\d+", s_in):
            return False
        return True

    if not locked_early and _should_enable_loose_heuristics(s_abs, locked_early, False):
        toks = list(_TIME_TOK.finditer(s_abs))
        def has_detail(m): return bool(m.group(2) or m.group(3))
        if len(toks) >= 2 and (has_detail(toks[0]) or has_detail(toks[1])):
            def tok_to_minutes(m):
                h = int(m.group(1)); mm = int(m.group(2) or 0); ap = (m.group(3) or "").lower()
                if ap in ("am","pm"): h = (0 if h == 12 else h) + (12 if ap == "pm" else 0)
                return h*60 + mm
            t1, t2 = tok_to_minutes(toks[0]), tok_to_minutes(toks[1])
            a, b = (t1, t2) if t1 <= t2 else (t2, t1)
            sh, sm, eh, em = a//60, a%60, b//60, b%60
            start_dt = now.replace(hour=sh, minute=sm, second=0, microsecond=0)
            end_dt   = now.replace(hour=eh, minute=em, second=0, microsecond=0)
            locked_early = True
            flags.append("lock:loose_timepair")

    # === 步驟 10：只有日期 → All-day ===
    all_day = False
    start_date_str = None
    end_date_str = None
    if not locked_early:
        if has_explicit_date(s_abs) and not _has_time_token(s_abs):
            anchor = _find_anchor_date(s_abs, tz, base_now=now)
            if anchor:
                start_date = anchor.date().isoformat()
                end_date = (anchor + timedelta(days=1)).date().isoformat()
                all_day = True
                locked_early = True
                flags.append("lock:all_day")
                flags.append("all_day")
                start_date_str, end_date_str = start_date, end_date

    # === 時長決策與 end 補齊 ===
    dur_minutes: Optional[int] = None
    if not all_day:
        if hinted_minutes and hinted_minutes > 0:
            dur_minutes = int(hinted_minutes)
        else:
            extracted = _extract_duration_minutes(s)
            if extracted and extracted > 0:
                dur_minutes = int(extracted)
        if not dur_minutes or dur_minutes <= 0:
            dur_minutes = int(default_minutes)
        dur_minutes = max(MIN_DUR, min(MAX_DUR, dur_minutes))
        if start_dt and not end_dt:
            end_dt = start_dt + timedelta(minutes=dur_minutes)
        if start_dt and end_dt and end_dt <= start_dt:
            end_dt = start_dt + timedelta(minutes=dur_minutes)

    # === 滾到隔天（僅限「只有時間或 today/今天」，且未 force now） ===
    ROLL_GRACE = 2  # minutes
    if start_dt and not all_day:
        has_only_time_or_today = (not has_explicit_date(s_abs)) and (
            re.search(r'\b(today|今天)\b', s_abs, re.I) or _has_time_token(s_abs)
        )
        if has_only_time_or_today and (not ('lock:now_or_bucket' in flags)) and start_dt <= now - timedelta(minutes=ROLL_GRACE):
            start_dt = start_dt + timedelta(days=1)
            if end_dt: end_dt = end_dt + timedelta(days=1)
            flags.append("rolled_to_next_day")

    # === 中文 AM/PM（若沒用英 AM/PM early lock）微調 ===
    if start_dt and not re.search(r'(?i)\b(am|pm)\b', s_abs):
        if re.search(r'(下午|晚上|晚間|夜間)', s_abs) and 1 <= start_dt.hour <= 11:
            start_dt = start_dt.replace(hour=(start_dt.hour % 12) + 12)
            if end_dt and end_dt <= start_dt:
                end_dt = start_dt + timedelta(minutes=dur_minutes or default_minutes)
        if re.search(r'凌晨', s_abs) and start_dt.hour == 12:
            start_dt = start_dt.replace(hour=0)

    # --- 格式化/清理 ---
    if start_dt:
        start_dt = start_dt.replace(second=0, microsecond=0)
    if end_dt:
        end_dt = end_dt.replace(second=0, microsecond=0)

    # 產生標題（先移除欄位段）
    scrub = re.sub(r"(?:\battendees?\b|受邀|來賓)\s*[:：][^\n]+", "", s, flags=re.I)
    scrub = re.sub(r"(?:\blocation\b|地點)\s*[:：][^\n,;]+", "", scrub, flags=re.I)
    scrub = re.sub(r"\b(body|description)\s*[:：][^\n]+", "", scrub, flags=re.I)
    scrub = re.sub(r"\bstart\s*[:：][^\n]+?(?=\s+\bend\b|[,;，、]|$)", "", scrub, flags=re.I)
    scrub = re.sub(r"\bend\s*[:：]\s*[0-2]?\d(?::[0-5]\d)?(?:\s*(?:am|pm))?", "", scrub, flags=re.I)
    # 額外清掉「this/next <weekday>」「今天/明早」等相對詞殘留，避免進 tidy_title 後出現非語意字
    scrub = re.sub(r'(?i)\b(this|next)\s+(mon|tue|wed|thu|fri|sat|sun|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', '', scrub)
    scrub = re.sub(r"(今天|明早)", "", scrub)    
    title = tidy_title(scrub, s)
    if explicit_title:
        pref = tidy_title(explicit_title, s)
        if pref: title = pref

    # 粗略信心值
    confidence = 0.6 + (0.2 if used_labeled else 0.0) + (0.05 if location else 0.0) + (0.05 if attendees else 0.0)
    confidence = max(0.0, min(1.0, confidence))

    # 版本旗標
    flags.append("ver:A21-hotfix1-6")
    print("[siiha-sdk] parse_event flags:", flags)

    result = {
        "parse_source": "sdk",
        "title": title,
        "body": body,
        "location": location or "",
        "attendees": attendees,
        "timeZone": tz,
        "start": start_date_str if all_day else (start_dt.isoformat() if start_dt else None),
        # all-day 必須回傳 end 的隔日日期（測試有驗）
        "end":   (end_date_str if all_day else (end_dt.isoformat() if end_dt else None)),
        "flags": flags,
        "confidence": confidence,
        "debugNowSource": _LAST_NOW_SOURCE[0],
    }
    if all_day:
        result["allDay"] = True
    return result

# =========================
# parse_event shell（保留原對外 API 與行為）
# =========================

def parse_event(text: str, tz: str = DEFAULT_TIMEZONE, default_minutes: int = 60) -> Dict:
    """
    殼層：決定有效時區與「現在」，並注入 core。
    維持：NOW_PROVIDER、now_src:* 旗標、回傳格式與 A19 相容。
    """
    eff_tz = _effective_tz(tz)
    TZZ = pytz.timezone(eff_tz)

    # 1) 先走 NOW_PROVIDER（維持相容）
    if NOW_PROVIDER is not None:
        raw_now = NOW_PROVIDER() if callable(NOW_PROVIDER) else NOW_PROVIDER
        now_src = "NOW_PROVIDER"
    else:
        # 2) 保留 cal.datetime 與 stdlib 偵測語意（最終仍要有值）
        raw_now, now_src = None, None
        cand = globals().get("datetime", None)
        if cand is not None:
            dt_cls = getattr(cand, "datetime", cand)
            if hasattr(dt_cls, "now"):
                try:
                    raw_now = dt_cls.now()
                    now_src = "cal.datetime"
                except Exception:
                    raw_now = None
        if raw_now is None:
            import datetime as _sysdt
            try:
                raw_now = _sysdt.datetime.now()
                now_src = "stdlib.datetime"
            except Exception:
                raw_now = _sysdt.datetime.now()  # 保底
                now_src = "fallback.now()"

    # 一致化為 eff_tz aware
    base_now = (TZZ.localize(raw_now) if raw_now.tzinfo is None else raw_now.astimezone(TZZ))
    try:
        _LAST_NOW_SOURCE[0] = now_src
    except Exception:
        pass

    # 交給 core
    r = parse_event_core(text, base_now=base_now, tz=eff_tz, default_minutes=default_minutes)

    # 若是 now/bucket 類，補 now_src:*（與 A19 一致）
    if ("lock:now_plus" in r.get("flags", [])) or ("lock:now_or_bucket" in r.get("flags", [])):
        if not any(str(f).startswith("now_src:") for f in r["flags"]):
            r["flags"].append(f"now_src:{now_src}")
    # timeZone 與 debug 欄位保持一致（core 已填，這裡保守覆寫一次）
    r["timeZone"] = eff_tz
    r["debugNowSource"] = now_src
    return r