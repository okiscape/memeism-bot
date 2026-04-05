"""Custom cog class"""
from datetime import datetime
from typing import (Callable, Literal,
				    TypeVar,
				    TYPE_CHECKING,
				    Union,
				    Optional,
				    List,
				    Sequence,
				    Dict,
				    Any,
				    Coroutine)

from disnake import (Colour, Permissions, 
					 Option, 
					 ApplicationCommandInteraction, 
					 ui, 
					 app_commands, 
					 Localised, 
					 MessageInteraction,
					 Invite,
					 CategoryChannel,
					 VoiceState,
					 Asset,
					 VoiceChannel,
					 member,
					 channel,
					 Localized,
					 VoiceClient,
					 Interaction,
					 InteractionType,
					 PermissionOverwrite,
					 MessageCommandInteraction, 
					 Button,
					 Interaction,
					 utils,
					 Member, 
					 TextChannel,
					 ActivityType,
					 User, 
					 Attachment,
					 Role,
					 Activity,
					 TextInputStyle,
					 Status,
					 File,
					 Webhook,
					 Message,
					 Guild,
					 ButtonStyle,
					 ModalInteraction,
					 SelectOption,
					 Embed as ___Embed,)
from disnake.ext import (
	tasks
)
from disnake.ext.commands import (Cog as disnake_cog, 
								  slash_command, 
								  command, 
								  InvokableSlashCommand, 
								  Param, 
								  ParamInfo, 
								  user_command, 
								  has_any_role,
								  context,
								  CommandError,
								  message_command,
								  guild_only,
								  check,
								  cooldown,
								  BucketType,
								  has_permissions,
								  errors)
from disnake.flags import InteractionContextTypes

event = disnake_cog.listener
listener = disnake_cog.listener

from utils import (config,
				   shortcuts as sh, 
					 emojis)

from utils.bot_class import MemeismBot

T = TypeVar("T")
LocalizedRequired = Union[str, "Localized[str]"] # type: ignore
LocalizedOptional = Union[Optional[str], "Localized[Optional[str]]"] # type: ignore
CommandCallback = Callable[[Callable[..., Coroutine[Any, Any, T][Any]]], InvokableSlashCommand]

View = ui.View
class Embed(___Embed):
	"""Кастомный эмбед
		Филды:

		[
			{
				"name": "Имя филда", 
				"value": "Значение филда"
			}, ...
		]
		
		Автор:

		{
			"name": "Имя автора",
			"url": "кликаемная ссылка",
			"avatar_url": "ссылка на аватарку"
		}
		
		Футер:

		{ 
			"text": "Текст футера",
			"icon": "Иконка футера" 
		}
		"""
	def __init__(self, *, 
		title: Any | None 					= None, 
		type: Literal['rich', 'image', 
				'video', 'gifv',
				'article', 'link'] | None 	= "rich", 
		description: Any | None 			= None, 
		url: Any | None 					= None, 
		timestamp: datetime | None 			= None, 
		color: int | Colour | Any | None 	= None,
		image: str | Asset | None 			= None,
		thumbnail: str | Asset | None 		= None,
		fields: list[dict[str, str, bool]] | None = None,
		author: dict[str, str, str] | None  = None,
		footer: str | dict[str, str] | None = None,
			) -> None:
		
		
		
		self._files = []
		
		super().__init__(title=title, type=type, description=description, url=url, timestamp=timestamp, color=color)

		if image:
			self.set_image(image)

		if thumbnail:
			self.set_thumbnail(thumbnail)

		if fields:
			try:
				for field in fields:
					try:
						if field["inline"] != None:
							inline = field["inline"]
						else:
							inline = field["inline"]
					except:
						inline = False
					self.add_field(name=field["name"], value=field["value"], inline=inline)
			except: pass

		if author:
			try:
				try:url = author["url"]
				except: url = None
				try: icon_url = author["avatar_url"]
				except: icon_url = None
				self.set_author(name=author["name"], url=url, icon_url=icon_url)
			except: pass
		
		if footer:
			if isinstance(footer, dict):
				self.set_footer(text=footer["text"], icon_url=footer["icon"])
			else:
				self.set_footer(text=footer)

class Cog(disnake_cog):
	"""Гвозди"""
	def __init__(self, bot: "MemeismBot") -> None:
		self.bot = bot
		self.listener = disnake_cog.listener
		self.event = self.listener
		self.Param = Param
		self.param = Param
		self.ApplicationCommandInteraction = ApplicationCommandInteraction

	@classmethod
	def context_command(cls, *args, **kwargs) -> Callable[[T], T]:
		return command(*args, **kwargs)

	@classmethod
	def Param(
		default: Union[Any, Callable[[ApplicationCommandInteraction], Any]] = ...,
		*,
		name: LocalizedOptional = None,
		description: LocalizedOptional = None,
		choices = None,
		converter: Optional[Callable[[ApplicationCommandInteraction, Any], Any]] = None,
		convert_defaults: bool = False,
		autocomplete: Optional[Callable[[ApplicationCommandInteraction, str], Any]] = None,
		channel_types: Optional[List[app_commands.ChannelType]] = None,
		lt: Optional[float] = None,
		le: Optional[float] = None,
		gt: Optional[float] = None,
		ge: Optional[float] = None,
		large: bool = False,
		min_length: Optional[int] = None,
		max_length: Optional[int] = None,
		**kwargs: Any,
	):
		description = kwargs.pop("desc", description)
		converter = kwargs.pop("conv", converter)
		autocomplete = kwargs.pop("autocomp", autocomplete)
		le = kwargs.pop("max_value", le)
		ge = kwargs.pop("min_value", ge)

		if kwargs:
			a = ", ".join(map(repr, kwargs))
			raise TypeError(f"Param() got unexpected keyword arguments: {a}")

		return ParamInfo(
			default,
			name=name,
			description=description,
			choices=choices,
			converter=converter,
			convert_default=convert_defaults,
			autocomplete=autocomplete,
			channel_types=channel_types,
			lt=lt,
			le=le,
			gt=gt,
			ge=ge,
			large=large,
			min_length=min_length,
			max_length=max_length,
		)

	@classmethod
	def slash_command(
			cls,
			name: LocalizedOptional = None,
			description: LocalizedOptional = None,
			dm_permission: Optional[bool] = False,
			default_member_permissions: Optional[Union[Permissions, int]] = None,
			nsfw: Optional[bool] = None,
			contexts: Optional[InteractionContextTypes] = None,
			options: Optional[List[Option]] = None,
			guild_ids: Optional[Sequence[int]] = None,
			connectors: Optional[Dict[str, str]] = None,
			auto_sync: Optional[bool] = None,
			extras: Optional[Dict[str, Any]] = None,
			**kwargs,
	) -> Callable[[CommandCallback], InvokableSlashCommand]:
		eff_ctx = contexts
		eff_dm = dm_permission
		if eff_ctx is None and dm_permission is False:
			eff_ctx = InteractionContextTypes(guild=True)
			eff_dm = None
		elif eff_ctx is not None:
			eff_dm = None
		return slash_command(                                 # type: ignore
			name=name, description=description, dm_permission=eff_dm,
			default_member_permissions=default_member_permissions, nsfw=nsfw,
			contexts=eff_ctx,
			options=options, guild_ids=guild_ids, connectors=connectors,
			auto_sync=auto_sync, extras=extras, **kwargs)
