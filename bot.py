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

CHECK_INTERVAL = 20  # seconds
last_sent_score = None


def get_match_info():
    url = f"https://api.cricapi.com/v1/match_info?apikey={API_KEY}&id={MATCH_ID}"
    res = requests.get(url, timeout=10).json()

    if res.get("status") != "success":
        print("API status not success:", res)
        return None

    data = res.get("data")
    if not data:
        print("No data in API response")
        return None

    return data


def format_score(data):
    scores = data.get("score", [])

    if not scores:
        return (
            f"🏏 {data['name']}\n"
            f"{data['venue']}\n\n"
            "Match not started yet."
        )

    score_lines = []
    for s in scores:
        score_lines.append(
            f"{s['inning']} : {s['r']}/{s['w']} ({s['o']} ov)"
        )

    message = (
        f"🏏 LIVE SCORE\n\n"
        f"{data['name']}\n"
        f"{data['venue']}\n\n"
        + "\n".join(score_lines)
    )
    return message


async def main():
    global last_sent_score

    # ✅ CONFIRM BOT IS RUNNING
    await bot.send_message(
        chat_id=CHAT_ID,
        text="🟢 Bot connected successfully!"
    )

    print("Bot loop started")

    while True:
        try:
            data = get_match_info()
            if not data:
                await asyncio.sleep(CHECK_INTERVAL)
                continue

            message = format_score(data)

            if last_sent_score is None or message != last_sent_score:
                await bot.send_message(chat_id=CHAT_ID, text=message)
                last_sent_score = message

            if data.get("matchEnded"):
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text="✅ Match ended."
                )
                break

            await asyncio.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("Error:", e)
            await asyncio.sleep(30)


asyncio.run(main())
