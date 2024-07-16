import os
import math
import numpy as np

from datetime import datetime, timedelta, time
from constants import (
  IS_VERBOSE, USE_EARNINGS_CSV, START_DATE, DATE_FORMAT,
  ZSCORE_WIN_PROBA, EASTERN_TZ,
)


def strformat(symbol, s):
    text = f"{symbol}: {s}"
    return text


def get_win_proba(side, option_type, zscore):
  return ZSCORE_WIN_PROBA[side][option_type][zscore]


def get_target_colname(zscore):
  return f"{zscore}_sigma_target"


def is_market_hours():
  market_open = time(9, 30)
  market_close = time(16, 0)

  now = datetime.now(EASTERN_TZ)

  return now.weekday() in (0,1,2,3,4) and market_open <= now.time() <= market_close


def count_trading_days(expiry_on):
  start = np.datetime64('today', 'D')
  end = np.datetime64(expiry_on + timedelta(days=1), 'D')
  
  trading_dte = np.busday_count(start, end)
  return trading_dte
  

def calc_annual_roi(contract) -> float:
  strike = contract['strike']
  expiry_date = datetime.strptime(contract['expiration_date'], DATE_FORMAT).date()
  bid = contract['bid']
  days_to_expiry = (expiry_date - datetime.now().date()).days
  
  roi = bid / strike
  annual_roi = roi * 365 / days_to_expiry if days_to_expiry > 0 else roi * 365
  return annual_roi


def printout(s=''):
  if not IS_VERBOSE:
    return
  print(s)


def calc_expected_price(current_price, mu, sigma, n, zscore):
  # Mean is linear with n.
  # Sigma is linear with sqrt(n).
  exp_strike = current_price * (1 + n*mu + zscore*math.sqrt(n)*sigma)
  return exp_strike


def read_earnings_dates_from_csv(symbol):
  filepath = f'earnings_dates/{symbol.lower()}.csv'
  if not os.path.exists(filepath):
    return []
  with open(filepath, 'r') as f:
    dates = f.read().splitlines()
    return dates

