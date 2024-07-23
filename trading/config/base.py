from datetime import datetime


IS_WIDESCREEN = True
IS_PHONE = False
MY_WIN_PROBA = 84  # in percent
SKIP_GRAPHS = False
SHOW_GRAPHS = True
IS_DEBUG = False
IS_VERBOSE = False
REGIME_START_DATE = '2023-01-01'
SHOULD_AVOID_EARNINGS = True
MIN_EXPIRY_DATESTR = '2025-01-01'
USE_EARNINGS_CSV = False
MIN_ZSCORE = 0.85  # 80% proba move

FROZEN_TEST_DATE = '2024-07-22'
CACHE_DIR = './cache'

NOW = datetime.utcnow()
