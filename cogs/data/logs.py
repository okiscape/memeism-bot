import datetime

import cog


class AuditLog(cog.Cog):
	def __init__(self, bot: cog.MemeismBot):
		self.bot = bot

	@cog.slash_command(
		name="set_log_channel",
		description="Установить канал для логов (per-server).",
		contexts=cog.InteractionContextTypes(guild=True),
	)
	async def set_log_channel(
		self,
		inter: cog.ApplicationCommandInteraction,
		channel: cog.TextChannel = cog.Param(description="Куда отправлять логи"),
	):
		await inter.response.defer(ephemeral=True)
		if not inter.guild:
			return
		# Разрешаем либо админам, либо тем, у кого есть manage_guild.
		perms = getattr(inter.author, "guild_permissions", None)
		if perms and not (getattr(perms, "administrator", False) or getattr(perms, "manage_guild", False)):
			await inter.edit_original_response("Нет прав для настройки логов.")
			return

		query = """
		INSERT INTO server_settings (guild_id, log_channel)
		VALUES (?, ?)
		ON CONFLICT(guild_id) DO UPDATE SET log_channel=excluded.log_channel
		"""
		await self.bot.database.sql_execute(query, (inter.guild.id, channel.id))

		embed = cog.Embed(
			title="Логи настроены",
			description=f"Канал логов: {channel.mention}",
			color=0x2F3136,
		)
		await inter.edit_original_response(embed=embed)

	async def _log_channel_id(self, guild_id: int) -> int | None:
		row = await self.bot.database.sql_fetchone(
			"SELECT log_channel FROM server_settings WHERE guild_id = ?",
			(guild_id,),
		)
		if not row or row[0] in (None, 0):
			return None
		return int(row[0])

	async def _send_log(self, guild_id: int, embed: cog.Embed) -> None:
		ch_id = await self._log_channel_id(guild_id)
		if not ch_id:
			return
		try:
			channel = await self.bot.fetch_channel(ch_id)
			if channel:
				await channel.send(embed=embed)
		except Exception:
			pass

	@cog.listener()
	async def on_message_edit(self, before: cog.Message, after: cog.Message) -> None:
		if before.author.bot or not after.guild:
			return
		if before.content == after.content:
			return

		ch_id = await self._log_channel_id(after.guild.id)
		if not ch_id:
			return

		embed = cog.Embed(color=0x2F3136, timestamp=datetime.datetime.now())
		embed.description = (
			f"> До:\n```{await cog.shortcuts.rmark(before.content)}```\n\n"
			f"> После:\n```{await cog.shortcuts.rmark(after.content)}```\n\n"
			f"> Автор:\n{before.author.mention} ({before.author.id})\n"
			f"[перейти к сообщению]({after.jump_url})"
		)
		embed.set_thumbnail(url=after.author.display_avatar.url)
		embed.set_author(
			name="Сообщение обновлено",
			icon_url="https://cdn.discordapp.com/attachments/914931081130696734/1158831359456985190/1696357157590.png?ex=651dad4e&is=651c5bce&hm=792a58a62586123f7fa70623235f81239f4b4ba5b566154ea8209e7c2e59d10b&",
		)
		await self._send_log(after.guild.id, embed)

	@cog.listener()
	async def on_message_delete(self, message: cog.Message):
		if not message.guild:
			return
		if message.author and message.author.bot:
			return
		if not await self._log_channel_id(message.guild.id):
			return

		n = "\n"
		atts = [a.url for a in message.attachments] or ["отсутствуют"]
		body = message.content or "*(пусто)*"
		author_line = (
			f"{message.author.mention}({message.author.id})"
			if message.author
			else "*(неизвестно)*"
		)
		thumb = message.author.display_avatar.url if message.author else None
		embed = cog.Embed(color=0x2F3136, timestamp=datetime.datetime.now())
		embed.description = (
			f"> Содержимое:\n{body}\n\n"
			f"> Вложения: {n.join(atts)}"
			f"> Автор:\n{author_line}"
		)
		if thumb:
			embed.set_thumbnail(url=thumb)
		embed.set_author(
			name="Сообщение удалено",
			icon_url="https://cdn.discordapp.com/attachments/914931081130696734/1158831360019013753/1696357158246.png?ex=651dad4e&is=651c5bce&hm=dc86e514b332cbf780dcc21bf5f435f0237ff75fc471aab5eaa327f607c208ad&",
		)
		await self._send_log(message.guild.id, embed)

	@cog.listener()
	async def on_member_join(self, member: cog.Member):
		if not await self._log_channel_id(member.guild.id):
			return
		embed = cog.Embed(color=0x2F3136, timestamp=datetime.datetime.now())
		embed.description = f"{member.mention} зашëл на сервер"
		embed.set_thumbnail(url=member.display_avatar.url)
		embed.set_author(
			name="Новый участник",
			icon_url="https://cdn.discordapp.com/attachments/914931081130696734/1158831360635572245/1696357163750.png?ex=651dad4e&is=651c5bce&hm=d4be9abb6b3ea5eebe1e04c050e0337e3623b7df3ee8f29640d899ae6635fbc1&",
		)
		await self._send_log(member.guild.id, embed)

	@cog.listener()
	async def on_member_remove(self, member: cog.Member):
		if not await self._log_channel_id(member.guild.id):
			return
		embed = cog.Embed(color=0x2F3136, timestamp=datetime.datetime.now())
		embed.description = f"{member.mention} вышëл с сервера"
		embed.set_thumbnail(url=member.display_avatar.url)
		embed.set_author(
			name="Участник ушёл",
			icon_url="https://cdn.discordapp.com/attachments/914931081130696734/1158831358970433647/1696357155286.png?ex=651dad4e&is=651c5bce&hm=5f2e3f9d7c9e98cc0428d847f002ee36f89ad65cd36becc0177ef3490efc38fb&",
		)
		await self._send_log(member.guild.id, embed)


def setup(bot):
	bot.add_cog(AuditLog(bot))
	bot.cog_reload(__name__)
