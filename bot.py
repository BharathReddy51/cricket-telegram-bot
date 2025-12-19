import os
import asyncio
import requests
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
MATCH_ID = os.getenv("MATCH_ID")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)