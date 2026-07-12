import json
from pathlib import Path

import disnake
from disnake.ext.commands import AutoShardedInteractionBot, Cog
from utils import bot_logging, config, database, emojis, shortcuts


class KisaBot(AutoShardedInteractionBot):
    """Custom Bot Class"""

    def __init__(self, cogs: list[str] = []) -> None:

        self.ApplicationCommandInteraction = disnake.ApplicationCommandInteraction
        self.config = config
        self.loaded_cogs: list[Cog] = []
        self.loaded_cogs_formatted = None
        self.logging = bot_logging.Logging()
        self.database = database.DatabaseManager(config.postgres_dsn)
        self.shortcuts = shortcuts
        self.custom_emojis = emojis

        intents = disnake.Intents.all()

        super().__init__(
            reload=True,
            status=disnake.Status.idle,
            intents=intents,
            enable_debug_events=True,
            proxy=config.proxy_url,
        )

        self.build_flat_files()
        self.i18n.load("translations/.flat")
        self._translation = shortcuts.Translation(self.i18n)
        self.translate = self._translation.translate

        self.cog_load(cogs)
        self.run_bot()

    def build_flat_files(self):
        base_path = Path("translations")
        output_path = Path("translations/.flat")
        output_path.mkdir(exist_ok=True)

        result = {}

        def flattenDict(data: dict, prefix: str | None = None) -> dict[str, str]:
            result: dict[str, str] = {}

            for key, value in data.items():
                current_key = f"{prefix}.{key}" if prefix else key

                if isinstance(value, dict):
                    result.update(flattenDict(value, current_key))
                elif isinstance(value, str):
                    result[current_key] = value
                else:
                    result[current_key] = str(value)

            return result

        for lang_dir in base_path.iterdir():
            if lang_dir.name == ".flat":
                continue
            if not lang_dir.is_dir():
                continue

            lang_code = lang_dir.name
            result[lang_code] = {}

            for json_file in lang_dir.glob("**/*.json"):
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                    result[lang_code].update(flattenDict(data))

        for lang, data in result.items():
            with open(output_path / f"{lang}.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    async def setup_hook(self):
        await self.database.init_schema()

    def run_bot(self):
        self.logging.info(
            "Starting...", f"Proxy: {self.config.proxy_url}", type="gateway"
        )
        self.run(self.config.bot_token)

    def dictFormat(self, data, indent=0, indent_str="| "):
        result = ""
        if isinstance(data, dict):
            if not data:
                result += indent_str * indent + "None\n"

            for key, value in data.items():
                result += indent_str * indent + str(key) + ":\n"
                result += self.dictFormat(value, indent + 1, indent_str)

        elif isinstance(data, list):
            if not data:
                result += indent_str * indent + "None\n"

            for item in data:
                result += self.dictFormat(item, indent + 1, indent_str)

        else:
            result += indent_str * indent + str(data) + "\n"
        return result

    async def on_ready(self):
        self.logging.info("Ready", type="gateway")
        await self.setup_hook()
        self.loaded_cogs = self.cogs
        loaded = {}
        for name in self.cogs:
            cog: Cog = self.get_cog(name)
            loaded[cog.__module__] = {"commands": [], "listeners": []}
            for command in cog.__cog_app_commands__:
                loaded[command.cog.__module__]["commands"].append(
                    command.qualified_name
                )

            for listener in cog.__cog_listeners__:
                loaded[command.cog.__module__]["listeners"].append(listener[0])

        self.loaded_cogs_formatted = self.dictFormat(loaded)

    async def on_disconnect(self):
        self.logging.warning("Disconnected", type="gateway")

    async def on_connect(self):
        self.logging.info("Connected", type="gateway")

    def cog_reload(self, __name__):
        """Уведомление о перезагрузке кога
        reload=True"""
        self.logging.debug("Cog reloaded", __name__, type="cogs")

    def cog_load(self, cogs: list[str]):
        self.logging.info("Cogs loading start...", type="cogs")

        for cog in cogs:
            self.logging.info(f"Cog ({cog}) load", type="cogs")
            self.load_extension(cog)
