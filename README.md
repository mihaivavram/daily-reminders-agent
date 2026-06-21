# Daily Reminders Agent

A tiny, zero-dependency tool that sends you a random reminder as a **phone push
notification** a few times a day. Reminders live in a GitHub Gist so you can
edit the list from anywhere (phone or browser) without touching the server.

```
Gist (reminders.txt)  --fetch-->  send_reminder.py  --ntfy POST-->  phone
                                        ^
                                       cron (3x/day)
```

- **Push channel:** [ntfy.sh](https://ntfy.sh) — free, no account, no API keys.
- **List storage:** a *secret* GitHub Gist, fetched fresh on every run.
- **Dependencies:** none. Pure Python standard library (works on Python 3.9.6).

---

## Setup

### 1. Install the ntfy app and subscribe

1. Install **ntfy** from the App Store / Play Store on your mobile device.
2. Pick a long, unguessable topic name, e.g. `mavram-reminders-9fk3qz`.
   (Anyone who knows the topic can read/post to it, so treat it like a password.)
3. In the app: **+ → Subscribe to topic →** enter that exact name.

### 2. Create the reminders gist

1. Go to <https://gist.github.com>, create a **secret** gist.
2. Name the file `reminders.txt`, one reminder per line. Blank lines and lines
   starting with `#` are ignored. Example:
   ```
   # health
   Drink a glass of water
   Stand up and stretch
   # mindset
   What are you grateful for right now?
   ```
3. Save, click **Raw**, and copy the URL. Remove the commit hash from the path
   so it always serves the latest version, i.e. use:
   `https://gist.githubusercontent.com/<user>/<id>/raw/reminders.txt`

### 3. Configure

You set three values: `NTFY_TOPIC`, `GIST_RAW_URL`, and optionally `NTFY_SERVER`
(only if you self-host ntfy). 

**Option B — use a `.env` file** (preferred if this repo will ever be public, so
the topic/URL aren't committed). Copy the template and fill it in:

```bash
cp .env.example .env
# edit .env with your values
``

```bash
# Load the environment every time before running the script
set -a; source .env; set +a
```

(See [.env.example](.env.example) for the cron-friendly way to source it.)

### 4. Test it

```bash
python3 send_reminder.py
```

You should get a push on your phone, and a line in `reminder.log` like
`... ntfy ok -> 'Drink a glass of water'`.

---

## Schedule it (cron, on the VPS)

**We recommend** running this on a machine that's always on — e.g. a small
**Ubuntu VPS** or a **Mac Mini / Mac Pro** at home — so cron can fire reliably
even when your laptop is asleep or offline.

Run `crontab -e` and add three lines (adjust the path and times). Times are in
the **server's** timezone — check with `timedatectl`.

Remember that cron users the server timezone, not yours, so adjust accordingly
```cron
0  9  * * *  cd /path/to/daily-reminders-agent && /usr/bin/python3 send_reminder.py >> reminder.log 2>&1
0  14 * * *  cd /path/to/daily-reminders-agent && /usr/bin/python3 send_reminder.py >> reminder.log 2>&1
0  19 * * *  cd /path/to/daily-reminders-agent && /usr/bin/python3 send_reminder.py >> reminder.log 2>&1
```

That sends one random reminder in the morning, afternoon, and evening.

If you configured with a `.env` file (Option B above), source it inside the cron
command, since cron won't load it on its own:

```cron
0  9  * * *  cd /path/to/daily-reminders-agent && set -a && . ./.env && set +a && /usr/bin/python3 send_reminder.py >> reminder.log 2>&1
```

---

## Adding more reminders later

Just edit the gist (gist.github.com → your gist → **Edit**) and add lines. The
next scheduled run picks up the change automatically — no SSH, no restart.

## How it avoids repeats

The last couple of sent reminders are recorded in `.reminder_state.json` and
excluded from the next random pick, so you don't get the same one twice in a
row. (If your list is shorter than that, it just picks randomly.)

## Troubleshooting

- **No notification:** check `reminder.log`. A `could not fetch reminders` line
  means a bad `GIST_RAW_URL`; an `ntfy send failed` line means a bad topic or
  no network. The script exits non-zero on failure so cron mail flags it too.
- **Wrong times:** cron uses the server timezone, not yours.
