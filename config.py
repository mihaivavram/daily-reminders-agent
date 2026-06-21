"""Configuration for the Daily Reminders Agent.

Edit the values below. None of these are encrypted secrets, but the ntfy topic
and the gist URL are unguessable and act as your access keys -- keep them
private. If you ever push this repo PUBLIC, move them into environment variables
instead (see README).
"""

import os

# --- ntfy (phone push notifications) -----------------------------------------
# A long, unguessable topic name. Anyone who knows it can post to / read from
# your topic, so make it random. Subscribe to this exact name in the ntfy app.
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "mavram-reminders-CHANGE-ME-9fk3qz")

# The ntfy server. Default is the free public server.
NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh")

# --- Reminders source (a secret GitHub Gist) ---------------------------------
# The RAW url of reminders.txt inside your gist, e.g.
# https://gist.githubusercontent.com/<user>/<id>/raw/reminders.txt
# (Omitting the commit hash makes it always serve the latest version.)
GIST_RAW_URL = os.environ.get(
    "GIST_RAW_URL",
    "https://gist.githubusercontent.com/USER/ID/raw/reminders.txt",
)

# --- Behaviour ---------------------------------------------------------------
# How many of the most-recently-sent reminders to avoid repeating.
AVOID_LAST_N = 2
