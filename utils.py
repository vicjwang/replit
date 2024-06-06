import os
import csv
from constants import IS_VERBOSE


def printout(s=''):
  if not IS_VERBOSE:
    return

  print(s)


def fetch_past_earnings_dates(symbol):
  filepath = f'earnings_dates/{symbol.lower()}.csv'
  if not os.path.exists(filepath):
    return []
  with open(filepath, 'r') as f:
    dates = f.read().splitlines()
    return dates