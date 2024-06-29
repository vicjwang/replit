import os
import requests
import statistics
import json
import pandas as pd

from datetime import datetime
from pandas.core.common import not_none
from utils import cached
from constants import START_DATE, USE_EARNINGS_CSV


TRADIER_API_KEY = os.environ['TRADIER_API_KEY']


def make_api_request(endpoint, params):
  response = requests.get(
    endpoint,
    params=params,
    headers={'Authorization': f'Bearer {TRADIER_API_KEY}', 'Accept': 'application/json'}
  )
  json_response = response.json()
  return json_response


def get_last_price(symbol: str) -> float:
  endpoint = 'https://api.tradier.com/v1/markets/quotes'
  params = {'symbols': symbol, 'greeks': 'false'}
  return make_api_request(endpoint, params)['quotes']['quote']['last']


@cached()
def fetch_historical_prices(symbol, start_date, end_date = None):
  endpoint = 'https://api.tradier.com/v1/markets/history'
  params = {'symbol': symbol, 'interval': 'daily', 'start': start_date, 'end': end_date, 'session_filter': 'open'}
  return make_api_request(endpoint, params)['history']['day']


@cached()
def fetch_options_expirations(symbol):
  endpoint = 'https://api.tradier.com/v1/markets/options/expirations'
  params = {'symbol': symbol, 'includeAllRoots': 'true', 'strikes': 'false'}
  return make_api_request(endpoint, params)['expirations']['date']


@cached(force_refresh=datetime.now().weekday() in (0,1,2,3,4) and 6 < datetime.now().hour < 13)
def fetch_options_chain(symbol, expiry_date, option_type=None, target_price=None, plus_minus=0):
  endpoint = 'https://api.tradier.com/v1/markets/options/chains'
  params = {'symbol': symbol, 'expiration': expiry_date, 'greeks': 'true'}
  chain = make_api_request(endpoint, params)['options']['option']

  max_chain_strike = chain[-1]['strike']
  if max_chain_strike < (target_price - plus_minus):
    print(f'Warning: Max strike {max_chain_strike} out of range for {expiry_date} target: {target_price}')
    return []

  if target_price:
    chain = [option for option in chain if abs(option['strike'] - target_price) < plus_minus]

  if option_type:
    chain = [option for option in chain if option['option_type'] == option_type]

  chain = sorted(chain, key=lambda option: option['strike'])
  
  return chain


def fetch_earnings_dates(symbol, start_date:str=None):

  if USE_EARNINGS_CSV:
    earnings_dates = read_earnings_dates_from_csv(symbol)
    return earnings_dates

  endpoint = 'https://api.tradier.com/beta/markets/fundamentals/calendars'
  params = {'symbols': symbol}
  resp = make_api_request(endpoint, params)[0]['results']

  # Response may have empty items so return first non-empty one.
  events = None
  for item in resp:
    events = item['tables']['corporate_calendars']
    if events:
        break

  if not events:
    return []

  # 7 = 1st quarter results, 8 = 2nd quarter, etc.
  earnings_dates = set()
  for event in events:
    begin_dt = event['begin_date_time']
    if start_date and begin_dt <= start_date:
      continue

    if event['event_type'] in {7,8,9,10}:
      earnings_dates.add(begin_dt)

  ret = list(reversed(sorted(earnings_dates)))
  return ret


def fetch_next_earnings_date(symbol):
  events = fetch_earnings_dates(symbol)

  today_datestr = datetime.now().strftime('%Y-%m-%d')

  future_events = sorted([event for event in events if event['begin_date_time'] > today_datestr], key=lambda event: event['begin_date_time'])

  next_event = sorted(relevant_events, key=lambda x: x['begin_date_time'])[0]['begin_date_time']
  today_str = str(datetime.now().date())
  return next_event if next_event > today_str else None


def fetch_past_earnings_dates(symbol):
  earnings_dates = fetch_earnings_dates(symbol, start_date=START_DATE)
  return [x for x in pd.to_datetime(earnings_dates) if x < datetime.now()]


def get_next_earnings_date(symbol):
  earnings_dates = fetch_earnings_dates(symbol, start_date=START_DATE)
  ret = [x for x in pd.to_datetime(earnings_dates) if x > datetime.now()][-1]
  return ret


def fetch_valuation_ratios(symbol):
  endpoint = 'https://api.tradier.com/beta/markets/fundamentals/ratios'
  params = {'symbols': symbol}
  response = make_api_request(endpoint, params)
  return response


if __name__ == '__main__':
    print(fetch_earnings_dates('DDOG'))