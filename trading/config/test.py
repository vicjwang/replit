from datetime import datetime


CACHE_DIR = './tests/saved'
IS_DEBUG = True
MIN_ZSCORE_THRESHOLD = 0
MY_WIN_PROBA = 0.90
REGIME_START_DATE = '2023-01-01'
SHOW_GRAPHS = False


# This cannot be patched at test runtime because @cached decorator is run once at definition time.
NOW = datetime(2024, 10, 23)

FORCE_REFRESH = False
