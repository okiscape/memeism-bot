from utils.bot_class import MemeismBot

MemeismBot(cogs=[
	"cogs.fun.modrinth",
  
  "cogs.data.logs",
  "cogs.data.rating",
  "cogs.data.serververse",
  "cogs.data.settings",
  "cogs.data.profile",
  
  "cogs.informations.feedback",
  "cogs.informations.infos",
  "cogs.informations.reminder",
  "cogs.informations.user_control_panel",

  "cogs.utils.cog_moderation",
  "cogs.utils.user",
  "cogs.utils.timestamp",
  "cogs.utils.dev_utils",
])