import os
import asyncio
import requests
from telegram import Bot

# ===== ENV VARIABLES (FROM RAILWAY) =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
MATCH_ID = os.getenv("MATCH_ID")
CHAT_ID = os.getenv("CHAT_ID")

# ===== TELEGRAM BOT =====
bot = Bot(token=BOT_TOKEN)

CHECK_INTERVAL = 5  # seconds
last_sent_score = None
bot = Bot(token=BOT_TOKEN)

last_score_state = {}
current_match_id = None


# ===== API HELPERS =====
def api_get(url):
    return requests.get(url, timeout=10).json()


def get_live_match_id():
    """AUTO-PICK NEXT LIVE MATCH"""
    url = f"https://api.cricapi.com/v1/currentMatches?apikey={API_KEY}&offset=0"
    res = api_get(url)

    if res.get("status") != "success":
        return None

    for m in res.get("data", []):
        if m.get("matchStarted") and not m.get("matchEnded"):
            return m["id"]

    return None


def get_match_info(match_id):
    url = f"https://api.cricapi.com/v1/match_info?apikey={API_KEY}&id={match_id}"
    res = api_get(url)

    if res.get("status") != "success":
        return None

    return res.get("data")


# ===== FORMATTERS =====
def format_live_score(data):
    teams = data["teamInfo"]
    short = {t["name"]: t["shortname"] for t in teams}

    lines = []
    for s in data.get("score", []):
        team = s["inning"].split(" Inning")[0].strip()
        lines.append(
            f"{short.get(team, team)} {s['r']}/{s['w']} ({s['o']})"
        )

    return (
        f"🏏 {data['name']}\n\n"
        + "\n".join(lines)
    )


def detect_events(data):
    """🚨 WICKET 🚨 + 4️⃣ FOUR 4️⃣+ 6️⃣ SIX 6️⃣"""
    alerts = []
    scores = data.get("score", [])

    for s in scores:
        key = s["inning"]
        prev = last_score_state.get(key)

        if prev:
            # 🚨 WICKET
            if s["w"] > prev["w"]:
                alerts.append(
                    f"🚨 WICKET 🚨\n{s['inning']} : {s['r']}/{s['w']} ({s['o']})"
                )

            # 🔥 FOUR / SIX
            run_diff = s["r"] - prev["r"]
            if run_diff == 4:
                alerts.append("4️⃣ FOUR 4️⃣!")
            elif run_diff >= 6:
                alerts.append("6️⃣ SIX 6️⃣!")

        last_score_state[key] = {
            "r": s["r"],
            "w": s["w"]
        }

    return alerts


def format_result(data):
    return (
        f"🏆 RESULT\n\n"
        f"{data['status']}\n"
        f"{data['venue']}"
    )


# ===== MAIN LOOP =====
async def main():
    global current_match_id

    await bot.send_message(
        chat_id=CHAT_ID,
        text="🟢 Cricket bot connected & monitoring live matches"
    )

    print("Bot loop started")

    while True:
        try:
            # 🔁 AUTO MATCH PICK
            if not current_match_id:
                current_match_id = get_live_match_id()
                if current_match_id:
                    last_score_state.clear()
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text="🔁 Auto-selected next live match"
                    )
                await asyncio.sleep(CHECK_INTERVAL)
                continue

            data = get_match_info(current_match_id)
            if not data:
                await asyncio.sleep(CHECK_INTERVAL)
                continue

            # 🎨 LIVE SCORE FORMAT
            score_msg = format_live_score(data)
            await bot.send_message(chat_id=CHAT_ID, text=score_msg)

            # 🚨 EVENTS
            alerts = detect_events(data)
            for alert in alerts:
                await bot.send_message(chat_id=CHAT_ID, text=alert)

            # 🏆 MATCH END
            if data.get("matchEnded"):
                result = format_result(data)
                await bot.send_message(chat_id=CHAT_ID, text=result)
                current_match_id = None

            await asyncio.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("Error:", e)
            await asyncio.sleep(30)


asyncio.run(main())