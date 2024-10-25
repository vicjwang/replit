import os
import pytz
from collections import namedtuple

from config import IS_WIDESCREEN, IS_PHONE


T_SIG_LEVELS = [0.01, .025, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.5,
                0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 0.975, 0.99]

FIG_WIDTH = 5 if IS_PHONE else 26 if IS_WIDESCREEN else 13.5
FIG_HEIGHT = 6 if IS_PHONE else 10 if IS_WIDESCREEN else 7.5
FIG_NCOLS = 1 if IS_PHONE else 2

# Using Unicode escape sequences
DELTA_UPPER = '\u0394'
DELTA_LOWER = '\u03B4'
SIGMA_UPPER = '\u03A3'
SIGMA_LOWER = '\u03C3'
MU = '\u03BC'
BOLD = '\033[1m'
BOLD_END = '\033[0m'

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
)

WATCHLIST = dict(
  AAPL=1,
  ABNB=1,
  AMZN=1,
  CRM=1,
  CRWD=1,
  DDOG=1,  # cc
  DIS=1,  # cc
  GOOG=1,
  GME=1,
  META=1,
  MDB=1,  # cc
  MSFT=1,
  MSTR=1,
  NVDA=1,
  OKTA=1,  # cc
  SNAP=1,  # cc
  SHOP=1,
  SQ=1,
  TSLA=1,
  TSM=1,
  TWLO=1,  # cc
  TXN=1,
  V=1,
)

DATE_FORMAT = '%Y-%m-%d'
EASTERN_TZ = pytz.timezone('US/Eastern')
