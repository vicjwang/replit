import statistics
import math
import sys
import matplotlib.pyplot as plt

import numpy as np

import pandas as pd

import backtest

from datetime import datetime, date, timedelta

from scipy.stats import norm

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


def select_max_greek_contract(chain, greek_key='delta'):
  if not chain:
    raise ValueError('No options found')

  max_seen = 0
  max_index = -1
  for i, option in enumerate(chain):
    greek = option['greeks'][greek_key]

    if greek > max_seen:
      max_seen = greek
      max_index = i
  return chain[max_index]


def filter_historical_prices(symbol, prices):
  if not earnings_dates or not SHOULD_AVOID_EARNINGS:
    return prices

  filtered_prices = []
  for i in range(len(prices)):
    if prices[i]['date'] in earnings_dates or prices[i - 1]['date'] in earnings_dates:
      continue

    filtered_prices.append(prices[i])

  return filtered_prices


def calc_historical_price_movement_stats(symbol, prices_df, periods=1, ax=None):
  earnings_dates = list(reversed(fetch_past_earnings_dates(symbol)))  # sorted in most recent first

  if not earnings_dates and SHOULD_AVOID_EARNINGS:
    raise ValueError('No earnings dates found.')

  high_52 = 0
  low_52 = 1_000_000_000
  year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

  change_df = pd.DataFrame({
    'date': prices_df['date'],
    'change': prices_df['close'].pct_change(periods=periods),
    'ref date': prices_df['date'].shift(periods)
  })

  # Loop through earnings and remove affected rows.
  this_df = pd.DataFrame()
  for i, earnings_date in enumerate(earnings_dates[:-1]):
    next_earnings_date = earnings_dates[i+1]
    earnings_df = change_df[(earnings_date < change_df['date']) & (earnings_date < change_df['ref date']) & (change_df['date'] < next_earnings_date)]

    this_df = pd.concat([this_df, earnings_df], ignore_index=True)

  mean = this_df['change'].mean()
  stdev = this_df['change'].std()
  year_ago_df = prices_df[(prices_df['date'] > year_ago)]
  high_52 = year_ago_df['close'].max()
  low_52 = year_ago_df['close'].min()

  if ax:
    min_bin = min(price_moves)
    max_bin = max(price_moves)
    x = np.arange(min_bin, max_bin, 0.001)

    ax.hist(price_moves, bins=x)
    ax.legend(title=f'Period={period}')

    # Graph normalized Gaussian.
    y = norm.pdf(x, mean, stdev)
    ax.plot(x, y, label='Normalized Gaussian')

  # return avg, stdev
  return mean, stdev, high_52, low_52


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


def fetch_optimal_option_expiry(symbol, last_close, expiry_days=None):
  expirations = fetch_filtered_options_expirations(symbol)

  # Find highest IV contract expiry.
  combined_chain = []
  for expiry in expirations:
    combined_chain += fetch_options_chain(symbol, expiry, 'call', last_close, plus_minus=31)

  if len(combined_chain) == 0:
    printout('No suitable options found.')
    return []

  max_iv_contract = select_max_greek_contract(combined_chain, 'smv_vol')
  max_iv_expiry = max_iv_contract['expiration_date']

  max_theta_contract = select_max_greek_contract(combined_chain, 'theta')
  max_theta_expiry = max_theta_contract['expiration_date']

  days_to_expiry = expiry_days or count_trading_days(str(datetime.today().date()), max_iv_expiry)

  printout(f'{days_to_expiry} trading days to max IV contract expiry {max_iv_expiry}\n')
  printout(f'max theta expiry: {max_theta_expiry}\n')

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
  prices_df = pd.DataFrame(fetch_historical_prices(symbol, start_date))
  last_close = prices_df.iloc[-1]['close']

  best_expiry, days_to_best_expiry = fetch_optimal_option_expiry(symbol, last_close)

  # Calculate average price change and sigma of 1 day.
  mu, sigma, high_52, low_52 = calc_historical_price_movement_stats(symbol, prices_df, periods=days_to_best_expiry, ax=ax)

  last_move = (last_close - prices_df.iloc[-2]['close'])/prices_df.iloc[-2]['close']
  printout(f'\033[01mLatest price: {last_close}, {"+" if last_move > 0 else ""}{round(last_move * 100, 2)}%\033[0m')

  # Find covered calls to sell.
  printout(f'52 week high: {high_52}')


  worthy_contracts = []


  # Pull closest strike to S (= expected avg+1 sigma) and delta D of chain.
  zscore = 1
  cc_exp_strike = calc_expected_strike(last_close, mu, sigma, 1, zscore)

  historical_itm_proba = backtest.calc_historical_itm_proba(symbol, prices_df, mu, sigma, days_to_best_expiry, zscore)

  printout(f'My expected *{zscore}* sigma move price: \033[32m{round(cc_exp_strike, 2)}\033[0m (aka {REFERENCE_CONFIDENCE*100}% confidence)')
  printout(f' mu={round(mu*100, 4)}%, sigma={round(sigma * 100, 4)}%, n={days_to_best_expiry}\n')
  printout(f'Historical delta for +1 sigma move in {days_to_best_expiry} days = \033[36m{round(historical_itm_proba, 2)}\033[0m (want this to be smaller than actual delta of target contract)\n')

  this_chain = fetch_options_chain(symbol, best_expiry, 'call', cc_exp_strike, plus_minus=last_close*sigma*0.5)

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

  # Do same thing for CSEP.
  printout(f'52 week low: {low_52}')

  zscore = -1
  csep_exp_strike = calc_expected_strike(last_close, mu, sigma, 1, zscore)


  printout(f'My expected *{zscore}* sigma move price: \033[32m{round(csep_exp_strike, 2)}\033[0m (aka {REFERENCE_CONFIDENCE*100}% confidence)')
  printout(f' mu={round(mu*100, 4)}%, sigma={round(sigma * 100, 4)}%, n={days_to_best_expiry}\n')
#  printout(f'Historical delta for -1 sigma move in {days_to_best_expiry} days = \033[36m{round(historical_itm_proba, 2)}\033[0m (want this to be smaller than actual delta of target contract)\n')

  this_chain = fetch_options_chain(symbol, best_expiry, 'put', csep_exp_strike, plus_minus=last_close*sigma*0.5)

  for _contract in this_chain:
    contract = _contract.copy()
    contract['annual_roi'] = calc_annual_roi(contract)
    pprint_contract(contract)
    should_sell = should_sell_csep(contract, csep_exp_strike)
    if should_sell:
      worthy_contracts.append(contract)

  return worthy_contracts

