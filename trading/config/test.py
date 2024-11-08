import pytz
from datetime import datetime


REGIME_START_DATE_DEFAULT = '2023-01-01'
TICKER_REGIME_START_DATE = dict(
  MDB='2023-10-10',
)

CACHE_DIR = './tests/saved'
IS_DEBUG = True
MIN_ZSCORE_THRESHOLD = 0
MY_WIN_PROBA = 0.90
SHOW_GRAPHS = False

WORTHY_MIN_BID = 0.1

# This cannot be patched at test runtime because @cached decorator is run once at definition time.
EASTERN_TIMEZONE = pytz.timezone('America/New_York')
NOW = datetime(2024, 10, 24, tzinfo=EASTERN_TIMEZONE)

FORCE_REFRESH = False
