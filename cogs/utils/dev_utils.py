import cog


class DevUtilsCog(cog.Cog):
    def __init__(self, bot: cog.KisaBot):
        self.bot = bot

    @cog.slash_command(name="cache")
    async def cachecontrol(self, inter: cog.ApplicationCommandInteraction):
        pass

    @cachecontrol.sub_command("clear", description="Clear database cache")
    async def cacheclear(self, inter: cog.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        await self.bot.database._clearCache()
        await inter.edit_original_response("Cache cleared!")

    @cog.slash_command(name="test_locale", guild_ids=[1489192937169359012])
    async def test_locale(self, inter: cog.ApplicationCommandInteraction):
        await inter.send(self.bot.translate(inter, "test_locales"))

    @cog.listener()
    async def on_interaction(self, inter: cog.Interaction):
        now = self.bot.shortcuts.now_datetime().strftime("%Y-%m-%d %H:%M:%S | ")

        if inter.type == cog.InteractionType.application_command:
            arguments = {}
            num = 0

            try:
                for argument in inter.data["options"]:
                    arguments[argument["name"]] = inter.data["options"][num]["value"]
                    num += 1

                arguments = f" | {arguments}"
            except:
                arguments = ""

            try:
                if inter.data["options"][0]["name"] not in arguments:
                    sub = f" {inter.data['options'][0]['name']}"
                else:
                    sub = ""
            except:
                sub = ""
            if inter.guild:
                guinfo = (
                    f"Guild name: '{inter.guild.name}' | Guild id: {inter.guild.id}"
                )
            else:
                guinfo = "DM"
            # print(f"{now}EXECUTE COMMAND | {guinfo} | {inter.author.global_name or inter.author.name} | {inter.author.id} | {inter.data['name']}{sub}{arguments}")
            self.bot.logging.info(
                f"{guinfo} | Author: {inter.author.global_name or inter.author.name} | {inter.author.id} | Args: {inter.data['name']}{sub}{arguments}",
                type="execute command",
            )

        if inter.type == cog.InteractionType.component:
            if inter.guild:
                guinfo = (
                    f"Guild name: '{inter.guild.name}' | Guild id: {inter.guild.id}"
                )
            else:
                guinfo = "DM"

            try:
                # print(f"{now}EXECUTE COMPONENT | {guinfo} | Author: {inter.author.global_name or inter.author.name} | {inter.author.id} | {inter.data['custom_id']} | {inter.data['values']}")
                self.bot.logging.info(
                    f"{guinfo} | Author: {inter.author.global_name or inter.author.name} | {inter.author.id} | Cus-id: {inter.data['custom_id']} | Values: {inter.data['values']}",
                    type="execute component",
                )
            except:
                # print(f"{now}EXECUTE COMPONENT | {guinfo} | Author: {inter.author.global_name or inter.author.name} | {inter.author.id} | {inter.data['custom_id']}")
                self.bot.logging.info(
                    f"{guinfo} | Author: {inter.author.global_name or inter.author.name} | {inter.author.id} | Cus-id: {inter.data['custom_id']}",
                    type="execute component",
                )

        if inter.type == cog.InteractionType.modal_submit:
            arguments = {}
            num = 0
            for value in inter.data["components"]:
                arguments[value["components"][0]["custom_id"]] = value["components"][0][
                    "value"
                ]
                num += 1
            if inter.guild:
                guinfo = (
                    f"Guild name: '{inter.guild.name}' | Guild id: {inter.guild.id}"
                )
            else:
                guinfo = "DM"

            # print(f"{now}EXECUTE MODAL | {guinfo}  | {inter.author.global_name} | {inter.author.id} | {inter.data['custom_id']}  | {arguments}")
            self.bot.logging.info(
                f"{guinfo} | Author: {inter.author.global_name or inter.author.name} | {inter.author.id} | Cus-id: {inter.data['custom_id']} | Inserts: {arguments}",
                type="complete modal",
            )

        if inter.type == cog.InteractionType.application_command_autocomplete:
            if inter.guild:
                guinfo = (
                    f"Guild name: '{inter.guild.name}' | Guild id: {inter.guild.id}"
                )
            else:
                guinfo = "DM"

            # print(f"{now}REQUEST AUTOCOMPLETE | {guinfo} | {inter.author.global_name or inter.author.name} | {inter.author.id} | {inter.data['name']}")
            self.bot.logging.info(
                f"{guinfo} | Author: {inter.author.global_name or inter.author.name} | {inter.author.id} | Name: {inter.data['name']}",
                type="autocomplete",
            )


def setup(bot: cog.KisaBot):
    bot.add_cog(DevUtilsCog(bot))
    bot.cog_reload(__name__)
