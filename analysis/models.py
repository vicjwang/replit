import math
import pandas as pd
import numpy as np
import sys

from vendors.tradier import (
  fetch_historical_prices,
  fetch_past_earnings_dates,
  get_next_earnings_date,
)

from constants import (
  START_DATE,
  SHOULD_AVOID_EARNINGS,
  MU,
  SIGMA_LOWER,
)


class PriceModel:
  
  _COLNAME_DAILY_CHANGE = 'daily_change'
  _COLNAME_IS_EARNINGS = 'is_earnings'
  _COLNAME_CLOSE = 'close'
  _COLNAME_DATE = 'date'
  _COLNAME_PREV_DAY = 'previous_trading_date'

  def __init__(self, symbol, start_date=START_DATE):
    self.symbol = symbol

    # Sorted in most recent first.
    self.past_earnings_dates = fetch_past_earnings_dates(symbol)
    self.next_earnings_date = get_next_earnings_date(symbol)

    # Some helper columns.
    self.prices_df = pd.DataFrame(fetch_historical_prices(symbol, start_date))
    self.prices_df[self._COLNAME_DATE] = pd.to_datetime(self.prices_df[self._COLNAME_DATE])
    self.prices_df[self._COLNAME_DAILY_CHANGE] = self.prices_df[self._COLNAME_CLOSE].pct_change(periods=1)
    self.prices_df[self._COLNAME_PREV_DAY] = pd.to_datetime(self.prices_df[self._COLNAME_DATE].shift(1))
    self.prices_df[self._COLNAME_IS_EARNINGS] = self.prices_df[self._COLNAME_DATE].isin(self.past_earnings_dates) | self.prices_df[self._COLNAME_PREV_DAY].isin(self.past_earnings_dates)
 
    # Use mask to include/exclude price movements on earnings dates.
    mask = [True] * len(self.prices_df)
    if SHOULD_AVOID_EARNINGS:
      mask = ~self.prices_df[self._COLNAME_IS_EARNINGS]

    # Save some key stats.
    self.daily_mean = self.prices_df[mask][self._COLNAME_DAILY_CHANGE].mean()
    self.daily_stdev = self.prices_df[mask][self._COLNAME_DAILY_CHANGE].std()
    self.print(f"{MU}={self.daily_mean} {SIGMA_LOWER}={self.daily_stdev}")

  def print(self, s):
    print(f"{self.symbol}: {s}")

  def get_next_earnings_date(self):
    return self.next_earnings_date
  
  def get_latest_price(self):
    return self.prices_df.iloc[-1][self._COLNAME_CLOSE]

  def get_latest_change(self):
    return self.prices_df.iloc[-1][self._COLNAME_DAILY_CHANGE]

  def get_daily_mean(self):
    return self.daily_mean

  def get_daily_stdev(self):
    return self.daily_stdev

  def predict_price(self, days, zscore):
    latest_price = self.get_latest_price()
    mu = self.get_daily_mean()
    sigma = self.get_daily_stdev()
    target_price = latest_price * (1 + days*mu + zscore*math.sqrt(days)*sigma)
    return target_price

  def print_latest(self):
    latest_price = self.get_latest_price() 
    latest_change = self.get_latest_change()
    print(f'{self.symbol}: ${latest_price}, {round(latest_change * 100, 2)}%')
   

