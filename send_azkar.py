#!/usr/bin/env python3
"""Schedule today's Azkar al-Sabah (after Fajr) and Azkar al-Masa (after Asr)
as ntfy push notifications, one dhikr per notification.

Run it once a day, shortly after midnight local time. It fetches the day's
prayer times from the Aladhan API and asks the ntfy server to deliver each
notification at the right moment, so the timing does not depend on when the
script itself runs.

Uses only the Python standard library (3.9+).

Usage:
  python send_azkar.py             # schedule today's notifications
  python send_azkar.py --dry-run   # print the schedule, send nothing
  python send_azkar.py --test      # send 3 notifications right now
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent

# Settings, all overridable with environment variables.
NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "")
NTFY_TOKEN = os.environ.get("NTFY_TOKEN", "")          # only for private ntfy servers
CITY = os.environ.get("CITY", "Riyadh")
COUNTRY = os.environ.get("COUNTRY", "Saudi Arabia")
METHOD = os.environ.get("METHOD", "4")                  # 4 = Umm al-Qura, Makkah
try:
    TZ = ZoneInfo(os.environ.get("TIMEZONE", "Asia/Riyadh"))
except Exception:  # Windows has no time-zone database unless `pip install tzdata`
    TZ = timezone(timedelta(hours=float(os.environ.get("UTC_OFFSET_HOURS", "3"))))
SABAH_OFFSET_MIN = int(os.environ.get("SABAH_OFFSET_MIN", "15"))  # minutes after Fajr
MASA_OFFSET_MIN = int(os.environ.get("MASA_OFFSET_MIN", "15"))    # minutes after Asr
GAP_SECONDS = int(os.environ.get("GAP_SECONDS", "30"))            # between notifications
CLICK_URL = os.environ.get("CLICK_URL", "")             # optional link on each notification

SESSIONS = {
    "sabah": {"prayer": "Fajr", "offset": SABAH_OFFSET_MIN,
              "label": "أذكار الصباح", "tag": "sunrise"},
    "masa": {"prayer": "Asr", "offset": MASA_OFFSET_MIN,
             "label": "أذكار المساء", "tag": "city_sunset"},
}

MAX_BYTES = 4000  # ntfy turns longer messages into attachments


def times_ar(count: int) -> str:
    if count == 1:
        return "مرة واحدة"
    if count == 2:
        return "مرتان"
    if 3 <= count <= 10:
        return f"{count} مرات"
    return f"{count} مرة"


def fetch_timings(day: date) -> dict:
    query = urllib.parse.urlencode({"city": CITY, "country": COUNTRY, "method": METHOD})
    url = f"https://api.aladhan.com/v1/timingsByCity/{day:%d-%m-%Y}?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "azkar-reminder/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if data.get("code") != 200:
        raise RuntimeError(f"Aladhan API error: {data}")
    return data["data"]["timings"]


def local_time(day: date, hhmm: str) -> datetime:
    hour, minute = map(int, hhmm.split()[0].split(":"))  # "04:45" or "04:45 (+03)"
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=TZ)


def build_messages(session: str, items: list) -> list:
    info = SESSIONS[session]
    picked = [it for it in items if it.get("only") in (None, session)]
    total = len(picked)
    out = []
    for i, it in enumerate(picked, 1):
        text = it.get("text") or it[session]
        if it.get("title"):
            text = f"﴿ {it['title']} ﴾\n{text}"
        body = f"{text}\n\n🔁 {times_ar(it['count'])} (×{it['count']})"
        if len(body.encode("utf-8")) > MAX_BYTES:
            print(f"warning: item {i} is too long for one notification", file=sys.stderr)
        out.append({
            "title": f"{info['label']} {i}/{total}",
            "message": body,
            "tags": [info["tag"]],
            # first one rings louder so you notice the start
            "priority": 4 if i == 1 else 3,
        })
    return out


def publish(msg: dict, deliver_at=None) -> None:
    payload = {"topic": NTFY_TOPIC, **msg}
    if CLICK_URL:
        payload["click"] = CLICK_URL
    if deliver_at is not None:
        payload["delay"] = str(int(deliver_at.timestamp()))
    headers = {"Content-Type": "application/json", "User-Agent": "azkar-reminder/1.0"}
    if NTFY_TOKEN:
        headers["Authorization"] = f"Bearer {NTFY_TOKEN}"
    req = urllib.request.Request(NTFY_SERVER, data=json.dumps(payload).encode("utf-8"),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        resp.read()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="print the schedule only")
    parser.add_argument("--test", action="store_true", help="send 3 notifications now")
    parser.add_argument("--date", help="YYYY-MM-DD (default: today in TIMEZONE)")
    args = parser.parse_args()

    if not NTFY_TOPIC and not args.dry_run:
        print("Set the NTFY_TOPIC environment variable first.", file=sys.stderr)
        return 1

    items = json.loads((HERE / "azkar.json").read_text(encoding="utf-8"))["items"]

    if args.test:
        publish({"title": "✅ تجربة", "message": "وصل الإشعار بنجاح. Azkar reminders are working.",
                 "tags": ["white_check_mark"], "priority": 3})
        publish(build_messages("sabah", items)[0])
        publish(build_messages("masa", items)[0])
        print("Sent 3 test notifications.")
        return 0

    now = datetime.now(TZ)
    day = date.fromisoformat(args.date) if args.date else now.date()
    timings = fetch_timings(day)
    print(f"{day}  {CITY}: Fajr {timings['Fajr']}  Asr {timings['Asr']}")

    sent = skipped = 0
    for session, info in SESSIONS.items():
        start = local_time(day, timings[info["prayer"]]) + timedelta(minutes=info["offset"])
        for n, msg in enumerate(build_messages(session, items)):
            when = start + timedelta(seconds=n * GAP_SECONDS)
            line = f"  {when:%H:%M:%S}  {msg['title']}"
            if when <= now + timedelta(seconds=15):
                print(line + "  (already passed, skipped)")
                skipped += 1
                continue
            print(line)
            if not args.dry_run:
                publish(msg, deliver_at=when)
            sent += 1

    verb = "Would schedule" if args.dry_run else "Scheduled"
    print(f"{verb} {sent} notifications ({skipped} skipped).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
