import datetime
import random

import cog
from utils import config


class InfoCommand(cog.Cog):
    def __init__(self, bot: cog.KisaBot):
        self.bot = bot

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
            title=self.bot.translate(inter, "info.avatar.title"),
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
            text=self.bot.translate(inter, "info.avatar.footer"),
            icon_url=inter.author.display_avatar.url,
        )
        await inter.edit_original_response(
            embed=e,
            view=self.bot.shortcuts.MessageDeleteView(),
        )

    @cog.user_command(name=cog.Localised(key="info.banner.usercommand.name"))
    async def banner(self, inter: cog.ApplicationCommandInteraction, user: cog.Member):
        await inter.response.defer(ephemeral=True)
        try:
            users: cog.User = await self.bot.fetch_user(user.id)
            if not users.banner:
                await inter.edit_original_response(
                    self.bot.translate(inter, "info.banner.error.no_banner")
                )
                return
            embed = cog.Embed(
                title=self.bot.translate(
                    inter, "info.banner.title", name=users.display_name
                ),
                color=0xEB459E,
            ).set_image(url=users.banner.url)
            await inter.edit_original_response(embed=embed)

        except Exception:
            await inter.edit_original_response(
                self.bot.translate(inter, "info.banner.error.fetch_failed")
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
        nsfw = self.bot.translate(
            inter, "common.yes" if channel.is_nsfw() else "common.no"
        )
        news = self.bot.translate(
            inter, "common.yes" if channel.is_news() else "common.no"
        )
        ts = int(channel.created_at.timestamp())
        embed = cog.Embed(
            title=self.bot.translate(
                inter, "info.channel.title", channel_name=channel.name
            ),
            description=self.bot.translate(
                inter,
                "info.channel.description",
                channel_id=channel.id,
                channel_mention=channel.mention,
                nsfw=nsfw,
                news=news,
                ts=ts,
            ),
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
            title=self.bot.translate(inter, "info.server.title", server_name=g.name),
        )
        guild.add_field(
            name=self.bot.translate(
                inter,
                "info.server.field.owner",
                emoji=self.bot.custom_emojis.icon_user_add,
            ),
            value=owner.mention if owner else "\u2014",
        )
        guild.add_field(
            name=self.bot.translate(
                inter,
                "info.server.field.created",
                emoji=self.bot.custom_emojis.icon_clock,
            ),
            value=f"<t:{crt}:R>",
        )
        guild.add_field(
            name=self.bot.translate(
                inter,
                "info.server.field.id",
                emoji=self.bot.custom_emojis.icon_paperclip,
            ),
            value=f"*{g.id}*",
        )
        guild.add_field(
            name=self.bot.translate(
                inter,
                "info.server.field.channels",
                emoji=self.bot.custom_emojis.icon_terminal,
            ),
            value=self.bot.translate(
                inter,
                "info.server.field.channels_value",
                text=len(g.text_channels),
                voice=len(g.voice_channels),
                forum=len(g.forum_channels),
                categories=len(g.categories),
            ),
        )
        guild.add_field(
            name=self.bot.translate(
                inter,
                "info.server.field.emojis",
                emoji=random.choice(self.bot.custom_emojis.thinkings),
                count=len(g.emojis),
            ),
            value=f"*{len(g.emojis)}*",
        )
        guild.add_field(
            name=self.bot.translate(
                inter,
                "info.server.field.roles",
                emoji=self.bot.custom_emojis.icon_layers,
                count=len(g.roles),
            ),
            value=self.bot.translate(inter, "info.server.field.roles_value"),
        )
        boosts = int(g.premium_subscription_count or 0)
        guild.add_field(
            name=self.bot.translate(
                inter,
                "info.server.field.members",
                emoji=self.bot.custom_emojis.icon_user,
            ),
            value=self.bot.translate(
                inter,
                "info.server.field.members_value",
                count=len(g.members),
                boosts=boosts,
            ),
        )
        guild.add_field(
            name=self.bot.translate(
                inter,
                "info.server.field.verification",
                emoji=self.bot.custom_emojis.icon_layers,
            ),
            value=f"*{int(g.verification_level.value)}*",
        )
        if g.icon:
            guild.set_thumbnail(url=g.icon.url)
        if g.banner:
            guild.set_image(url=g.banner.url)
        await inter.edit_original_response(
            embed=guild,
            components=[
                cog.ui.Button(
                    label=self.bot.translate(inter, "info.server.button.roles"),
                    style=cog.ButtonStyle.secondary,
                    custom_id="server_button_role",
                    row=0,
                ),
                cog.ui.Button(
                    label=self.bot.translate(inter, "info.server.button.categories"),
                    style=cog.ButtonStyle.secondary,
                    custom_id="server_button_category",
                    row=1,
                ),
            ],
        )

    @cog.slash_command(
        name="ping", description=cog.Localised("Check bot latency", key="ping_desc")
    )
    async def ping(self, inter: cog.ApplicationCommandInteraction):
        await inter.response.defer()
        pingg = self.bot.latency * 1000
        await inter.edit_original_response(
            self.bot.translate(inter, "info.ping.response", ping=round(pingg))
        )

    @cog.slash_command(
        name="info", description=cog.Localised("Bot information", key="info_desc")
    )
    async def info(self, inter: cog.ApplicationCommandInteraction):
        await inter.response.defer()

        bot_created = int(self.bot.user.created_at.timestamp())
        embed = cog.Embed(
            title=self.bot.translate(inter, "info.main.title"),
            url=config.support_invite_url,
            description=self.bot.translate(inter, "info.main.summary"),
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(
            text=self.bot.translate(
                inter, "info.main.footer", user_display_name=inter.author.display_name
            ),
        )
        embed.add_field(
            name=self.bot.translate(inter, "info.main.field.developer_server.title"),
            value=self.bot.translate(
                inter,
                "info.main.field.developer_server.value",
                invite_url=config.support_invite_url,
            ),
            inline=False,
        )
        embed.add_field(
            name=self.bot.translate(inter, "info.main.field.created_at.title"),
            value=self.bot.translate(
                inter, "info.main.field.created_at.value", timestamp=bot_created
            ),
            inline=False,
        )

        embed.add_field(
            name=self.bot.translate(inter, "info.main.field.version.title"),
            value=self.bot.translate(
                inter,
                "info.main.field.version.value",
                number=config.version_number,
                name=config.version_name,
            ),
            inline=False,
        )

        cmd_sum = (
            len(self.bot.all_user_commands)
            + len(self.bot.all_message_commands)
            + len(self.bot.all_slash_commands)
        )

        embed.add_field(
            name=self.bot.translate(inter, "info.main.field.commands.title"),
            value=self.bot.translate(
                inter,
                "info.main.field.commands.value",
                cmd_sum=cmd_sum,
                slash_count=len(self.bot.all_slash_commands),
                message_count=len(self.bot.all_message_commands),
                user_count=len(self.bot.all_user_commands),
            ),
            inline=True,
        )

        await inter.edit_original_response(embed=embed)

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
        add_label = self.bot.translate(
            inter, "info.invite.add_label", bot_name=self.bot.user.display_name
        )
        e = cog.Embed(
            title=self.bot.translate(
                inter, "info.invite.title", user_name=inter.author.display_name
            ),
            description=self.bot.translate(inter, "info.invite.description"),
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
                    label=self.bot.translate(inter, "info.invite.button.dev_server"),
                    emoji=self.bot.custom_emojis.icon_help,
                    style=cog.ButtonStyle.link,
                    url=config.support_invite_url,
                ),
            ],
        )

    @cog.user_command(
        name=cog.Localised("Get user avatar", key="info.avatar.usercommand.name")
    )
    async def user_avatar_cmd(
        self,
        inter: cog.ApplicationCommandInteraction,
        member: cog.User,
    ):
        await inter.response.defer(ephemeral=True)
        e = cog.Embed(
            title=self.bot.translate(inter, "info.avatar.title"),
            url=str(member.avatar.url) if member.avatar else None,
            color=0x333333,
            timestamp=datetime.datetime.now(),
            author={
                "name": f"{member.global_name} | {member.name}",
                "icon": member.display_avatar.url,
            },
            image=member.display_avatar.url,
            footer={
                "text": self.bot.translate(inter, "info.avatar.footer"),
                "icon": inter.author.display_avatar.url,
            },
        )
        if member.display_avatar != member.avatar:
            e.set_thumbnail(url=member.avatar.url)

        await inter.edit_original_response(f"{inter.author.mention}", embed=e)

    @cog.listener()
    async def on_button_click(self, inter: cog.MessageInteraction):
        if inter.component.custom_id not in (
            "server_button_category",
            "server_button_role",
        ):
            return
        if inter.component.custom_id == "server_button_role":
            role_list = []
            for role in inter.guild.roles:
                role_list.append(f"<@&{role.id}> `({role.id})`\n")
            role_emb = cog.Embed(
                title=self.bot.translate(
                    inter, "info.server.roles.title", server_name=inter.guild.name
                ),
                description=" ".join(role_list),
            )
            if inter.guild.icon:
                role_emb.set_author(
                    icon_url=inter.guild.icon.url, name=inter.guild.name
                )
            await inter.response.send_message(embed=role_emb, ephemeral=True)
        elif inter.component.custom_id == "server_button_category":
            role_emb = cog.Embed(
                title=self.bot.translate(
                    inter,
                    "info.server.categories.title",
                    server_name=inter.guild.name,
                ),
            )
            for cat in inter.guild.categories:
                nsfw = self.bot.translate(
                    inter, "common.yes" if cat.nsfw else "common.no"
                )
                role_emb.add_field(
                    name=f"`{cat.name}`",
                    value=self.bot.translate(
                        inter,
                        "info.server.categories.field",
                        id=cat.id,
                        count=len(cat.channels) - 1,
                        nsfw=nsfw,
                    ),
                )
            if inter.guild.icon:
                role_emb.set_author(
                    icon_url=inter.guild.icon.url, name=inter.guild.name
                )
            await inter.response.send_message(embed=role_emb, ephemeral=True)


def setup(bot: cog.KisaBot):
    bot.add_cog(InfoCommand(bot))
    bot.cog_reload(__name__)
