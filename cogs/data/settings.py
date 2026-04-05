import asyncio
import datetime
import re

import disnake
import langcodes

import cog

def _parse_color(val, default: int) -> int:
  if val in (None, ""):
    return default
  try:
    return int(val)
  except Exception:
    try:
      return int(str(val).strip(), 16)
    except Exception:
      return default


class CustomGreet(cog.ui.Modal):
  def __init__(self, bot: cog.MemeismBot, inter: cog.ApplicationCommandInteraction, type: str = ""):
    self.bot = bot
    self.type = type
    if self.type == "goodbye":
      title, clabel = "Кастомное прощание", "Текст прощания"
      self.column = "custom_fare"
      self._msg = "прощание"
    else:
      title, clabel = "Кастомное приветствие", "Текст приветствия"
      self.column = "custom_greet"
      self._msg = "приветствие"

    super().__init__(
      title=title,
      components=[
        cog.ui.TextInput(
          label=clabel,
          style=cog.TextInputStyle.paragraph,
          custom_id="inputted",
          placeholder="""
{{member.mention}}
{{member.name}}
{{server.name}}
{{server.members}}
{{server.owner}}""",
          max_length=700,
          min_length=1,
        )
      ],
      custom_id=f"custom_greet_{type or 'hi'}",
    )

  async def callback(self, inter: cog.ModalInteraction):
    guild_id = inter.guild_id
    if not await self.bot.database.sql_fetchone(
      "SELECT guild_id FROM server_settings WHERE guild_id = ?",
      (guild_id,),
    ):
      await self.bot.database.sql_execute(
        "INSERT INTO server_settings (guild_id) VALUES (?)",
        (guild_id,),
      )
    await self.bot.database.sql_execute(
      f"UPDATE server_settings SET {self.column} = ? WHERE guild_id = ?",
      (inter.text_values["inputted"], guild_id),
    )
    await inter.response.send_message(
      f"Кастомное {self._msg} установлено!",
      ephemeral=True,
    )


class EmbedGen(cog.ui.Modal):
  def __init__(self, inter: cog.ApplicationCommandInteraction, bot: cog.MemeismBot):
    self.bot = bot
    super().__init__(
      title="Пост",
      components=[
        cog.ui.TextInput(label="Текст поста", custom_id="message_content", required=False),
        cog.ui.TextInput(label="Заголовок эмбэда", custom_id="embed_title", required=False),
        cog.ui.TextInput(
          label="Текст эмбэда",
          custom_id="embed_description",
          required=False,
          style=cog.TextInputStyle.paragraph,
          max_length=3000,
        ),
        cog.ui.TextInput(
          label="Цвет эмбэда | HEX",
          custom_id="embed_color",
          required=False,
          max_length=6,
          min_length=6,
        ),
        cog.ui.TextInput(label="Картинка эмбэда", custom_id="embed_image", required=False),
      ],
      custom_id="embed_gen_post",
    )

  async def callback(self, inter: cog.ModalInteraction):
    await inter.response.defer(ephemeral=True)
    if not inter.guild:
      await inter.edit_original_response("Только на сервере.")
      return

    if not await self.bot.database.sql_fetchone(
      "SELECT guild_id FROM server_settings WHERE guild_id = ?",
      (inter.guild_id,),
    ):
      await self.bot.database.sql_execute(
        "INSERT INTO server_settings (guild_id) VALUES (?)",
        (inter.guild_id,),
      )

    row = await self.bot.database.sql_fetchone(
      "SELECT post_channel FROM server_settings WHERE guild_id = ?",
      (inter.guild_id,),
    )
    post_channel_id = row[0] if row else None
    if not post_channel_id:
      await inter.edit_original_response("Не отправлено, канал для постов не установлен!")
      return

    channel = inter.guild.get_channel(int(post_channel_id))
    if not channel or not isinstance(channel, disnake.TextChannel):
      await inter.edit_original_response("Не отправлено: канал для постов недоступен.")
      return

    tv = inter.text_values
    msg_text = tv["message_content"] or None
    embed_title = tv["embed_title"] or None
    embed_desc = tv["embed_description"] or None
    embed_color_raw = tv["embed_color"] or ""
    embed_image = tv["embed_image"] or None

    embed = None
    if embed_desc is not None or embed_title is not None or embed_image:
      embed = cog.Embed()
      if embed_title is not None:
        embed.title = embed_title
      if embed_image:
        try:
          embed.set_image(url=embed_image)
        except Exception:
          pass
      if embed_desc is not None:
        embed.description = embed_desc

    if embed is not None and embed_color_raw:
      try:
        embed.color = int(embed_color_raw, 16)
      except Exception:
        pass

    try:
      if embed is not None:
        sent = await channel.send(content=msg_text, embed=embed)
      else:
        sent = await channel.send(content=tv["message_content"] or "")
      await inter.edit_original_response(f"Отправлено {sent.jump_url}")
    except Exception as e:
      await inter.edit_original_response(f"Ошибка отправки: {e}")


class Settings(cog.Cog):
  def __init__(self, bot: cog.MemeismBot):
    self.bot = bot

  async def _ensure_row(self, guild_id: int) -> None:
    if not await self.bot.database.readServerSettings(guild_id):
      await self.bot.database.createServerSettings(
        "INSERT INTO server_settings (guild_id) VALUES (?)",
        (guild_id,),
      )

  async def parse_time(self, input_time: str) -> int:
    matches = re.findall(r"[чм]", input_time)
    time_dict = {m: input_time.count(m) for m in matches}
    seconds = 0
    for key, value in time_dict.items():
      if key == "ч":
        seconds += value * 3600
      if key == "м":
        seconds += value * 60
    return seconds

  def _bot_top_role(self, guild: disnake.Guild) -> disnake.Role | None:
    me = guild.me
    return me.top_role if me else None

  async def _render_template(self, template: str, member: cog.Member) -> str:
    out = template
    out = out.replace("{{member.mention}}", member.mention)
    out = out.replace("{{member.name}}", await self.bot.shortcuts.rmark(member.display_name))
    out = out.replace("{{server.name}}", await self.bot.shortcuts.rmark(member.guild.name))
    mc = getattr(member.guild, "member_count", None) or len(getattr(member.guild, "members", []) or [])
    out = out.replace("{{server.members}}", str(mc))
    owner = member.guild.owner
    owner_mention = owner.mention if owner else ""
    out = out.replace("{{server.owner}}", await self.bot.shortcuts.rmark(owner_mention))
    return out

  @cog.slash_command(name="guild")
  async def guild(self, inter: cog.ApplicationCommandInteraction):
    pass

  @guild.sub_command(name="setting", description="Просмотр настроек сервера")
  @cog.has_permissions(administrator=True)
  async def setting_cmd(self, inter: cog.ApplicationCommandInteraction):
    await inter.response.defer(ephemeral=True)
    await self._ensure_row(inter.guild_id)

    row = await self.bot.database.sql_fetchone(_SS_ROW, (inter.guild_id,))
    if not row:
      await inter.edit_original_response("Настройки не найдены.")
      return

    (
      _guild_id,
      mute_role,
      join_channel,
      leave_channel,
      post_channel,
      auto_role,
      private_cr_channel,
      private_category,
      logs_channel,
      average_language,
      custom_greet,
      custom_fare,
      greet_color,
      greet_image,
      fare_color,
      fare_image,
      ticket_category,
      verified_role,
      bad_words,
      bad_action,
      _notified_mods,
      _notify_ch,
      _notify_text,
      _fare_text,
    ) = row

    settings = {
      "mute_role": mute_role,
      "join_channel": join_channel,
      "leave_channel": leave_channel,
      "post_channel": post_channel,
      "auto_role": auto_role,
      "private_create_channel": private_cr_channel,
      "private_category": private_category,
      "logs_channel": logs_channel,
      "language": average_language,
      "custom_greet_text": custom_greet,
      "custom_fare_text": custom_fare,
      "custom_greet_color": greet_color,
      "custom_greet_image": greet_image,
      "custom_fare_color": fare_color,
      "custom_fare_image": fare_image,
      "ticket_category": ticket_category,
      "verified_role": verified_role,
      "bad_words": bad_words,
      "bad_action": bad_action,
    }

    verce = ""
    link = await self.bot.database.sql_fetchone(
      "SELECT guild_id1, channel1, guild_id2, channel2 FROM serververse WHERE guild_id1 = ? OR guild_id2 = ? LIMIT 1",
      (inter.guild.id, inter.guild.id),
    )
    if link:
      guild_id1, channel1, guild_id2, channel2 = link
      try:
        apposite = channel2 if int(guild_id1) == inter.guild.id else channel1
        this_ch_id = channel1 if int(guild_id1) == inter.guild.id else channel2
        apposite_channel = await self.bot.fetch_channel(int(apposite))
        mine_channel = await self.bot.fetch_channel(int(this_ch_id))
        verce = (
          f"\n**Serververce**\n{mine_channel.guild.name}(`{mine_channel.guild.id}`)\n"
          f"#{mine_channel.name} - {mine_channel.mention} `({mine_channel.id})` \n"
          f"\n{apposite_channel.guild.name}(`{apposite_channel.guild.id}`)\n"
          f"#{apposite_channel.name} - {apposite_channel.mention} `({apposite_channel.id})`"
        )
      except Exception:
        verce = ""

    def _role_mention(rid):
      if not rid:
        return "не настроено"
      try:
        r = inter.guild.get_role(int(rid))
        return r.mention if r else "не настроено"
      except Exception:
        return "не настроено"

    def _ch_mention(cid):
      if not cid:
        return "не настроено"
      try:
        ch = inter.guild.get_channel(int(cid))
        return ch.mention if ch else "не настроено"
      except Exception:
        return "не настроено"

    settings["mute_role"] = _role_mention(settings["mute_role"])
    settings["auto_role"] = _role_mention(settings["auto_role"])
    settings["join_channel"] = _ch_mention(settings["join_channel"])
    settings["leave_channel"] = _ch_mention(settings["leave_channel"])
    settings["post_channel"] = _ch_mention(settings["post_channel"])

    try:
      settings["private_create_channel"] = _ch_mention(settings["private_create_channel"])
    except Exception:
      settings["private_create_channel"] = "не настроено"

    try:
      pc = settings["private_category"]
      if pc:
        cat = inter.guild.get_channel(int(pc))
        settings["private_category"] = cat.name if cat else "не настроено"
      else:
        settings["private_category"] = (
          "категория канала для создания «приватки»"
          if settings["private_create_channel"] != "не настроено"
          else "не настроено"
        )
    except Exception:
      settings["private_category"] = "не настроено"

    settings["logs_channel"] = _ch_mention(settings["logs_channel"])

    try:
      settings["language"] = langcodes.get(str(settings["language"])).display_name()
    except Exception:
      settings["language"] = settings["language"] or "не настроено"

    try:
      settings["verified_role"] = _role_mention(verified_role)
    except Exception:
      settings["verified_role"] = "не настроено"

    greet_embed = None
    greet_text = ""
    if settings["custom_greet_text"]:
      greet = settings["custom_greet_text"]
      done_greet = greet.replace("{{member.mention}}", inter.author.mention)
      done_greet = done_greet.replace("{{member.name}}", await self.bot.shortcuts.rmark(inter.author.display_name))
      done_greet = done_greet.replace("{{server.name}}", await self.bot.shortcuts.rmark(inter.guild.name))
      done_greet = done_greet.replace("{{server.members}}", str(len(inter.guild.members)))
      done_greet = done_greet.replace("{{server.owner}}", await self.bot.shortcuts.rmark(inter.guild.owner.mention))
      color = _parse_color(settings["custom_greet_color"], 0x82E868)
      greet_embed = cog.Embed(
        title=f"[ + ] {cog.utils.escape_markdown(inter.author.display_name)}",
        description=done_greet,
        color=color,
      ).set_author(name="Это превью приветствия")
      try:
        if settings["custom_greet_image"]:
          greet_embed.set_image(url=settings["custom_greet_image"])
      except Exception:
        pass
      greet_aaaa = settings["custom_greet_image"]
      if greet_aaaa:
        greet_aaaa = f"[htttps://...]({settings['custom_greet_image']})"
      greet_text = (
        f"\n\nRAW приветствие: ```{greet}```\nЦвет приветствия: #{color:06x}\n"
        f"Картинка приветствия: {greet_aaaa or 'не настроено'}"
      )
    else:
      greet_text = ""

    fare_embed = None
    fare_text = ""
    if settings["custom_fare_text"]:
      fare = settings["custom_fare_text"]
      done_fare = fare.replace("{{member.mention}}", inter.author.mention)
      done_fare = done_fare.replace("{{member.name}}", await self.bot.shortcuts.rmark(inter.author.display_name))
      done_fare = done_fare.replace("{{server.name}}", await self.bot.shortcuts.rmark(inter.guild.name))
      done_fare = done_fare.replace("{{server.members}}", str(len(inter.guild.members)))
      done_fare = done_fare.replace("{{server.owner}}", await self.bot.shortcuts.rmark(inter.guild.owner.mention))
      color = _parse_color(settings["custom_fare_color"], 0xFD4C3C)
      fare_aaaa = settings["custom_fare_image"]
      if fare_aaaa:
        fare_aaaa = f"[htttps://...]({settings['custom_fare_image']})"
      fare_text = (
        f"\n\nRAW Прощание: ```{fare}```\nЦвет прощания: #{str(hex(color)).replace('0x', '')}\n"
        f"Картинка прощания: {fare_aaaa or 'не настроено'}"
      )
      fare_embed = cog.Embed(
        title=f"[ - ] {cog.utils.escape_markdown(inter.author.display_name)}",
        description=done_fare,
        color=color,
        author={"name": "Это превью прощания"},
      )
      try:
        if settings["custom_fare_image"]:
          fare_embed.set_image(url=settings["custom_fare_image"])
      except Exception:
        pass
    else:
      fare_text = ""

    if settings["bad_words"]:
      bw = f"\n\n - Запрещенные слова: ```{settings['bad_words']}``` - Мера наказания: `{settings['bad_action'] or 'delete'}`"
    else:
      bw = ""

    setting_embed = cog.Embed(
      title=f"Настройки {inter.guild.name}",
      description=(
        f" - Канал приветствий: {settings['join_channel']}\n\n"
        f" - Канал прощаний: {settings['leave_channel']}\n\n"
        f" - Канал оповещений: {settings['post_channel']}\n\n"
        f" - Мут роль: {settings['mute_role']}\n\n"
        f" - Авто-роль: {settings['auto_role']}\n\n"
        f" - Канал создания приватного голосового чата: {settings['private_create_channel']}\n\n"
        f" - Категория приватных чатов: {settings['private_category']}\n\n"
        f" - Канал для логов: {settings['logs_channel']}\n\n"
        f" - Роль верификации: {settings['verified_role']}\n\n"
        f" - Язык сервера по умолчанию: {settings['language']}{bw}"
        f"{verce}{greet_text}{fare_text}"
      ),
      color=0xFFFFFF,
    )

    embed_list = [setting_embed]
    if greet_embed:
      embed_list.append(greet_embed)
    if fare_embed:
      embed_list.append(fare_embed)
    await inter.edit_original_response(embeds=embed_list)

  @guild.sub_command(name="reset", description="Сброс параметра настроек или всего сервера")
  @cog.has_permissions(administrator=True)
  async def reset(
    self,
    inter: cog.ApplicationCommandInteraction,
    setting: str = cog.Param(
      autocomplete=cog.sh.generate_pick(
        [
          "Мут-роль",
          "Прощание",
          "Авто-роль",
          "Канал логов",
          "Приветствие",
          "Язык сервера",
          "Канал прощаний",
          "Роль верификации",
          "Канал публикаций",
          "Запрещенные слова",
          "Канал приветствий",
          "Категория для тикетов",
          "Язык сервера по умолчанию",
          "Категория для спец. комнат",
          "Уведомляемый канал предупреждений",
          "Канал для создания для спец. комнат",
          "Мера наказания за запрещенные слова",
          "Текст уведомления о запрещенном слове",
          "Уведомляемые модераторы предупреждений",
          "Сбросить сервер",
        ]
      ),
      description="Параметр который будет сброшен",
    ),
  ):
    await inter.response.defer(ephemeral=True)
    await self._ensure_row(inter.guild_id)

    if setting == "Сбросить сервер":
      await inter.edit_original_response(
        content=(
          "> Все настройки будут сброшены, а учётная запись сервера будет удалена из базы."
        ),
        components=[
          disnake.ui.ActionRow(
            disnake.ui.Button(
              label="Я уверен (а)",
              style=disnake.ButtonStyle.danger,
              custom_id="server_restart_setting",
            ),
            disnake.ui.Button(
              label="Нет, когда нибудь потом",
              style=disnake.ButtonStyle.secondary,
              custom_id="self_delete_button",
            ),
          )
        ],
      )
      return

    async def _u(sql: str, params: tuple):
      await self.bot.database.sql_execute(sql, params)

    gid = inter.guild_id
    if setting == "Язык сервера" or setting == "Язык сервера по умолчанию":
      await _u("UPDATE server_settings SET average_language = NULL WHERE guild_id = ?", (gid,))
      await inter.edit_original_response("Язык сервера сброшен")
    elif setting == "Запрещенные слова":
      await _u("UPDATE server_settings SET bad_words = NULL WHERE guild_id = ?", (gid,))
      await inter.edit_original_response("Запрещенные слова сброшены")
    elif setting == "Уведомляемые модераторы предупреждений":
      await _u("UPDATE server_settings SET notified_moderators = NULL WHERE guild_id = ?", (gid,))
      await inter.edit_original_response("Уведомляемые модераторы сброшены")
    elif setting == "Уведомляемый канал предупреждений":
      await _u("UPDATE server_settings SET notify_channel = NULL WHERE guild_id = ?", (gid,))
      await inter.edit_original_response("Уведомляемый канал сброшен")
    elif setting == "Мера наказания за запрещенные слова":
      await _u("UPDATE server_settings SET bad_words_action = NULL WHERE guild_id = ?", (gid,))
      await inter.edit_original_response("Мера наказания за запрещенные слова сброшена")
    elif setting == "Текст уведомления о запрещенном слове":
      await _u("UPDATE server_settings SET notify_text = NULL WHERE guild_id = ?", (gid,))
      await inter.edit_original_response("Текст уведомления о запрещенном слове сброшен")
    elif setting == "Канал приветствий":
      await _u("UPDATE server_settings SET join_channel = NULL WHERE guild_id = ?", (gid,))
      await inter.edit_original_response("Канал приветствий отключен")
    elif setting == "Канал прощаний":
      await _u("UPDATE server_settings SET leave_channel = NULL WHERE guild_id = ?", (gid,))
      await inter.edit_original_response("Канал прощаний отключен")
    elif setting == "Канал публикаций":
      await _u("UPDATE server_settings SET post_channel = NULL WHERE guild_id = ?", (gid,))
      await inter.edit_original_response("Канал публикаций отключен")
    elif setting == "Мут-роль":
      await _u("UPDATE server_settings SET mute_role = NULL WHERE guild_id = ?", (gid,))
      await inter.edit_original_response("Роль мута сброшена")
    elif setting == "Авто-роль":
      await _u("UPDATE server_settings SET auto_role = NULL WHERE guild_id = ?", (gid,))
      await inter.edit_original_response("Авто-роль сброшена")
    elif setting == "Канал логов":
      await _u("UPDATE server_settings SET log_channel = NULL WHERE guild_id = ?", (gid,))
      await inter.edit_original_response("Канал логов отключен")
    elif setting == "Роль верификации":
      await _u("UPDATE server_settings SET verified_role = NULL WHERE guild_id = ?", (gid,))
      await inter.edit_original_response("Роль верификации сброшена")
    elif setting == "Категория для тикетов":
      await _u("UPDATE server_settings SET ticket_category = NULL WHERE guild_id = ?", (gid,))
      await inter.edit_original_response("Категория для тикетов сброшена")
    elif setting == "Прощание":
      await _u(
        "UPDATE server_settings SET custom_fare = NULL, fare_color = NULL, fare_image = NULL, fare_text = NULL WHERE guild_id = ?",
        (gid,),
      )
      await inter.edit_original_response("Прощание сброшено")
    elif setting == "Приветствие":
      await _u(
        "UPDATE server_settings SET custom_greet = NULL, greet_color = NULL, greet_image = NULL WHERE guild_id = ?",
        (gid,),
      )
      await inter.edit_original_response("Приветствие сброшено")
    elif setting == "Категория для спец. комнат":
      await _u("UPDATE server_settings SET private_category = NULL WHERE guild_id = ?", (gid,))
      await inter.edit_original_response("Категория для спец. комнат сброшена")
    elif setting == "Канал для создания для спец. комнат":
      await _u("UPDATE server_settings SET private_cr_channel = NULL WHERE guild_id = ?", (gid,))
      await inter.edit_original_response("Канал для создания спец. комнат сброшен")
    else:
      await inter.edit_original_response("Неизвестный параметр.")

  @cog.listener()
  async def on_button_click(self, inter: cog.MessageInteraction):
    if inter.component.custom_id != "server_restart_setting":
      return
    await inter.response.defer(ephemeral=True)
    await self.bot.database.sql_execute(
      "DELETE FROM server_settings WHERE guild_id = ?",
      (inter.guild_id,),
    )
    await inter.edit_original_response("Настройки сервера удалены.", components=None)

  @guild.sub_command(name="mute", description="Выдать роль мута на время")
  @cog.has_permissions(manage_roles=True)
  async def guild_mute(
    self,
    inter: cog.ApplicationCommandInteraction,
    member: cog.Member = cog.Param(description="Пользователь получающий роль мута"),
    time: str = cog.Param(description="Время мута. Формат: ##ч##м"),
  ):
    await inter.response.defer(ephemeral=True)
    await self._ensure_row(inter.guild_id)

    row = await self.bot.database.sql_fetchone(
      "SELECT mute_role FROM server_settings WHERE guild_id = ?",
      (inter.guild_id,),
    )
    mute_rid = row[0] if row else None
    if not mute_rid:
      await inter.edit_original_response(
        "Ваш сервер недостаточно настроен (роль мута).\n"
        "Выберите роль мута в команде `/guild set mute_role`."
      )
      return

    mute_role = inter.guild.get_role(int(mute_rid))
    if not mute_role:
      await inter.edit_original_response("Роль мута не найдена на сервере.")
      return

    sec = await self.parse_time(time)
    if sec <= 0:
      await inter.edit_original_response("Укажите время (например 1ч30м).")
      return

    await member.add_roles(mute_role)
    delta = datetime.timedelta(seconds=sec)
    until = int(datetime.datetime.now().timestamp() + sec)
    await inter.edit_original_response(
      f"{member.mention} замучен на {delta} / <t:{until}:R>"
    )
    await asyncio.sleep(sec)
    try:
      await member.remove_roles(mute_role)
    except Exception:
      pass

  @guild.sub_command(name="post", description="Отправить пост в канал оповещений")
  @cog.has_permissions(manage_webhooks=True)
  async def post_cmd(self, inter: cog.ApplicationCommandInteraction):
    await inter.response.send_modal(EmbedGen(inter, self.bot))

  @guild.sub_command_group(name="set")
  async def s3t(self, inter: cog.ApplicationCommandInteraction):
    pass

  @s3t.sub_command(name="annoucment_channel", description="Канал для постов / оповещений")
  @cog.has_permissions(administrator=True)
  async def set_annoucment(
    self,
    inter: cog.ApplicationCommandInteraction,
    channel: cog.TextChannel = cog.Param(description="Канал оповещений будет занесен в базу"),
  ):
    await inter.response.defer(ephemeral=True)
    await self._ensure_row(inter.guild_id)
    await self.bot.database.sql_execute(
      "UPDATE server_settings SET post_channel = ? WHERE guild_id = ?",
      (channel.id, inter.guild_id),
    )
    await inter.edit_original_response(f"Канал оповещений установлен на <#{channel.id}>")

  @s3t.sub_command(name="farewell_image", description="Баннер для прощаний")
  @cog.has_permissions(administrator=True)
  async def set_farewell_image(
    self,
    inter: cog.ApplicationCommandInteraction,
    image: str = cog.Param(description="Ссылка на изображение с огурцами"),
  ):
    await inter.response.defer(ephemeral=True)
    await self._ensure_row(inter.guild_id)
    await self.bot.database.sql_execute(
      "UPDATE server_settings SET fare_image = ? WHERE guild_id = ?",
      (image, inter.guild_id),
    )
    await inter.edit_original_response(f"Баннер для прощаний установлен[.]({image})")

  @s3t.sub_command(name="greetings_image", description="Баннер для приветствий")
  @cog.has_permissions(administrator=True)
  async def set_greet_image(
    self,
    inter: cog.ApplicationCommandInteraction,
    image: str = cog.Param(description="Ссылка на изображение с ананасами"),
  ):
    await inter.response.defer(ephemeral=True)
    await self._ensure_row(inter.guild_id)
    await self.bot.database.sql_execute(
      "UPDATE server_settings SET greet_image = ? WHERE guild_id = ?",
      (image, inter.guild_id),
    )
    await inter.edit_original_response(f"Баннер для приветствий установлен[.]({image})")

  @s3t.sub_command(name="greetings_color", description="Цвет приветствий (HEX)")
  @cog.has_permissions(administrator=True)
  async def set_greet_color(
    self,
    inter: cog.ApplicationCommandInteraction,
    hex_code: str = cog.Param(
      description="Код цвета в HEX | Пример: FFFFFF ; 888fff ; 000444",
      max_length=6,
      min_length=6,
    ),
  ):
    await inter.response.defer(ephemeral=True)
    await self._ensure_row(inter.guild_id)
    try:
      done_color = int(hex_code, 16)
    except Exception:
      await inter.edit_original_response("Не удалось сохранить цвет! Проверьте формат!")
      return
    await self.bot.database.sql_execute(
      "UPDATE server_settings SET greet_color = ? WHERE guild_id = ?",
      (str(done_color), inter.guild_id),
    )
    await inter.edit_original_response(
      embed=cog.Embed(title=f"Цвет приветствий установлен на: #{hex_code}", color=done_color)
    )

  @s3t.sub_command(name="farewell_color", description="Цвет прощаний (HEX)")
  @cog.has_permissions(administrator=True)
  async def set_farewell_color(
    self,
    inter: cog.ApplicationCommandInteraction,
    hex_code: str = cog.Param(
      description="Код цвета в HEX | Пример: FFFFFF ; 888fff ; 000444",
      max_length=6,
      min_length=6,
    ),
  ):
    await inter.response.defer(ephemeral=True)
    await self._ensure_row(inter.guild_id)
    try:
      done_color = int(hex_code, 16)
    except Exception:
      await inter.edit_original_response("Не удалось сохранить цвет! Проверьте формат!")
      return
    await self.bot.database.sql_execute(
      "UPDATE server_settings SET fare_color = ? WHERE guild_id = ?",
      (str(done_color), inter.guild_id),
    )
    await inter.edit_original_response(
      embed=cog.Embed(title=f"Цвет прощаний установлен на: #{hex_code}", color=done_color)
    )

  @s3t.sub_command(name="default_language", description="Язык сервера по умолчанию")
  @cog.has_permissions(administrator=True)
  async def set_language(
    self,
    inter: cog.ApplicationCommandInteraction,
    code: str = cog.Param(description="Код языка | Examples: ru, en, br, fr"),
  ):
    await inter.response.defer(ephemeral=True)
    if not langcodes.tag_is_valid(code):
      await inter.edit_original_response("Пожалуйста введите корректный код языка!")
      return
    await self._ensure_row(inter.guild_id)
    await self.bot.database.sql_execute(
      "UPDATE server_settings SET average_language = ? WHERE guild_id = ?",
      (code, inter.guild_id),
    )
    await inter.edit_original_response(
      f"Язык сервера по умолчанию установлен на: {langcodes.get(code).display_name()}\n\n"
      "Но учтите язык сервера по умолчанию используется в случаях когда:\n"
      "1. Я не могу перевести ответ на язык пользователя\n"
      "2. В уведомлениях ( приветствия, логи и уведомления владельцу сервера )"
    )

  @s3t.sub_command(name="greetings_channel", description="Канал приветствий")
  @cog.has_permissions(administrator=True)
  async def set_greetings_channel(
    self,
    inter: cog.ApplicationCommandInteraction,
    channel: cog.TextChannel = cog.Param(description="Канал приветствий будет занесен в базу"),
  ):
    await inter.response.defer(ephemeral=True)
    await self._ensure_row(inter.guild_id)
    await self.bot.database.sql_execute(
      "UPDATE server_settings SET join_channel = ? WHERE guild_id = ?",
      (channel.id, inter.guild_id),
    )
    await inter.edit_original_response(f"Канал приветствий установлен на <#{channel.id}>")

  @s3t.sub_command(name="add_bad_word", description="Добавить запрещённые слова")
  @cog.has_permissions(administrator=True)
  async def add_bad_word(
    self,
    inter: cog.ApplicationCommandInteraction,
    word_s: str = cog.Param(description="Слова (через пробел) или слово"),
  ):
    await inter.response.defer(ephemeral=True)
    await self._ensure_row(inter.guild_id)
    row = await self.bot.database.sql_fetchone(
      "SELECT bad_words FROM server_settings WHERE guild_id = ?",
      (inter.guild_id,),
    )
    old = (row[0] if row and row[0] else "") or ""
    old_words = (old.strip() + " " + word_s.strip()).strip() if old.strip() else word_s.strip()
    await self.bot.database.sql_execute(
      "UPDATE server_settings SET bad_words = ? WHERE guild_id = ?",
      (old_words, inter.guild_id),
    )
    await inter.edit_original_response("Новые слова добавлены!")

  @s3t.sub_command(name="custom_greet", description="Текст приветствия (кастом)")
  @cog.has_permissions(administrator=True)
  async def set_custom_greet(self, inter: cog.ApplicationCommandInteraction):
    await inter.response.send_modal(CustomGreet(self.bot, inter, ""))

  @s3t.sub_command(name="custom_farewell", description="Текст прощания (кастом)")
  @cog.has_permissions(administrator=True)
  async def set_custom_farewell(self, inter: cog.ApplicationCommandInteraction):
    await inter.response.send_modal(CustomGreet(self.bot, inter, "goodbye"))

  @s3t.sub_command(name="private_create", description="Голосовой канал для создания приваток")
  @cog.has_permissions(administrator=True)
  async def set_private_create(
    self,
    inter: cog.ApplicationCommandInteraction,
    channel: cog.VoiceChannel = cog.Param(description="Канал для создания приватки будет занесен в базу"),
  ):
    await inter.response.defer(ephemeral=True)
    await self._ensure_row(inter.guild_id)
    await self.bot.database.sql_execute(
      "UPDATE server_settings SET private_cr_channel = ? WHERE guild_id = ?",
      (channel.id, inter.guild_id),
    )
    row = await self.bot.database.sql_fetchone(_SS_ROW, (inter.guild_id,))
    pcc = row[6] if row else channel.id
    await inter.edit_original_response(
      f"Канал для создания приватного голосового канала установлен на <#{pcc}>"
    )

  @s3t.sub_command(name="private_category", description="Категория для приватных голосовых")
  @cog.has_permissions(administrator=True)
  async def set_private_category(
    self,
    inter: cog.ApplicationCommandInteraction,
    category: cog.CategoryChannel = cog.Param(description="Категория будет занесена в базу"),
  ):
    await inter.response.defer(ephemeral=True)
    await self._ensure_row(inter.guild_id)
    await self.bot.database.sql_execute(
      "UPDATE server_settings SET private_category = ? WHERE guild_id = ?",
      (category.id, inter.guild_id),
    )
    await inter.edit_original_response(
      f"Категория для созданных приватных голосовых каналов установлена на {category.name}"
    )

  @s3t.sub_command(name="notify_channel", description="Канал уведомлений от бота")
  @cog.has_permissions(administrator=True)
  async def set_notify_channel(
    self,
    inter: cog.ApplicationCommandInteraction,
    channel: cog.TextChannel = cog.Param(description="Канал для уведомлений от бота"),
  ):
    await inter.response.defer(ephemeral=True)
    await self._ensure_row(inter.guild_id)
    await self.bot.database.sql_execute(
      "UPDATE server_settings SET notify_channel = ? WHERE guild_id = ?",
      (channel.id, inter.guild_id),
    )
    await inter.edit_original_response(f"Канал для уведомлений установлен - {channel.mention}")

  @s3t.sub_command(name="farewell_channel", description="Канал прощаний")
  @cog.has_permissions(administrator=True)
  async def set_farewell_channel(
    self,
    inter: cog.ApplicationCommandInteraction,
    channel: cog.TextChannel = cog.Param(description="Канал прощаний будет занесен в базу"),
  ):
    await inter.response.defer(ephemeral=True)
    await self._ensure_row(inter.guild_id)
    await self.bot.database.sql_execute(
      "UPDATE server_settings SET leave_channel = ? WHERE guild_id = ?",
      (channel.id, inter.guild_id),
    )
    await inter.edit_original_response(f"Канал прощаний установлен на {channel.mention}")

  @s3t.sub_command(name="set_bad_word_penalty", description="Мера наказания за запрещённые слова")
  @cog.has_permissions(administrator=True)
  async def set_bad_word_penalty(
    self,
    inter: cog.ApplicationCommandInteraction,
    type: str = cog.Param(
      default="info",
      description="Тип наказаний (или info — справка)",
    ),
  ):
    await inter.response.defer(ephemeral=True)
    if type != "info":
      await self._ensure_row(inter.guild_id)
      await self.bot.database.sql_execute(
        "UPDATE server_settings SET bad_words_action = ? WHERE guild_id = ?",
        (type, inter.guild_id),
      )
      await inter.edit_original_response(f"Тип наказаний за запрещенные слова установлен на `{type}`")
    else:
      await inter.edit_original_response(
        embed=cog.Embed(
          title="Типы существующих наказаний",
          description=(
            "**К каждому наказанию можно добавить `d` в начало чтобы дополнительно удалить сообщение**\n"
            "**`mute`** - мут участника при отправке запрещенного слова\n"
            "**`notify_moderators`** - уведомление модераторов(если установлены) о отправке запрещенного слова\n"
            "**`delete`** - просто удалить сообщение\n"
            "**`notify_channel`** - уведомление в установленный канал о отправке запрещенного слова\n"
          ),
          color=0x2F3136,
        )
      )

  @s3t.sub_command(name="auto_role", description="Авто-роль для новичков")
  @cog.has_permissions(administrator=True)
  async def set_autorole(
    self,
    inter: cog.ApplicationCommandInteraction,
    role: cog.Role = cog.Param(description="Эта роль будет выдаваться каждому новому участнику"),
  ):
    await inter.response.defer(ephemeral=True)
    await self._ensure_row(inter.guild_id)
    await self.bot.database.sql_execute(
      "UPDATE server_settings SET auto_role = ? WHERE guild_id = ?",
      (role.id, inter.guild_id),
    )
    bot_tr = self._bot_top_role(inter.guild)
    if bot_tr and role.position > bot_tr.position:
      err = cog.Embed(
        color=0xDB553F,
        title="Роль бота ниже той что вы установили!",
        description=(
          f"Бот не может выдавать роли которые выше его специальной роли!\n\n"
          f"Поднимите роль {bot_tr.mention} выше {role.mention}"
        ),
      )
      await inter.edit_original_response(
        content=f"Теперь роль {role.mention} будет иметь каждый новый участник",
        embed=err,
      )
    else:
      await inter.edit_original_response(f"Теперь роль {role.mention} будет иметь каждый новый участник")

  @s3t.sub_command(name="mute_role", description="Роль мута")
  @cog.has_permissions(administrator=True)
  async def mute_role_cmd(
    self,
    inter: cog.ApplicationCommandInteraction,
    role: cog.Role = cog.Param(description="Роль которая будет даваться на время по команде /guild mute"),
  ):
    await inter.response.defer(ephemeral=True)
    try:
      role = inter.guild.get_role(cog.utils.get(inter.guild.roles, name=role.name).id)
    except Exception:
      pass
    await self._ensure_row(inter.guild_id)
    await self.bot.database.sql_execute(
      "UPDATE server_settings SET mute_role = ? WHERE guild_id = ?",
      (role.id, inter.guild_id),
    )
    bot_tr = self._bot_top_role(inter.guild)
    if bot_tr and role.position > bot_tr.position:
      err = cog.Embed(
        color=0xDB553F,
        title="Роль бота ниже той что вы установили!",
        description=(
          f"## Бот не может выдавать роли которые выше его специальной роли!\n\n"
          f"**Поднимите роль {bot_tr.mention} выше {role.mention}**"
        ),
      )
      await inter.edit_original_response(
        content=f"Ролью мута теперь является <@&{role.id}>",
        embed=err,
      )
    else:
      await inter.edit_original_response(f"Ролью мута теперь является <@&{role.id}>")

  @s3t.sub_command(name="logs_channel", description="Канал логов")
  @cog.has_permissions(administrator=True)
  async def logs_channel_cmd(
    self,
    inter: cog.ApplicationCommandInteraction,
    channel: cog.TextChannel = cog.Param(
      description="Канал в который будут отправляться уведомления о событиях на сервере / логи"
    ),
  ):
    await inter.response.defer(ephemeral=True)
    await self._ensure_row(inter.guild_id)
    await self.bot.database.sql_execute(
      "UPDATE server_settings SET log_channel = ? WHERE guild_id = ?",
      (channel.id, inter.guild_id),
    )
    await inter.edit_original_response(f"Каналом логов теперь является -> <#{channel.id}>")

  @s3t.sub_command(name="verified_role", description="Роль верификации")
  @cog.has_permissions(administrator=True)
  async def set_verified_role(
    self,
    inter: cog.ApplicationCommandInteraction,
    role: cog.Role = cog.Param(description="Роль, которая будет выдаваться после верификации"),
  ):
    await inter.response.defer(ephemeral=True)
    try:
      role = inter.guild.get_role(cog.utils.get(inter.guild.roles, name=role.name).id)
    except Exception:
      pass
    await self._ensure_row(inter.guild_id)
    await self.bot.database.sql_execute(
      "UPDATE server_settings SET verified_role = ? WHERE guild_id = ?",
      (role.id, inter.guild_id),
    )
    row = await self.bot.database.sql_fetchone(_SS_ROW, (inter.guild_id,))
    vr = row[17] if row else role.id
    ar = row[5] if row else None
    bot_tr = self._bot_top_role(inter.guild)
    if bot_tr and role.position > bot_tr.position:
      err = cog.Embed(
        color=0xDB553F,
        title="Роль бота ниже роли верификации!",
        description=(
          f"## Бот не может выдавать роли которые выше его специальной роли!\n\n"
          f"**Поднимите роль {bot_tr.mention} выше {role.mention}**"
        ),
      )
      await inter.edit_original_response(
        content=f"Ролью верификации теперь является <@&{vr}>",
        embed=err,
      )
    elif ar and int(ar) == int(role.id):
      await inter.edit_original_response(
        "Роль верификации установлена!\n> ⚠ Предупреждение: авто-роль и роль верификации одинаковы. "
        "Мы не рекомендуем выдавать роль верификации автоматически!\n"
      )
    else:
      await inter.edit_original_response(f"Ролью верификации теперь является <@&{vr}>")

  @s3t.sub_command(name="ticket_category", description="Категория для тикетов")
  @cog.has_permissions(administrator=True)
  async def set_ticket_category(
    self,
    inter: cog.ApplicationCommandInteraction,
    category: cog.CategoryChannel = cog.Param(description="Категория тикетов"),
  ):
    await inter.response.defer(ephemeral=True)
    await self._ensure_row(inter.guild_id)
    await self.bot.database.sql_execute(
      "UPDATE server_settings SET ticket_category = ? WHERE guild_id = ?",
      (category.id, inter.guild_id),
    )
    await inter.edit_original_response(f"Категория тикетов установлена: {category.mention}")

  @s3t.sub_command(name="notified_moderators", description="ID модераторов для уведомлений (через пробел)")
  @cog.has_permissions(administrator=True)
  async def set_notified_moderators(
    self,
    inter: cog.ApplicationCommandInteraction,
    moderator_ids: str = cog.Param(description="Пример: 123 456 789"),
  ):
    await inter.response.defer(ephemeral=True)
    await self._ensure_row(inter.guild_id)
    await self.bot.database.sql_execute(
      "UPDATE server_settings SET notified_moderators = ? WHERE guild_id = ?",
      (moderator_ids.strip(), inter.guild_id),
    )
    await inter.edit_original_response("Список уведомляемых модераторов обновлён.")

  @cog.listener()
  async def on_member_join(self, member: cog.Member):
    if not member.guild or member.bot:
      return

    serversettings = await self.bot.database.readServerSettings(member.guild.id)
    
    if not serversettings:
      return
    serversettings = serversettings[0]

    if serversettings.auto_role:
      try:
        r = member.guild.get_role(int(serversettings.auto_role))
        if r:
          await member.add_roles(r)
      except Exception:
        pass

    if not serversettings.join_channel:
      return

    try:
      channel = await member.guild.fetch_channel(int(serversettings.join_channel))
    except Exception:
      try:
        await member.guild.owner.send(
          embed=cog.Embed(
            title="Ошибка настроек сервера",
            description=(
              "Ошибка с каналом отправки уведомлений о входе пользователей.\n"
              "Проверьте мои права отправлять туда сообщения или переустановите/пересоздайте канал"
            ),
            color=0xEF5350,
          )
        )
      except Exception:
        pass
      return
    
    if not channel:
      return

    if not serversettings.greet_text:
      embed = cog.Embed(
        title=f"[ + ] {cog.utils.escape_markdown(member.display_name)}",
        description=f"{member.mention} now with us!",
        color=0x82E868,
      )
      if serversettings.greet_image:
        try:
          embed.set_image(url=serversettings.greet_image)
        except Exception:
          pass
      await channel.send(content=f"||{member.mention}||", embed=embed)
      return

    try:
      done = await self._render_template(serversettings.greet_text, member)
      color = _parse_color(serversettings.greet_color, 0x82E868)
      embed = cog.Embed(
        title=f"[ + ] {cog.utils.escape_markdown(member.display_name)}",
        description=done,
        color=color,
      )
      if serversettings.greet_image:
        try:
          embed.set_image(url=serversettings.greet_image)
        except Exception:
          pass
      await channel.send(content=f"||{member.mention}||", embed=embed)
    except Exception:
      try:
        await member.guild.owner.send(
          embed=cog.Embed(
            title="Ошибка настроек сервера",
            description=(
              "Ошибка с каналом отправки уведомлений о входе пользователей.\n"
              "Проверьте мои права отправлять туда сообщения или переустановите/пересоздайте канал"
            ),
            color=0xEF5350,
          )
        )
      except Exception:
        pass

  @cog.listener()
  async def on_member_remove(self, member: cog.Member):
    if not member.guild or member.bot:
      return

    row = await self.bot.database.sql_fetchone(
      """
      SELECT leave_channel, custom_fare, fare_color, fare_image
      FROM server_settings WHERE guild_id = ? LIMIT 1
      """,
      (member.guild.id,),
    )
    if not row:
      return

    leave_channel_id, custom_fare, fare_color, fare_image = row
    if not leave_channel_id:
      return

    try:
      channel = await member.guild.fetch_channel(int(leave_channel_id))
    except Exception:
      try:
        await member.guild.owner.send(
          embed=cog.Embed(
            title="Ошибка настроек сервера",
            description=(
              "Ошибка с каналом отправки уведомлений о входе пользователей.\n"
              "Проверьте мои права отправлять туда сообщения или переустановите/пересоздайте канал"
            ),
            color=0xEF5350,
          )
        )
      except Exception:
        pass
      return
    if not channel:
      return

    if not custom_fare:
      embed = cog.Embed(
        title=f"[ - ] {cog.utils.escape_markdown(member.display_name)}",
        description=f"{member.mention} вышел(а)!",
        color=0xFD4C3C,
      )
      if fare_image:
        try:
          embed.set_image(url=fare_image)
        except Exception:
          pass
      await channel.send(content=f"||{member.mention}||", embed=embed)
      return

    try:
      done = await self._render_template(custom_fare, member)
      color = _parse_color(fare_color, 0xFD4C3C)
      embed = cog.Embed(
        title=f"[ - ] {cog.utils.escape_markdown(member.display_name)}",
        description=done,
        color=color,
      )
      if fare_image:
        try:
          embed.set_image(url=fare_image)
        except Exception:
          pass
      await channel.send(embed=embed)
    except Exception:
      try:
        await member.guild.owner.send(
          embed=cog.Embed(
            title="Ошибка настроек сервера",
            description=(
              "Ошибка с каналом отправки уведомлений о входе пользователей.\n"
              "Проверьте мои права отправлять туда сообщения или переустановите/пересоздайте канал"
            ),
            color=0xEF5350,
          )
        )
      except Exception:
        pass


def setup(bot: cog.MemeismBot):
  bot.add_cog(Settings(bot))
  bot.cog_reload(__name__)