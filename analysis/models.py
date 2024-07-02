import math
import pandas as pd

from vendors.tradier import (
  fetch_historical_prices,
  fetch_past_earnings_dates,
)

from constants import (
  START_DATE,
  SHOULD_AVOID_EARNINGS,
)


class PriceModel:
  
  _COLNAME_DAILY_CHANGE = 'daily change'
  _COLNAME_IS_EARNINGS = 'is earnings'
  _COLNAME_CLOSE = 'close'
  _COLNAME_DATE = 'date'
  _COLNAME_PREV_DAY = 'previous trading date'

  def __init__(self, symbol, start_date=START_DATE):
    self.symbol = symbol

    # Sorted in most recent first.
    self.earnings_dates = fetch_past_earnings_dates(symbol)

    # Add some helper columns.
    self.prices_df = pd.DataFrame(fetch_historical_prices(symbol, start_date))
    self.prices_df[self._COLNAME_DATE] = pd.to_datetime(self.prices_df[self._COLNAME_DATE])
    self.prices_df[self._COLNAME_DAILY_CHANGE] = self.prices_df[self._COLNAME_CLOSE].pct_change(periods=1)
    self.prices_df[self._COLNAME_PREV_DAY] = pd.to_datetime(self.prices_df[self._COLNAME_DATE].shift(1))
    self.prices_df[self._COLNAME_IS_EARNINGS] = self.prices_df[self._COLNAME_DATE].isin(self.earnings_dates) | self.prices_df[self._COLNAME_PREV_DAY].isin(self.earnings_dates)
 
    # Use mask to include/exclude price movements on earnings dates.
    mask = [True] * len(self.prices_df)
    if SHOULD_AVOID_EARNINGS:
      mask = self.prices_df[self._COLNAME_IS_EARNINGS]

    # Save some key stats.
    self.daily_mean = self.prices_df[mask][self._COLNAME_DAILY_CHANGE].mean()
    self.daily_stdev = self.prices_df[mask][self._COLNAME_DAILY_CHANGE].std()
  
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
    target_price = latest_price * (1 + days*self.get_daily_mean() + zscore*math.sqrt(days)*self.get_daily_stdev())
    return target_price

  def print_latest(self):
    latest_price = self.get_latest_price() 
    latest_change = self.get_latest_change()
    print(f'{self.symbol}: ${latest_price}, {round(latest_change * 100, 2)}%')
    
