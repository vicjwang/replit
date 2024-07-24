import os
import math
import numpy as np
import scipy.stats as stats

import config

from datetime import datetime, timedelta, time
from constants import DATE_FORMAT, EASTERN_TZ


def strformat(symbol, s):
    text = f"{symbol}: {s}"
    return text


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
  if dof == 1:
    raise ValueError('No T critical value exists for dof=1')
  return stats.t.ppf(a, dof)


def get_target_colname(sig_level):
  return f"{round(sig_level, 2)}_target"


def is_market_hours():
  market_open = time(9, 30)
  market_close = time(16, 0)
  eastern_now = config.NOW.astimezone(EASTERN_TZ)
  return eastern_now.weekday() in (0,1,2,3,4) and market_open <= eastern_now.time() <= market_close


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


def calc_expected_price(current_price, mu, sigma, n, tscore=None):
  # Mean is linear with n.
  # Sigma is linear with sqrt(n).
  exp_strike = current_price * (1 + n*mu + tscore*math.sqrt(n)*sigma)
  return exp_strike


def read_earnings_dates_from_csv(symbol):
  filepath = f'earnings_dates/{symbol.lower()}.csv'
  if not os.path.exists(filepath):
    return []
  with open(filepath, 'r') as f:
    dates = f.read().splitlines()
    return dates

