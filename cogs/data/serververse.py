import io

import cog
from utils.types import AsyncLRUTTLCache, Filter, SerververseRecord

_PENDING_TTL = 600


def _author_hook_name(member: cog.Member | cog.User) -> str:
    return str(member.display_name or member.global_name or member.name)


class Serververse(cog.Cog):
    def __init__(self, bot: cog.KisaBot):
        self.bot = bot
        self.pending_links = AsyncLRUTTLCache(maxsize=128, ttl=_PENDING_TTL)

    async def _send_via_webhook(
        self,
        dest_channel_id: int,
        author: cog.User,
        message: cog.Message,
    ) -> None:
        dest = await self.bot.fetch_channel(dest_channel_id)
        if not dest:
            return

        hook_name = _author_hook_name(author)

        hooks = await dest.webhooks()
        hook = next((h for h in hooks if getattr(h, "name", None) == hook_name), None)

        if hook is None:
            try:
                hook = await dest.create_webhook(
                    name=hook_name,
                    avatar=author.display_avatar,
                    reason="kisa serververse: webhook as proxy for user",
                )
            except Exception:
                hook = await dest.create_webhook(
                    name=hook_name,
                    reason="kisa serververse: webhook as proxy for user",
                )

        files = []
        for attachment in message.attachments or []:
            try:
                data = await attachment.read()
                buf = io.BytesIO(data)
                buf.seek(0)
                files.append(cog.File(buf, attachment.filename))
            except Exception:
                pass

        await hook.send(
            content=message.content or None,
            avatar_url=str(author.display_avatar.url),
            files=files or None,
        )

    async def _find_link_between(
        self, guild_a: int, guild_b: int
    ) -> SerververseRecord | None:
        rows = await self.bot.database.readSerververse(guild_id=guild_a, channel_id=0)
        for row in rows:
            if {row.guild_id1, row.guild_id2} == {guild_a, guild_b}:
                return row
        return None

    @cog.listener()
    async def on_message(self, message: cog.Message) -> None:
        if not message.guild:
            return
        if not message.author or message.author.bot:
            return
        if not message.content and not message.attachments:
            return

        src_channel_id = message.channel.id
        rows = await self.bot.database.readSerververse(
            guild_id=message.guild.id, channel_id=src_channel_id
        )
        if not rows:
            return

        dest_ids = set()
        for settings in rows:
            if src_channel_id == settings.channel_id1 and settings.channel_id2:
                dest_ids.add(settings.channel_id2)
            elif src_channel_id == settings.channel_id2 and settings.channel_id1:
                dest_ids.add(settings.channel_id1)

        for dest_id in dest_ids:
            await self._send_via_webhook(dest_id, message.author, message)

    @cog.slash_command(name="serververse")
    async def verce(self, inter: cog.ApplicationCommandInteraction):
        pass

    @verce.sub_command(
        name="link",
        description=cog.Localised("", key="serververse.link.description"),
    )
    @cog.has_permissions(administrator=True)
    async def create_link(
        self,
        inter: cog.ApplicationCommandInteraction,
        target_server: str = cog.Param(
            description=cog.Localised("", key="serververse.link.option.target"),
        ),
    ):
        if not inter.guild:
            return
        await inter.response.defer(ephemeral=True)

        try:
            target_id = int(target_server)
        except ValueError:
            await inter.edit_original_response(
                self.bot.translate(inter, "serververse.link.error.invalid_id")
            )
            return

        if not any(g.id == target_id for g in self.bot.guilds):
            await inter.edit_original_response(
                self.bot.translate(inter, "serververse.link.error.not_on_server")
            )
            return

        existing = await self._find_link_between(inter.guild.id, target_id)
        if existing:
            await inter.edit_original_response(
                self.bot.translate(inter, "serververse.link.error.already_linked")
            )
            return

        pending = await self.pending_links.get(inter.guild.id)
        if pending and pending[0] == target_id:
            await self.bot.database.createSerververse(
                guild_id1=pending[0],
                channel_id1=pending[1],
                guild_id2=inter.guild.id,
                channel_id2=inter.channel.id,
            )
            await inter.edit_original_response(
                self.bot.translate(inter, "serververse.link.completed")
            )
            return

        already = await self.pending_links.get(target_id)
        if already:
            await inter.edit_original_response(
                self.bot.translate(inter, "serververse.link.error.already_invited")
            )
            return

        await self.pending_links.set(target_id, (inter.guild.id, inter.channel.id))
        await inter.edit_original_response(
            self.bot.translate(inter, "serververse.link.invitation_sent")
        )

    @verce.sub_command(
        name="channel",
        description=cog.Localised("", key="serververse.channel.description"),
    )
    @cog.has_permissions(administrator=True)
    async def change_channel(self, inter: cog.ApplicationCommandInteraction):
        if not inter.guild:
            return
        await inter.response.defer(ephemeral=True)

        rows = await self.bot.database.readSerververse(
            guild_id=inter.guild.id, channel_id=0, limit=20
        )
        if not rows:
            await inter.edit_original_response(
                self.bot.translate(inter, "serververse.channel.not_found")
            )
            return

        for v in rows:
            if v.guild_id1 == inter.guild.id and v.channel_id2:
                other_guild_id = v.guild_id2
                other_channel_id = v.channel_id2
                break
            elif v.guild_id2 == inter.guild.id and v.channel_id1:
                other_guild_id = v.guild_id1
                other_channel_id = v.channel_id1
                break
        else:
            await inter.edit_original_response(
                self.bot.translate(inter, "serververse.channel.error")
            )
            return

        await self.bot.database.createSerververse(
            guild_id1=other_guild_id,
            channel_id1=other_channel_id,
            guild_id2=inter.guild.id,
            channel_id2=inter.channel.id,
        )
        await inter.edit_original_response(
            self.bot.translate(inter, "serververse.channel.changed")
        )

    @verce.sub_command(
        name="unlink",
        description=cog.Localised("", key="serververse.unlink.description"),
    )
    @cog.has_permissions(administrator=True)
    async def unlink(self, inter: cog.ApplicationCommandInteraction):
        if not inter.guild:
            return
        await inter.response.defer(ephemeral=True)

        rows = await self.bot.database.readSerververse(
            guild_id=inter.guild.id, channel_id=0, limit=50
        )
        if not rows:
            await inter.edit_original_response(
                self.bot.translate(inter, "serververse.unlink.not_found")
            )
            return

        seen = set()
        lines = []
        for v in rows:
            if v.guild_id1 == inter.guild.id:
                other_gid, other_cid = v.guild_id2, v.channel_id2
            else:
                other_gid, other_cid = v.guild_id1, v.channel_id1
            key = (other_gid, other_cid)
            if key in seen:
                continue
            seen.add(key)

            guild = self.bot.get_guild(other_gid)
            server = guild.name if guild else f"`{other_gid}`"
            channel = (
                f"#{guild.get_channel(other_cid).name}"
                if guild and guild.get_channel(other_cid)
                else f"`{other_cid}`"
            )
            lines.append(f"{server} → {channel}")

        pairs = {(v.guild_id1, v.guild_id2) for v in rows} | {
            (v.guild_id2, v.guild_id1) for v in rows
        }
        for g1, g2 in pairs:
            await self.bot.database.deleteSerververse(g1, g2)

        await inter.edit_original_response(
            self.bot.translate(
                inter,
                "serververse.unlink.completed",
                details="\n".join(lines),
            )
        )

    @verce.sub_command(
        name="info",
        description=cog.Localised("", key="serververse.info.description"),
    )
    async def link_info(self, inter: cog.ApplicationCommandInteraction):
        if not inter.guild:
            return
        await inter.response.defer(ephemeral=True)

        rows = await self.bot.database.readSerververse(
            guild_id=inter.guild.id, channel_id=inter.channel.id, cacheOverwrite=True
        )
        if not rows:
            await inter.edit_original_response(
                self.bot.translate(inter, "serververse.info.not_found")
            )
            return

        other_guild_id = None
        other_channel_id = None
        for v in rows:
            if v.guild_id1 == inter.guild.id and v.channel_id1 == inter.channel.id:
                other_guild_id = v.guild_id2
                other_channel_id = v.channel_id2
                break
            elif v.guild_id2 == inter.guild.id and v.channel_id2 == inter.channel.id:
                other_guild_id = v.guild_id1
                other_channel_id = v.channel_id1
                break

        if not other_guild_id or not other_channel_id:
            await inter.edit_original_response(
                self.bot.translate(inter, "serververse.info.not_found")
            )
            return

        other_guild = self.bot.get_guild(other_guild_id)
        if not other_guild:
            await inter.edit_original_response(
                self.bot.translate(inter, "serververse.info.not_accessible")
            )
            return

        other_channel = other_guild.get_channel(other_channel_id)
        channel_name = getattr(other_channel, "name", str(other_channel_id))

        category_name = None
        if other_channel and other_channel.category:
            category_name = other_channel.category.name

        embed = cog.Embed(
            title=self.bot.translate(
                inter, "serververse.info.title", server_name=other_guild.name
            ),
            description=(
                f"**{self.bot.translate(inter, 'serververse.info.channel', channel_name=channel_name)}**\n"
                + (
                    self.bot.translate(
                        inter,
                        "serververse.info.category",
                        category_name=category_name,
                    )
                    if category_name
                    else self.bot.translate(inter, "serververse.info.no_category")
                )
            ),
        )
        if other_guild.icon:
            embed.set_thumbnail(url=other_guild.icon.url)

        await inter.edit_original_response(embed=embed)

        await self.bot.database.readSerververse(
            guild_id=inter.guild.id, channel_id=inter.channel.id, cacheOverwrite=True
        )


def setup(bot: cog.KisaBot):
    bot.add_cog(Serververse(bot))
    bot.cog_reload(__name__)
