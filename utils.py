import os
import math
import pandas as pd
import pickle

from datetime import datetime, timedelta
from constants import (
  IS_VERBOSE, REFERENCE_CONFIDENCE, USE_EARNINGS_CSV, START_DATE,
  CACHE_DIR
)


def cached(force_refresh=False):
  """
  A function that creates a decorator which will use "cache_filepath" for caching the results of the decorated function "fn".
  """
  def decorator(fn):  # define a decorator for a function "fn"

    def wrapped(*args, **kwargs):   # define a wrapper that will finally call "fn" with all arguments

      # if cache exists -> load it and return its content
      today_date = datetime.now().strftime('%Y%m%d')
      cache_filename = f'{today_date}-{fn.__name__}-{"_".join([arg for arg in args])}.pkl'
      cache_filepath = os.path.join(CACHE_DIR, cache_filename)
      if os.path.exists(cache_filepath) and not force_refresh:
        with open(cache_filepath, 'rb') as cachehandle:
          print("using cached result from '%s'" % cache_filepath)
          return pickle.load(cachehandle)

      # execute the function with all arguments passed
      res = fn(*args, **kwargs)

      # write to cache file
      with open(cache_filepath, 'wb') as cachehandle:
        print("saving result to cache '%s'" % cache_filepath)
        pickle.dump(res, cachehandle)

      return res

    return wrapped

  return decorator


def calc_dte(expiry: str):
  today = datetime.now()
  expiry_dt = datetime.strptime(expiry, '%Y-%m-%d') + timedelta(days=1)

  trading_dte = len(pd.date_range(start=today, end=expiry_dt, freq='B'))
  return trading_dte
  

def calc_annual_roi(contract) -> float:
  strike = contract['strike']
  expiry_date = datetime.strptime(contract['expiration_date'], '%Y-%m-%d').date()
  bid = contract['bid']
  days_to_expiry = (expiry_date - datetime.now().date()).days
  
  roi = bid / strike
  annual_roi = roi * 365 / days_to_expiry if days_to_expiry > 0 else roi * 365
  return annual_roi


def get_option_contract_str(contract):
  desc = contract['description']
  last = contract['last']
  annual_roi = round(contract['annual_roi']*100, 2)
  theta = round(contract['greeks']['theta'], 4)
  delta = round(contract['greeks']['delta'], 4)
  gamma = round(contract['greeks']['gamma'], 4)
  vega = round(contract['greeks']['vega'], 4)
  iv = round(contract['greeks']['smv_vol'], 4)
  return f"""{desc}:
    last={last}
    annual_roi={annual_roi}%
    iv={iv}
    delta={delta}
    theta={theta}
    gamma={gamma}
    vega={vega}"""


def printout(s=''):
  if not IS_VERBOSE:
    return

  print(s)


def calc_expected_strike(current_price, mu, sigma, n, zscore):
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


def count_trading_days(start_date, end_date):
  # Ensure the dates are in the correct format
  start_date = pd.to_datetime(start_date)
  end_date = pd.to_datetime(end_date)

  # Create a date range between the start and end dates
  date_range = pd.date_range(start=start_date, end=end_date)

  # Filter out only the weekdays (Monday to Friday)
  weekdays = date_range[date_range.weekday < 5]

  # Return the count of weekdays
  return len(weekdays)
