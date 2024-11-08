import os
import math
import numpy as np
import scipy.stats as stats

import config

from datetime import datetime, timedelta, time
from constants import DATE_FORMAT, EASTERN_TZ


MARKET_OPEN = time(9, 30)
MARKET_CLOSE = time(16, 00)


def strformat(symbol, s):
    text = f"{symbol}: {s}"
    return text


def calc_spread(win_proba, premium):
  # Assume 0 EV.
  return premium * win_proba / (1 - win_proba)


def get_sig_level(side, option_type, win_proba):
  if side == 'long' and option_type == 'call':
    return 1 - win_proba
  if side == 'long' and option_type == 'put':
    return win_proba
  if side == 'short' and option_type == 'call':
    return win_proba
  if side == 'short' and option_type == 'put':
    return 1 - win_proba


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
  # a := alpha aka "significance level" of "single tail"
  # dof := degrees of freedom
  # NOTE: Assumes underlying distribution is normal.
  if dof == 0:
    return None
  return stats.t.ppf(a, dof)


def get_zscore(phi):
  return stats.norm.ppf(phi)


def get_target_colname(sig_level, suffix='target'):
  return f"{round(sig_level, 3)}_{suffix}"


def is_weekend():
  return config.NOW.weekday() in (5, 6)


def is_workday():
  return config.NOW.weekday() in (0, 1, 2, 3, 4)


def is_before_market_hours():
  return config.NOW.time() < MARKET_OPEN and is_workday()


def is_after_market_hours():
  return MARKET_CLOSE < config.NOW.time() and is_workday()


def is_market_hours():
  return MARKET_OPEN < config.NOW.time() < MARKET_CLOSE and is_workday()


def count_trading_days(expiry_on):
  start = np.datetime64(config.NOW.date(), 'D')
  end = np.datetime64(expiry_on + timedelta(days=1), 'D')
  
  trading_dte = np.busday_count(start, end)
  return trading_dte
  

def calc_annual_roi(contract) -> float:
  strike = contract['strike']
  expiry_date = datetime.strptime(contract['expiration_date'], DATE_FORMAT).date()
  bid = contract['bid']
  dte = (expiry_date - config.NOW.date()).days
  
  roi = bid / strike
  annual_roi = roi * 365 / dte if dte > 0 else roi * 365
  return annual_roi


def printout(s=''):
  if not config.IS_VERBOSE:
    return
  print(s)


def calc_target_price(current_price, mu, sigma, n, xscore):
  # xscore := either tscore or zscore
  # Mean is linear with n.
  # Sigma is linear with sqrt(n).
  target_price = current_price * math.exp(n*mu + xscore*math.sqrt(n)*sigma)
  return target_price


def read_earnings_dates_from_csv(symbol):
  filepath = f'earnings_dates/{symbol.lower()}.csv'
  if not os.path.exists(filepath):
    return []
  with open(filepath, 'r') as f:
    dates = f.read().splitlines()
    return dates


def compute_cdf(zscore):
  return stats.norm.cdf(zscore)
