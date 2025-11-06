
import os
import csv
import time
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler


ENV_PATH = "individual.env"
CSV_PATH = "hashtag_single_trial.csv"

WELCOME_TEXT = (
    "Welcome to the hashtag game!\n"
    "Hey there <@{user_id}>! Write a hashtag to describe the event you read about.\n"
    "_Just reply with your hashtag now._"
)

THANKS_TEXT = "✅ Thanks! Your hashtag has been recorded."
NUDGE_TEXT = "Type `start` to begin the hashtag game."


load_dotenv(ENV_PATH)

BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
APP_TOKEN = os.getenv("SLACK_APP_TOKEN")  # required for Socket Mode

# Initialize the Slack app
app = App(token=BOT_TOKEN, signing_secret=SIGNING_SECRET)

# Tracks which users we are currently expecting a hashtag from.
awaiting_response = {} # {user_id: True/False}


def dm(user_id, text):
    """Send a DM to a user."""
    app.client.chat_postMessage(channel=user_id, text=text)

def ensure_csv_header(path):
    """Create the CSV with a header if it doesn't exist yet."""
    if os.path.exists(path):
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["unix_time", "user_id", "hashtag"])

def strip_hashtag(text):
    # Trim spaces and remove all leading '#' (e.g., "#Tag" -> "Tag")
    t = text.strip()
    t = t.lstrip("#").strip()
    return t

def save_hashtag(user_id, raw_text):
    ensure_csv_header(CSV_PATH)
    stripped = strip_hashtag(raw_text)
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([time.time(), user_id, stripped])

def start_flow(user_id):
    """Begin the single-trial flow for a user."""
    awaiting_response[user_id] = True
    dm(user_id, WELCOME_TEXT.format(user_id=user_id))

def handle_submission(user_id, text):
    """Handle the user's hashtag submission."""
    save_hashtag(user_id, text)
    dm(user_id, THANKS_TEXT)
    awaiting_response[user_id] = False  # lock to single submission


# Event Handlers (DMs)


#    Handles all incoming messages from users.
@app.event("message")
def on_message_events(body, event, say, logger):
    user_id = event["user"]      # Identify which user sent the message
    text = event["text"].strip()   #(remove leading/trailing spaces from the message text)

    # If the user types "start", we record that they are now in the game
    # and send them the welcome prompt asking for a hashtag.
    if text.lower() == "start":
        awaiting_response[user_id] = True
        dm(user_id, WELCOME_TEXT.format(user_id=user_id))

     # Once the user is marked as awaiting (awaiting_hashtag[user_id]=True), 
     # their next message is treated as a hashtag.   
    elif awaiting_response.get(user_id):
        save_hashtag(user_id, text)
        dm(user_id, THANKS_TEXT)
        awaiting_response[user_id] = False # mark as complete so they can’t resubmit




if __name__ == "__main__":
    print("Starting Hashtag Bot (single-trial, DM only)")
    SocketModeHandler(app, APP_TOKEN).start()
