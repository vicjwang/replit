from datetime import datetime


IS_WIDESCREEN = True
IS_PHONE = False
MY_WIN_PROBA = 0.85
SKIP_GRAPHS = False
SHOW_GRAPHS = True
IS_DEBUG = False
IS_VERBOSE = False
REGIME_START_DATE = '2022-01-01'
SHOULD_AVOID_EARNINGS = True
MIN_EXPIRY_DATESTR = '2025-01-01'
USE_EARNINGS_CSV = False
MIN_ZSCORE_THRESHOLD = 0  #0.85  # 80% proba move

WORTHY_MIN_BID = 0.1  #0.8
WORTHY_MIN_ROI = 0  #0.2
MAX_STRIKE = 280

FROZEN_TEST_DATE = '2024-07-22'
CACHE_DIR = './cache'

TRADIER_THROTTLE_RATE = 59  # per minute
TRADIER_THROTTLE_PERIOD = 61  # in seconds

NOW = datetime.utcnow()
NUM_PARALLEL_JOBS = 2
FORCE_REFRESH = True
