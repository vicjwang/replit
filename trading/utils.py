import os
import math
import numpy as np
import scipy.stats as stats

import config

from datetime import datetime, timedelta, time
from constants import DATE_FORMAT, ZSCORE_WIN_PROBA, EASTERN_TZ


def strformat(symbol, s):
    text = f"{symbol}: {s}"
    return text


def get_win_proba(side, option_type, sig_level):
  if side == 'long' and option_type == 'call':
    return 1 - sig_level
  if side == 'long' and option_type == 'put':
    return sig_level
  if side == 'short' and option_type == 'call':
    return sig_level
  if side == 'short' and option_type == 'put':
    return 1 - sig_level


def get_tscore(a, dof):
  return stats.t.ppf(a, dof)


def get_target_colname(sig_level):
  return f"{sig_level}_target"


def is_market_hours():

  if config.ENV == 'test':
    return False

  market_open = time(9, 30)
  market_close = time(16, 0)

  now = datetime.now(EASTERN_TZ)

  return now.weekday() in (0,1,2,3,4) and market_open <= now.time() <= market_close


def count_trading_days(expiry_on):
  start = np.datetime64(datetime.now().date(), 'D')
  end = np.datetime64(expiry_on + timedelta(days=1), 'D')
  
  trading_dte = np.busday_count(start, end)
  return trading_dte
  

def calc_annual_roi(contract) -> float:
  strike = contract['strike']
  expiry_date = datetime.strptime(contract['expiration_date'], DATE_FORMAT).date()
  bid = contract['bid']
  dte = (expiry_date - datetime.now().date()).days
  
  roi = bid / strike
  annual_roi = roi * 365 / dte if dte > 0 else roi * 365
  return annual_roi


def printout(s=''):
  if not config.IS_VERBOSE:
    return
  print(s)


def calc_expected_price(current_price, mu, sigma, n, zscore=None, tscore=None):
  assert tscore or zscore
  t_or_z_score = tscore or zscore

  # Mean is linear with n.
  # Sigma is linear with sqrt(n).
  exp_strike = current_price * (1 + n*mu + t_or_z_score*math.sqrt(n)*sigma)
  return exp_strike


def read_earnings_dates_from_csv(symbol):
  filepath = f'earnings_dates/{symbol.lower()}.csv'
  if not os.path.exists(filepath):
    return []
  with open(filepath, 'r') as f:
    dates = f.read().splitlines()
    return dates

