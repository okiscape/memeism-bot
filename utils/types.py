from collections import OrderedDict
import time, asyncio

class Filter:
	def __init__(self, column: str, value: any, operator: str = "="):
		self.column: str = column
		self.operator: str = operator

		if value == False:
			self.value: int = 0
		elif value == True:
			self.value = 1
		else:
			self.value: any = value

class AsyncLRUTTLCache:
	def __init__(self, maxsize: int = 1024, ttl: int = 300):
		self.maxsize = maxsize
		self.ttl = ttl
		self.store = OrderedDict()  # key -> (value, expire_ts)
		self.lock = asyncio.Lock()

	async def clear(self):
		async with self.lock:
			self.store.clear()
			# self.store.clear()	del self.store[item]

	async def get(self, key):
		async with self.lock:
			item = self.store.get(key)
			if not item:
				return None
			value, expire = item
			if expire is not None and time.time() > expire:
				# expired
				del self.store[key]
				return None
			# mark as recently used
			self.store.move_to_end(key)
			return value

	async def set(self, key, value):
		async with self.lock:
			if key in self.store:
				del self.store[key]
			self.store[key] = (value, time.time() + self.ttl if self.ttl else None)
			# evict if too many
			while len(self.store) > self.maxsize:
				self.store.popitem(last=False)

	async def resolve(self, key, resolver_coro):
		"""Возвращает cached value или вызывает resolver_coro() для получения и сохранения."""
		val = await self.get(key)
		if val is not None:
			return val
		# not cached -> resolve
		value = await resolver_coro()
		if value is not None:
			await self.set(key, value)
		return value

class FiltersGroup:
	def __init__(self, operator: str, filters: list[Filter]):
		"""
		Args:
			operator (str): Логический оператор для группы ('AND' или 'OR')
			filters (list[Filter]): Список фильтров в группе
		"""
		self.operator: str = operator.upper()
		self.filters: list[Filter] = filters        
		if self.operator not in ['AND', 'OR']:
			raise ValueError("Operator must be 'AND' or 'OR'")

class Join:
	def __init__(self, table: str, alias: str = None, filters: list[Filter] = [], type: str = "INNER JOIN", ):
		self.table: str = table
		self.alias: str = alias
		self.type: str = type 
		self.filters: list[Filter] = filters


# db types

class SocialRatingRecord:
  def __init__(self, user_id: int, rating: int):
    self.user_id = user_id
    self.rating = rating
	
class UserSettingsRecord:
  def __init__(self, user_id: int, timezone: str | None, osu_username: str | None):
    self.user_id = user_id
    self.timezone = timezone
    self.osu_username = osu_username

class UserProfileRecord:
  def __init__(self, user_id: int, about_me: str, color: str, custom_image: str):
    self.user_id = user_id
    self.about_me = about_me
    self.color = color
    self.custom_image = custom_image
		
class SerververseRecord:
  def __init__(self, 
      guild_id1: int,
      channel_id1: int,
      guild_id2: int,
      channel_id2: int,
    ):
    self.guild_id1 = int(guild_id1)
    self.channel_id1 = int(channel_id1)
    self.guild_id2 = int(guild_id2)
    self.channel_id2 = int(channel_id2)

class ServerSettingsRecord:
  def __init__(self,
      guild_id: int,
      average_language: str,
      bad_words: str,
      notified_moderators: str,
      notify_channel: int,
      bad_words_action: str,
      join_channel: int,
      leave_channel: int,
      post_channel: int,
      mute_role: int,
      auto_role: int,
      log_channel: int,
      verified_role: int,
      ticket_category: int,
      fare_text: str,
      fare_color: str,
      fare_image: str,
      greet_text: str,
      greet_color: str,
      greet_image: str):
    self.guild_id = guild_id
    self.average_language = average_language
    self.bad_words = bad_words
    self.notified_moderators: list[int] = notified_moderators.split(",")
    self.notify_channel = notify_channel
    self.bad_words_action = bad_words_action
    self.join_channel = join_channel
    self.leave_channel = leave_channel
    self.post_channel = post_channel
    self.mute_role = mute_role
    self.auto_role = auto_role
    self.log_channel = log_channel
    self.verified_role = verified_role
    self.ticket_category = ticket_category
    self.fare_text = fare_text
    self.fare_color = fare_color
    self.fare_image = fare_image
    self.greet_text = greet_text
    self.greet_color = greet_color
    self.greet_image = greet_image