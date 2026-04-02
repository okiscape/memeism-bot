import disnake, datetime as dt
import cog

async def get_time_in_timezone(offset: int):
		utc_now = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=offset)

		return utc_now

class SelfDeleteButton(cog.View):
	def __init__(self): super().__init__(timeout=None)
	
	@disnake.ui.button(emoji='<:IconDeleteTrashcan:750152850310561853>', style=disnake.ButtonStyle.secondary)
	async def selfdeletesbutton(self, button: cog.ui.Button, inter: cog.MessageInteraction):
		await inter.message.delete()

class UserEdit(cog.ui.View):
	def __init__(self, member: cog.Member, bot: cog.MemeismBot, inter):
		super().__init__(timeout=None)
		self.member = member
		self.bot = bot
		self.inter = inter

	@disnake.ui.button(style=disnake.ButtonStyle.secondary, emoji=cog.emojis.icon_code, custom_id="user_expand_button")
	async def fullver(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
		member = self.member
		await inter.response.defer()

		sub_type = await self.bot.db_execute(f"SELECT m.`sub_type` FROM membership m WHERE user_id = {member.id}")
		custom_color = self.bot.config.colors.blurple
		if str(sub_type) == "('1',)":
			about_mes: tuple = await self.bot.db_execute(f"SELECT m.`about_me` FROM membership m WHERE user_id = {member.id}")

			custom_color = await self.bot.db_execute(f"SELECT m.`color` FROM membership m WHERE user_id = {member.id}")

			custom_image: tuple = await self.bot.db_execute(f"SELECT m.`custom_image` FROM membership m WHERE user_id = {member.id}")

			custom_rang = "\n## Подписчик Mitsuki Membership"

			custom_image = str(custom_image).replace("('", "").replace("',)", "")
			if custom_color != (None,):
				custom_color = int(str(custom_color).replace("('", "").replace("',)", ""), 16)

			if about_mes[0] != None:
				about_me = about_mes[0].replace("\\n","\n")
			else:
				about_me = None
		else:
			custom_rang = ""
			sub_type = [0]
			about_me, custom_color, custom_image = None, self.bot.config.colors.blurple, None
			
		sub = {
			"user_id": member.id, 
			"about_me": about_me, 
			"color": custom_color, 
			"sub_type": sub_type[0],
			"custom_image": custom_image
		}

		undone = await self.bot.db_execute(f"SELECT * FROM `social_rating` WHERE user_id = {member.id}", fetch="all")
		try:
			kekb = {
			   "user_id": int(undone[0][0]),
				"rating": int(undone[0][1])
			}
			reting = f'\nСоциальный рейтинг: **{kekb["rating"]}**'
		except: 
			reting = ""
			
		times_c = int(member.created_at.timestamp())#type: ignore
		try:
			times_j = int(member.joined_at.timestamp())#type: ignore
		except:
			pass
		badges = []
		if member.public_flags.active_developer:
			badges.append(f'{self.bot.custom_emojis.active_developer} Активный разработчик\n')
		if member.public_flags.hypesquad_balance:
			badges.append(f'{self.bot.custom_emojis.hypesquad_balance} HypeSquad: Balance\n')
		if member.public_flags.hypesquad_bravery:
			badges.append(f'{self.bot.custom_emojis.hypesquad_bravery} HypeSquad: Bravery\n')
		if member.public_flags.hypesquad_brilliance:
			badges.append(f'{self.bot.custom_emojis.hypesquad_brilliance} HypeSquad: Brilliance\n')
		if member.public_flags.hypesquad:
			badges.append(f'{self.bot.custom_emojis.hypesquad_events} HypeSquad События\n')
		if member.public_flags.bug_hunter:
			badges.append(f'{self.bot.custom_emojis.bug_hunter} Bug Hunter\n')
		if member.public_flags.moderator_programs_alumni:
			badges.append(f'{self.bot.custom_emojis.elder_moderator} Раннее подтверждённый модератор Discord\n')
		if member.public_flags.discord_certified_moderator or member.public_flags.early_verified_bot_developer:
			badges.append(f'{self.bot.custom_emojis.moderator} Подтверждённый модератор Discord\n')
		if member.public_flags.early_supporter:
			badges.append(f'{self.bot.custom_emojis.early_support} Раннее поддержавший\n')

		if member.bot:
			if member.public_flags.verified_bot:
				badges.append('Бот(подтвержден)')
			else:
				badges.append('Бот')
		
		if member.public_flags.verified_bot_developer:
			badges.append(f'{self.bot.custom_emojis.verify_developer} Первопроходец - верефицированный разработчик бота\n')
		if member.discriminator == '0':
			badges.append(f'{self.bot.custom_emojis.none_nickname_hashtag} "Без циферок"\n')

		if type(custom_color) == tuple:
			col = custom_color[0]

		else: 
			try: col = int(custom_color)
			except: col = self.bot.config.col_blurple
		
		embed = disnake.Embed(
		 title=f'{member.display_name}',
		 color=col,
		 description=await self.bot.shortcuts.tbc(inter, f'Пользователь {member.name}, и информация о нем{custom_rang}{reting}'))
		discriminator = f'#{member.discriminator}'
		if member.discriminator == '0':
			discriminator = ""

		zone = await self.bot.db_execute(f"SELECT timezone FROM user_setting WHERE user_id = {member.id}")

		if zone:
			if zone[0] != None:
				zone_code = int(zone[0].replace("UTC ", ""))
				timezone = await get_time_in_timezone(zone_code)
				embed.add_field(name=await self.bot.shortcuts.tbc(inter, "⏰ | Время"), value=f"Часовой пояс: **{zone[0]}**\nВремя: **{timezone.strftime('%H:%M:%S')}**", inline=False)

		embed.add_field(name=await self.bot.shortcuts.tbc(inter, "👤 | Имя пользователя"),
						value=f"`{member.name}{discriminator}`",
						inline=True)
		
		if badges != []:
			embed.add_field(name=await self.bot.shortcuts.tbc(inter, ":medal: | Значки"), value=await self.bot.shortcuts.tbc(inter, f"".join(badges)), inline=False)
		else:
			pass
		embed.add_field(name=await self.bot.shortcuts.tbc(inter, f'{self.bot.custom_emojis.icon_ping} | Упоминание'), value=member.mention)
		embed.add_field(name=await self.bot.shortcuts.tbc(inter, "🆔 | Идентификатор"), value=member.id)
		embed.add_field(name=await self.bot.shortcuts.tbc(inter, ":date: | Регистрация аккаунта"), value=f"<t:{times_c}:R>", inline=False)

		try:
			embed.add_field(name=await self.bot.shortcuts.tbc(inter, ':date: | Зашёл на сервер'), value=f"<t:{times_j}:R>", inline=True)
		except:
			pass

		try:
			banner_user_fetch: disnake.User = await self.bot.fetch_user(member.id)
			banner_url = banner_user_fetch.banner.url
			banner = disnake.Embed(title=await self.bot.shortcuts.tbc(inter, 'Профильные Медиа-файлы'),  
			  color=custom_color)
			sls = ""
			secav = ""
			if member.display_avatar != member.avatar:
				sls = "ы"
				secav = f'\n[htttps://cdn.discordapp.com/display_avatars...]({member.display_avatar})'

			banner.add_field(name=await self.bot.shortcuts.tbc(inter, f'Ссылка на баннер'), value=f'[htttps://cdn.discordapp.com/banners...]({banner_url})', inline=False)
			banner.add_field(name=await self.bot.shortcuts.tbc(inter, f'Ссылка на аватар{sls}'), value=f'[htttps://cdn.discordapp.com/avatars...]({member.avatar}){secav}', inline=False)
			banner.set_image(banner_url)
			banner.set_thumbnail(url=f'{member.avatar}')
		except:
			embed.set_thumbnail(url=f'{member.avatar}')
			banner = None 
			
		if f'{member.status}' == 'offline':
			status = f'{self.bot.custom_emojis.status_offline} '
		if f'{member.status}' == 'idle':
			status = f'{self.bot.custom_emojis.status_idle} '
		if f'{member.status}' == 'dnd':
			status = f'{self.bot.custom_emojis.status_dnd} '
		if f'{member.status}' == 'online':
			status = f'{self.bot.custom_emojis.status_online} '
		try:
			bio = member.activity.type
		except:
			bio = 'чефир'
		if bio == disnake.ActivityType.custom: 
			if member.activity.name != None:
				custom = f' | {member.activity.name}'
			elif member.activity.name == None:
				if f'{member.status}' == 'offline':
					custom = await self.bot.shortcuts.tbc(inter, '| Не в сети')
				if f'{member.status}' == 'idle':
					custom = await self.bot.shortcuts.tbc(inter, '| Не активен(а)')
				if f'{member.status}' == 'dnd':
					custom = await self.bot.shortcuts.tbc(inter, '| Не беспокоить')
				if f'{member.status}' == 'online':
					custom = await self.bot.shortcuts.tbc(inter, '| В сети')
		else:
			if f'{member.status}' == 'offline':
				custom = await self.bot.shortcuts.tbc(inter, '| Не в сети')
			if f'{member.status}' == 'idle':
				custom = await self.bot.shortcuts.tbc(inter, '| Не активен(а)')
			if f'{member.status}' == 'dnd':
				custom = await self.bot.shortcuts.tbc(inter, '| Не беспокоить')
			if f'{member.status}' == 'online':
				custom = await self.bot.shortcuts.tbc(inter, '| В сети')

		service = []
		if 'desktop' in member._client_status:
			service.append(self.bot.custom_emojis.apps_pc)
		if 'web' in member._client_status:
			service.append(self.bot.custom_emojis.apps_web)
		if 'mobile' in member._client_status:
			service.append(self.bot.custom_emojis.apps_mobile)
		serversi = ''
		if service != []:
			ser = "".join(service)
			serversi = f'{ser} | '
		embed.add_field(name=await self.bot.shortcuts.tbc(inter, f"{status} | Статус"), value=f"{serversi}{status}{custom}", inline=True)

		try:
			embed.add_field(name=await self.bot.shortcuts.tbc(inter, "🎨 | Цвета"), 
			  value=await self.bot.shortcuts.tbc(inter, f'Цвет верхней роли: {member.color}'), inline=False)
		except: pass

		spotify_embed = None
		for activity in member.activities:
			if isinstance(activity, disnake.Spotify):
				n = "\n"
				desc = f"""{await self.bot.shortcuts.tbc(inter, f'||> Узнать подробнее про проигроваемый трек можно через команду "Что слушает..."||')}\n{await self.bot.shortcuts.tbc(inter, 'От исполнителя: ')} `{activity.artist}`\n{await self.bot.shortcuts.tbc(inter, f'Альбом')}: `{activity.album}`"""
				spotify_embed = disnake.Embed(color=self.bot.config.colors.spotify_main,
					 title=f'{self.bot.custom_emojis.spotify_logo} {activity.title}', 
					 url=activity.track_url,
					 type='rich',
					 description=desc)
				spotify_embed.set_author(name=await self.bot.shortcuts.tbc(inter, f'{member.name} сейчас слушает...'), icon_url=member.avatar)
				spotify_embed.set_thumbnail(activity.album_cover_url)

		if sub['sub_type'] == "1":
			if sub['custom_image'] not in ["NONE--", None] or sub['about_me'] != None:
				if sub["about_me"] != None:
					membership = disnake.Embed(title="MISTUKI MEMBERSHIP", color=col)
					membership.add_field(name=await self.bot.shortcuts.tbc(inter, "Обо мне"), value=sub['about_me'], inline=False)

					if sub['custom_image'] != None and sub['custom_image'].startswith('http'):
						try:
							membership.set_image(
								sub['custom_image'])
						except:pass
				else:
					membership = None
			else:	
				membership = None
			
		else:
			membership = None

		embedss = [embed]

		if banner is not None:
			embedss.append(banner)

		if membership is not None:
			embedss.append(membership)
		
		if spotify_embed is not None:
			embedss.append(spotify_embed)

		await inter.edit_original_response(embeds=embedss, view=SelfDeleteButton())

class User(cog.Cog):

	def __init__(self, bot: cog.MemeismBot):
		self.bot = bot

	@cog.guild_only()
	@cog.slash_command(name='user',
				   description=disnake.Localised(string="Show user information", key="user_desc")
				   )
	async def slash_user(self, inter: disnake.ApplicationCommandInteraction, 
			  member: disnake.Member = cog.Param(description='Упомяни пользователя для получения информации о его аккаунте', 
											 default=lambda a: a.author)):
		await inter.response.defer(ephemeral=True)

		times_c = int(member.created_at.timestamp())#type: ignore

		try:
			times_j = int(member.joined_at.timestamp())#type: ignore
			date = f'Зашёл(а) на сервер: <t:{times_j}:R>\n'
		except:
			date = ""

		emb = disnake.Embed(title=await self.bot.shortcuts.tbc(inter, 
										 f'Краткая информация о: {member.global_name}'), color=0xaefeff)

		names = [f'> Имя пользователя: `{member.name}`', f'> Ник пользователя: `{member.global_name or member.name}`', f'> Отображаемое имя: `{member.display_name}`']

		emb.add_field(name=await self.bot.shortcuts.tbc(inter, '📛 | Имена'), value="\n".join(names), inline=False)
		try:
			emb.set_thumbnail(member.avatar)
		except:
			pass

		spotify_embed = None
		for activity in member.activities:
			if isinstance(activity, disnake.Spotify):
				spotify_embed = disnake.Embed(color=self.bot.config.colors.spotify_main,
					 title=f'{self.bot.custom_emojis.spotify_logo} {activity.title}', 
					 url=activity.track_url,
					 type='article',
					 description=await self.bot.shortcuts.tbc(inter, f'От исполнителя: `{activity.artist}`\nАльбом: `{activity.album}`'))
				spotify_embed.set_author(name=await self.bot.shortcuts.tbc(inter, f'{member.global_name} сейчас слушает...', member.global_name), icon_url=member.avatar)
				spotify_embed.set_thumbnail(activity.album_cover_url)

		emb.add_field(name=await self.bot.shortcuts.tbc(inter, '📅 | Даты'), value=await self.bot.shortcuts.tbc(inter, f"{date}Аккаунт создан: <t:{times_c}:R>"))
		emb.add_field(name=await self.bot.shortcuts.tbc(inter, '🆔 | Идентификатор пользователя'), value=f"```{member.id}```",inline=False)
		try:
			banner_user_fetch: disnake.User = await self.bot.fetch_user(member.id)
			banner_url = banner_user_fetch.banner.url
			emb.set_image(banner_url)
		except:
			banner = None 

		try:
			try:
				await inter.edit_original_response(embeds=[emb, spotify_embed, banner], view=UserEdit(member=member, bot=self.bot, inter=inter))
			except:
				await inter.edit_original_response(embeds=[emb, spotify_embed], view=UserEdit(member=member, bot=self.bot, inter=inter))
		except:
			await inter.edit_original_response(embed=emb, view=UserEdit(member=member, bot=self.bot, inter=inter))

	@cog.guild_only()
	@cog.user_command(name=disnake.Localised(string="User information", key="user_desc"))
	async def user(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member):
		await inter.response.defer(ephemeral=True)
		
		sub_type = await self.bot.db_execute(f"SELECT m.`sub_type` FROM membership m WHERE user_id = {member.id}")
		custom_color = self.bot.config.colors.blurple
		
		

		if str(sub_type) == "('1',)":
			about_mes: tuple = await self.bot.db_execute(f"SELECT m.`about_me` FROM membership m WHERE user_id = {member.id}")

			custom_color = await self.bot.db_execute(f"SELECT m.`color` FROM membership m WHERE user_id = {member.id}")

			custom_image: tuple = await self.bot.db_execute(f"SELECT m.`custom_image` FROM membership m WHERE user_id = {member.id}")

			custom_rang = "\n> **Подписчик Mitsuki Membership**"

			custom_image = custom_image[0]
			if custom_color != (None,):
				try:
					custom_color = int(custom_color[0], 16)
				except: custom_color = self.bot.config.colors.blurple

			if about_mes[0] != None:
				about_me = about_mes[0].replace("\\n","\n")
			else:
				about_me = ""
		else:
			custom_rang = ""
			sub_type = [0]
			about_me, custom_color, custom_image = None, self.bot.config.colors.blurple, None
			
		sub = {
			"user_id": member.id, 
			"about_me": about_me, 
			"color": custom_color, 
			"sub_type": sub_type[0],
			"custom_image": custom_image
		}

		undone = await self.bot.db_execute(f"SELECT * FROM `social_rating` WHERE user_id = {member.id}", fetch="all")

		try:
			kekb = {
			   "user_id": int(undone[0][0]),
				"rating": int(undone[0][1])
			}
			reting = f'\nСоциальный рейтинг: **{kekb["rating"]}**'
		except: 
			reting = ""
			
		times_c = int(member.created_at.timestamp())#type: ignore
		try:
			times_j = int(member.joined_at.timestamp())#type: ignore
		except:
			pass
		badges= []
		
		
		if member.bot:
			if member.public_flags.verified_bot:
				badges.append('Бот(подтвержден)')
			else:
				badges.append('Бот')
		else:

			if member.public_flags.active_developer:
				badges.append(f'{self.bot.custom_emojis.active_developer} Активный разработчик\n')
			if member.public_flags.hypesquad_balance:
				badges.append(f'{self.bot.custom_emojis.hypesquad_balance} HypeSquad: Balance\n')
			if member.public_flags.hypesquad_bravery:
				badges.append(f'{self.bot.custom_emojis.hypesquad_bravery} HypeSquad: Bravery\n')
			if member.public_flags.hypesquad_brilliance:
				badges.append(f'{self.bot.custom_emojis.hypesquad_brilliance} HypeSquad: Brilliance\n')
			if member.public_flags.hypesquad:
				badges.append(f'{self.bot.custom_emojis.hypesquad_events} HypeSquad События\n')
			if member.public_flags.bug_hunter:
				badges.append(f'{self.bot.custom_emojis.bug_hunter} Bug Hunter\n')
			if member.public_flags.moderator_programs_alumni:
				badges.append(f'{self.bot.custom_emojis.elder_moderator} Раннее подтверждённый модератор Discord\n')
			if member.public_flags.discord_certified_moderator or member.public_flags.early_verified_bot_developer:
				badges.append(f'{self.bot.custom_emojis.moderator} Подтверждённый модератор Discord\n')
			if member.public_flags.early_supporter:
				badges.append(f'{self.bot.custom_emojis.early_support} Раннее поддержавший\n')
	
			if member.public_flags.verified_bot_developer:
				badges.append(f'{self.bot.custom_emojis.verify_developer} Первопроходец - верефицированный разработчик бота\n')
		
		if type(custom_color) == tuple:
			col = custom_color[0]

		else: 
			try: col = int(custom_color)
			except: col = self.bot.config.col_blurple
		
		embed = disnake.Embed(
		 title=f'{member.display_name}',
		 color=col,
		 description=await self.bot.shortcuts.tbc(inter, f'Пользователь {member.name}, и информация о нем{custom_rang}{reting}'))
		discriminator = f'#{member.discriminator}'
		if member.discriminator == '0':
			discriminator = ""
		embed.add_field(name=await self.bot.shortcuts.tbc(inter, "👤 | Имя пользователя"),
						value=f"`{member.name}{discriminator}`",
						inline=True)
		

		zone = await self.bot.db_execute(f"SELECT timezone FROM user_setting WHERE user_id = {member.id}")
		
		if zone:
			if zone[0] != None:
				zone_code = int(zone[0].replace("UTC ", "") or 0)
				timezone = await get_time_in_timezone(zone_code)
				embed.add_field(name=await self.bot.shortcuts.tbc(inter, "⏰ | Время"), value=f"Часовой пояс: **{zone[0]}**\nВремя: **{timezone.strftime('%H:%M:%S')}**", inline=False)

		if badges != []:
			embed.add_field(name=await self.bot.shortcuts.tbc(inter, ":medal: | Значки"), value=await self.bot.shortcuts.tbc(inter, f"".join(badges)), inline=False)
		else:
			pass
		embed.add_field(name=await self.bot.shortcuts.tbc(inter, f'{self.bot.custom_emojis.icon_ping} | Упоминание'), value=member.mention)
		embed.add_field(name=await self.bot.shortcuts.tbc(inter, "🆔 | Идентификатор"), value=member.id)
		embed.add_field(name=await self.bot.shortcuts.tbc(inter, ":date: | Регистрация аккаунта"), value=f"<t:{times_c}:R>", inline=False)
		
		try:
			embed.add_field(name=await self.bot.shortcuts.tbc(inter, ':date: | Зашёл на сервер'), value=f"<t:{times_j}:R>", inline=True)
		except:
			pass

		try:
			banner_user_fetch: disnake.User = await self.bot.fetch_user(member.id)
			banner_url = banner_user_fetch.banner.url
			banner = disnake.Embed(title=await self.bot.shortcuts.tbc(inter, 'Профильные Медиа-файлы'),  
			  color=custom_color)
			sls = ""
			
			secav = ""
			if member.display_avatar != member.avatar:
				sls = "ы"
				secav = f'\n[htttps://cdn.discordapp.com/display_avatars...]({member.display_avatar})'

			banner.add_field(name=await self.bot.shortcuts.tbc(inter, f'Ссылка на баннер'), value=f'[htttps://cdn.discordapp.com/banners...]({banner_url})', inline=False)
			banner.add_field(name=await self.bot.shortcuts.tbc(inter, f'Ссылка на аватар{sls}'), value=f'[htttps://cdn.discordapp.com/avatars...]({member.avatar}){secav}', inline=False)
			banner.set_image(banner_url)
			banner.set_thumbnail(url=f'{member.avatar}')
		except:
			embed.set_thumbnail(url=f'{member.avatar}')
			
			banner = None 
			
		if f'{member.status}' == 'offline':
			status = f'{self.bot.custom_emojis.status_offline} '
		if f'{member.status}' == 'idle':
			status = f'{self.bot.custom_emojis.status_idle} '
		if f'{member.status}' == 'dnd':
			status = f'{self.bot.custom_emojis.status_dnd} '
		if f'{member.status}' == 'online':
			status = f'{self.bot.custom_emojis.status_online} '
		
		try:
			bio = member.activity.type
		except:
			bio = 'чефир'
		if bio == disnake.ActivityType.custom: 
			if member.activity.name != None:
				custom = f' | {member.activity.name}'
			elif member.activity.name == None:
				if f'{member.status}' == 'offline':
					custom = await self.bot.shortcuts.tbc(inter, '| Не в сети')
				if f'{member.status}' == 'idle':
					custom = await self.bot.shortcuts.tbc(inter, '| Не активен(а)')
				if f'{member.status}' == 'dnd':
					custom = await self.bot.shortcuts.tbc(inter, '| Не беспокоить')
				if f'{member.status}' == 'online':
					custom = await self.bot.shortcuts.tbc(inter, '| В сети')
		else:
			if f'{member.status}' == 'offline':
				custom = await self.bot.shortcuts.tbc(inter, '| Не в сети')
			if f'{member.status}' == 'idle':
				custom = await self.bot.shortcuts.tbc(inter, '| Не активен(а)')
			if f'{member.status}' == 'dnd':
				custom = await self.bot.shortcuts.tbc(inter, '| Не беспокоить')
			if f'{member.status}' == 'online':
				custom = await self.bot.shortcuts.tbc(inter, '| В сети')
		
		service = []
		if 'desktop' in member._client_status:
			service.append(self.bot.custom_emojis.apps_pc)
		if 'web' in member._client_status:
			service.append(self.bot.custom_emojis.apps_web)
		if 'mobile' in member._client_status:
			service.append(self.bot.custom_emojis.apps_mobile)
		
		serversi = ''
		if service != []:
			ser = "".join(service)
			serversi = f'{ser} | '
		embed.add_field(name=await self.bot.shortcuts.tbc(inter, f"{status} | Статус"), value=f"{serversi}{status}{custom}", inline=True)
		
		try:
			embed.add_field(name=await self.bot.shortcuts.tbc(inter, "🎨 | Цвета"), 
			  value=await self.bot.shortcuts.tbc(inter, f'Цвет верхней роли: {member.color}'), inline=False)
		except: pass
		
		spotify_embed = None
		for activity in member.activities:
			if isinstance(activity, disnake.Spotify):
				n = "\n"
				desc = f"""{await self.bot.shortcuts.tbc(inter, f'||> Узнать подробнее про проигроваемый трек можно через команду "Что слушает..."||')}
{await self.bot.shortcuts.tbc(inter, 'От исполнителя: ')} `{activity.artist}`
{await self.bot.shortcuts.tbc(inter, f'Альбом')}: `{activity.album}`"""
				spotify_embed = disnake.Embed(color=self.bot.config.colors.spotify_main,
					 title=f'{self.bot.custom_emojis.spotify_logo} {activity.title}', 
					 url=activity.track_url,
					 type='rich',
					 description=desc)
				spotify_embed.set_author(name=await self.bot.shortcuts.tbc(inter, f'{member.name} сейчас слушает...'), icon_url=member.avatar)
				spotify_embed.set_thumbnail(activity.album_cover_url)

		if sub['sub_type'] == "1":
			if sub['custom_image'] not in ["NONE--", None] or sub['about_me'] != None:
				if sub["about_me"] != None:
					membership = disnake.Embed(title="MISTUKI MEMBERSHIP", color=col)
					membership.add_field(name=await self.bot.shortcuts.tbc(inter, "Обо мне"), value=sub['about_me'], inline=False)

					if sub['custom_image'] != None and sub['custom_image'].startswith('http'):
						try:
							membership.set_image(
								sub['custom_image'])
						except:pass
				else:
					membership = None
			else:	
				membership = None
			
		else:
			membership = None

		embedss = [embed]
		

		if banner is not None:
			embedss.append(banner)

		if membership is not None:
			embedss.append(membership)
		
		if spotify_embed is not None:
			embedss.append(spotify_embed)
		

		await inter.edit_original_response(embeds=embedss)

	@cog.slash_command(name="profile")
	async def profile(self, inter: disnake.ApplicationCommandInteraction): pass
	
	@profile.sub_command(name="timezone", description=disnake.Localised(key="user_profile_timezone", string="Set timezone for your public profile"))
	async def timezone(self, inter: disnake.ApplicationCommandInteraction, zone: str = cog.Param(
			description="Выберите часовой пояс / город",
			autocomplete=cog.shortcuts.generate_pick(
					[
					"UTC -12",
					"UTC -11",
					"UTC -10",
					"UTC -9",
					"UTC -7",
					"UTC -8",
					"UTC -6",
					"UTC -5",
					"UTC -4",
					"UTC -3",
					"UTC -2",
					"UTC -1",
					"UTC ",
					"UTC +1",
					"UTC +2",
					"UTC +3",
					"UTC +4",
					"UTC +5",
					"UTC +6",
					"UTC +7",
					"UTC +8",
					"UTC +9",
					"UTC +10",
					"UTC +11",
					"UTC +12"])
					)
				):
		loget = await self.bot.db_execute(f'SELECT * FROM `user_setting` WHERE `user_id` = "{inter.author.id}";')

		if loget == None:
			await self.bot.db_execute(f'INSERT INTO `user_setting` (user_id) VALUES ({inter.author.id});')
			loget = await self.bot.db_execute(f'SELECT * FROM `user_setting` WHERE `user_id` = "{inter.author.id}";')

		zone_code = int(zone.replace("UTC ", "") or 0)

		timezone = await get_time_in_timezone(zone_code)
		
		await self.bot.db_execute(f"UPDATE `user_setting` SET `timezone` = \"{zone}\" WHERE `user_id` = {inter.author.id} LIMIT 1;")

		await inter.response.send_message(f"Часовой пояс установлен на {zone}\nВремя: `{timezone.strftime('%d/%m/%Y, %H:%M:%S')}`")

def setup(bot):
	bot.add_cog(User(bot))
	bot.cog_reload(__name__)