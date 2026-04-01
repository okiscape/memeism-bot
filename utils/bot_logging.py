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
	
	def info(self, label: str, *kwargs):
		"""%Y-%m-%d %H:%M:%S | INFO | {label} | {kwargs} | {kwargs} | {kwargs}..."""
		now = shortcuts.now_datetime()
		messages = []
		for arg in kwargs:
			messages.append(arg)

		print(f'{now.strftime("%Y-%m-%d %H:%M:%S |")} INFO | {label.upper()} | {" | ".join(messages)}')

		main_logger.info(f'{label} | {" | ".join(messages)}')
	
	def warning(self, label: str, *kwargs):
		"""%Y-%m-%d %H:%M:%S | WARNING | {label} | {kwargs} | {kwargs} | {kwargs}..."""
		now = shortcuts.now_datetime()
		messages = []
		for arg in kwargs: messages.append(arg)
		print(f'{now.strftime("%Y-%m-%d %H:%M:%S |")} INFO | {label.upper()} | {" | ".join(messages)}')
		main_logger.warning(f'{label} | {" | ".join(messages)}')

	def debug(self, label: str, *kwargs):
		"""%Y-%m-%d %H:%M:%S | DEBUG | {label} | {kwargs} | {kwargs} | {kwargs}..."""
		now = shortcuts.now_datetime()
		messages = []
		for arg in kwargs:
			messages.append(arg)

		print(f'{now.strftime("%Y-%m-%d %H:%M:%S |")} DEBUG | {label.upper()} | {" | ".join(messages)}')

		main_logger.debug(f'{label} | {" | ".join(messages)}')
	
	def error(self, label: str, *kwargs):
		"""%Y-%m-%d %H:%M:%S | ERROR | {label} | {kwargs} | {kwargs} | {kwargs}..."""
		now = shortcuts.now_datetime()
		messages = []
		for arg in kwargs:
			messages.append(arg)
		
		print(f'{now.strftime("%Y-%m-%d %H:%M:%S |")} ERROR | {label.upper()} | {" | ".join(messages)}')

		main_logger.error(f'{label} | {" | ".join(messages)}')

	def fatal(self, label: str, *kwargs):
		"""%Y-%m-%d %H:%M:%S | FATAL | {label} | {kwargs} | {kwargs} | {kwargs}..."""
		now = shortcuts.now_datetime()
		messages = []
		for arg in kwargs:
			messages.append(arg)
		
		print(f'{now.strftime("%Y-%m-%d %H:%M:%S |")} FATAL | {label.upper()} | {" | ".join(messages)}')

		main_logger.fatal(f'{label} | {" | ".join(messages)}')
	
	def critical(self, label: str, *kwargs):
		"""%Y-%m-%d %H:%M:%S | CRITICAL | {label} | {kwargs} | {kwargs} | {kwargs}..."""
		now = shortcuts.now_datetime()
		messages = []
		for arg in kwargs:
			messages.append(arg)
		
		print(f'{now.strftime("%Y-%m-%d %H:%M:%S |")} CRITICAL | {label.upper()} | {" | ".join(messages)}')

		main_logger.critical(f'{label} | {" | ".join(messages)}')