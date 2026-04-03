import io

import cog


def _author_hook_name(member: cog.Member | cog.User) -> str:
	return str(member.name or member.global_name or member.display_name)


class Serververse(cog.Cog):
	def __init__(self, bot: cog.MemeismBot):
		self.bot = bot

	async def _get_link_row(self, guild_id: int) -> tuple | None:
		return await self.bot.database.sql_fetchone(
			"""
			SELECT guild_id1, channel1, guild_id2, channel2
			FROM serververse
			WHERE guild_id1 = ? OR guild_id2 = ?
			LIMIT 1
			""",
			(guild_id, guild_id),
		)

	async def _send_via_webhook(
		self,
		dest_channel_id: int,
		author: cog.User,
		message: cog.Message,
	) -> None:
		dest = await self.bot.fetch_channel(dest_channel_id)
		if not dest:
			return

		hook_name = _author_hook_name(author)

		hooks = await dest.webhooks()
		hook = next((h for h in hooks if getattr(h, "name", None) == hook_name), None)

		if hook is None:
			try:
				hook = await dest.create_webhook(
					name=hook_name,
					avatar=author.avatar,
					reason="ServerVerce",
				)
			except Exception:
				hook = await dest.create_webhook(name=hook_name, reason="ServerVerce")

		files = []
		for attachment in message.attachments or []:
			try:
				data = await attachment.read()
				buf = io.BytesIO(data)
				buf.seek(0)
				files.append(cog.File(buf, attachment.filename))
			except Exception:
				pass

		await hook.send(
			content=message.content or None,
			avatar_url=str(author.display_avatar.url),
			files=files or None,
		)

	@cog.listener()
	async def on_message(self, message: cog.Message) -> None:
		if not message.guild:
			return
		if not message.author or message.author.bot:
			return
		if not message.content and not message.attachments:
			return

		row = await self._get_link_row(message.guild.id)
		if not row:
			return

		guild_id1, channel1, guild_id2, channel2 = row

		src_channel_id = message.channel.id
		dest_channel_id: int | None = None

		if src_channel_id == int(channel1):
			dest_channel_id = int(channel2) if channel2 else None
		elif src_channel_id == int(channel2):
			dest_channel_id = int(channel1) if channel1 else None

		if not dest_channel_id:
			return

		await self._send_via_webhook(dest_channel_id, message.author, message)

	@cog.slash_command(
		name="serververce",
		description="Связать чаты между серверами (ServerVerce).",
	)
	async def verce(self, inter: cog.ApplicationCommandInteraction):
		pass

	@verce.sub_command(name="create_link")
	@cog.has_permissions(administrator=True)
	async def create_verce(
		self,
		inter: cog.ApplicationCommandInteraction,
		apposite: str = cog.Param(
			description="ID сервера, с которым будем связать чаты",
		),
	):
		if not inter.guild:
			return
		await inter.response.defer(ephemeral=True)

		try:
			apposite_id = int(apposite)
		except ValueError:
			await inter.edit_original_response("Неверный ID сервера.")
			return

		row = await self._get_link_row(apposite_id)
		if row:
			guild_id1, channel1, guild_id2, channel2 = row
			if int(guild_id1) == apposite_id:
				await self.bot.database.sql_execute(
					"UPDATE serververse SET guild_id2 = ?, channel2 = ? WHERE guild_id1 = ?",
					(inter.guild.id, inter.channel.id, apposite_id),
				)
			else:
				await self.bot.database.sql_execute(
					"UPDATE serververse SET guild_id1 = ?, channel1 = ? WHERE guild_id2 = ?",
					(inter.guild.id, inter.channel.id, apposite_id),
				)
			await inter.edit_original_response("Связь установлена!")
			return

		await self.bot.database.sql_execute(
			"""
			INSERT INTO serververse (guild_id1, channel1, guild_id2, channel2)
			VALUES (?, ?, ?, ?)
			""",
			(inter.guild.id, inter.channel.id, apposite_id, 0),
		)
		await inter.edit_original_response(
			"Первый сервер установлен!\nПовторите это действие на втором сервере и чаты будут связаны!"
		)

	@verce.sub_command(name="change_channel")
	@cog.has_permissions(administrator=True)
	async def change_verce(self, inter: cog.ApplicationCommandInteraction):
		if not inter.guild:
			return
		await inter.response.defer(ephemeral=True)

		row = await self._get_link_row(inter.guild.id)
		if not row:
			await inter.edit_original_response("Связь не найдена.")
			return

		guild_id1, channel1, guild_id2, channel2 = row

		if int(guild_id1) == inter.guild.id:
			await self.bot.database.sql_execute(
				"UPDATE serververse SET channel1 = ? WHERE guild_id1 = ?",
				(inter.channel.id, inter.guild.id),
			)
			await inter.edit_original_response("Канал перенаправления сообщений изменён!")
			return

		if int(guild_id2) == inter.guild.id:
			await self.bot.database.sql_execute(
				"UPDATE serververse SET channel2 = ? WHERE guild_id2 = ?",
				(inter.channel.id, inter.guild.id),
			)
			await inter.edit_original_response("Канал перенаправления сообщений изменён!")
			return

		await inter.edit_original_response("Не удалось понять, какую сторону менять.")


def setup(bot: cog.MemeismBot):
	bot.add_cog(Serververse(bot))
	bot.cog_reload(__name__)

