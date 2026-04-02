import datetime
import random

import aiohttp
import cog
from utils import config


class InfoCommand(cog.Cog):
	def __init__(self, bot: cog.MemeismBot):
		self.bot = bot

	async def slash_slaves(self, num: int) -> str:
		if num % 10 == 1 and num % 100 != 11:
			return f"{num} отзыв"
		if num % 10 in (2, 3, 4) and not (12 <= num % 100 <= 14):
			return f"{num} отзыва"
		return f"{num} отзывов"

	@cog.slash_command(
		name="avatar",
		description=cog.Localised("Request a user avatar", key="avatar_desc"),
	)
	async def avatar(
		self,
		inter: cog.ApplicationCommandInteraction,
		member: cog.Member = cog.Param(description="Чей аватар", default=None),
	):
		await inter.response.defer()
		member = member or inter.author
		e = cog.Embed(
			title=await self.bot.shortcuts.tbc(inter, "Ссылка на аватар"),
			url=str(member.avatar.url) if member.avatar else None,
			color=0x333333,
			timestamp=datetime.datetime.now(),
		)
		e.set_author(
			name=f"{member.global_name} | {member.name}",
			icon_url=member.display_avatar.url,
		)
		if member.display_avatar != member.avatar:
			e.set_thumbnail(url=member.avatar.url)
		e.set_image(url=member.display_avatar.url)
		e.set_footer(
			text=await self.bot.shortcuts.tbc(inter, f"Запросил {inter.author.display_name}"),
			icon_url=inter.author.display_avatar.url,
		)
		await inter.edit_original_response(
			embed=e,
			view=self.bot.shortcuts.MessageDeleteView(),
		)

	@cog.user_command(name=cog.Localised("Get banner", key="get_banner_name"))
	async def banner(self, inter: cog.ApplicationCommandInteraction, user: cog.Member):
		await inter.response.defer(ephemeral=True)
		try:
			users: cog.User = await self.bot.fetch_user(user.id)
			if not users.banner:
				await inter.edit_original_response(
					await self.bot.shortcuts.tbc(
						inter,
						f"Произошла ошибка! Скорее всего у {user.mention} нет баннера!",
					)
				)
				return
			embed = cog.Embed(
				title=await self.bot.shortcuts.tbc(
					inter,
					f"Баннер {users.display_name} ",
					users.display_name,
				),
				color=0xEB459E,
			).set_image(url=users.banner.url)
			await inter.edit_original_response(embed=embed)
			
		except Exception:
			await inter.edit_original_response(
				await self.bot.shortcuts.tbc(
					inter,
					f"Произошла ошибка! Скорее всего у {user.mention} нет баннера!",
				)
			)

	@cog.slash_command(
		name="channel",
		description=cog.Localised("Channel information", key="channel_get_name"),
	)
	async def info_channel(
		self,
		inter: cog.ApplicationCommandInteraction,
		channel: cog.TextChannel = cog.Param(description="Канал"),
	):
		await inter.response.defer()
		nsfw = "Да" if channel.is_nsfw() else "Нет"
		news = "Да" if channel.is_news() else "Нет"
		ts = int(channel.created_at.timestamp())
		embed = cog.Embed()
		embed.title = await self.bot.shortcuts.tbc(inter, f"Информация о канале #{channel.name}")
		embed.description = await self.bot.shortcuts.tbc(
			inter,
			f"ID канала: `{channel.id}`\n"
			f"Упоминание канала: {channel.mention}\n\n"
			f"NSFW канал: {nsfw}\n\n"
			f"Новостной канал: {news}\n\n"
			f"Дата создания канала: <t:{ts}:R> / в <t:{ts}:F>",
		)
		await inter.edit_original_response(embed=embed)

	@cog.slash_command(
		name="server",
		description=cog.Localised("Server information", key="server_desc"),
		contexts=cog.InteractionContextTypes(guild=True),
	)
	async def server(self, inter: cog.ApplicationCommandInteraction):
		await inter.response.defer()
		g = inter.guild
		crt = int(g.created_at.timestamp() + 10800)
		owner = g.owner
		guild = cog.Embed(
			title=await self.bot.shortcuts.tbc(inter, f"Информация о {g.name}"),
		)
		guild.add_field(
			name=await self.bot.shortcuts.tbc(
				inter,
				f"{self.bot.custom_emojis.icon_user_add} Владелец",
			),
			value=owner.mention if owner else "—",
		)
		guild.add_field(
			name=await self.bot.shortcuts.tbc(inter, f"{self.bot.custom_emojis.icon_clock} Создан"),
			value=f"<t:{crt}:R>",
		)
		guild.add_field(
			name=await self.bot.shortcuts.tbc(inter, f"{self.bot.custom_emojis.icon_paperclip} ID сервера"),
			value=f"*{g.id}*",
		)
		guild.add_field(
			name=await self.bot.shortcuts.tbc(inter, f"{self.bot.custom_emojis.icon_terminal} Каналы"),
			value=await self.bot.shortcuts.tbc(
				inter,
				f"Текстовые каналы: *{len(g.text_channels)}*\n"
				f"Голосовые каналы: *{len(g.voice_channels)}*\n"
				f"Форумы: *{len(g.forum_channels)}*\n"
				f"Категории: *{len(g.categories)}*",
			),
		)
		guild.add_field(
			name=await self.bot.shortcuts.tbc(
				inter,
				f"{random.choice(self.bot.custom_emojis.thinkings)} Кол-во эмоджи",
			),
			value=f"*{len(g.emojis)}*",
		)
		guild.add_field(
			name=await self.bot.shortcuts.tbc(
				inter,
				f"{self.bot.custom_emojis.icon_layers}Роли: {len(g.roles)}",
			),
			value=await self.bot.shortcuts.tbc(
				inter,
				"Чтобы увидеть отметки всех ролей нажмите кнопку ниже",
			),
		)
		boosts = int(g.premium_subscription_count or 0)
		guild.add_field(
			name=await self.bot.shortcuts.tbc(inter, f"{self.bot.custom_emojis.icon_user} Участники"),
			value=await self.bot.shortcuts.tbc(
				inter,
				f"*{len(g.members)} участников*\n*{boosts} бустов*",
			),
		)
		guild.add_field(
			name=await self.bot.shortcuts.tbc(inter, f"{self.bot.custom_emojis.icon_layers} Уровень проверки"),
			value=f"*{int(g.verification_level)}*",
		)
		if g.icon:
			guild.set_thumbnail(url=g.icon.url)
		if g.banner:
			guild.set_image(url=g.banner.url)
		await inter.edit_original_response(
			embed=guild,
			components=[
				cog.ui.Button(
					label=await self.bot.shortcuts.tbc(inter, "Посмотреть роли сервера"),
					style=cog.ButtonStyle.secondary,
					custom_id="server_button_role",
					row=0,
				),
				cog.ui.Button(
					label=await self.bot.shortcuts.tbc(inter, "Посмотреть категории сервера"),
					style=cog.ButtonStyle.secondary,
					custom_id="server_button_category",
					row=1,
				),
			],
		)

	@cog.slash_command(name="ping", description=cog.Localised("Check bot latency", key="ping_desc"))
	async def ping(self, inter: cog.ApplicationCommandInteraction):
		await inter.response.defer()
		pingg = self.bot.latency * 1000
		await inter.edit_original_response(
			await self.bot.shortcuts.tbc(
				inter,
				f":ping_pong: Понг!\nЗадержка {round(pingg)}!",
			)
		)

	@cog.slash_command(name="info", description=cog.Localised("Bot information", key="info_desc"))
	async def info(self, inter: cog.ApplicationCommandInteraction):
		await inter.response.defer()

		bot_created = int(self.bot.user.created_at.timestamp())
		embed = cog.Embed(
			title=await self.bot.shortcuts.tbc(inter, "Обо мне"),
			url=config.support_invite_url,
			description=await self.bot.shortcuts.tbc(
				inter,
				"memeism — океан интеграций",
			),
			color=config.gray,
		)
		embed.set_thumbnail(url=self.bot.user.display_avatar.url)
		embed.set_footer(
			text=await self.bot.shortcuts.tbc(
				inter,
				"Информация запрошена: {}".format(inter.author.display_name),
			),
		)
		embed.add_field(
			name=await self.bot.shortcuts.tbc(
				inter,
				f"{self.bot.custom_emojis.flvbsbshed} | Сервер разработки",
			),
			value=config.support_invite_url,
			inline=False,
		)
		embed.add_field(
			name=await self.bot.shortcuts.tbc(inter, f"{self.bot.custom_emojis.icon_clock} | Дата создания"),
			value=f"<t:{bot_created}:D> | <t:{bot_created}:R>",
			inline=False,
		)
		
		embed.add_field(
			name=await self.bot.shortcuts.tbc(inter, f"{self.bot.custom_emojis.icon_duoup} | Версия"),
			value=await self.bot.shortcuts.tbc(
				inter,
				f"Версия: `{config.version_number}`\n"
				f"Тайтл версии: `{config.version_name}`",
			),
			inline=False,
		)
		
		cmd_sum = (
			len(self.bot.all_user_commands)
			+ len(self.bot.all_message_commands)
			+ len(self.bot.all_slash_commands)
		)
		embed.add_field(
			name=await self.bot.shortcuts.tbc(inter, f"{self.bot.custom_emojis.icon_command} | Кол-во комманд:"),
			value=await self.bot.shortcuts.tbc(
				inter,
				f"Сумма: {cmd_sum}\n"
				f"Слеш комманды: {len(self.bot.all_slash_commands)}\n"
				f"Команды для сообщений: {len(self.bot.all_message_commands)}\n"
				f"Команды для пользователей: {len(self.bot.all_user_commands)}",
			),
			inline=True,
		)

		bid = config.support_boticord_bot_id or self.bot.user.id
		boticord: cog.Embed | None = None
		try:
			async with aiohttp.ClientSession() as session:
				async with session.get(f"https://api.boticord.top/v3/bots/{bid}") as response:
					if response.status != 200:
						raise RuntimeError("boticord")
					data = await response.json()
					result = data.get("result") or {}
					ratings_rows = result.get("ratings") or []
					reviews = result.get("reviews") or []
					ratings: dict[str, int] = {str(i): 0 for i in range(1, 6)}
					rating_counter = 0
					rating_sum = 0
					for rating in ratings_rows:
						c = int(rating.get("count") or 0)
						r = int(rating.get("rating") or 0)
						rating_sum += c
						ratings[str(r)] = c
						rating_counter += c * r
					if rating_sum <= 0:
						raise RuntimeError("no ratings")
					avg = rating_counter / rating_sum
					text = await self.bot.shortcuts.tbc(
						inter,
						f"Оценки: \n## Средняя оценка: {avg} ⭐\n"
						f"> `5` ⭐ | {await self.slash_slaves(ratings['5'])}\n"
						f"> `4` ⭐ | {await self.slash_slaves(ratings['4'])}\n"
						f"> `3` ⭐ | {await self.slash_slaves(ratings['3'])}\n"
						f"> `2` ⭐ | {await self.slash_slaves(ratings['2'])}\n"
						f"> `1` ⭐ | {await self.slash_slaves(ratings['1'])}\n",
					)
					boticord = cog.Embed(
						title=await self.bot.shortcuts.tbc(
							inter,
							f"{self.bot.custom_emojis.boticord_logo} | Информация с **Boticord**",
						),
						description=text,
						color=config.boticord_blue,
					)
					if reviews:
						rv = reviews[0]
						author = (rv.get("author") or {}).get("username", "?")
						cd = rv.get("createdDate")
						content = str(rv.get("content") or "")
						stars = rv.get("rating", "")
						if cd:
							try:
								tr = round(
									datetime.datetime.fromisoformat(
										str(cd).replace("Z", "+00:00")
									).timestamp()
								)
								when = f"<t:{tr}:R>"
							except Exception:
								when = str(cd)
						else:
							when = "—"
						boticord.add_field(
							name=await self.bot.shortcuts.tbc(inter, "Последний отзыв"),
							value=(
								f"> {author} | {when}\n> {stars} ⭐\n\n"
								f"{await self.bot.shortcuts.tbc(inter, content)}"
							),
							inline=False,
						)
		except Exception:
			boticord = None

		if boticord:
			await inter.edit_original_response(embeds=[embed, boticord])
		else:
			await inter.edit_original_response(embed=embed)

	# @cog.slash_command(
	# 	name="support",
	# 	description=cog.Localised("Support the bot! please ;-;", key="support_desc"),
	# )
	async def support(self, inter: cog.ApplicationCommandInteraction):
		await inter.response.defer()
		sup = cog.Embed(
			title=await self.bot.shortcuts.tbc(inter, "Поддержка"),
			description=await self.bot.shortcuts.tbc(
				inter,
				"Благодарим вас за будущую помощь боту!\n"
				"Можете отправить нам идею для функции или помочь финансово!",
			),
			color=0xFF58A5,
		)
		sup2 = cog.Embed(
			title=await self.bot.shortcuts.tbc(inter, "Мониторинги"),
			description=await self.bot.shortcuts.tbc(
				inter,
				"Так же мы есть на мониторингах, если вы не можете по какой либо причине "
				"помочь финансово вы можете поднять бота на мониторингах!",
			),
			color=0xFF58A5,
		)
		bid = config.support_boticord_bot_id or self.bot.user.id
		sup2.add_field(
			await self.bot.shortcuts.tbc(inter, "Мониторинги на которых есть бот"),
			value=f"[Boticord V2](https://app.arbuz.pro/bot/{bid})",
		)
		donate = config.donation_url or "https://www.donationalerts.com/r/quavier"
		await inter.edit_original_response(
			embeds=[sup, sup2],
			components=[
				cog.ui.Button(
					label=await self.bot.shortcuts.tbc(inter, "Помочь боту финансово"),
					url=donate,
					style=cog.ButtonStyle.link,
				),
			],
		)

	@cog.slash_command(
		name="invite",
		description=cog.Localised("Invite me!", key="invite_desc"),
	)
	async def invite(self, inter: cog.ApplicationCommandInteraction):
		await inter.response.defer(ephemeral=True)
		cid = self.bot.user.id
		url = (
			f"https://discord.com/oauth2/authorize?client_id={cid}"
			f"&permissions=285280256824&scope=bot%20applications.commands"
		)
		add_label = await self.bot.shortcuts.tbc(inter, f"Добавить {self.bot.user.display_name}")
		e = cog.Embed(
			title=await self.bot.shortcuts.tbc(inter, f" Привет {inter.author.display_name}!"),
			description=await self.bot.shortcuts.tbc(
				inter,
				"Нажми кнопки ниже, чтобы пригласить бота на свои сервера, "
				"или зайти на наш сервер разработки!",
			),
			color=config.accent_color,
		)
		await inter.edit_original_response(
			embed=e,
			components=[
				cog.ui.Button(
					label=add_label,
					emoji=self.bot.custom_emojis.icon_user_add,
					style=cog.ButtonStyle.link,
					url=url,
				),
				cog.ui.Button(
					label=await self.bot.shortcuts.tbc(inter, "Сервер разработки"),
					emoji=self.bot.custom_emojis.icon_help,
					style=cog.ButtonStyle.link,
					url=config.support_invite_url,
				),
			],
		)

	@cog.user_command(name=cog.Localised("Get user avatar", key="user_avatar"))
	async def user_avatar_cmd(
		self,
		inter: cog.ApplicationCommandInteraction,
		member: cog.User,
	):
		await inter.response.defer(ephemeral=True)
		e = cog.Embed(
			title=await self.bot.shortcuts.tbc(inter, "Ссылка на аватар"),
			url=str(member.avatar.url) if member.avatar else None,
			color=0x333333,
			timestamp=datetime.datetime.now(),
		)
		e.set_author(
			name=f"{member.global_name} | {member.name}",
			icon_url=member.display_avatar.url,
		)
		if member.display_avatar != member.avatar:
			e.set_thumbnail(url=member.avatar.url)
		e.set_image(url=member.display_avatar.url)
		e.set_footer(
			text=await self.bot.shortcuts.tbc(inter, f"Запросил {inter.author.display_name}"),
			icon_url=inter.author.display_avatar.url,
		)
		await inter.edit_original_response(f"{inter.author.mention}", embed=e)

	@cog.listener()
	async def on_button_click(self, inter: cog.MessageInteraction):
		if inter.component.custom_id not in ("server_button_category", "server_button_role"):
			return
		if inter.component.custom_id == "server_button_role":
			role_list = []
			for role in inter.guild.roles:
				role_list.append(f"<@&{role.id}> `({role.id})`\n")
			role_emb = cog.Embed(
				title=f"Роли сервера {inter.guild.name}",
				description=" ".join(role_list),
				color=config.spotify_main,
			)
			if inter.guild.icon:
				role_emb.set_author(icon_url=inter.guild.icon.url, name=inter.guild.name)
			await inter.response.send_message(embed=role_emb, ephemeral=True)
		elif inter.component.custom_id == "server_button_category":
			role_emb = cog.Embed(
				title=f"Каналы сервера {inter.guild.name}",
				color=config.spotify_main,
			)
			for cat in inter.guild.categories:
				nsfw = "Да" if cat.nsfw else "Нет"
				role_emb.add_field(
					name=f"`{cat.name}`",
					value=f"ID: {cat.id}\nКол-во каналов: {len(cat.channels) - 1}\nNSFW: {nsfw}",
				)
			if inter.guild.icon:
				role_emb.set_author(icon_url=inter.guild.icon.url, name=inter.guild.name)
			await inter.response.send_message(embed=role_emb, ephemeral=True)


def setup(bot: cog.MemeismBot):
	bot.add_cog(InfoCommand(bot))
	bot.cog_reload(__name__)
