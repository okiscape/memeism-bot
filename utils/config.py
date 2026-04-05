import os

import pytz
from dotenv import dotenv_values

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = dotenv_values()


def _int(key: str, default: int | None = None) -> int | None:
	value = env.get(key)
	if value is None or value == "":
		return default
	return int(value)


local_tz = pytz.timezone("Europe/Moscow")

bot_token = env["BOT_TOKEN"]

def _truthy(s: str | None) -> bool:
	if s is None or str(s).strip() == "":
		return False
	return str(s).strip().lower() in ("1", "true", "yes", "on")

_raw_proxy = env.get("PROXY_URL")
if _truthy(env.get("PROXY_DISABLED")) or _truthy(env.get("NO_PROXY")):
	proxy_url = None
else:
	proxy_url = (
		_raw_proxy.strip()
		if _raw_proxy
		and str(_raw_proxy).strip()
		and str(_raw_proxy).strip().lower() not in ("none", "null", "off", "false", "0", "-")
		else None
	)

db_path = os.path.join(_PROJECT_ROOT, "utils", "data", "base.sqlite")

bot_owner_id = _int("BOT_OWNER_ID")
dev_guild_id = _int("DEV_GUILD_ID")
feedback_channel_id = _int("FEEDBACK_CHANNEL_ID")
feedback_ping_user_id = _int("FEEDBACK_PING_USER_ID")
profile_edits_log_channel = _int("PROFILE_EDITS_CHANNEL_ID")

support_invite_url = env.get("SUPPORT_INVITE_URL") or "https://discord.gg"

version_name = env.get("BOT_VERSION_NAME") or "memeism"
version_number = env.get("BOT_VERSION_NUMBER") or "0.1"

class colors:
	spotify_main = 0x1ED760
	blurple = 0x5665F4
	pastel_yellow = 0xFFDC97
	pastel_red = 0xED4245
	mitsuki_col = 0xECE5CF
	success = 0xA3E77F
	gray = 0x2f3136
	deny = 0xcc0000
	osu_main = 0xfb65a7
	osu_second = 0xe27496
	light_blue = 0x7abdd5
	light_pink = 0xffacd0
	boticord = 0x24aef3
	beige = 0xfdeddc
	verification = 0xa2a1fc