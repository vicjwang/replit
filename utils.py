import os
import math
import pandas as pd
import pickle
import pytz
import subprocess

from datetime import datetime, timedelta, time
from constants import (
  IS_VERBOSE, USE_EARNINGS_CSV, START_DATE, DATE_FORMAT,
)


def is_market_hours():
  market_open = time(9, 30)
  market_close = time(16, 0)

  eastern = pytz.timezone('US/Eastern')
  now = datetime.now(eastern)

  return now.weekday() in (0,1,2,3,4) and market_open <= now.time() <= market_close


def calc_dte(expiry: str):
  today = datetime.now()
  expiry_dt = datetime.strptime(expiry, DATE_FORMAT) + timedelta(days=1)

  trading_dte = len(pd.date_range(start=today, end=expiry_dt, freq='B'))
  return trading_dte
  

def calc_annual_roi(contract) -> float:
  strike = contract['strike']
  expiry_date = datetime.strptime(contract['expiration_date'], DATE_FORMAT).date()
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
