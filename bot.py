from telegram import Bot
import os

test_bot = Bot(token=os.getenv("8465888851:AAE6Za4sC5NM3CwA6k9mOmulbWpwsP2wrkg"))
print(test_bot.get_me())