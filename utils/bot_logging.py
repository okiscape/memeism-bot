import logging
from utils import config, shortcuts
from time import mktime

main_logger = logging.Logger("main")
cogs_logger = logging.Logger("cogs")
disnake_hand = logging.getLogger("client")

handler = logging.FileHandler(filename='.log', encoding='utf-8', mode='w')

class DateFormatter(logging.Formatter):
	def __init__(self,datefmt, fmt, *args, **kwargs):
		super(DateFormatter, self).__init__(datefmt=datefmt, fmt=fmt)

	def formatTime(self, record, datefmt=None):
		ct = self.converter(record.created)
		dt = shortcuts.datetime_from_timestamp(mktime(ct) + record.msecs / 1000.)
		return dt

handler.setFormatter(
	DateFormatter(datefmt="%d.%b %H:%M:%S", timezone=config.local_tz, fmt='%(asctime)s | %(levelname)s | %(name)s - %(message)s')
			)

disnake_hand.addHandler(handler)
main_logger.addHandler(handler)
cogs_logger.addHandler(handler)


class Logging:
	def __init__(self):
		self.warn = self.warning
		self.log = self.info
	
	def info(self, *kwargs, type: str):
		"""%Y-%m-%d %H:%M:%S | INFO | {type} | {kwargs} | {kwargs} | {kwargs}..."""
		now = shortcuts.now_datetime()
		messages = []
		for arg in kwargs:
			messages.append(str(arg))

		print(f'{now.strftime("%Y-%m-%d %H:%M:%S |")} INFO | {type.upper()} | {" | ".join(messages)}')

		main_logger.info(f'{type} | {" | ".join(messages)}')
	
	def warning(self, *kwargs, type: str):
		"""%Y-%m-%d %H:%M:%S | WARNING | {type} | {kwargs} | {kwargs} | {kwargs}..."""
		now = shortcuts.now_datetime()
		messages = []
		for arg in kwargs: messages.append(str(arg))
		print(f'{now.strftime("%Y-%m-%d %H:%M:%S |")} INFO | {type.upper()} | {" | ".join(messages)}')
		main_logger.warning(f'{type} | {" | ".join(messages)}')

	def debug(self, *kwargs, type: str):
		"""%Y-%m-%d %H:%M:%S | DEBUG | {type} | {kwargs} | {kwargs} | {kwargs}..."""
		now = shortcuts.now_datetime()
		messages = []
		for arg in kwargs:
			messages.append(str(arg))

		print(f'{now.strftime("%Y-%m-%d %H:%M:%S |")} DEBUG | {type.upper()} | {" | ".join(messages)}')

		main_logger.debug(f'{type} | {" | ".join(messages)}')
	
	def error(self, *kwargs, type: str):
		"""%Y-%m-%d %H:%M:%S | ERROR | {type} | {kwargs} | {kwargs} | {kwargs}..."""
		now = shortcuts.now_datetime()
		messages = []
		for arg in kwargs:
			messages.append(str(arg))
		
		print(f'{now.strftime("%Y-%m-%d %H:%M:%S |")} ERROR | {type.upper()} | {" | ".join(messages)}')

		main_logger.error(f'{type} | {" | ".join(messages)}')

	def fatal(self, *kwargs, type: str):
		"""%Y-%m-%d %H:%M:%S | FATAL | {type} | {kwargs} | {kwargs} | {kwargs}..."""
		now = shortcuts.now_datetime()
		messages = []
		for arg in kwargs:
			messages.append(str(arg))
		
		print(f'{now.strftime("%Y-%m-%d %H:%M:%S |")} FATAL | {type.upper()} | {" | ".join(messages)}')

		main_logger.fatal(f'{type} | {" | ".join(messages)}')
	
	def critical(self, *kwargs, type: str):
		"""%Y-%m-%d %H:%M:%S | CRITICAL | {type} | {kwargs} | {kwargs} | {kwargs}..."""
		now = shortcuts.now_datetime()
		messages = []
		for arg in kwargs:
			messages.append(str(arg))
		
		print(f'{now.strftime("%Y-%m-%d %H:%M:%S |")} CRITICAL | {type.upper()} | {" | ".join(messages)}')

		main_logger.critical(f'{type} | {" | ".join(messages)}')