import disnake

import cog


class SelfDeleteButton(cog.View):
    def __init__(self, bot: cog.KisaBot):
        super().__init__(timeout=None)
        self.bot = bot

    @disnake.ui.button(
        emoji="<:IconDeleteTrashcan:750152850310561853>",
        style=disnake.ButtonStyle.secondary,
    )
    async def selfdeletesbutton(self, _, inter: disnake.MessageInteraction):
        await inter.message.delete()


class User(cog.Cog):
    def __init__(self, bot: cog.KisaBot):
        self.bot = bot

    async def _user_info(
        self, inter: cog.ApplicationCommandInteraction, member: cog.Member
    ):
        profile_fetch = await self.bot.database.readUserProfiles(member.id)
        profile = profile_fetch[0] if profile_fetch else None

        custom_color = self.bot.config.colors.blurple

        if profile and getattr(profile, "color", None):
            custom_color = int(profile.color, 16)

        userrating = await self.bot.database.readSocialRating(user_id=member.id)
        rating_str = (
            self.bot.translate(inter, "social_rating", rating=userrating[0].rating)
            if userrating
            else ""
        )

        times_c = int(member.created_at.timestamp())
        times_j = None
        try:
            times_j = int(member.joined_at.timestamp())
        except:
            pass

        status_map = {
            "offline": (
                self.bot.custom_emojis.status_offline,
                self.bot.translate(inter, "common.status.offline"),
            ),
            "idle": (
                self.bot.custom_emojis.status_idle,
                self.bot.translate(inter, "common.status.idle"),
            ),
            "dnd": (
                self.bot.custom_emojis.status_dnd,
                self.bot.translate(inter, "dnd"),
            ),
            "online": (
                self.bot.custom_emojis.status_online,
                self.bot.translate(inter, "common.status.online"),
            ),
        }
        status_emoji, status_text = status_map.get(
            str(member.status),
            (
                self.bot.custom_emojis.status_online,
                self.bot.translate(inter, "common.status.online"),
            ),
        )

        if (
            member.activity
            and member.activity.type == disnake.ActivityType.custom
            and getattr(member.activity, "name", None)
        ):
            status_text = f"{cog.sh.rmark(member.activity.name)}"
        else:
            status_text = f"{status_text}"

        service = []
        client_status = getattr(member, "_client_status", {}) or {}
        if "desktop" in client_status:
            service.append(self.bot.translate(inter, "common.device.desktop"))
        if "web" in client_status:
            service.append(self.bot.translate(inter, "common.device.web"))
        if "mobile" in client_status:
            service.append(self.bot.translate(inter, "common.device.mobile"))

        serversi = ", ".join(service) if service else None

        media_links = []  # list of formatted translations. Guild avatar, Global avatar, Global banner, Guild banner

        fetched_user = await self.bot.fetch_user(member.id)
        if fetched_user.banner:
            media_links.append(
                self.bot.translate(
                    inter,
                    "user.response.global_banner",
                    banner=fetched_user.banner.url,
                )
            )
        if member.guild_banner:
            media_links.append(
                self.bot.translate(
                    inter,
                    "user.response.guild_banner",
                    banner=member.guild_banner.url,
                )
            )
        if member.avatar:
            media_links.append(
                self.bot.translate(
                    inter,
                    "user.response.global_avatar",
                    avatar=member.avatar.url,
                )
            )
        if member.guild_avatar:
            media_links.append(
                self.bot.translate(
                    inter,
                    "user.response.guild_avatar",
                    avatar=member.guild_avatar.url,
                )
            )

        description = f"""
{self.bot.translate(inter, "user.response.id", id=member.id)}
{self.bot.translate(inter, "user.response.names", global_name=member.global_name, username=member.name)}
{self.bot.translate(inter, "user.response.status", emoji=status_emoji, value=status_text)} {f"({serversi})" if serversi else ""}
{self.bot.translate(inter, "user.response.joined_at", timestamp=times_j)}
{self.bot.translate(inter, "user.response.created_at", timestamp=times_c)}
{self.bot.translate(inter, "user.response.media_files", links=", ".join(media_links))}
"""
        usersettings = await self.bot.database.readUserSettings(member.id)
        if usersettings:
            userset = usersettings[0]
            if userset.timezone:
                zone_code = userset.timezone
                if userset.timezone != "UTC":
                    zone_code = int(userset.timezone.replace("UTC", ""))
                else:
                    zone_code = 0
                timezone = await cog.sh.get_time_in_timezone(zone_code)
                description += self.bot.translate(
                    inter,
                    "user.response.timezone",
                    tz=userset.timezone,
                    time=timezone.strftime(format="%H:%M:%S %d/%m/%Y"),
                )

        spotify_embed = None
        for activity in member.activities:
            if isinstance(activity, disnake.Spotify):
                spotify_pl = cog.sh.build_spotify_placeholders(activity)
                desc = cog.sh.replace_placeholders(
                    f"{self.bot.translate(inter, 'user.response.spotify.artist')}\n"
                    f"{self.bot.translate(inter, 'user.response.spotify.album')}",
                    spotify_pl,
                )
                spotify_embed = cog.Embed(
                    color=self.bot.config.colors.spotify_main
                    if not custom_color
                    else custom_color,
                    title=cog.sh.replace_placeholders(
                        f"{self.bot.custom_emojis.spotify_logo} {{spotify.title}}",
                        spotify_pl,
                    ),
                    url=activity.track_url,
                    description=desc,
                    thumbnail=activity.album_cover_url,
                    author={
                        "name": self.bot.translate(
                            inter,
                            "user.response.spotify.author",
                            name=member.display_name or member.name,
                        ),
                        "icon": member.avatar.url,
                    },
                )
                break

        membership = None
        if profile and (profile.about_me or profile.custom_image):
            membership = cog.Embed(
                color=custom_color,
                image=getattr(profile, "custom_image", None),
                description=getattr(profile, "about_me", None),
            )
        embed = cog.Embed(
            title=self.bot.translate(
                inter, "user.response.title", name=member.display_name
            ),
            color=custom_color,
            description=description,
            thumbnail=member.display_avatar,
        )

        embedss = [embed]
        if membership:
            embedss.append(membership)
        if spotify_embed:
            embedss.append(spotify_embed)

        await inter.edit_original_response(embeds=embedss, components=[])

    @cog.guild_only()
    @cog.slash_command(
        name="user", description=disnake.Localized(key="user.slash.description")
    )
    async def slash_user(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member = cog.Param(
            description=disnake.Localized(key="user.slash.option.member.description"),
            default=lambda i: i.author,
        ),
    ):
        await inter.response.defer()

        print("slash used")
        await self._user_info(inter, member)
        print("slash responded")

    @cog.guild_only()
    @cog.user_command(name=disnake.Localized(key="user.usercommand.name"))
    async def user(
        self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member
    ):
        await inter.response.defer()
        await self._user_info(inter, member)


def setup(bot):
    bot.add_cog(User(bot))
    bot.cog_reload(__name__)
