import os, time, csv
import uuid
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from mixing import network_connection_spatial
import traceback  # make sure this is at the top with other imports


load_dotenv()
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]  # Socket Mode
GAME_CHANNEL_ID = os.environ.get("GAME_CHANNEL_ID")  

app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)

ROUND_TIMEOUT_SECONDS = 60  # or whatever you want

round_state = {}                   # Tracks per-round metadata (e.g., start/end timestamps)
# round_state structure:
# {
#   round_id: {
#       "pair": (player_a, player_b),           # tuple of player IDs in this round
#       "trial": int,                           # trial number this round belongs to
#       "subs": {player_id: hashtag_str | None},# each player’s submission (None until submitted)
#       "submitted": {player_id: bool},         # whether each player submitted
#       "completed": bool,                      # True when both submitted
#       "started_at": float,                    # Unix timestamp when round started
#       "channel_id": str,                      # Slack channel ID for this round
#       "game_outcome": str | None              # "✅ match" or "❌ no match"
#   },
#   ...
# }
player_points = defaultdict(int)   # Maps user_id -> accumulated score

current_game = {
    "players": [],         
    "channel_id": None,
    "trialnum": 0,
    "neighborsize": 2,
    "current_trial": 0,
    "schedule_by_trial": {},   # {t: [(a,b), ...]}
    "rids_by_trial": {},       # {t: [rid, ...]}
    "csv_path": None,          # auto-append here
}

_csv_lock = threading.Lock() #creates a lock object — ensures only one thread at a time can access a the CSV file

def make_round_id():
    return uuid.uuid4().hex #changed round id from datetime-->UUID (due to concurrent player submissions)

def normalize_tag(s):
    """Lowercase, drop a single leading '#', trim whitespace. Return '' for no hashtag submissions."""
    if not s:
        return ""
    s = s.strip()
    if s.startswith("#"):
        s = s[1:].strip()
    return s.lower()

def get_channel_players(client, channel_id):
    """Return all user IDs in the channel (excluding the bot itself)."""
    bot_user_id = client.auth_test()["user_id"]
    resp = client.conversations_members(channel=channel_id)
    members = resp.get("members", [])
    return [m for m in members if m != bot_user_id]

def score_and_outcome(rid):
    """Evaluate a round, update points and store outcome."""
    st = round_state.get(rid)
    if not st or not st["completed"]:
        return
    a, b = st["pair"]
    sa = normalize_tag(st["subs"][a]) #hashtag submission from player a
    sb = normalize_tag(st["subs"][b]) #hashtag submission from player b
    if sa and sb and sa == sb:
        st["game_outcome"] = "match"
        player_points[a] += 1
        player_points[b] += 1
    else:
        st["game_outcome"] = "no match"

def build_pair_schedule_spatial(players, *, randseed=1, trialnum=5, neighborsize=4): #default parameters, do not c
    """Builds a pairing schedule (player1, player2, trial_number) using spatial network logic.
    
    Each row in the output corresponds to a pair of players for a given trial.
    Example output of this function:
        [
            ('@U01', '@U02', 1),
            ('@U03', '@U04', 1),
            ('@U01', '@U03', 2),
            ...
        ]

    Notes:
    - Do NOT tune `trialnum` or `neighborsize` here.
      These are default values only — the actual experiment parameters
      should be set in the main control flow inside `on_mention()`
    - For a fully connected (homogeneous) network where every player
      interacts with every other player, set: 
        neighborsize = len(players) - 1
    """    
    idx_to_user = {i + 1: u for i, u in enumerate(players)}
    conn = network_connection_spatial(
        randseed=randseed,
        nodesnum=len(players),
        trialnum=trialnum,
        neighborsize=neighborsize,
    )
    # Convert the NumPy array of network connections into a standard Python list.
    # Each row has the format: [player1_index, player2_index, trial_number]
    connection_list = conn.tolist()

    # Sort connections by trial number(row 2) first, then by player1 index(row 0), then by player2 index(row 1).
    connection_list.sort(key=lambda row: (row[2], row[0], row[1]))

    # Map player indices to usernames, keeping the trial number for scheduling
    pair_schedule = []
    for player1_idx, player2_idx, trial_num in connection_list:
        player1 = idx_to_user[player1_idx]
        player2 = idx_to_user[player2_idx]
        pair_schedule.append((player1, player2, int(trial_num)))  # int(trial_num) because coming from numpy.int64

    return pair_schedule


def group_pairs_by_trial(schedule_with_trials):
    """takes schedule made in build_pair_schedule_spatial and groups by trial number
    [(a,b,t)] -> {t: [(a,b), ...]}"""
    grouped = defaultdict(list)
    for a, b, t in schedule_with_trials:
        grouped[t].append((a, b))
    return dict(sorted(grouped.items()))

ROUND_TIMEOUT_SECONDS = 60  # or whatever you want

def schedule_round_timeout(rid, client, timeout=ROUND_TIMEOUT_SECONDS):
    """
    After `timeout` seconds, if the round is still open,
    mark it as closed due to timeout, write CSV, and maybe advance the trial.
    """
    def _timeout_worker():
        time.sleep(timeout)

        st = round_state.get(rid)
        if not st:
            return

        # If already closed (both submitted and handled), do nothing
        if st.get("closed"):
            return

        # Round timed out
        st["closed"] = True
        if not st.get("game_outcome"):
            st["game_outcome"] = "timeout"

        # Write a row even if one or both hashtags are missing
        _append_round_to_csv(rid)

        # Try to advance to the next trial
        maybe_advance_trial(client)

    threading.Thread(target=_timeout_worker, daemon=True).start()

# CSV helpers (auto-write) 
def _init_csv():
    """Initializes CSV with headers and returns path."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"submissions_{ts}.csv"
    with _csv_lock, open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "round_id",
            "trial",
            "player_a",
            "player_b",
            "player_a_hashtag",
            "player_b_hashtag",
            "completed",      # 0 = incomplete, 1 = both submitted
            "started_at",
            "game_outcome",
        ])
    return path

def _append_round_to_csv(rid):
    """Append one round's submission data and outcome to the game CSV."""
    st = round_state.get(rid)
    if not st:
        return

    a, b = st["pair"]

    # Safe even if one or both players never submitted
    sa = st["subs"].get(a, "")
    sb = st["subs"].get(b, "")

    row = [
        rid,
        st["trial"],
        a,
        b,
        sa,
        sb,
        1 if st.get("completed") else 0,  # 1 only if both submitted
        st["started_at"],
        st.get("game_outcome"),
    ]

    path = current_game.get("csv_path")
    if not path:
        return

    with _csv_lock, open(path, "a", newline="") as f:
        csv.writer(f).writerow(row)

def _announce_match(client, rid: str):
    """
    Send round result only to the two players in this pair (ephemeral),
    instead of posting anything to the whole channel.
    """
    st = round_state.get(rid)
    if not st:
        return

    a, b = st["pair"]
    ch = st["channel_id"]

    sa = (st["subs"].get(a) or "").strip()
    sb = (st["subs"].get(b) or "").strip()
    outcome = st.get("game_outcome") or "no outcome recorded"

    # Get each player's current points (if you use player_points dict)
    points_a = player_points.get(a, 0)
    points_b = player_points.get(b, 0)

    # Message just for player a
    client.chat_postEphemeral(
        channel=ch,
        user=a,
        text=(
            f"*Trial {st['trial']} result*\n"
            f"• Your hashtag: `{sa or '(no hashtag)'}`\n"
            f"• Partner: `{sb or '(no hashtag)'}`\n"
            f"• Outcome: *{outcome}*\n"
            f"• Your total points: *{points_a}*"
        ),
    )

    # Message just for player b
    client.chat_postEphemeral(
        channel=ch,
        user=b,
        text=(
            f"*Trial {st['trial']} result (just for you)*\n"
            f"• Your hashtag: `{sb or '(no hashtag)'}`\n"
            f"• Partner <@{a}>: `{sa or '(no hashtag)'}`\n"
            f"• Outcome: *{outcome}*\n"
            f"• Your total points: *{points_b}*"
        ),
    )




# Trial orchestration 
def _send_pair_ephemerals(client, channel_id, a, b, t, rid):
    """
    Set up round state for pair (a, b) in trial t and send each their ephemeral
    with a 'Submit hashtag' button that opens the modal.
    """
    # Create round record
    round_state[rid] = {
        "pair": (a, b),
        "trial": t,
        "subs": {a: "", b: ""},           # empty string instead of None
        "submitted": {a: False, b: False},
        "completed": False,               # both submitted?
        "closed": False,                  # finished by submit or timeout
        "started_at": datetime.now().isoformat(),
        "channel_id": channel_id,
        "game_outcome": None,
    }

    # Send ephemerals to both, with a button that clearly shows the trial
    for user, partner in ((a, b), (b, a)):
        client.chat_postEphemeral(
            channel=channel_id,
            user=user,
            text=f"*Trial {t}* • You are matched with <@{partner}>.",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Trial {t}*\n Click below to submit your hashtag."
                    },
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": f"Submit hashtag (Trial {t})"
                            },
                            "style": "primary",
                            "action_id": "open_submit_modal",  # wired to the @app.action below
                            "value": rid,                       # we pass rid so we can look up trial later
                        }
                    ]
                }
            ],
        )

    # Start timeout clock for this round
    schedule_round_timeout(rid, client)



def start_trial(client, t):
    """Open all pairs for trial t (concurrent within trial)."""
    ch = current_game["channel_id"]
    pairs = current_game["schedule_by_trial"][t]
    rids = []

    # Ensure everyone appears on /scores including players with 0 points.
    for u in current_game["players"]:
        _ = player_points[u]

    # len(pairs) = number of player pairs for this trial
    # we make 1 thread per pair so all pairs can start concurrently
    with ThreadPoolExecutor(max_workers=len(pairs)) as pool:
        for a, b in pairs:
            rid = make_round_id()
            rids.append(rid)
            pool.submit(_send_pair_ephemerals, client, ch, a, b, t, rid)

    # after all threads complete, store the round IDs for this trial
    current_game["rids_by_trial"][t] = rids
    current_game["current_trial"] = t


def maybe_advance_trial(client):
    """If all pairs in current trial are closed (submitted or timed out), open the next trial (if any)."""
    t = current_game["current_trial"]
    rids = current_game["rids_by_trial"].get(t, [])
    if not rids:
        return

    # All rounds must be closed, regardless of whether both submitted
    if all(round_state[r].get("closed") for r in rids):
        next_t = t + 1
        if next_t <= current_game["trialnum"]:
            start_trial(client, next_t)
        else:
            app.client.chat_postMessage(
                channel=current_game["channel_id"],
                text="All trials complete. Type `@Demo App scores` for the leaderboard."
            )




# ============== Actions & Views ==============

@app.action("open_submit_modal")
def open_submit_modal(ack, body, client):
    ack()

    user = body["user"]["id"]
    rid = body["actions"][0]["value"]  # we passed rid in the button
    st = round_state.get(rid)
    if not st:
        return

    trial_num = st["trial"]  # get the trial #

    trigger_id = body["trigger_id"]

    client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "submit_hashtag_view",
            "private_metadata": rid,
            
            # Modal title with trial #
            "title": {
                "type": "plain_text",
                "text": f"Trial {trial_num}"
            },

            "submit": {"type": "plain_text", "text": "Submit"},
            "close": {"type": "plain_text", "text": "Cancel"},

            "blocks": [
                {
                    "type": "input",
                    "block_id": "hs",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "val",
                        "initial_value": "#",
                        "placeholder": {"type": "plain_text", "text": "#example"}
                    },
                    "label": {"type": "plain_text", "text": "Write a Hashtag for the event"}
                }
            ]
        }
    )


@app.view("submit_hashtag_view")
def handle_submit(ack, body, client, view):
    """
    Handles a player's hashtag submission from the modal form.
    Updates the round state, scores if both players submitted,
    and advances to the next trial when ready.
    """
    ack()

    # Extract metadata from Slack payload
    rid = view["private_metadata"]    # passed from open_submit_modal()
    user = body["user"]["id"]
    try:
        value_raw = (view["state"]["values"]["hs"]["val"]["value"] or "").strip()
    except Exception:
        value_raw = ""

    # If, for any reason, this round_id doesn’t exist in memory anymore, bail quietly
    if rid not in round_state:
        return

    st = round_state[rid]
    a, b = st["pair"]
    ch = st["channel_id"]

    # store a cleaned value (CSV has no leading '#')
    value_clean = value_raw[1:].strip() if value_raw.startswith("#") else value_raw

    st["subs"][user] = value_clean
    st["submitted"][user] = True

    # let this user know we're waiting on their partner 
    client.chat_postEphemeral(channel=ch, user=user, text="⏳ Waiting for your partner’s submission…")

    # If both submitted: complete, score, outcome, notify both, append CSV, maybe advance trial
    if st["submitted"][a] and st["submitted"][b]:
        st["completed"] = True
        st["closed"] = True

        score_and_outcome(rid)  # sets st['game_outcome'] and gives +1 each on match

        # append to CSV immediately
        _append_round_to_csv(rid)

        _announce_match(client, rid)

        # Check if all rounds in this trial are complete/closed and start the next one
        maybe_advance_trial(client)



# ============== Mention-based controls ==================
@app.event("app_mention")
def on_mention(body, say, client):
    """
    Controls via mention in channel:
      @Demo App start
      @Demo App scores
   
    """
    #Extract message context
    event = body.get("event", {})
    text = (event.get("text") or "").lower()
    channel_id = event.get("channel")

    #when "@Demo App start" is typed in the channel then launches a new game.
    if "start" in text:
        players = get_channel_players(client, channel_id)  # even count assumed
        trialnum = 5 #tunable
        neighborsize = 4 #tunable

       # Generate round schedule using spatial pairing logic
        schedule = build_pair_schedule_spatial(
            players,
            randseed=1,
            trialnum=trialnum,
            neighborsize=neighborsize,
        )
        schedule_by_trial = group_pairs_by_trial(schedule)

       # Initialize player scores (ensures 0 shows on leaderboard)
        for u in players:
            _ = player_points[u]

        # Create a new CSV log for this session
        csv_path = _init_csv()

        # Reset and store the current game configuration
        current_game.update({
            "players": players,
            "channel_id": channel_id,
            "trialnum": trialnum,
            "neighborsize": neighborsize,
            "current_trial": 0,
            "schedule_by_trial": schedule_by_trial,
            "rids_by_trial": {},
            "csv_path": csv_path,
        })
        # Announce game start and begin first trial
        say(f"Hashtag Game starting with {len(players)} players • {trialnum} trials.")
        start_trial(client, 1)
        return

    #when "@Demo App scores" is typed in the channel then bot displays current leaderboard.
    if "scores" in text:
        for u in current_game.get("players", []):
            _ = player_points[u]
        lines = [f"<@{u}>: {pts}" for u, pts in sorted(player_points.items(), key=lambda x: (-x[1], x[0]))] # Sort by score (descending), then user ID (stable)
        say("*Leaderboard*\n" + ("\n".join(lines) if lines else "_No scores yet._"))
        return

    # Fallback help
    say("Try: `@Demo App start` to begin, `@Demo App scores` to view the leaderboard.")









# ============== Entrypoint ==============
if __name__ == "__main__":
    missing = [k for k in ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET", "SLACK_APP_TOKEN"] if not os.environ.get(k)]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")
    print("Starting Socket Mode handler...")
    SocketModeHandler(app, SLACK_APP_TOKEN).start()