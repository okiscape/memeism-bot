from datetime import datetime
from utils import config
import googletrans, disnake

def now_datetime(): return datetime.now(config.local_tz)
def datetime_from_timestamp(timestamp: int): return datetime.fromtimestamp(timestamp, config.local_tz)

def generate_autocomplete_choices(choices: list[str]):
	async def returned(inter, string: str) -> list[str]:
		string = string.lower()
		return [lang for lang in choices if string in lang.lower()]

	return returned


async def tbc(inter: disnake.ApplicationCommandInteraction, text: str, do_not_translate: str = None, translate_type: str = "user"):

	
	"""tbc - translate-by-client
	
	Перевод строки на язык клиента дискорда или сервера по коду языка.
	
	Типы:
		"user": перевод строки по клиента автора
		"guild": перевод строки по языку сервера из базы"""
	
	if do_not_translate is None:
		if translate_type == "user":
			try:
				translated = await googletrans.Translator().translate(text, inter.locale.name)
				return translated.text
			except:
				try:
					translated = await googletrans.Translator().translate(text, 'en')
					return translated.text
				except:
					return text
				
		elif translate_type == "guild":
			cur = await get_cursor()
			cur.execute(f"SELECT * FROM `setting` WHERE `guild_id` = {inter.guild_id}")
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
					translated = googletrans.Translator().translate(text, inter.locale.name)
					return translated.text
				except:
					try:
						translated = googletrans.Translator().translate(text, "en")
						return translated.text
					except:
						return text
					
			elif translate_type == "guild":
				cur = await get_cursor()
				cur.execute(f"SELECT * FROM `setting` WHERE `guild_id` = {inter.guild_id}")
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
