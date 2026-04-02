import aiosqlite
from utils.bot_logging import Logging
from utils.types import Filter, FiltersGroup, Join

log = Logging()

db_scheme = {
  "user_setting": {
      ""
  },
  "membership": {
    "user_id": "INTEGER NOT NULL",
    "sub_type": "TEXT",
    "about_me": "TEXT",
    "color": "TEXT",
    "custom_image": "TEXT"
  },
  "server_settings": {
      "guild_id": "INTEGER NOT NULL",
      "average_language": "TEXT",
      "bad_words": "TEXT", # INT,INT,INT,
      "notified_moderators": "TEXT",
      "notify_channel": "INTEGER",
      "bad_action": "TEXT",
      "notify_text": "TEXT",
      "join_channel": "INTEGER",
      "leave_channel": "INTEGER",
      "post_channel": "INTEGER",
      "mute_role": "INTEGER",
      "auto_role": "INTEGER",
      "log_channel": "INTEGER",
      "verified_role": "INTEGER",
      "ticket_category": "INTEGER",
      "custom_fare": "TEXT",
      "fare_color": "TEXT",
      "fare_image": "TEXT",
      "custom_greet": "TEXT",
      "greet_color": "TEXT",
      "greet_image": "TEXT"
  },
  "social_rating": {
      "user_id": "INTEGER NOT NULL PRIMARY KEY",
      "rating": "INTEGER NOT NULL"
  },
  "serververse": {
      "guild_id2": "INTEGER NOT NULL",
      "channel2": "INTEGER NOT NULL",
      "guild_id1": "INTEGER NOT NULL",
      "channel1": "INTEGER NOT NULL"
  }
}
# { table: {column-name: column-type} }
# todo: create script to create db using this 


class BasicDBManager:
  def __init__(self, db_path: str):
    self.db_path = db_path
    self.connection: aiosqlite.Connection = ...

  async def create(self, table: str, data: dict):
      self.logging.log(f"Start dbm.create for {table}", 
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
      await self.execute(query, values)

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
                  where_clauses.append('(' + f' {filter_item.operator} '.join(group_clauses) + ')')
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
      filters: list[Filter] = [],
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

      self.bot.log(f"Start dbm.update for {table}", 
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
      await self.execute(query, params)

  async def delete(self, table: str, filters: list[Filter] | list[FiltersGroup]):
      self.bot.log(f"Start dbm.delete from {table}",
          f"Filters: {
              [filter.__dict__ for filter in filters]
          }",
          type="pos")
      where_clauses, params = self.generateWhereClauses(filters)

      query = f"""
DELETE FROM {table}
WHERE {' AND '.join(where_clauses)}
"""
      await self.execute(query, tuple(a for a in params))
    

class DatabaseManager:
  def __init__(self, db_path: str):
    self.db = BasicDBManager(db_path)
  