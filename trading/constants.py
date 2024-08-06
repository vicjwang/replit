import os
import pytz
from collections import namedtuple

from config import IS_WIDESCREEN, IS_PHONE


T_SIG_LEVELS = [0.01, .025, 0.05, 0.10, 0.15, 0.5, 0.85, 0.90, 0.95, 0.975, 0.99]

PHI_ZSCORE = {
  # Includes entire left tail aka values directly taken from Standard Normal Table.
  0.01: -2.33,
  0.025: -1.96,
  0.05: -1.645,
  0.1: -1.28,
  0.15: -1.036,
  0.16: -1,
  0.5: 0,
  0.84: 1,
  0.85: 1.036,
  0.90: 1.28,
  0.95: 1.645,
  0.975: 1.96,
  0.99: 2.33,
}

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

Stock = namedtuple('Stock', ['symbol', 'name', 'next_earnings'], defaults=(None, None, None))

STOCKS = [
  Stock('AAPL', name='Apple Inc.', next_earnings='2024-07-26'),
  Stock(symbol='ABNB', name='Airbnb', next_earnings='2024-08-01'),
  Stock(symbol='AMZN', name='amazon', next_earnings='2024-08-01'),
  Stock(symbol='BRK/B', name='berkshire'),
  Stock('CRM', name='Salesforce'),
  Stock(symbol='CRWD', name='crowdstrike', next_earnings='2024-06-04'),
  Stock(symbol='DIS', name='disney', next_earnings='2024-08-14'),
  Stock(symbol='DDOG', name='datadog', next_earnings='2024-08-07'),
  Stock(symbol='GOOG', name='google', next_earnings='2024-07-23'),
  Stock(symbol='HTZ', name='hertz'),
  Stock(symbol='META', name='facebook', next_earnings='2024-07-24'),
  Stock(symbol='MDB', name='mongodb', next_earnings='2024-08-30'),
  Stock(symbol='MSFT', name='microsoft', next_earnings='2024-07-22'),
  Stock(symbol='MSTR', name='Microstrategy', next_earnings='2024-07-30'),
  Stock(symbol='NET', name='Cloudflare', next_earnings='2024-08-01'),
  Stock(symbol='NVDA', name='nvidia', next_earnings='2024-08-21'),
  Stock(symbol='OKTA', name='okta', next_earnings='2024-08-29'),
  Stock(symbol='SHOP', name='Shopify', next_earnings='2024-08-07'),
  Stock(symbol='SNAP', name='snapchat', next_earnings='2024-07-23'),
  Stock(symbol='SQ', name='Square'),
  Stock(symbol='SVOL', name='SVOL'),
  Stock(symbol='TSLA', name='tesla', next_earnings='2024-07-16'),
  Stock(symbol='TWLO', name='twilio', next_earnings='2024-08-13'),
  Stock(symbol='TSM', name='TSM', next_earnings='2024-07-18'),
  Stock(symbol='TXN', name='Texas Instruments', next_earnings='2024-07-23'),
  Stock(symbol='V', name='Visa'),
  #Stock(symbol='GME', name='Gamestop'),
]

COVERED_CALLS = dict(
  DIS=1,  # cc
  OKTA=1,  # cc
  SNAP=1,  # cc
  TWLO=1,  # cc
  CRWD=1,
)

WATCHLIST = dict(
  AAPL=1,
  ABNB=1,
  AMZN=1,
  CRM=1,
  DDOG=1,  # cc
  GOOG=1,
  GME=1,
  META=1,
  MDB=1,  # cc
  MSFT=1,
  MSTR=1,
  NVDA=1,
  SHOP=1,
  SQ=1,
  TSLA=1,
  TSM=1,
  TXN=1,
  V=1,
)

DATE_FORMAT = '%Y-%m-%d'
EASTERN_TZ = pytz.timezone('US/Eastern')


################
## Deprecated ##
################
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

