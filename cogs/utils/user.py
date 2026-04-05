import disnake
import datetime as dt
import cog

class SelfDeleteButton(cog.View):
    def __init__(self, bot: cog.MemeismBot):
        super().__init__(timeout=None)
        self.bot = bot

    @disnake.ui.button(
        emoji='<:IconDeleteTrashcan:750152850310561853>',
        style=disnake.ButtonStyle.secondary
    )
    async def selfdeletesbutton(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.message.delete()


class User(cog.Cog):
    def __init__(self, bot: cog.MemeismBot):
        self.bot = bot

    async def _user_info(self, inter: cog.ApplicationCommandInteraction, member: cog.Member):
      profile_fetch = await self.bot.database.readUserProfiles(member.id)
      profile = profile_fetch[0] if profile_fetch else None

      custom_color = self.bot.config.colors.blurple

      if profile and getattr(profile, 'color', None):
        custom_color = int(profile.color, 16)

      userrating = await self.bot.database.readSocialRating(user_id=member.id)
      rating_str = self.bot.translate(inter, "social_rating", rating=userrating[0].rating) if userrating else ""

      times_c = int(member.created_at.timestamp())
      times_j = None
      try:
          times_j = int(member.joined_at.timestamp())
      except:
          pass


      status_map = {
        'offline': (self.bot.custom_emojis.status_offline, self.bot.translate(inter, "offline")),
        'idle':    (self.bot.custom_emojis.status_idle,    self.bot.translate(inter, "idle")),
        'dnd':     (self.bot.custom_emojis.status_dnd,     self.bot.translate(inter, "dnd")),
        'online':  (self.bot.custom_emojis.status_online,  self.bot.translate(inter, "online")),
      }
      status_emoji, status_text = status_map.get(
          str(member.status), 
          (self.bot.custom_emojis.status_online, self.bot.translate(inter, "online")))

      if (member.activity and member.activity.type == disnake.ActivityType.custom and 
        getattr(member.activity, 'name', None)):
        status_text = f'{cog.sh.rmark(member.activity.name)}'
      else:
        status_text = f'{status_text}'


      service = []
      client_status = getattr(member, '_client_status', {}) or {}
      if 'desktop' in client_status:
        service.append("Desktop")
      if 'web' in client_status:
        service.append("Web")
      if 'mobile' in client_status:
        service.append("Mobile")

      serversi = ", ".join(service) if service else None


      media_links = [] # list of formatted translations. Guild avatar, Global avatar, Global banner, Guild banner

      fetched_user = await self.bot.fetch_user(member.id)
      if fetched_user.banner:
        media_links.append(self.bot.translate(
          inter,
          "user.main.description.global_banner",
          banner=fetched_user.banner.url)
        )
      if member.guild_banner:
        media_links.append(self.bot.translate(
          inter,
          "user.main.description.guild_banner",
          banner=member.guild_banner.url)
        )
      if member.avatar:
        media_links.append(self.bot.translate(
          inter,
          "user.main.description.global_avatar",
          avatar=member.avatar.url)
        )
      if member.guild_avatar:
        media_links.append(self.bot.translate(
          inter,
          "user.main.description.guild_avatar",
          avatar=member.guild_avatar.url)
        )

      description = f"""
{self.bot.translate(inter, "user.main.description.id", id=member.id)}
{self.bot.translate(inter, "user.main.description.names", global_name=member.global_name, username=member.name)}
{self.bot.translate(inter, "user.main.description.status", emoji=status_emoji, value=status_text)}{"\n - " + self.bot.translate(inter, "user.main.description.status_from", platforms=serversi) if serversi else ""}
{self.bot.translate(inter, "user.main.description.joined_at", timestamp=times_j)}
{self.bot.translate(inter, "user.main.description.created_at", timestamp=times_c)}
{self.bot.translate(inter, "user.main.description.media_files", links=", ".join(media_links))}
"""
      usersettings = await self.bot.database.readUserSettings(member.id)
      if usersettings:
          userset = usersettings[0]
          if userset.timezone:
            zone_code = int(userset.timezone.replace("UTC", ""))
            timezone = await cog.sh.get_time_in_timezone(zone_code)
            description += self.bot.translate(
              inter, 
              "user.main.description.timezone",
              tz=userset.timezone,
              time=timezone.strftime(format='%H:%M:%S')
            )

      # Spotify
      spotify_embed = None
      for activity in member.activities:
          if isinstance(activity, disnake.Spotify):
              desc = (
                  f"{self.bot.translate(inter, 'spotify_more_info')}\n"
                  f"{self.bot.translate(inter, 'spotify_artist')}`{activity.artist}`\n"
                  f"{self.bot.translate(inter, 'spotify_album')}`{activity.album}`"
              )
              spotify_embed = cog.Embed(
                  color=self.bot.config.colors.spotify_main,
                  title=f'{self.bot.custom_emojis.spotify_logo} {activity.title}',
                  url=activity.track_url,
                  description=desc
              )
              spotify_embed.set_author(
                  name=self.bot.translate(inter, "spotify_listening", name=member.display_name or member.name),
                  icon_url=member.avatar.url
              )
              spotify_embed.set_thumbnail(activity.album_cover_url)
              break

      membership = None
      if profile and (profile.about_me or profile.custom_image):
        membership = cog.Embed(
          color=custom_color,
          image=getattr(profile, 'custom_image', None),
          description=getattr(profile, 'about_me', None)
        )
      embed = cog.Embed(
        title=self.bot.translate(inter, "user.main.title", name=member.display_name),
        color=custom_color,
        description=description,
        thumbnail=member.display_avatar
      )

      embedss = [embed]
      if membership:
          embedss.append(membership)
      if spotify_embed:
          embedss.append(spotify_embed)

      await inter.edit_original_response(embeds=embedss, components=[])

    @cog.guild_only()
    @cog.slash_command(
        name='user',
        description=disnake.Localized(key="user_desc")
    )
    async def slash_user(self, 
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member = cog.Param(
          description=disnake.Localized(key="user_param_desc"),
          default=lambda i: i.author
      )):
      await inter.response.defer()

      print("slash used")
      await self._user_info(inter, member)
      print("slash responded")

    @cog.guild_only()
    @cog.user_command(name=disnake.Localized(key="user_desc"))
    async def user(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member):
      await inter.response.defer()
      await self._user_info(inter, member)

def setup(bot):
    bot.add_cog(User(bot))
    bot.cog_reload(__name__)