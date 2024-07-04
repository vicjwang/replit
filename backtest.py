import numpy as np
import os
import pickle
import pandas as pd
import vectorbt as vbt

from decorators import cached
from utils import (
  calc_expected_price,
)
from vendors.tradier import fetch_past_earnings_dates


def calc_historical_itm_proba(symbol, prices, mu, sigma, trading_days, zscore, contract_type='c'):
  earnings_dates = fetch_past_earnings_dates(symbol)

  df = pd.DataFrame(prices)
  df['date'] = df['date']
  # Add column of expected price in n days.
  df['expected_price'] = df.apply(lambda x: calc_expected_price(x['close'], mu, sigma, 1, zscore), axis=1)

  # If start days is before earnings and n days later is after earnings, use None.
  df['expected_expiry'] = pd.to_datetime(df['date']) + pd.Timedelta(trading_days, unit='d')

  for earnings_date in earnings_dates:
    df.loc[(df['date'] < earnings_date) & (df['expected_expiry'] > earnings_date), 'expected_price'] = None

  # Add column of boolean if actual price < expeected price column (for cc).
  df['actual_price'] = df['close'].shift(-1*trading_days)

  if contract_type == 'c':
    df['is_itm'] = df['actual_price'] >= df['expected_price']
  elif contract_type == 'p':
    df['is_itm'] = df['actual_price'] <= df['expected_price']

  # Tally count of True values divide by total count.
  proba = len(df[df['is_itm'] == True])/len(df['expected_price'].dropna())

  return proba



@cached()
def fetch_prices(symbols):
  df = vbt.YFData.download(symbols, missing_index='drop').get('Close')
  return df


def buy_mag7_strategy():

  # Fetch historical stock price data
  symbols = ['AAPL', 'AMZN', 'META', 'GOOG', 'MSFT', 'NVDA', 'NFLX', 'TSLA']
  data = fetch_prices(symbols)
  
  # Calculate interval returns
  interval_days = 252
  returns = data.pct_change(interval_days).dropna()[::interval_days]
  
  # Rank stocks based on returns. Higher rank is higher returns.
  rank = returns.rank(axis=1)

  # Strategy is to sell current holding to buy highest performing stock in past year, if different.
  buy_signal = rank == len(symbols)
  sell_signal = buy_signal.shift(1, fill_value=False)

  data = data[data.index.isin(buy_signal.index)]

  # Backtest with vectorbt
  pf = vbt.Portfolio.from_signals(
      data,
  		entries=buy_signal,
      exits=sell_signal,
      init_cash=10_000,
      group_by=True,
      cash_sharing=True,
      call_seq='auto',
      freq='d',
  )
  
  # Display portfolio stats
  print(pf.stats(group_by=True))
  print(pf.orders.records_readable)

  pf_total = pf.total_return()
  print(pf_total)


if __name__ == '__main__':
#  buy_mag7_strategy()
  fetch_prices('NVDA') 
