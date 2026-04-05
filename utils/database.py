import os

import aiosqlite
from utils.bot_logging import Logging
from utils.types import (
  Filter, FiltersGroup, Join, AsyncLRUTTLCache, 
  ServerSettingsRecord, SerververseRecord, 
  SocialRatingRecord, UserProfileRecord, 
  UserSettingsRecord)

logging = Logging()

db_schema = {
  "user_settings": {
      "user_id": "INTEGER PRIMARY KEY",
      "timezone": "TEXT",
      "osu_username": "TEXT"
  },
  "membership": {
    "user_id": "INTEGER PRIMARY KEY",
    "about_me": "TEXT",
    "color": "TEXT",
    "custom_image": "TEXT",
    "is_active": "INTEGER NOT NULL DEFAULT 1"
  },
  "server_settings": {
      "guild_id": "INTEGER PRIMARY KEY",
      "average_language": "TEXT",
      "bad_words": "TEXT", # INT,INT,INT,
      "notified_moderators": "TEXT",
      "notify_channel": "INTEGER",
      "bad_words_action": "TEXT",
      "join_channel": "INTEGER",
      "leave_channel": "INTEGER",
      "post_channel": "INTEGER",
      "mute_role": "INTEGER",
      "auto_role": "INTEGER",
      "log_channel": "INTEGER",
      "verified_role": "INTEGER",
      "ticket_category": "INTEGER",
      "fare_text": "TEXT",
      "fare_color": "TEXT",
      "fare_image": "TEXT",
      "greet_text": "TEXT",
      "greet_color": "TEXT",
      "greet_image": "TEXT"
  },
  "social_rating": {
      "user_id": "INTEGER PRIMARY KEY",
      "rating": "INTEGER DEFAULT 0"
  },
  "serververse": {
      "guild_id2": "INTEGER NOT NULL",
      "channel_id2": "INTEGER NOT NULL",
      "guild_id1": "INTEGER NOT NULL",
      "channel_id1": "INTEGER NOT NULL"
  }
}
# { table: {column-name: column-type} }

class DbQueryReturn:
  def __init__(self, cur, fetchone, fetchall):
    self.cur = cur
    self.fetchone: tuple = fetchone
    self.fetchall: tuple = fetchall

class BasicDBManager:
  def __init__(self, db_path: str):
    self.db_path = db_path
    self.connection: aiosqlite.Connection = ...

  async def connect(self) -> None:
    self.connection = await aiosqlite.connect(self.db_path)

  async def execute(self, query: str, *params, no_fetch: bool = False):
    ftdquery = " ".join([line.strip() for line in query.splitlines()]).strip()

    logging.info("db internal", f"Query: \"{ftdquery}\"", f"Params: {params}", type="DB")
    fetch = await self.connection.execute(query, *params)
    await self.connection.commit()
    fetchall = await fetch.fetchall()

    if fetchall != []:
        fetchone = fetchall[0]
    else: 
        fetchone = None

    logging.info("Fetchall", fetchall, type="DB")
    logging.info("Fetchone", fetchone, type="DB")
    
    if not no_fetch:
      return DbQueryReturn(fetch, 
                  fetchone,
                  fetchall)

  async def create(self, table: str, **data: dict):
      logging.log("db internal", f"Start create for {table}", 
          ", ".join([f"{k}: {v}" for k,v in data.items()]),
          type="pos")

      fields = {k: (1 if v else 0) if isinstance(v, bool) else v for k, v in data.items()}
      
      columns = [f'"{k}"' for k in fields.keys()]
      values = list(fields.values())
      placeholders = ["?" for _ in values]

      query = f"""
INSERT INTO {table}
  ({", ".join(columns)})
VALUES
  ({", ".join(placeholders)})
  """
      await self.execute(query, values, no_fetch=True)

  def generateWhereClauses(self,
                          filters: list[Filter] | list[FiltersGroup]):
      where_clauses: list[str] = []
      params: list = []

      def _quote_col(col: str) -> str:
          # don't quote if it's a qualified column (contains dot) or already quoted
          col = str(col)
          if '.' in col or col.startswith('"') or col.endswith('"'):
              return col
          return f'"{col}"'

      for filter_item in filters or []:
          # Group of filters (AND / OR)
          if isinstance(filter_item, FiltersGroup):
              group_clauses: list[str] = []
              for flt in filter_item.filters or []:
                  col = _quote_col(flt.column)
                  op = (flt.operator or "=").upper()
                  val = flt.value

                  # dict-valued special filter (e.g. {'op': 'IS NOT', 'val': 'NULL'})
                  if isinstance(val, dict):
                      op = val.get('op', op)
                      v = val.get('val')
                      # if val is a literal SQL fragment (like NULL), insert directly
                      if v is None or (isinstance(v, str) and v.upper() == 'NULL'):
                          group_clauses.append(f"{col} {op} NULL")
                      else:
                          group_clauses.append(f"{col} {op} ?")
                          params.append(v)
                      continue

                  # IN operator handling
                  if op == 'IN':
                      # list/tuple -> placeholders
                      if isinstance(val, (list, tuple)) and len(val) > 0:
                          placeholders = ', '.join(['?' for _ in val])
                          group_clauses.append(f"{col} IN ({placeholders})")
                          params.extend(val)
                      # preformatted tuple string like "(1,2)" (Filter may have converted it)
                      elif isinstance(val, str) and val.strip().startswith('(') and val.strip().endswith(')'):
                          group_clauses.append(f"{col} IN {val}")
                      # empty list -> always false
                      elif val is None or (isinstance(val, (list, tuple)) and len(val) == 0):
                          group_clauses.append('0')
                      else:
                          group_clauses.append(f"{col} IN (?)")
                          params.append(val)
                      continue

                  # IS / IS NOT with None
                  if op in ('IS', 'IS NOT') and (val is None or (isinstance(val, str) and val.upper() == 'NULL')):
                      group_clauses.append(f"{col} {op} NULL")
                      continue

                  # column reference (e.g. "k.ownerId") - no param
                  if isinstance(val, str) and '.' in val and not (val.strip().startswith('(') or val.strip().startswith("'")):
                      group_clauses.append(f"{col} {flt.operator} {val}")
                      continue

                  # Default case - use placeholder
                  group_clauses.append(f"{col} {flt.operator} ?")
                  params.append(val)

              # join group's clauses with operator and wrap in parentheses
              if group_clauses:
                  where_clauses.append(f' {filter_item.operator} '.join(group_clauses))
              continue

          # Single Filter
          col = _quote_col(filter_item.column)
          op = filter_item.operator.upper()
          val = filter_item.value

          if isinstance(val, dict):
              op = val.get('op', op)
              v = val.get('val')
              if v is None or (isinstance(v, str) and v.upper() == 'NULL'):
                  where_clauses.append(f"{col} {op} NULL")
                  continue
              where_clauses.append(f"{col} {op} ?")
              params.append(v)
              continue

          if op == 'IN':
              if isinstance(val, (list, tuple)) and len(val) > 0:
                  placeholders = ', '.join(['?' for _ in val])
                  where_clauses.append(f"{col} IN ({placeholders})")
                  params.extend(val)
                  continue

              if isinstance(val, str) and val.strip().startswith('(') and val.strip().endswith(')'):
                  where_clauses.append(f"{col} IN {val}")
                  continue
              # empty -> false
              if val is None or (isinstance(val, (list, tuple)) and len(val) == 0):
                  where_clauses.append('0')
                  continue
              where_clauses.append(f"{col} IN (?)")
              params.append(val)
              continue

          if op in ('IS', 'IS NOT') and (val is None or (isinstance(val, str) and val.upper() == 'NULL')):
              where_clauses.append(f"{col} {op} NULL")
              continue

          if isinstance(val, str) and '.' in val and not (val.strip().startswith('(') or val.strip().startswith("'")):
              where_clauses.append(f"{col} {filter_item.operator} {val}")
              continue

          where_clauses.append(f"{col} {filter_item.operator} ?")
          params.append(val)

      return where_clauses, params

  def generateJoinClauses(self,
                          joins: list[Join]):
      join_clauses, params = [], []
      for join in joins:
          join_clause = f"{join.type} {join.table}"
          if join.alias:
              join_clause += f" {join.alias}"

          # Формируем условия JOIN
          if join.filters:
              join_conditions = []
              
              for filter in join.filters:
                  if isinstance(filter.value, dict):
                      # Специальные операторы (IS NOT NULL и т.д.)
                      op = filter.operator
                      val = filter.value
                      join_conditions.append(f"{filter.column} {op} {val}")
                  elif isinstance(filter.value, str) and '.' in filter.value:
                      # Это ссылка на другую колонку
                      join_conditions.append(f"{filter.column} = {filter.value}")
                  else:
                      # Это значение для подстановки
                      join_conditions.append(f"{filter.column} = ?")
                      params.append(filter.value)
              
              join_clause += " ON " + " AND ".join(join_conditions)
          
          join_clauses.append(join_clause)
      
      return join_clauses, params

  async def read(
      self, 
      table: str,
      columns: list[str], 
      joins: list[Join] = [],
      filters: list[Filter] | list[FiltersGroup] = [],
      orderBy: str = None,
      orderDir: str = "DESC",
      limit: int = -1,
      offset: int = 0
  ):
      """
Универсальный метод для чтения данных из БД с поддержкой фильтров, JOIN и сортировки.

Args:
  table (str): Имя таблицы
  columns (list[str]): Список колонок для выборки
  joins (list[Join], optional): Список объектов Join для соединения таблиц.
  Каждый Join содержит:
  - table: имя присоединяемой таблицы
  - alias: псевдоним таблицы (опционально)
  - type: тип JOIN (LEFT/INNER/RIGHT, по умолчанию INNER)
  - filters: список объектов Filter для условий ON\n
  filters (list[Filter], optional): Список объектов Filter для условий WHERE.
  Каждый Filter содержит:
  - column: имя колонки
  - value: значение для сравнения или специальный оператор
  orderBy (str, optional): Колонка для сортировки. Defaults to None.
  orderDir (str, optional): Направление сортировки (ASC/DESC). Defaults to "DESC".
  limit (int, optional): Ограничение количества записей. Defaults to -1 (без ограничений).
  offset (int, optional): Смещение от начала выборки. Defaults to 0.

Returns:
  DbQueryReturn: Объект с результатами запроса (fetchone/fetchall)

Examples:
  - Простой запрос
  ```
  users = await dbm.read(
      table="users",
      columns=["tgId", "userName"]
  )```

  - С фильтрами
  ```
  user = await dbm.read(
      table="users",
      columns=["*"],
      filters=[Filter("tgId", 123456)]
  )```

  - С IS NOT NULL
  ```
  active_users = await dbm.read(
      table="users",
      columns=["tgId", "userName"],
      filters=[Filter("tariffId", {"op": "IS NOT", "val": "NULL"})]
  )```

  - С JOIN
  ```
  keys = await dbm.read(
      table="keys k",
      columns=[
          "k.keyId",
          "k.keyName",
          "u.tgId as ownerId"
      ],
      joins=[
          Join(
              table="users",
              alias="u",
              filters=[Filter("u.userId", "k.ownerId")]
          )
      ],
      filters=[Filter("k.keyId", 123)]
  )```

  - Сложный запрос с множественными JOIN
  ```
  result = await dbm.read(
      table="keys k",
      columns=[
          "k.keyId",
          "u.tgId",
          "p.protocolName",
          "s.serverName"
      ],
      joins=[
          Join(
              table="users",
              alias="u",
              filters=[Filter("u.userId", "k.ownerId")]
          ),
          Join(
              table="protocols",
              alias="p",
              type="LEFT JOIN",
              filters=[Filter("p.protocolId", "k.protocolId")]
          ),
          Join(
              table="servers",
              alias="s",
              filters=[Filter("s.serverId", "k.serverId")]
          )
      ],
      filters=[Filter("u.tgId", 123456)],
      orderBy="k.createdAt",
      orderDir="DESC",
      limit=10
  )```
"""

      _joingen = self.generateJoinClauses(joins)
      join_clauses = _joingen[0]
      params = [*_joingen[1]]

      _wheregen = self.generateWhereClauses(filters)
      where_clauses = _wheregen[0]
      params = [*params, *_wheregen[1]]

      query = f"""
SELECT DISTINCT {", ".join((f"\"{column}\"" if "." not in column else column) for column in columns)} 
FROM {table}
{" ".join(join_clauses) if join_clauses else ""}
{f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""}
{f"ORDER BY {orderBy} {orderDir}" if orderBy else ""}
{f"LIMIT {limit}" if limit > -1 else ""}
{f"OFFSET {offset}" if offset > 0 else ""}
"""
      result = await self.execute(query, tuple(params))
      return result
  
  async def update(self, table: str, filters: list[Filter], **updates):
      """Update row from dict.

{key: newValue}"""

      logging.info("db internal", f"Start update for {table}", 
        f'filters: {[f"{filter.column}={filter.value}" for filter in filters]}',
        f"updates: {updates}",
        type="pos")
      updates = {k: (1 if v else 0) if isinstance(v, bool) else v for k, v in updates.items()}
      
      set_parts = []
      params = []
      for col, val in updates.items():
          set_parts.append(f'"{col}" = ?')
          params.append(val)

      where_clauses = []
      if filters:
          for filter in filters:
              if isinstance(filter.value, dict):
                  # Специальные операторы (IS NOT NULL и т.д.)
                  op = filter.value.get('op', '=')
                  val = filter.value.get('val') 
                  where_clauses.append(f"{filter.column if '.' in filter.column else f'"{filter.column}"'} {op} {val}")
              elif isinstance(filter.value, str) and '.' in filter.value:
                  # Это ссылка на другую колонку
                  where_clauses.append(f"{filter.column if '.' in filter.column else f'"{filter.column}"'} = {filter.value}")
              else:
                  # Обычное значение для подстановки
                  where_clauses.append(f"{filter.column if '.' in filter.column else f'"{filter.column}"'} = ?")
                  params.append(filter.value)

      query = f"""
UPDATE {table} 
SET {", ".join(set_parts)}
WHERE {' AND '.join(where_clauses)}
"""
      await self.execute(query, params, no_fetch=True)

  async def delete(self, table: str, filters: list[Filter] | list[FiltersGroup]):
    logging.info("db internal", f"Start delete from {table}",
        f"Filters: {
            [filter.__dict__ for filter in filters]
        }",
        type="pos")
    where_clauses, params = self.generateWhereClauses(filters)

    query = f"""
DELETE FROM {table}
WHERE {' AND '.join(where_clauses)}
"""
    await self.execute(query, tuple(a for a in params), no_fetch=True)
    

class Caches:
  def __init__(self):
    self.cacheSettings = {
        "long": {
            "maxsize": 1024,
            "ttl": 3600
        },
        "mid": {
            "maxsize": 1024,
            "ttl": 450
        },
        "short": {
            "maxsize": 1024,
            "ttl": 150
        }
    }
    self.serverSettings = AsyncLRUTTLCache(**self.cacheSettings["long"])
    self.serververse = AsyncLRUTTLCache(**self.cacheSettings["long"])
    self.socialRating = AsyncLRUTTLCache(**self.cacheSettings["short"])
    self.membership = AsyncLRUTTLCache(**self.cacheSettings["mid"])
    self.userSetting = AsyncLRUTTLCache(**self.cacheSettings["mid"])
    self.userProfiles = AsyncLRUTTLCache(**self.cacheSettings["mid"])

class DatabaseManager:
  def __init__(self, db_path: str):
    self.db_path = db_path
    self.db = BasicDBManager(db_path)
          
    self.caches = Caches()

  def _ensure_db_dir(self) -> None:
    parent = os.path.dirname(os.path.abspath(self.db_path))
    if parent:
      os.makedirs(parent, exist_ok=True)

  async def _clearCache(self):
    for attr_name in dir(self.caches):
      if attr_name.startswith('_cache') and attr_name.endswith('Store'):
        cache_store: AsyncLRUTTLCache = getattr(self, attr_name)
        await cache_store.clear()

  async def init_schema(self) -> None:
    await self.db.connect()
    self._ensure_db_dir()

    cmds = []
    for table_name in db_schema:
      table = db_schema[table_name]
      columns = []
      for column_name in table:
        columns.append(f"{column_name} {table[column_name]}")
        
      cmds.append(f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})")

    for cmd in cmds:
      await self.db.execute(cmd)
    logging.info("schema ready", self.db_path, type="DB")

  async def _getCached(self, store: AsyncLRUTTLCache, key: str):
    try:
        cached = await store.get(key)
    except Exception:
        cached = None
    
    if cached is not None:
        return cached
    return None

  
  async def readUserSettings(self,
      user_id: int = None,
      limit: int = 10, 
      offset: int = 0,
      orderBy: str = None,
      orderDir: str = "DESC",
      cacheOverwrite: bool = False) -> list[UserSettingsRecord]:
    _cachekey = f"{user_id};{limit};{offset};{orderBy};{orderDir}"
    if not cacheOverwrite:
      cached = await self._getCached(
        store=self.caches.userSetting,
        key=_cachekey
      )
      if cached:
        return cached
    filters = []
    if user_id:
       filters.append(Filter("user_id", user_id))

    fetch = (await self.db.read(
      table="user_settings",
      columns=[
        "user_id",
        "timezone",
        "osu_username"
      ],
      filters=filters
    )).fetchall
    
    to_return: list[UserSettingsRecord] = []

    for row in fetch:
       to_return.append(
          UserSettingsRecord(
             user_id=row[0],
             timezone=row[1],
             osu_username=row[2]
          )
       )
    
    await self.caches.userSetting.set(
      _cachekey,
      to_return
    )

    return to_return

  async def createUserSettings(self, 
      user_id: int,
      timezone: str = None,
      osu_username: str = None  
    ):
    await self.db.create(
      table="user_settings",
      user_id=user_id,
      timezone=timezone,
      osu_username=osu_username
    )
  
  async def updateUserSettings(self, 
      user_id: int,
      timezone: str = '',
      osu_username: str = ''  
    ):
    updates = {}
    if timezone != "": updates["timezone"] = timezone
    if osu_username != '': updates["osu_username"] = osu_username

    await self.db.update(
      table="user_settings",
      filters=[
         Filter("user_id", user_id)
      ],
      **updates
    )
    

  async def readUserProfiles(self, 
      user_id: int = None,
      limit: int = 10, 
      offset: int = 0,
      orderBy: str = None,
      orderDir: str = "DESC",
      cacheOverwrite: bool = False) -> list[UserProfileRecord]:
    
    _cachekey = f"{user_id};{limit};{offset};{orderBy};{orderDir}"
    if not cacheOverwrite:
      cached = await self._getCached(
        store=self.caches.userProfiles,
        key=_cachekey
      )
      if cached:
        return cached
    filters = []
    if user_id:
       filters.append(Filter("user_id", user_id))

    fetch = (await self.db.read(
      table="user_profiles",
      columns=[
        "user_id",
        "about_me",
        "color",
        "custom_image"
      ],
      filters=filters
    )).fetchall
    
    to_return: list[UserProfileRecord] = []

    for row in fetch:
       to_return.append(
          UserProfileRecord(
             user_id=row[0],
             about_me=row[1],
             color=row[2],
             custom_image=row[3]
          )
       )
    
    await self.caches.userProfiles.set(
      _cachekey,
      to_return
    )

    return to_return

  async def createUserProfile(self, 
      user_id: int,
      about_me: str = None,
      color: str = None,
      custom_image: str = None
    ):
    await self.db.create(
      table="user_profiles",

      user_id=user_id,
      about_me=about_me,
      color=color,
      custom_image=custom_image
    )
  
  async def updateUserProfile(self, 
      user_id: int,
      about_me: str = "no_change",
      color: str = "no_change",
      custom_image: str = "no_change"
    ):
    updates = {}
    if about_me != "no_change": updates["about_me"] = about_me
    if color != 'no_change': updates["color"] = color
    if custom_image != "no_change": updates["custom_image"] = custom_image
    
    await self.db.update(
      table="user_profiles",
      filters=[
         Filter("user_id", user_id)
      ],
      **updates
    )


  async def createSerververse(self, 
      guild_id1: int,
      channel_id1: int,
      guild_id2: int,
      channel_id2: int,):
    await self.db.create(
      table="serververse",

      guild_id1=guild_id1,
      guild_id2=guild_id2,
      channel_id1=channel_id1,
      channel_id2=channel_id2,
    )

  async def readSerververse(self, 
      guild_id: int, 
      channel_id: int = None,
      limit: int = 10, 
      offset: int = 0,
      orderBy: str = None,
      orderDir: str = "DESC",
      cacheOverwrite: bool = False) -> list[SerververseRecord]:
    
    _cachekey = f"{guild_id};{channel_id};{limit};{offset};{orderBy};{orderDir}"
    if not cacheOverwrite:
      cached = await self._getCached(
        store=self.caches.serververse,
        key=_cachekey
      )
      if cached:
        return cached

    filters = [
      FiltersGroup("OR", [
        Filter("guild_id1", guild_id),
        Filter("guild_id2", guild_id)
      ])
    ]
    if channel_id:
      filters.append(
        FiltersGroup("OR", [
          Filter("channel_id1", channel_id),
          Filter("channel_id2", channel_id)
        ])
      )

    fetch = (await self.db.read(
      table="serververse",
      columns=[
        "guild_id1",
        "channel_id1",
        "guild_id2",
        "channel_id2"
      ],
      filters=filters
    )).fetchall
    
    to_return: list[ServerSettingsRecord] = []

    for row in fetch:
       to_return.append(
          SerververseRecord(
            guild_id1=row[0],
            channel_id1=row[1],
            guild_id2=row[2],
            channel_id2=row[3]
          )
       )
    
    await self.caches.serververse.set(
      _cachekey,
      to_return
    )

    return to_return

  async def deleteSerververse():
    ...
    #todo  

  # функции обновления серверверса быть не должно, он обновляется вручную прямо из кода через db.update


  async def readServerSettings(self, guild_id: int, 
      limit: int = 10, 
      offset: int = 0,
      orderBy: str = None,
      orderDir: str = "DESC",
      cacheOverwrite: bool = False) -> list[ServerSettingsRecord]:
    
    _cachekey = f"{guild_id};{limit};{offset};{orderBy};{orderDir}"
    if not cacheOverwrite:
      cached = await self._getCached(
        store=self.caches.serverSettings,
        key=_cachekey
      )
      if cached:
        return cached
    filters = []
    if guild_id:
       filters.append(Filter("guild_id", guild_id))

    fetch = (await self.db.read(
      table="server_settings",
      columns=[
        "guild_id",
        "average_language",
        "bad_words",
        "notified_moderators",
        "notify_channel",
        "bad_words_action",
        "join_channel",
        "leave_channel",
        "post_channel",
        "mute_role",
        "auto_role",
        "log_channel",
        "verified_role",
        "ticket_category",
        "fare_text",
        "fare_color",
        "fare_image",
        "greet_text",
        "greet_color",
        "greet_image"
      ],
      filters=filters
    )).fetchall
    
    to_return: list[ServerSettingsRecord] = []

    for row in fetch:
       to_return.append(
          ServerSettingsRecord(
            guild_id=row[0],
            average_language=row[1],
            bad_words=row[2],
            notified_moderators=row[3],
            notify_channel=row[4],
            bad_words_action=row[5],
            join_channel=row[6],
            leave_channel=row[7],
            post_channel=row[8],
            mute_role=row[9],
            auto_role=row[10],
            log_channel=row[11],
            verified_role=row[12],
            ticket_category=row[13],
            fare_text=row[14],
            fare_color=row[15],
            fare_image=row[16],
            greet_text=row[17],
            greet_color=row[18],
            greet_image=row[19],
          )
       )
    
    await self.caches.serverSettings.set(
      _cachekey,
      to_return
    )

    return to_return

  async def createServerSettings():
    ...
    # todo
  async def updateServerSettings():
    ...
    # todo
  async def deleteServerSettings():
    ...
    # todo
  

  async def updateSocialRating(self, user_id: int, to_rating: int):
    await self.db.update(
      table="social_rating",
      filters=[
         Filter("user_id", user_id)
      ],
      rating=to_rating
    )

  async def createSocialRating(self, user_id: int, to_rating: int):
    await self.db.create(
      table="social_rating",
      user_id=user_id, rating=to_rating
    )
  
  async def readSocialRating(self, 
      user_id: int = None, 
      limit: int = 10, 
      offset: int = 0,
      orderBy: str = None,
      orderDir: str = "DESC",
      cacheOverwrite: bool = False) -> list[SocialRatingRecord]:
    
    _cachekey = f"{user_id};{limit};{offset};{orderBy};{orderDir}"
    if not cacheOverwrite:
      cached = await self._getCached(
        store=self.caches.socialRating,
        key=_cachekey
      )
      if cached:
        return cached
    filters = []
    if user_id:
       filters.append(Filter("user_id", user_id))

    fetch = (await self.db.read(
      table="social_rating",
      columns=[
         "user_id",
         "rating"
      ],
      filters=filters
    )).fetchall
    
    to_return: list[SocialRatingRecord] = []

    for row in fetch:
       to_return.append(
          SocialRatingRecord(
             user_id=row[0],
             rating=row[1]
          )
       )
    
    await self.caches.socialRating.set(
      _cachekey,
      to_return
    )

    return to_return
  
  async def deleteSocialRating():
    ...
    # todo