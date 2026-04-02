import random

import cog
from utils import config


class MyModal(cog.ui.Modal):
	def __init__(self, inter: cog.ApplicationCommandInteraction, bot: cog.MemeismBot):
		self.bot = bot
		plus_addictions = random.choice(["Бот супер!", "Ну так.. средне", "*иблюп*"])
		if plus_addictions == "Бот супер!":
			ratings = f"{random.randint(7, 10)}\u005C10"
		elif plus_addictions == "Ну так.. средне":
			ratings = f"{random.randint(4, 6)}\u005C10"
		else:
			ratings = f"{random.randint(0, 10)}\u005C10"

		components = [
			cog.ui.TextInput(
				label="Оценка от 1/10",
				placeholder=ratings,
				custom_id="Оценка от 1/10",
				style=cog.TextInputStyle.short,
				max_length=5,
			),
			cog.ui.TextInput(
				label="Дополнительный текст (не обязательно)",
				placeholder=plus_addictions,
				custom_id="Дополнительный текст",
				required=False,
				style=cog.TextInputStyle.paragraph,
			),
		]
		super().__init__(title="Отзыв", components=components, custom_id="bot_feedback")


class Feedback(cog.Cog):
	def __init__(self, bot: cog.MemeismBot):
		self.bot = bot

	@cog.listener()
	async def on_modal_submit(self, inter: cog.ModalInteraction):
		if inter.custom_id != "bot_feedback":
			return
		if not config.feedback_channel_id:
			await inter.response.send_message(
				"Обратная связь не настроена (FEEDBACK_CHANNEL_ID в .env).",
				ephemeral=True,
			)
			return

		embed = cog.Embed(title="Отзыв", description=f"ID автора: `{inter.author.id}`")
		embed.set_author(
			name=f"{inter.author.global_name} | {inter.author.name} | {inter.author.display_name}",
			icon_url=inter.author.display_avatar.url,
		)
		embed.set_image(config.embed_feedback_footer)
		for key, value in inter.text_values.items():
			if value[:1024] != "":
				embed.add_field(
					name=key.capitalize(),
					value=value[:1024],
					inline=False,
				)

		sender_channel = self.bot.get_channel(config.feedback_channel_id)
		if not sender_channel:
			await inter.response.send_message(
				await cog.shortcuts.tbc(inter, "Канал для отзывов не найден."),
				ephemeral=True,
			)
			return

		ping = (
			f"<@{config.feedback_ping_user_id}>"
			if config.feedback_ping_user_id
			else None
		)
		await sender_channel.send(content=ping, embed=embed)
		await inter.response.send_message(
			"Благодарю за отзыв от всего своего роботизировонного сердца <3!",
			ephemeral=True,
		)

	@cog.slash_command(
		name="feedback",
		description=cog.Localised("Leave a review about the bot", key="feedback_desc"),
	)
	async def feedback_cmd(self, inter: cog.ApplicationCommandInteraction):
		await inter.response.send_modal(MyModal(inter, self.bot))


def setup(bot):
	bot.add_cog(Feedback(bot))
	bot.cog_reload(__name__)
