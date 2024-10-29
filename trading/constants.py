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
