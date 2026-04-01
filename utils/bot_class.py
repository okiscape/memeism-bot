import disnake
from disnake.ext.commands import InteractionBot, Cog
from utils import config, bot_logging, database


class MemeismBot(InteractionBot):
  """Custom Bot Class"""
  def __init__(self, cogs: list[str] = None) -> None:
    
    self.ApplicationCommandInteraction = disnake.ApplicationCommandInteraction
    self.config  = config
    self.loaded_cogs: list[Cog] = None
    self.loaded_cogs_formatted = None
    self.logging = bot_logging.Logging()
    self.database = database.DatabaseManager(config.db_path)
    
    intents = disnake.Intents.all()

    super().__init__(reload=True, 
            status=disnake.Status.dnd, 
            intents=intents,
            enable_debug_events=True)
    self.cog_load(cogs)
    self.run_bot()
  
  def run_bot(self):
    self.logging.info("client", "STARTING")
    self.run(self.config.bot_token)

  def dictFormat(self, data, indent=0, indent_str='| '):
    result = ""
    if isinstance(data, dict):
      if not data:
        result += indent_str * indent + "None\n"

      for key, value in data.items():
        result += indent_str * indent + str(key) + ':\n'
        result += self.dictFormat(value, indent + 1, indent_str)

    elif isinstance(data, list):
      if not data:
        result += indent_str * indent + "None\n"

      for item in data:
        result += self.dictFormat(item, indent + 1, indent_str)
        
    else:
      result += indent_str * indent + str(data) + '\n'
    return result

  async def on_ready(self):
    self.logging.info("client","READY")
    self.loaded_cogs = self.cogs
    loaded = {}
    for name in self.cogs:
      cog: Cog = self.get_cog(name)
      loaded[cog.__module__] = {"commands": [], "listeners": []}
      for command in cog.__cog_app_commands__:
        loaded[command.cog.__module__]["commands"].append(command.qualified_name)

      for listener in cog.__cog_listeners__:
        loaded[command.cog.__module__]["listeners"].append(listener[0])

    self.loaded_cogs_formatted = self.dictFormat(loaded)
  
  async def on_disconnect(self):
    self.logging.warning("client","DISCONNECT")

  async def on_connect(self):
    self.logging.info("client","CONNECT")

  def cog_reload(self, __name__):
    """Уведомление о перезагрузке кога
    reload=True"""
    self.logging.debug("modules", "RELOAD", __name__)

  def cog_load(self, cogs: list[str]):
    self.logging.info("client", "LOAD COGS")

    for cog in cogs:
      self.logging.info("COGS", f"Cog ({cog}) load")
      self.load_extension(cog)
