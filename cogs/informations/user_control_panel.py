import random

import cog
from utils import config


async def _embed_500(bot: cog.MemeismBot, inter: cog.MessageInteraction, description: str) -> cog.Embed:
	return (
		cog.Embed(
			title="<:X_:1050456898450763857> | Ошибка: `500`",
			description=await bot.shortcuts.tbc(inter, description),
			color=config.pastel_red,
			type="article",
		)
		.set_thumbnail(url=config.embed_err_thumb)
		.set_image(url=config.embed_err_banner)
	)


class KickModal(cog.ui.Modal):
	def __init__(self, target: cog.Member, bot: cog.MemeismBot):
		self.target = target
		self.bot = bot
		comp = [
			cog.ui.TextInput(
				label="Причина кика",
				custom_id="kick_reason",
				style=cog.TextInputStyle.short,
				placeholder="Можно оставить пустой*",
				required=False,
			)
		]
		super().__init__(title="Подтверждение кика", components=comp)

	async def callback(self, inter: cog.ModalInteraction):
		reason = inter.text_values.get("kick_reason") or None
		await self.target.kick(reason=reason)
		await inter.response.send_message(
			embed=cog.Embed(
				title=f"{self.target.display_name} кикнут!",
				color=0xFFD400,
			),
			ephemeral=True,
		)


class BanCheck(cog.ui.Modal):
	def __init__(self, target: cog.Member, bot: cog.MemeismBot):
		self.target = target
		self.bot = bot
		self.captcha_1 = random.randint(0, 999999)
		self.captcha_2 = random.randint(0, 999999)
		self.captcha_3 = random.randint(0, 999999)
		self.captcha_4 = random.randint(0, 999999)
		components = [
			cog.ui.TextInput(
				label="Введи капчу для подтверждения бана",
				custom_id="captch_title",
				placeholder="Здесь можно указать причину, пустота разрешена",
				style=cog.TextInputStyle.short,
				max_length=200,
				required=False,
			),
			cog.ui.TextInput(
				label=str(self.captcha_1),
				custom_id="captcha_1",
				style=cog.TextInputStyle.short,
				max_length=6,
				required=True,
			),
			cog.ui.TextInput(
				label=str(self.captcha_2),
				custom_id="captcha_2",
				style=cog.TextInputStyle.short,
				max_length=6,
				required=True,
			),
			cog.ui.TextInput(
				label=str(self.captcha_3),
				custom_id="captcha_3",
				style=cog.TextInputStyle.short,
				max_length=6,
				required=True,
			),
			cog.ui.TextInput(
				label=str(self.captcha_4),
				custom_id="captcha_4",
				style=cog.TextInputStyle.short,
				max_length=6,
				required=True,
			),
		]
		super().__init__(title="Подтверждение бана", components=components)

	async def callback(self, inter: cog.ModalInteraction):
		tv = inter.text_values
		try:
			ok = (
				self.captcha_1 == int(tv["captcha_1"])
				and self.captcha_2 == int(tv["captcha_2"])
				and self.captcha_3 == int(tv["captcha_3"])
				and self.captcha_4 == int(tv["captcha_4"])
			)
		except (ValueError, KeyError):
			ok = False

		if not ok:
			await inter.response.send_message(
				"Капча не пройдена! Действие отменено",
				ephemeral=True,
			)
			return

		reason = tv.get("captch_title") or None
		await self.target.ban(reason=reason)
		await inter.response.send_message(
			f"{self.target.mention} забанен!",
			ephemeral=True,
		)


class NickModal(cog.ui.Modal):
	def __init__(self, target: cog.Member):
		self.target = target
		components = [
			cog.ui.TextInput(
				label="Введите никнейм",
				custom_id="nickname",
				placeholder='Напиши тут "Ресет никнейма" если нужно поставить обычный ник',
				style=cog.TextInputStyle.short,
				max_length=32,
				required=True,
			)
		]
		super().__init__(title="Изменение никнейма", components=components)

	async def callback(self, inter: cog.ModalInteraction):
		val = inter.text_values["nickname"]
		if val.lower() == "ресет никнейма":
			await self.target.edit(nick=self.target.name)
			await inter.response.send_message(
				embed=cog.Embed(title="Ник ресетнут!", color=0xFFD400),
				ephemeral=True,
			)
		else:
			await self.target.edit(nick=val)
			await inter.response.send_message(
				embed=cog.Embed(title="Ник установлен!", color=0xFFD400),
				ephemeral=True,
			)


class RoleList(cog.ui.View):
	def __init__(self, author: cog.Member, target: cog.Member, bot: cog.MemeismBot):
		super().__init__(timeout=None)
		self.target = target
		self.author = author
		self.bot = bot

	async def _deny_voice(self, inter: cog.MessageInteraction):
		await inter.response.send_message(
			embed=cog.Embed(
				title="Ошибочка",
				description=			await self.bot.shortcuts.tbc(
					inter,
					"Для изменения параметров касаемо голосового чата пользователь должен быть в голосовом чате!",
				),
				color=0xFFD400,
			).set_image(url=config.embed_error_small),
			ephemeral=True,
		)

	async def _perm_denied(self, inter: cog.MessageInteraction):
		await inter.response.send_message(
			embed=await _embed_500(
				self.bot,
				inter,
				"У бота недостаточно прав для выполнения этой команды!\n"
				"необходимые права: Изменение никнейма, бан, кик, выключать микрофон/выключать звук участникам",
			),
			ephemeral=True,
		)

	@cog.ui.string_select(
		placeholder="Действия с участником",
		options=[
			cog.SelectOption(
				label="Замутить",
				description="Выключить микрофон в голосовом чате",
			),
			cog.SelectOption(
				label="Выключить звук",
				description="Выключить звук в голосовом чате",
			),
			cog.SelectOption(
				label="Забанить",
				description="Кикнуть без возможности возврата (разбан возможен)",
			),
			cog.SelectOption(label="Кикнуть", description="Выгнать с сервера"),
			cog.SelectOption(
				label="Изменить никнейм",
				description="Изменить никнейм на сервере",
			),
		],
		min_values=1,
		max_values=1,
	)
	async def member_actions(self, select: cog.ui.StringSelect, inter: cog.MessageInteraction):
		bt = inter.guild.get_member(self.bot.user.id).guild_permissions
		ch = select.values[0]

		if ch == "Выключить звук":
			if not bt.deafen_members:
				await self._perm_denied(inter)
				return
			if not self.target.voice:
				await self._deny_voice(inter)
				return
			deaf = self.target.voice.deaf
			await self.target.edit(deafen=not deaf)
			if deaf:
				title, desc = "Звук включен!", f"Теперь `{self.target.display_name}` слышит остальных!"
			else:
				title, desc = "Звук выключен!", f"Теперь `{self.target.display_name}` не слышит остальных!"
			await inter.response.send_message(
				embed=cog.Embed(title=title, description=desc, color=0xFFD400),
				ephemeral=True,
			)
			return

		if ch == "Кикнуть":
			if not bt.kick_members:
				await self._perm_denied(inter)
				return
			await inter.response.send_modal(KickModal(self.target, self.bot))
			return

		if ch == "Забанить":
			if not bt.ban_members:
				await self._perm_denied(inter)
				return
			await inter.response.send_modal(BanCheck(self.target, self.bot))
			return

		if ch == "Замутить":
			if not bt.mute_members:
				await self._perm_denied(inter)
				return
			if not self.target.voice:
				await self._deny_voice(inter)
				return
			mu = self.target.voice.mute
			await self.target.edit(mute=not mu)
			if mu:
				title, desc = "Микрофон включен!", f"`{self.target.display_name}` вернули право голоса"
			else:
				title, desc = "Микрофон выключен!", f"`{self.target.display_name}` отобрали право голоса"
			await inter.response.send_message(
				embed=cog.Embed(title=title, description=desc, color=0xFFD400).set_image(
					url=config.embed_success_banner
				),
				ephemeral=True,
			)
			return

		if ch == "Изменить никнейм":
			if not bt.manage_nicknames:
				await self._perm_denied(inter)
				return
			await inter.response.send_modal(NickModal(self.target))
			return


class UserControlPanel(cog.Cog):
	def __init__(self, bot: cog.MemeismBot):
		self.bot = bot

	@cog.slash_command(
		name="control",
		description=cog.Localised("User control panel for moderators", key="control_desc"),
	)
	@cog.has_permissions(
		manage_nicknames=True,
		mute_members=True,
		ban_members=True,
		deafen_members=True,
		kick_members=True,
	)
	async def control_panel(
		self,
		inter: cog.ApplicationCommandInteraction,
		target: cog.Member = cog.Param(description="Участник"),
	):
		await inter.response.defer(ephemeral=True)
		bt = inter.guild.get_member(self.bot.user.id).guild_permissions
		required = (
			bt.manage_nicknames,
			bt.mute_members,
			bt.deafen_members,
			bt.ban_members,
			bt.kick_members,
		)
		if not all(required):
			await inter.edit_original_response(
				embed=await _embed_500(
					self.bot,
					inter,
					"У бота недостаточно прав для выполнения этой команды!\n"
					"необходимые права: Изменение никнейма, бан, кик, выключать микрофон/выключать звук участникам",
				)
			)
			return

		voicetitle = ""
		voiceparams: list[str] = []
		if target.voice:
			if target.voice.deaf:
				voicetitle = "Голосовой чат:\n"
				voiceparams.append("Заглушен сервером")
			if target.voice.mute:
				voicetitle = "Голосовой чат:\n"
				voiceparams.append("Замучен сервером")

		done_text = f"""{voicetitle}{", ".join(voiceparams)}ID пользователя: `{target.id}`""" if voiceparams else f"ID пользователя: `{target.id}`"
		embed = (
			cog.Embed(
				title=await self.bot.shortcuts.tbc(
					inter,
					f"Панель управления: {target.display_name}",
				),
				description=done_text,
				color=0xFF0740,
			)
			.set_thumbnail(url=target.display_avatar.url)
			.set_image(url=config.embed_panel_strip)
		)
		view = RoleList(author=inter.author, target=target, bot=self.bot)
		await inter.edit_original_response(embed=embed, view=view)


def setup(bot):
	bot.add_cog(UserControlPanel(bot))
	bot.cog_reload(__name__)
