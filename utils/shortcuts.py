from datetime import datetime
from utils import config, emojis
import inspect
import googletrans, disnake

def now_datetime(): return datetime.now(config.local_tz)
def datetime_from_timestamp(timestamp: int): return datetime.fromtimestamp(timestamp, config.local_tz)


def _locale_dest(inter: disnake.ApplicationCommandInteraction) -> str:
	loc = getattr(inter.locale, "value", str(inter.locale))
	return (loc or "en").split("-")[0]


def stbc(inter: disnake.ApplicationCommandInteraction, text: str) -> str:
	# googletrans translate can be async in newer versions; keep sync-safe fallback.
	if inspect.iscoroutinefunction(googletrans.Translator.translate):
		return text
	try:
		return googletrans.Translator().translate(text, dest=_locale_dest(inter)).text
	except Exception:
		try:
			return googletrans.Translator().translate(text, dest="en").text
		except Exception:
			return text


async def rmark(text: str) -> str:
	return disnake.utils.escape_markdown(text or "")


class MessageDeleteView(disnake.ui.View):
	"""Как в Mitsuki: только эмодзи, без проверки автора."""

	def __init__(self) -> None:
		super().__init__(timeout=None)

	@disnake.ui.button(emoji=emojis.icon_remove, style=disnake.ButtonStyle.secondary, row=0)
	async def remove_button(
		self,
		_: disnake.ui.Button,
		inter: disnake.MessageInteraction,
	) -> None:
		await inter.message.delete()


def generate_autocomplete_choices(choices: list[str]):
	async def returned(inter, string: str) -> list[str]:
		string = string.lower()
		return [lang for lang in choices if string in lang.lower()]

	return returned


def generate_pick(choices: list[str]):
	"""Как в Mitsuki — alias для autocomplete."""
	return generate_autocomplete_choices(choices)


async def tbc(inter: disnake.ApplicationCommandInteraction, text: str, do_not_translate: str = None, translate_type: str = "user"):

	
	"""tbc - translate-by-client
	
	Перевод строки на язык клиента дискорда или сервера по коду языка.
	
	Типы:
		"user": перевод строки по клиента автора
		"guild": перевод строки по языку сервера из базы"""
	
	if do_not_translate is None:
		if translate_type == "user":
			try:
				translated = await googletrans.Translator().translate(text, _locale_dest(inter))
				return translated.text
			except:
				try:
					translated = await googletrans.Translator().translate(text, 'en')
					return translated.text
				except:
					return text
				
		elif translate_type == "guild":
			cur = await get_cursor()
			cur.execute(f"SELECT * FROM `server_settings` WHERE `guild_id` = {inter.guild_id}")
			server_language = cur.fetchone()
			try:
				translated = googletrans.Translator().translate(text, server_language)
				return translated.text
			except:
				translated = googletrans.Translator().translate(text, 'en')
				return translated.text
		
	else:
		try:
			if translate_type == "user":
				try:
					translated = googletrans.Translator().translate(text, dest=_locale_dest(inter))
					return translated.text
				except:
					try:
						translated = googletrans.Translator().translate(text, dest="en")
						return translated.text
					except:
						return text
					
			elif translate_type == "guild":
				cur = await get_cursor()
				cur.execute(f"SELECT * FROM `server_settings` WHERE `guild_id` = {inter.guild_id}")
				server_language = cur.fetchone()
				try:
					translated = googletrans.Translator().translate(text, server_language)
					return translated.text
				except:
					translated = googletrans.Translator().translate(text, "en")
					return translated.text
				
		except:
			translated = googletrans.Translator().translate(text, 'en')
			return translated.text
