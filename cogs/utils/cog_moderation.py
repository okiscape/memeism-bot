from pathlib import Path

import cog
from utils import config


def _cogs_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _project_root() -> Path:
    return _cogs_root().parent


def iter_cog_extensions() -> list[str]:
    cogs_dir = _cogs_root()
    root = _project_root()
    out: list[str] = []
    for path in sorted(cogs_dir.rglob("*.py")):
        if path.name.startswith("__"):
            continue
        mod = ".".join(path.relative_to(root).with_suffix("").parts)
        out.append(mod)
    return out


class CogModeration(cog.Cog):
    def __init__(self, bot: cog.KisaBot):
        self.bot = bot

    def _allowed(self, inter: cog.ApplicationCommandInteraction) -> bool:
        return (
            config.bot_owner_id is not None and inter.author.id == config.bot_owner_id
        )

    async def _guard(self, inter: cog.ApplicationCommandInteraction) -> bool:
        if self._allowed(inter):
            return True
        await inter.response.send_message("Нет доступа.", ephemeral=True)
        return False

    def _normalize_ext(self, extension: str) -> str:
        ext = extension.strip()
        if ext.startswith("cogs."):
            return ext
        return f"cogs.{ext}"

    @cog.slash_command(
        name="cog_unload",
        description="Выгрузить модуль кога",
        guild_ids=[config.dev_guild_id] if config.dev_guild_id else None,
    )
    async def unload_cog(
        self,
        inter: cog.ApplicationCommandInteraction,
        extension: str = cog.Param(
            description="Например: data.logs или cogs.data.logs"
        ),
    ):
        if not await self._guard(inter):
            return
        await inter.response.defer(ephemeral=True)
        ext = self._normalize_ext(extension)
        try:
            self.bot.unload_extension(ext)
            await inter.edit_original_response(f"Выгружен: `{ext}`")
        except Exception as e:
            await inter.edit_original_response(f"Ошибка: `{e!s}`")

    @cog.slash_command(
        name="cog_reload",
        description="Перезагрузить один ког",
        guild_ids=[config.dev_guild_id] if config.dev_guild_id else None,
    )
    async def reload_cog(
        self,
        inter: cog.ApplicationCommandInteraction,
        extension: str = cog.Param(),
    ):
        if not await self._guard(inter):
            return
        await inter.response.defer(ephemeral=True)
        ext = self._normalize_ext(extension)
        try:
            self.bot.reload_extension(ext)
            await inter.edit_original_response(f"Перезагружен: `{ext}`")
        except Exception as e:
            await inter.edit_original_response(f"Ошибка: `{e!s}`")

    @cog.slash_command(
        name="cog_load",
        description="Загрузить ког",
        guild_ids=[config.dev_guild_id] if config.dev_guild_id else None,
    )
    async def load_cog(
        self,
        inter: cog.ApplicationCommandInteraction,
        extension: str = cog.Param(),
    ):
        if not await self._guard(inter):
            return
        await inter.response.defer(ephemeral=True)
        ext = self._normalize_ext(extension)
        try:
            self.bot.load_extension(ext)
            await inter.edit_original_response(f"Загружен: `{ext}`")
        except Exception as e:
            await inter.edit_original_response(f"Ошибка: `{e!s}`")

    @cog.slash_command(
        name="cog_reload_all",
        description="Перезагрузить все модули под cogs/",
        guild_ids=[config.dev_guild_id] if config.dev_guild_id else None,
    )
    async def reload_all_cogs(self, inter: cog.ApplicationCommandInteraction):
        if not await self._guard(inter):
            return
        await inter.response.defer(ephemeral=True)
        errors: list[str] = []
        extensions = iter_cog_extensions()
        for ext in extensions:
            try:
                if ext in self.bot.extensions:
                    self.bot.reload_extension(ext)
                else:
                    self.bot.load_extension(ext)
            except Exception as e:
                errors.append(f"{ext}: {e!s}")
        if errors:
            msg = "\n".join(errors[:20])
            if len(errors) > 20:
                msg += f"\n… и ещё {len(errors) - 20}"
            await inter.edit_original_response(msg[:2000])
        else:
            await inter.edit_original_response(
                f"ОК, обработано модулей: {len(extensions)}"
            )


def setup(bot):
    if not (config.dev_guild_id and config.bot_owner_id):
        return
    bot.add_cog(CogModeration(bot))
    bot.cog_reload(__name__)
