#!/usr/bin/env python3
"""Daily Reminders Agent.

Fetches a list of reminders from a secret GitHub Gist, randomly picks one
(avoiding the most recently sent), and sends it to your phone as an ntfy push
notification. Designed to be run from cron a few times per day.

Zero third-party dependencies -- standard library only.
"""

import json
import os
import random
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

import config

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, ".reminder_state.json")
LOG_FILE = os.path.join(HERE, "reminder.log")
HTTP_TIMEOUT = 15  # seconds


def log(message):
    """Append a timestamped line to the log file and print it."""
    line = "{} {}".format(datetime.now(timezone.utc).isoformat(timespec="seconds"), message)
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError as exc:  # logging must never crash the run
        print("WARN could not write log file: {}".format(exc))


def fetch_reminders(url):
    """Fetch the gist and return a list of reminder strings.

    Skips blank lines and lines starting with '#'. Raises on network/HTTP error.
    """
    req = urllib.request.Request(url, headers={"User-Agent": "daily-reminders-agent"})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        raw = resp.read().decode("utf-8")
    reminders = []
    for line in raw.splitlines():
        text = line.strip()
        if text and not text.startswith("#"):
            reminders.append(text)
    return reminders


def load_state():
    """Return the saved state dict, or a fresh one if missing/corrupt."""
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"recent": []}


def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2)
    except OSError as exc:
        log("WARN could not write state file: {}".format(exc))


def pick_reminder(reminders, recent):
    """Pick a random reminder, avoiding recently sent ones when possible."""
    candidates = [r for r in reminders if r not in recent]
    if not candidates:  # short list / everything recently sent
        candidates = reminders
    return random.choice(candidates)


def send_ntfy(text):
    """POST the reminder to ntfy. Raises on failure (non-2xx or network)."""
    url = "{}/{}".format(config.NTFY_SERVER.rstrip("/"), config.NTFY_TOPIC)
    req = urllib.request.Request(
        url,
        data=text.encode("utf-8"),
        method="POST",
        headers={
            "Title": "Reminder",
            "Tags": "bell",
            "User-Agent": "daily-reminders-agent",
        },
    )
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        if not (200 <= resp.status < 300):
            raise urllib.error.HTTPError(url, resp.status, "non-2xx response", resp.headers, None)


def main():
    # 1. Fetch the reminders list.
    try:
        reminders = fetch_reminders(config.GIST_RAW_URL)
    except Exception as exc:  # network/HTTP/decoding -- don't send anything
        log("ERROR could not fetch reminders: {}".format(exc))
        return 1

    if not reminders:
        log("ERROR reminders list is empty -- nothing to send")
        return 1

    # 2. Pick one, avoiding recent repeats.
    state = load_state()
    recent = state.get("recent", [])
    reminder = pick_reminder(reminders, recent[-config.AVOID_LAST_N:])

    # 3. Send via ntfy.
    try:
        send_ntfy(reminder)
    except Exception as exc:
        log("ERROR ntfy send failed for {!r}: {}".format(reminder, exc))
        return 1

    # 4. Record success.
    recent.append(reminder)
    state["recent"] = recent[-max(config.AVOID_LAST_N, 1):]
    state["last_sent_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    save_state(state)
    log("ntfy ok -> {!r}".format(reminder))
    return 0


if __name__ == "__main__":
    sys.exit(main())
