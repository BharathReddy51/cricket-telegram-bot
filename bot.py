import asyncio
import requests
import os

from telegram import Bot


BOT_TOKEN = os.getenv("8465888851:AAE6Za4sC5NM3CwA6k9mOmulbWpwsP2wrkg")
API_KEY = os.getenv("dc580eed-fac9-4ab1-891a-75fe83ce3710")
MATCH_ID = os.getenv("13a8d87a-aec5-44e2-8fe8-b6fc1beb0587")
CHAT_ID = os.getenv("@Gouravcricketslive")
CHECK_INTERVAL = 20  # seconds (safe)

# ==================
bot = Bot(token=BOT_TOKEN)
last_sent_score = None

def get_match_info():
    url = f"https://api.cricapi.com/v1/match_info?apikey={API_KEY}&id={MATCH_ID}"
    res = requests.get(url).json()

    if res.get("status") != "success":
        print("API status not success:", res)
        return None

    if "data" not in res or res["data"] is None:
        print("No data in API response:", res)
        return None

    return res["data"]


def format_score(data):
    scores = data.get("score", [])
    if not scores:
        return f"🏏 {data['name']}\n\nMatch not started yet."

    score_lines = []
    for s in scores:
        line = f"{s['inning']} : {s['r']}/{s['w']} ({s['o']} ov)"
        score_lines.append(line)

    message = (
        f"🏏 LIVE SCORE\n\n"
        f"{data['name']}\n"
        f"{data['venue']}\n\n"
        + "\n".join(score_lines)
    )
    return message

async def main():
    global last_sent_score

    # Test message (confirms bot + chat_id works)
    await bot.send_message(
        chat_id=CHAT_ID,
        text="🟢 Bot connected. Waiting for live score updates."
    )

    while True:
        try:
            data = get_match_info()
            if not data:
                await asyncio.sleep(CHECK_INTERVAL)
                continue

            # ✅ CREATE message HERE (this was missing)
            message = format_score(data)

            if last_sent_score is None or message != last_sent_score:
                await bot.send_message(chat_id=CHAT_ID, text=message)
                last_sent_score = message

            if data.get("matchEnded"):
                await bot.send_message(chat_id=CHAT_ID, text="✅ Match ended.")
                break

            await asyncio.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("Error:", e)
            await asyncio.sleep(30)


asyncio.run(main())
