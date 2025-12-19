import os
import asyncio
import requests
from telegram import Bot

# ========== ENV VARIABLES ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
MATCH_ID = os.getenv("MATCH_ID")   # 🔒 FIXED MATCH
CHAT_ID = os.getenv("CHAT_ID")

CHECK_INTERVAL = 5  # safe for free API

bot = Bot(token=BOT_TOKEN)

last_score_state = {}
last_sent_score = None
# ==================================


def api_get(url):
    return requests.get(url, timeout=10).json()


def get_match_info():
    url = f"https://api.cricapi.com/v1/match_info?apikey={API_KEY}&id={MATCH_ID}"
    res = api_get(url)

    if res.get("status") != "success":
        print("API error:", res)
        return None

    return res.get("data")


def format_live_score(data):
    short_names = {
        t["name"]: t["shortname"]
        for t in data.get("teamInfo", [])
    }

    lines = []
    for s in data.get("score", []):
        team = s["inning"].split(" Inning")[0]
        short = short_names.get(team, team)
        lines.append(f"{short} {s['r']}/{s['w']} ({s['o']} ov)")

    return (
        f"🏏 LIVE SCORE\n\n"
        f"{data['name']}\n"
        f"{data['venue']}\n\n"
        + "\n".join(lines)
    )


def detect_events(data):
    alerts = []

    for s in data.get("score", []):
        key = s["inning"]
        prev = last_score_state.get(key)

        if prev:
            # 🚨 WICKET
            if s["w"] > prev["w"]:
                alerts.append(
                    f"🚨 WICKET 🚨\n"
                    f"{s['inning']} : {s['r']}/{s['w']} ({s['o']} ov)"
                )

            # 4️⃣ FOUR
            run_diff = s["r"] - prev["r"]
            if run_diff == 4:
                alerts.append("4️⃣ FOUR 4️⃣")

            # 6️⃣ SIX
            elif run_diff >= 6:
                alerts.append("6️⃣ SIX 6️⃣")

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


async def main():
    global last_sent_score

    await bot.send_message(
        chat_id=CHAT_ID,
        text="🟢 Cricket bot connected & tracking selected match"
    )

    print("Bot loop started")

    while True:
        try:
            data = get_match_info()
            if not data:
                await asyncio.sleep(CHECK_INTERVAL)
                continue

            # 🎨 LIVE SCORE
            score_message = format_live_score(data)
            if score_message != last_sent_score:
                await bot.send_message(chat_id=CHAT_ID, text=score_message)
                last_sent_score = score_message

            # 🚨 EVENTS
            alerts = detect_events(data)
            for alert in alerts:
                await bot.send_message(chat_id=CHAT_ID, text=alert)

            # 🏆 MATCH END
            if data.get("matchEnded"):
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=format_result(data)
                )
                break  # 🔒 STOP AFTER MATCH ENDS

            await asyncio.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("Error:", e)
            await asyncio.sleep(30)


asyncio.run(main())
