from datetime import datetime

import cog


class Timestamp(cog.Cog):
    def __init__(self, bot: cog.KisaBot):
        self.bot = bot

    @cog.slash_command(name="timestamp")
    async def timestamp(self, inter: cog.ApplicationCommandInteraction):
        pass

    @timestamp.sub_command(
        name="now",
        description=cog.Localised("Current timestamp", key="timestamp_now_desc"),
    )
    async def now(self, inter: cog.ApplicationCommandInteraction):
        code = int(datetime.now().timestamp())
        timestamps = []
        for cd in ("d", "D", "t", "T", "f", "F", "R", ""):
            if cd:
                timestamps.append(f"`<t:{code}:{cd}>` -> <t:{code}:{cd}>")
            else:
                timestamps.append(str(code))
        await inter.response.send_message("\n".join(timestamps))


def setup(bot):
    bot.add_cog(Timestamp(bot))
    bot.cog_reload(__name__)
