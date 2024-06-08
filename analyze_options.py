import statistics
import math
import sys
import matplotlib.pyplot as plt

import numpy as np

import pandas as pd

import backtest

from datetime import datetime, date, timedelta

from utils import (
  fetch_past_earnings_dates, printout,
  count_trading_days,
  calc_expected_strike,
)

from tradier import (
  make_api_request,
  get_last_price,
  fetch_historical_prices,
  fetch_options_expirations,
  fetch_options_chain,
  fetch_next_earnings_date,
)

from constants import (
  SHOULD_AVOID_EARNINGS,
  REFERENCE_CONFIDENCE,
  START_DATE,
  NOTABLE_DELTA_MAX,
  WORTHY_ROI,
)
  

def select_max_iv_contract(chain):
  if not chain:
    raise ValueError('No options found')

  max_seen = 0
  max_index = -1
  for i, option in enumerate(chain):
    bid_iv = option['greeks']['bid_iv']

    if bid_iv > max_seen:
      max_seen = bid_iv
      max_index = i
  return chain[max_index]


def filter_historical_prices(symbol, prices):  
  earnings_dates = set(fetch_past_earnings_dates(symbol))
  if not earnings_dates or not SHOULD_AVOID_EARNINGS:
    return prices

  filtered_prices = []
  for i in range(len(prices)):
    if prices[i]['date'] in earnings_dates or prices[i - 1]['date'] in earnings_dates:
      continue

    filtered_prices.append(prices[i])

  return filtered_prices


def calc_historical_price_movement_stats(prices, period=1, ax=None):

  price_moves = []

  high_52 = 0
  low_52 = 1_000_000_000
  year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

  # iterate from 0 to len - period
  for i in range(0, len(prices) - period):

    price_move = (prices[i + period]['close'] - prices[i]['close'])/prices[i]['close']
    price_moves.append(price_move)
    
    # Store high and lows for past year.
    if prices[i]['close'] > high_52 and prices[i]['date'] > year_ago:
      high_52 = prices[i]['close']
      
    if prices[i]['close'] < low_52 and prices[i]['date'] > year_ago:
      low_52 = prices[i]['close']

  if ax:
    min_bin = min(price_moves)
    max_bin = max(price_moves)
    ax.hist(price_moves, bins=np.arange(min_bin, max_bin, 0.001))
    ax.legend(title=f'Period={period}')

  # return avg, stdev
  return statistics.mean(price_moves), statistics.stdev(price_moves), high_52, low_52, len(price_moves)





def fetch_filtered_options_expirations(symbol, expiry_days=None):

  # Get all expirations up to 7 weeks.
  expirations = fetch_options_expirations(symbol)[4:7]

  expiry_date = (datetime.now() + timedelta(days=expiry_days)).strftime('%Y-%m-%d') if expiry_days else None
  default_date = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')

  # NOTE next earnings call date - consider up to week before earnings.
  next_earnings_date = fetch_next_earnings_date(symbol)

  # String comparisons default to 'z' to ensure min works properly.
  date_cutoff = min(next_earnings_date or 'z', expiry_date or 'z', default_date)

  # If there is no next earnings date, use 2 months from now right before theta crush.
  expirations = [expiry for expiry in expirations if (datetime.strptime(date_cutoff, '%Y-%m-%d') - datetime.strptime(expiry, '%Y-%m-%d')).days > 0]

  printout(f'Next earnings date: {next_earnings_date}\n')
  return expirations


def fetch_optimal_expiry(symbol, last_close, expiry_days=None):
  expirations = fetch_filtered_options_expirations(symbol)

  # Find highest IV contract expiry.
  combined_chain = []
  for expiry in expirations:
    combined_chain += fetch_options_chain(symbol, expiry, 'call', last_close, plus_minus=31)

  if len(combined_chain) == 0:
    printout('No suitable options found.')
    return []

  max_iv_contract = select_max_iv_contract(combined_chain)
  max_iv_expiry = max_iv_contract['expiration_date']

  days_to_expiry = expiry_days or count_trading_days(str(datetime.today().date()), max_iv_expiry)
  
  printout(f'{days_to_expiry} trading days to max IV contract expiry {max_iv_expiry}\n')

  return max_iv_expiry, days_to_expiry


def calc_annual_roi(contract):
  strike = contract['strike']
  expiry_date = contract['expiration_date']
  bid = contract['bid']
  days_to_expiry = (datetime.strptime(expiry_date, '%Y-%m-%d').date() - date.today()).days

  roi = bid / strike
  annualized_roi = roi * 365 / days_to_expiry
  return annualized_roi


def pprint_contract(contract):
  strike = contract['strike']
  delta = contract['greeks']['delta']
  bid = contract['bid']
  ask = contract['ask']
  last = contract['last']
  annual_roi = contract['annual_roi']
  printout(contract['description'])
  printout(f' bid={bid}, ask={ask} last={last} delta={round(delta, 4)} annual_roi={round(annual_roi, 2)}')

  # TODO: how to print?
  #printout(f' is strike higher than within 1% of 52 week high? {strike > high_52*.99}')

  return


def should_sell_cc(contract, exp_strike):
  # Strategy: if market thinks strike at delta = 0.158 is HIGHER than my expected +1 sigma strike, sell covered call.
  #    aka Rule: if strike(delta=0.158) > S, sell CC.
  #
  # 2 price points to sell CC:
  #    1) at S if D is > 0.158
  #      Ex. market: current price is $85. At avg+1 sigma = $100 and marketDelta = 50%, I sell CC at $100 because I think price won't hit $100.
  #    2) at market delta = 0.158 if strike > S
  #      Ex. market: current price is $85. At marketDelta = 15.8%, strike is $110. But avg+1 sigma = $90 so I think $110 is basically zero so sell CC at $110.
  strike = contract['strike']
  delta = contract['greeks']['delta']
  roi = contract['annual_roi']

  is_market_overest = (strike - exp_strike)/exp_strike > -0.02 and delta > REFERENCE_CONFIDENCE
  is_delta_notable = REFERENCE_CONFIDENCE <= delta <= NOTABLE_DELTA_MAX
  is_roi_worthy = roi > WORTHY_ROI

  should_sell = is_roi_worthy and any([
    is_market_overest,
    is_delta_notable,
  ])
  printout(f' Sell cc? {should_sell}')
  return should_sell


def should_sell_csep(contract, exp_strike):
  strike = contract['strike']
  delta = contract['greeks']['delta']

  should_sell = (strike - exp_strike)/exp_strike > -0.02 and delta > REFERENCE_CONFIDENCE
  printout(f' Sell csep? {should_sell}')
  return should_sell


def determine_overpriced_option_contracts(symbol, start_date=START_DATE, ax=None):
  historical_prices = fetch_historical_prices(symbol, start_date)
  last_close = historical_prices[-1]['close']
  last_move = (historical_prices[-1]['close'] - historical_prices[-2]['close'])/historical_prices[-2]['close']
  printout(f'Latest price: {last_close}, {"+" if last_move > 0 else ""}{round(last_move * 100, 2)}%')
  
  prices = filter_historical_prices(symbol, historical_prices)

  best_expiry, days_to_best_expiry = fetch_optimal_expiry(symbol, last_close)

  worthy_contracts = []

  # Calculate average price change and sigma of 1 day.
  mu, sigma, high_52, low_52, size = calc_historical_price_movement_stats(prices, ax=ax)

  # Find covered calls to sell.
  printout(f'52 week high: {high_52}')

  # Pull closest strike to S (= expected avg+1 sigma) and delta D of chain.
  cc_exp_strike = calc_expected_strike(last_close, mu, sigma, days_to_best_expiry, +1)

  historical_itm_proba = backtest.calc_historical_itm_proba(symbol, prices, mu, sigma, days_to_best_expiry)

  printout(f'My expected *1* sigma move price: \033[32m{round(cc_exp_strike, 2)}\033[0m (aka {REFERENCE_CONFIDENCE*100}% confidence)')
  printout(f' mu={round(mu*100, 4)}%, sigma={round(sigma * 100, 4)}%, n={days_to_best_expiry}\n')
  printout(f'Historical delta for 1 sigma move in {days_to_best_expiry} days = \033[36m{round(historical_itm_proba, 2)}\033[0m (want this to be smaller than actual delta of target contract)\n')

  this_chain = fetch_options_chain(symbol, best_expiry, 'call', cc_exp_strike, plus_minus=last_close*3*sigma)

  for i, _contract in enumerate(this_chain):
    contract = _contract.copy()
    contract['annual_roi'] = calc_annual_roi(contract)
    if i == len(this_chain)//2:
      print(f'\033[33m', end='')
      pprint_contract(contract)
      print('\033[0m', end='')
    else:
      pprint_contract(contract)
      
    should_sell = last_move > .3*sigma and should_sell_cc(contract, cc_exp_strike)
    if should_sell:
      worthy_contracts.append(contract)

  printout('\n' + '*' * 10 + '\n')

  """
  # Do same thing for CSEP.
  printout(f'52 week low: {low_52}')

  csep_exp_strike = calc_expected_strike(last_close, mu, sigma, days_to_best_expiry, -1)
  this_chain = fetch_options_chain(symbol, best_expiry, 'put', csep_exp_strike, plus_minus=last_close*3*sigma)

  for _contract in this_chain:
    contract = _contract.copy()
    contract['annual_roi'] = calc_annual_roi(contract)
    pprint_contract(contract)
    should_sell = should_sell_csep(contract, csep_exp_strike)
    if should_sell:

      worthy_contracts.append(contract)

  
  """

  

  return worthy_contracts

