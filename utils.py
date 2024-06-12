import os
import math
import pandas as pd
from constants import IS_VERBOSE, REFERENCE_CONFIDENCE


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
  exp_strike = current_price * (1 + n*mu + zscore*sigma/math.sqrt(n))
  return exp_strike


def fetch_past_earnings_dates(symbol):
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
