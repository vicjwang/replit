from collections import namedtuple


IS_WIDESCREEN = True
IS_PHONE = False
MY_WIN_PROBA = 84  # in percent
SHOW_GRAPHS = True
IS_DEBUG = True
IS_VERBOSE = False
START_DATE = '2023-01-01'
SHOULD_AVOID_EARNINGS = True
MIN_EXPIRY_DATESTR = '2025-01-01'
USE_EARNINGS_CSV = False

WORTHY_MIN_BID = 0.5
WORTHY_MIN_ROI = 0.2

PHI_ZSCORE = {
  # Includes entire left tail aka values directly taken from Standard Normal Table.
  1: -2.33,
  5: -1.645,
  10: -1.28,
  16: -1,
  50: 0,
  84: 1,
  90: 1.28,
  95: 1.645,
  99: 2.33,
}

WIN_PROBA_ZSCORE = dict(
  short=dict(
    # For short put (aka CSEP), to keep premium without assignment aka expire OTM:
    #   - 84 win proba -> zscore = -1
    #   - 50 win proba -> zscore = 0
    #   - 16 win proba -> zscore = 1
    put={p: -1*z for p, z in PHI_ZSCORE.items()},
  
    # For short call (aka CC), to keep premium without assignment aka expire OTM:
    #   - 84 win proba -> zscore = 1
    #   - 50 win proba -> zscore = 0
    #   - 16 win proba -> zscore = -1
    call=PHI_ZSCORE.copy(),
  )
)
ZSCORE_WIN_PROBA = dict(
  short=dict(
    put={z: p for p, z in WIN_PROBA_ZSCORE['short']['put'].items()},
    call={z: p for p, z in WIN_PROBA_ZSCORE['short']['call'].items()},
  )
)

NOTABLE_DELTA_MAX = .2

FIG_WIDTH = 5 if IS_PHONE else 26 if IS_WIDESCREEN else 13.5
FIG_HEIGHT = 6 if IS_PHONE else 10 if IS_WIDESCREEN else 7.5
FIG_NCOLS = 1 if IS_PHONE else 2

# Using Unicode escape sequences
DELTA_UPPER = '\u0394'
DELTA_LOWER = '\u03B4'
SIGMA_UPPER = '\u03A3'
SIGMA_LOWER = '\u03C3'
MU = '\u03BC'

SIDE_SHORT = 'short'

Ticker = namedtuple('Ticker', ['symbol', 'name', 'next_earnings'], defaults=(None, None, None))

TICKERS = [
  Ticker('AAPL', name='Apple Inc.', next_earnings='2024-07-26'),
  Ticker(symbol='ABNB', name='Airbnb', next_earnings='2024-08-01'),
  Ticker(symbol='AMZN', name='amazon', next_earnings='2024-08-01'),
  Ticker(symbol='BRK/B', name='berkshire'),
  Ticker('CRM', name='Salesforce'),
  Ticker(symbol='CRWD', name='crowdstrike', next_earnings='2024-06-04'),
  Ticker(symbol='DIS', name='disney', next_earnings='2024-08-14'),
  Ticker(symbol='DDOG', name='datadog', next_earnings='2024-08-07'),
  Ticker(symbol='GOOG', name='google', next_earnings='2024-07-23'),
  Ticker(symbol='HTZ', name='hertz'),
  Ticker(symbol='META', name='facebook', next_earnings='2024-07-24'),
  Ticker(symbol='MDB', name='mongodb', next_earnings='2024-08-30'),
  Ticker(symbol='MSFT', name='microsoft', next_earnings='2024-07-22'),
  Ticker(symbol='MSTR', name='Microstrategy', next_earnings='2024-07-30'),
  Ticker(symbol='NET', name='Cloudflare', next_earnings='2024-08-01'),
  Ticker(symbol='NVDA', name='nvidia', next_earnings='2024-08-21'),
  Ticker(symbol='OKTA', name='okta', next_earnings='2024-08-29'),
  Ticker(symbol='SHOP', name='Shopify', next_earnings='2024-08-07'),
  Ticker(symbol='SNAP', name='snapchat', next_earnings='2024-07-23'),
  Ticker(symbol='SQ', name='Square'),
  Ticker(symbol='SVOL', name='SVOL'),
  Ticker(symbol='TSLA', name='tesla', next_earnings='2024-07-16'),
  Ticker(symbol='TWLO', name='twilio', next_earnings='2024-08-13'),
  Ticker(symbol='TSM', name='TSM', next_earnings='2024-07-18'),
  Ticker(symbol='TXN', name='Texas Instruments', next_earnings='2024-07-23'),
  #Ticker(symbol='GME', name='Gamestop'),
]

COVERED_CALLS = dict(
  DDOG=1,  # cc
  DIS=1,  # cc
  OKTA=1,  # cc
  MDB=1,  # cc
  SNAP=1,  # cc
  TWLO=1,  # cc
)

CSEPS = dict(
  AAPL=1,
  ABNB=1,
  AMZN=1,
  CRM=1,
  CRWD=1,
  GOOG=1,
  META=1,
  GME=1,
  MSFT=1,
  MSTR=1,
  NVDA=1,
  SHOP=1,
  SQ=1,
  TSLA=1,
  TSM=1,
  TXN=1,
)

LTDITM_PUTS = dict(
  MDB=1,  # cc
  SNAP=1,  # cc
  MSTR=1,
  AMZN=1,
  TSLA=1,
  TSM=1,
  TXN=1,
  NVDA=1,
)

DATE_FORMAT = '%Y-%m-%d'
CACHE_DIR = './cache'
