#!/usr/bin/env python3
"""Post Azkar al-Sabah (after Fajr) or Azkar al-Masa (after Asr) to a Telegram
channel, at the right minute for that day's prayer times.

GitHub starts this script a little before the prayer. The script looks up the
day's prayer times (Aladhan API, Umm al-Qura method), waits until
prayer time + offset, then posts the azkar as a few Telegram messages.

Uses only the Python standard library (3.9+).

Usage:
  python send_azkar.py                    # pick the session by time of day, wait, post
  python send_azkar.py --session masa     # force a session
  python send_azkar.py --now              # post right away, no waiting
  python send_azkar.py --dry-run          # print the messages, send nothing
  python send_azkar.py --test             # post a short test message now
  python send_azkar.py --find-chat-id     # show chat IDs the bot can see
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent

# Settings, all overridable with environment variables.
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT = os.environ.get("TELEGRAM_CHAT", "")              # "@channelname" or "-100..."
CITY = os.environ.get("CITY", "Riyadh")
COUNTRY = os.environ.get("COUNTRY", "Saudi Arabia")
METHOD = os.environ.get("METHOD", "4")                  # 4 = Umm al-Qura, Makkah
try:
    TZ = ZoneInfo(os.environ.get("TIMEZONE", "Asia/Riyadh"))
except Exception:  # Windows has no time-zone database unless `pip install tzdata`
    TZ = timezone(timedelta(hours=float(os.environ.get("UTC_OFFSET_HOURS", "3"))))
OFFSET_MIN = {
    "sabah": int(os.environ.get("SABAH_OFFSET_MIN", "15")),  # minutes after Fajr
    "masa": int(os.environ.get("MASA_OFFSET_MIN", "15")),    # minutes after Asr
}
MAX_LATE_MIN = 120   # if we are later than this, skip instead of posting stale azkar

SESSIONS = {
    "sabah": {"prayer": "Fajr", "label": "☀️ أذكار الصباح", "prayer_ar": "الفجر"},
    "masa": {"prayer": "Asr", "label": "🌇 أذكار المساء", "prayer_ar": "العصر"},
}
TELEGRAM_LIMIT = 3800  # Telegram allows 4096 characters per message
SEPARATOR = "\n\n━━━━━━━━━━\n\n"


def times_ar(count: int) -> str:
    if count == 1:
        return "مرة واحدة"
    if count == 2:
        return "مرتان"
    if 3 <= count <= 10:
        return f"{count} مرات"
    return f"{count} مرة"


def fetch_day(day) -> dict:
    query = urllib.parse.urlencode({"city": CITY, "country": COUNTRY, "method": METHOD})
    url = f"https://api.aladhan.com/v1/timingsByCity/{day:%d-%m-%Y}?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "azkar-reminder/2.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if data.get("code") != 200:
        raise RuntimeError(f"Aladhan API error: {data}")
    return data["data"]


def local_time(day, hhmm: str) -> datetime:
    hour, minute = map(int, hhmm.split()[0].split(":"))  # "04:45" or "04:45 (+03)"
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=TZ)


def build_messages(session: str, items: list, day_info: dict) -> list:
    """Return the azkar as a list of Telegram messages, each under the limit."""
    info = SESSIONS[session]
    h = day_info["date"]["hijri"]
    hijri = f"{h['weekday']['ar']} {h['day']} {h['month']['ar']} {h['year']}هـ"
    header = (f"{info['label']}\n{hijri}\n"
              f"🕌 {info['prayer_ar']}: {day_info['timings'][info['prayer']].split()[0]} · {CITY}")

    blocks = []
    picked = [it for it in items if it.get("only") in (None, session)]
    for i, it in enumerate(picked, 1):
        text = it.get("text") or it[session]
        title = f" ﴿ {it['title']} ﴾" if it.get("title") else ""
        blocks.append(f"{i}.{title}\n{text}\n🔁 {times_ar(it['count'])}")

    messages, current = [], header
    for block in blocks:
        if len(current) + len(SEPARATOR) + len(block) > TELEGRAM_LIMIT:
            messages.append(current)
            current = block
        else:
            current += SEPARATOR + block
    messages.append(current + "\n\nتقبل الله منا ومنكم 🤲")
    return messages


def telegram(method: str, payload: dict) -> dict:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        raise SystemExit(f"Telegram error {err.code}: {body}")


def send(text: str) -> None:
    telegram("sendMessage", {"chat_id": CHAT, "text": text,
                             "disable_web_page_preview": True})


def find_chat_id() -> None:
    result = telegram("getUpdates", {"allowed_updates": ["channel_post", "message", "my_chat_member"]})
    seen = {}
    for upd in result.get("result", []):
        for key in ("channel_post", "message", "my_chat_member"):
            chat = upd.get(key, {}).get("chat")
            if chat:
                seen[chat["id"]] = chat.get("title") or chat.get("username") or chat.get("first_name")
    if not seen:
        print("No chats found. Post any message in your channel, then run this again.")
    for chat_id, name in seen.items():
        print(f"Chat ID: {chat_id}    Name: {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--session", choices=["sabah", "masa", "auto"], default="auto")
    parser.add_argument("--now", action="store_true", help="post right away, no waiting")
    parser.add_argument("--dry-run", action="store_true", help="print only, send nothing")
    parser.add_argument("--test", action="store_true", help="post a short test message")
    parser.add_argument("--find-chat-id", action="store_true")
    args = parser.parse_args()

    if not args.dry_run and not BOT_TOKEN:
        print("Set the TELEGRAM_BOT_TOKEN secret first.", file=sys.stderr)
        return 1
    if args.find_chat_id:
        find_chat_id()
        return 0
    if not args.dry_run and not CHAT:
        print("Set the TELEGRAM_CHAT secret first.", file=sys.stderr)
        return 1
    if args.test:
        send("✅ تم الربط بنجاح\nستصلكم أذكار الصباح بعد الفجر وأذكار المساء بعد العصر بإذن الله.")
        print("Test message sent.")
        return 0

    now = datetime.now(TZ)
    session = args.session
    if session == "auto":
        session = "sabah" if now.hour < 10 else "masa"
    info = SESSIONS[session]

    day_info = fetch_day(now.date())
    target = local_time(now.date(), day_info["timings"][info["prayer"]]) \
        + timedelta(minutes=OFFSET_MIN[session])
    print(f"{now:%Y-%m-%d %H:%M} {CITY}: {info['prayer']} "
          f"{day_info['timings'][info['prayer']]}, posting {session} at {target:%H:%M}")

    items = json.loads((HERE / "azkar.json").read_text(encoding="utf-8"))["items"]
    messages = build_messages(session, items, day_info)

    if args.dry_run:
        for n, msg in enumerate(messages, 1):
            print(f"\n----- message {n}/{len(messages)} ({len(msg)} chars) -----\n{msg}")
        return 0

    if not args.now:
        wait = (target - datetime.now(TZ)).total_seconds()
        if wait < -MAX_LATE_MIN * 60:
            print("Too late for this session today, skipping.")
            return 0
        if wait > 0:
            print(f"Waiting {wait / 60:.0f} minutes...")
            time.sleep(wait)

    for msg in messages:
        send(msg)
        time.sleep(1.5)
    print(f"Posted {len(messages)} messages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
