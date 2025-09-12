import os

HOME = os.path.expanduser('~')
CONFIG_DIR = os.path.join(HOME, '.omga_cli')
os.makedirs(CONFIG_DIR, exist_ok=True)

HISTORY_FILE = os.path.join(CONFIG_DIR, 'history.txt')
CACHE_DB = os.path.join(CONFIG_DIR, 'cache.sqlite')
LOG_FILE = os.path.join(CONFIG_DIR, 'log.txt')