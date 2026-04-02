import cog

class ExampleCog(cog.Cog):
	def __init__(self, bot: cog.Mitsuki):
		self.bot = bot

	@cog.slash_command(name="example_command")
	async def steamc(self, inter: cog.ApplicationCommandInteraction):
		await inter.response.send_message("Example command!")

def setup(bot: cog.MemeismBot):
	bot.add_cog(ExampleCog(bot))
	bot.cog_reload(__name__)