import cog, aiohttp, datetime
import random


class Modrinth(cog.Cog):

	def __init__(self, bot: cog.MemeismBot):
		self.bot = bot

	@cog.slash_command(name='modrinth', description=cog.Localised(string="Information about the Mod/Shader/Resource Pack/User on the \"Modbrinth\" platform", key="modrinth_desc"))
	async def project(self, inter: cog.ApplicationCommandInteraction,
					  data_type: str = cog.Param(description='Укажи тип информации которую будем искать',
												 autocomplete=cog.shortcuts.generate_pick(
						["Пакет ресурсов / Ресурс пак", "Шейдер", "Мод / Дата-пак(Пакет данных) / Плагин", "Пользователь", 'Сборка / Модпак']
												 )),
					  query: str = cog.Param(description='Запрос')):

		await inter.response.defer(ephemeral=True)
		if data_type == "Сборка / Модпак":
			uri = f'search?query="{query}"&limit=1&facets=[["project_type:modpack"]]'

			async with aiohttp.ClientSession() as session:
				async with session.get(url=f'https://api.modrinth.com/v2/{uri}') as response:
					modget = await response.json()
				await session.close()

			if modget['hits'] == []:
				await inter.edit_original_response(content=await self.bot.shortcuts.tbc(inter, 'Такой проект не найден!'))

			else:
				first = modget['hits'][0]

				async with aiohttp.ClientSession() as session:
					async with session.get(url=f'https://api.modrinth.com/v2/user/{first["author"]}') as response:
						author = await response.json()
					await session.close()

				category: str = ', '.join(first['categories']).title()

				mod = cog.Embed(
					title=first["title"],
					url=f'https://modrinth.com/modpack/{first["slug"]}',
					color=0x82e868
					)

				mod.add_field(name=await self.bot.shortcuts.tbc(inter, 'Информация'),
		  			value=await self.bot.shortcuts.tbc(inter, f'Автор сборки: [{first["author"]}](https://modrinth.com/user/{author["username"]})\nЛицензия: {first["license"]}'))

				try:
					mod.add_field(name=await self.bot.shortcuts.tbc(inter, "Категории"), value=f'```{category}```', inline=False)
				except: pass

				try: mod.add_field(name=await self.bot.shortcuts.tbc(inter, 'Описание'),
		  			value=first["description"],
					inline=False)
				except:pass

				cdate = datetime.datetime.fromisoformat(first['date_created'])
				udate = datetime.datetime.fromisoformat(first['date_modified'])

				mod.add_field(name=await self.bot.shortcuts.tbc(inter, 'Даты'),
		   					value=await self.bot.shortcuts.tbc(inter, f"Сборка создана: {cog.utils.format_dt(cdate, 'f')}\nСборка обновлена в последний раз: {cog.utils.format_dt(udate, 'f')}"),
							inline=False)

				mod.add_field(name=await self.bot.shortcuts.tbc(inter, f'Последняя версия сборки: {first["latest_version"]}'), value='|',
					inline=False)

				mod.add_field(name=await self.bot.shortcuts.tbc(inter, f'Статистика'),
		  			value=await self.bot.shortcuts.tbc(inter, f"Установок: {first['downloads']}\nОтслеживаний: {first['follows']}"), inline=True)

				mod.set_thumbnail(url=first["icon_url"])

				button = [
					cog.ui.Button(label=await self.bot.shortcuts.tbc(inter, 'Страница сборки'), style=cog.ButtonStyle.url,
		       		url=f'https://modrinth.com/modpack/{first["slug"]}'),

					cog.ui.Button(label=await self.bot.shortcuts.tbc(inter, 'Страница автора'), style=cog.ButtonStyle.url,
		       		url=f'https://modrinth.com/user/{author["username"]}', row=1)
				]


				if first['featured_gallery'] != None:
					featured_gallery = cog.Embed(color=0x82e868)
					featured_gallery.set_image(url=first["featured_gallery"])

				else:
					featured_gallery = cog.Embed(color=0x82e868)
					featured_gallery.set_image(url=random.choice(first['gallery']))
				try:
					await inter.edit_original_response(embeds=[mod, featured_gallery], components=button)
				except:
					await inter.edit_original_response(embed=mod, components=button)

		elif data_type == "Пакет ресурсов / Ресурс пак":
			uri = f'search?query="{query}"&limit=1&facets=[["project_type:resourcepack"]]'

			async with aiohttp.ClientSession() as session:
				async with session.get(url=f'https://api.modrinth.com/v2/{uri}') as response:
					modget = await response.json()
				await session.close()


			if modget['hits'] == []:
				await inter.edit_original_response(content=await self.bot.shortcuts.tbc(inter, 'Такой проект не найден!'))

			else:
				first = modget['hits'][0]

				async with aiohttp.ClientSession() as session:
					async with session.get(url=f'https://api.modrinth.com/v2/user/{first["author"]}') as response:
						author = await response.json()
					await session.close()

				category: str = ', '.join(first['categories']).title()

				mod = cog.Embed(
					title=first["title"],
					url=f'https://modrinth.com/resourcepack/{first["slug"]}',
					color=0x82e868)

				mod.add_field(name=await self.bot.shortcuts.tbc(inter, 'Информация'),
		  			value=await self.bot.shortcuts.tbc(inter, f'Автор пакета ресурсов: [{first["author"]}](https://modrinth.com/user/{author["username"]})\nЛицензия: {first["license"]}'))

				mod.add_field(name="Категории", value=f'```{category}```', inline=False)

				try: mod.add_field(name=await self.bot.shortcuts.tbc(inter, 'Описание'),
		  			value=first["description"],
					inline=False)
				except:pass

				cdate = datetime.datetime.fromisoformat(first['date_created'])
				udate = datetime.datetime.fromisoformat(first['date_modified'])
				mod.add_field(name=await self.bot.shortcuts.tbc(inter, 'Даты'),
		   					value=await self.bot.shortcuts.tbc(inter, f"П.Р. создан: {cog.utils.format_dt(cdate, 'f')}\nП.Р. обновнен в последний раз: {cog.utils.format_dt(udate, 'f')}"),
							inline=False)

				mod.add_field(name=await self.bot.shortcuts.tbc(inter, f'Последняя версия "ресурс-пака": {first["latest_version"]}'), value="|",
					inline=False)

				mod.add_field(name=await self.bot.shortcuts.tbc(inter, f'Статистика'),
		  			value=await self.bot.shortcuts.tbc(inter, f"Установок: {first['downloads']}\nОтслеживаний: {first['follows']}"), inline=True)

				mod.set_thumbnail(url=first["icon_url"])

				button = [
					cog.ui.Button(label=await self.bot.shortcuts.tbc(inter, 'Страница ресурс-пака'), style=cog.ButtonStyle.url,
		       		url=f'https://modrinth.com/resourcepack/{first["slug"]}', row=1),

					cog.ui.Button(label=await self.bot.shortcuts.tbc(inter, 'Страница автора'), style=cog.ButtonStyle.url,
		       		url=f'https://modrinth.com/user/{author["username"]}', row=1)
				]

				color = 0x82e868
				jcolor = None
				async with aiohttp.ClientSession() as session:
					async with session.get(url=f'https://api.modrinth.com/v2/project/{first["slug"]}') as response:
						jcolor = await response.json()
						jcolor = jcolor["color"]
					await session.close()

				if jcolor != None:
					color = jcolor

				if first['featured_gallery'] != None:
					featured_gallery = cog.Embed(color=color)
					featured_gallery.set_image(url=first["featured_gallery"])
				else:
					featured_gallery = cog.Embed(color=color)
					featured_gallery.set_image(url=random.choice(first['gallery']))
				try:
					await inter.edit_original_response(embeds=[mod, featured_gallery], components=button)
				except:
					await inter.edit_original_response(embed=mod, components=button)

		elif data_type == "Шейдер":
			uri = f'search?query="{query}"&limit=1&facets=[["project_type:shader"]]'

			async with aiohttp.ClientSession() as session:
				async with session.get(url=f'https://api.modrinth.com/v2/{uri}') as response:
					modget = await response.json()
				await session.close()


			if modget['hits'] == []:
				await inter.edit_original_response(content='Такой проект не найден!')

			else:
				first = modget['hits'][0]

				category: str = ', '.join(first['categories']).title()

				async with aiohttp.ClientSession() as session:
					async with session.get(url=f'https://api.modrinth.com/v2/user/{first["author"]}') as response:
						author = await response.json()

				mod = cog.Embed(
					title=first["title"],
					url=f'https://modrinth.com/shader/{first["slug"]}',
					color=0x82e868)

				mod.add_field(name='Информация',
		  			value=f'Автор шейдера: [{first["author"]}](https://modrinth.com/user/{author["username"]})\nЛицензия: {first["license"]}')

				mod.add_field(name="Категории шейдера", value=f'```{category}```', inline=False)

				try: mod.add_field(name='Описание',
		  			value=first["description"],
					inline=False)
				except:pass

				cdate = datetime.datetime.fromisoformat(first['date_created'])
				udate = datetime.datetime.fromisoformat(first['date_modified'])
				mod.add_field(name='Даты',
		   					value=f"Шейдер создан: {cog.utils.format_dt(cdate, 'f')}\n Шейдер обновнен в последний раз: {cog.utils.format_dt(udate, 'f')}",
							inline=False)

				mod.add_field(name=f'Последняя версия шейдера: {first["latest_version"]}', value="|",
					inline=False)

				mod.add_field(name=f'Статистика',
		  			value=f"Установок: {first['downloads']}\nОтслеживаний: {first['follows']}", inline=True)

				mod.set_thumbnail(url=first["icon_url"])
				if first['featured_gallery'] != None:
					featured_gallery = cog.Embed(color=0x82e868)
					featured_gallery.set_image(url=first["featured_gallery"])
				else:
					featured_gallery = cog.Embed(color=0x82e868)
					featured_gallery.set_image(url=random.choice(first['gallery']))

				button = [
					cog.ui.Button(label='Страница шейдера', style=cog.ButtonStyle.url,
		       		url=f'https://modrinth.com/shader/{first["slug"]}', row=1),

					cog.ui.Button(label='Страница автора', style=cog.ButtonStyle.url,
		       		url=f'https://modrinth.com/user/{author["username"]}', row=2)
				]

				try:
					await inter.edit_original_response(embeds=[mod, featured_gallery], components=button)
				except:
					await inter.edit_original_response(embed=mod, components=button)

		elif data_type == "Мод / Дата-пак(Пакет данных) / Плагин":
			uri = f'search?query="{query}"&limit=1&facets=[["project_type:mod"]]'
			async with aiohttp.ClientSession() as session:
				async with session.get(url=f'https://api.modrinth.com/v2/{uri}') as response:
					modget = await response.json()
				await session.close()



			if modget['hits'] == [] :
				await inter.edit_original_response(content='Такой проект не найден!')

			else:
				first = modget['hits'][0]

				if first['client_side'] == 'required':
					client = 'Необходим'

				elif first['client_side'] == 'unsupported':
					client = 'Не поддерживается'

				elif first['client_side'] == 'optional':
					client = 'Поддерживается'


				if first['server_side'] == 'optional':
					server = 'Поддерживается'

				elif first['server_side'] == 'unsupported':
					server = 'Не поддерживается'

				elif first['server_side'] == 'required':
					server = 'Необходим'

				cdate = datetime.datetime.fromisoformat(first['date_created'])
				udate = datetime.datetime.fromisoformat(first['date_modified'])

				async with aiohttp.ClientSession() as session:
					async with session.get(url=f'https://api.modrinth.com/v2/user/{first["author"]}') as response:
						author = await response.json()
					await session.close()

				mod = cog.Embed(
					title=first["title"],
					url=f'https://modrinth.com/mod/{first["slug"]}',
					color=0x82e868)


				mod.add_field(name=await self.bot.shortcuts.tbc(inter, 'Информация'),
		  			value=await self.bot.shortcuts.tbc(inter, f'Автор мода: [{first["author"]}](https://modrinth.com/user/{author["username"]})\nЛицензия: {first["license"]}\n"Клиент-сайд": {client}\n"Сервер-сайд": {server}'))

				try:
					category = ', '.join(first['categories'])
					mod.add_field(name=await self.bot.shortcuts.tbc(inter, "Категории"), value=f'```{category}```', inline=False)
				except:
					category = ', '.join(first['display_categories'])
					mod.add_field(name=await self.bot.shortcuts.tbc(inter, "Категории"), value=f'```{category}```', inline=False)

				mod.add_field(name=await self.bot.shortcuts.tbc(inter, 'Даты'),
		   					value=await self.bot.shortcuts.tbc(inter, f"Мод создан: {cog.utils.format_dt(cdate, 'f')}\n Мод обновнен в последний раз: {cog.utils.format_dt(udate, 'f')}"),
							inline=False)

				try:
					mod.add_field(name=await self.bot.shortcuts.tbc(inter, 'Описание'),
		  				value=first["description"],
						inline=False)
				except:
					pass


				mod.add_field(name=await self.bot.shortcuts.tbc(inter, f'Последняя версия мода: {first["latest_version"]}'), value="|")


				mod.add_field(name=await self.bot.shortcuts.tbc(inter, f'Статистика'),
		  			value=await self.bot.shortcuts.tbc(inter, f"Установок: {first['downloads']}\nОтслеживаний: {first['follows']}"))

				mod.set_thumbnail(url=first["icon_url"])

				if first['featured_gallery'] != None:
					featured_gallery = cog.Embed(color=0x82e868)
					featured_gallery.set_image(url=first["featured_gallery"])
				else:
					try:
						featured_gallery = cog.Embed(color=0x82e868)
						featured_gallery.set_image(url=random.choice(first['gallery']))
					except:pass

				button = [
					cog.ui.Button(label=await self.bot.shortcuts.tbc(inter, 'Страница мода'), style=cog.ButtonStyle.url,
		       		url=f'https://modrinth.com/mod/{first["slug"]}', row=1),

					cog.ui.Button(label=await self.bot.shortcuts.tbc(inter, 'Страница автора'), style=cog.ButtonStyle.url,
		       		url=f'https://modrinth.com/user/{author["username"]}', row=2)
				]

				try:
					await inter.edit_original_response(embeds=[mod, featured_gallery], components=button)
				except:
					await inter.edit_original_response(embed=mod, components=button)

		elif data_type == "Пользователь":
			uri = f"user/{query}"
			async with aiohttp.ClientSession() as session:
				async with session.get(url=f'https://api.modrinth.com/v2/{uri}') as response:
					modget = await response.json()
				await session.close()


			thumbnail = modget["avatar_url"]
			ide = modget['id']

			role = ""

			if modget['role'] != None:
				if modget['role'] == "developer":
					role = await self.bot.shortcuts.tbc(inter, '⚙ Разработчик')
				elif modget['role'] == "moderator":
					role = await self.bot.shortcuts.tbc(inter, '🛡 Модератор')

			embed = cog.Embed(title=f"{modget['username']}", url=f'https://modrinth.com/user/{ide}',
					color=0x82e868)

			try: embed.set_thumbnail(thumbnail)
			except: pass

			if modget['bio'] != None:
				embed.add_field(name='БИО', value=f"{role}```{modget['bio']}```",
		  	    inline=False)

			button = [
				cog.ui.Button(label=await self.bot.shortcuts.tbc(inter, 'Страница пользователя'), style=cog.ButtonStyle.url,
		       		url=f'https://modrinth.com/user/{modget["id"]}', row=1)
			]

			if modget['email'] != None:
				embed.add_field(name=await self.bot.shortcuts.tbc(inter, 'Электронная почта'), value=modget['email'])

			embed.add_field(name=await self.bot.shortcuts.tbc(inter, 'ID пользователя'),
		   					value=modget["id"])

			if modget["github_id"] != None:
				embed.add_field(name='GitHub ID',
		   					value=modget["github_id"])

			date = datetime.datetime.fromisoformat(modget['created'])

			embed.add_field(name=await self.bot.shortcuts.tbc(inter, 'Аккаунт создан'),
		   					value=f"{cog.utils.format_dt(date, 'f')}\n{cog.utils.format_dt(date, 'R')}")

			await inter.edit_original_response(embed=embed, components=button)


def setup(bot):
	bot.add_cog(Modrinth(bot))
	bot.cog_reload(__name__)
