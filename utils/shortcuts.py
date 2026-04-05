import datetime
from utils import config, emojis
import inspect
import googletrans, disnake

def now_datetime(): return datetime.datetime.now(config.local_tz)
def datetime_from_timestamp(timestamp: int): return datetime.datetime.fromtimestamp(timestamp, config.local_tz)

def rmark(text: str) -> str:
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


async def get_time_in_timezone(offset: int):
  """Получить время в указанном UTC offset"""
  utc_now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=offset)
  return utc_now

def generate_pick(choices: list[str]):
  """Как в Mitsuki — alias для autocomplete."""
  return generate_autocomplete_choices(choices)

class Translation:
  def __init__(self, i18n: disnake.LocalizationProtocol):
    self.i18n = i18n

  def translate(self, inter: disnake.ApplicationCommandInteraction, key: str, **kwargs):
    text = self.i18n.get(key)
    if text:
      text = text.get(inter.locale.value)
    
    if text is None:
      return key
    
    return text.format(**kwargs) if kwargs else text

  
  # inter.guild_locale.value

  
  # return text
  
  # """tbc - translate-by-client
  
  # Перевод строки на язык клиента дискорда или сервера по коду языка.
  
  # Типы:
  #   "user": перевод строки по клиента автора
  #   "guild": перевод строки по языку сервера из базы"""
  
  # if do_not_translate is None:
  #   if translate_type == "user":
  #     try:
  #       translated = await googletrans.Translator().translate(text, _locale_dest(inter))
  #       return translated.text
  #     except:
  #       try:
  #         translated = await googletrans.Translator().translate(text, 'en')
  #         return translated.text
  #       except:
  #         return text
        
  #   elif translate_type == "guild":
  #     cur = await get_cursor()
  #     cur.execute(f"SELECT * FROM `server_settings` WHERE `guild_id` = {inter.guild_id}")
  #     server_language = cur.fetchone()
  #     try:
  #       translated = googletrans.Translator().translate(text, server_language)
  #       return translated.text
  #     except:
  #       translated = googletrans.Translator().translate(text, 'en')
  #       return translated.text
    
  # else:
  #   try:
  #     if translate_type == "user":
  #       try:
  #         translated = googletrans.Translator().translate(text, dest=_locale_dest(inter))
  #         return translated.text
  #       except:
  #         try:
  #           translated = googletrans.Translator().translate(text, dest="en")
  #           return translated.text
  #         except:
  #           return text
          
  #     elif translate_type == "guild":
  #       cur = await get_cursor()
  #       cur.execute(f"SELECT * FROM `server_settings` WHERE `guild_id` = {inter.guild_id}")
  #       server_language = cur.fetchone()
  #       try:
  #         translated = googletrans.Translator().translate(text, server_language)
  #         return translated.text
  #       except:
  #         translated = googletrans.Translator().translate(text, "en")
  #         return translated.text
        
  #   except:
  #     translated = googletrans.Translator().translate(text, 'en')
  #     return translated.text
