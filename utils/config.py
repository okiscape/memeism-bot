import pytz
from dotenv import dotenv_values
env = dotenv_values()

local_tz = pytz.timezone('Europe/Moscow')

bot_token = env["BOT_TOKEN"]
proxy_url = env["PROXY_URL"]

db_path = "utils/data/base.sqlite"