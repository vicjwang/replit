import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sys

import config

from datetime import timedelta

from vendors.tradier import (
  fetch_historical_prices,
  fetch_past_earnings_dates,
  fetch_next_earnings_date,
)

from constants import (
  DATE_FORMAT,
  MU,
  SIGMA_LOWER,
)

from utils import calc_expected_price, strformat


class PriceModel:
  
  _COLNAME_DAILY_CHANGE = 'daily_change'
  _COLNAME_IS_EARNINGS = 'is_earnings'
  _COLNAME_CLOSE = 'close'
  _COLNAME_DATE = 'date'
  _COLNAME_PREV_DAY = 'previous_trading_date'

  def __init__(self, symbol, start_date=config.REGIME_START_DATE, avoid_earnings=config.SHOULD_AVOID_EARNINGS):
    self.symbol = symbol

    # Sorted in most recent first.
    self.past_earnings_dates = fetch_past_earnings_dates(symbol)
    self.next_earnings_date = fetch_next_earnings_date(symbol)

    # Some helper columns.
    self.prices_df = pd.DataFrame(fetch_historical_prices(symbol, start_date))
    self.prices_df[self._COLNAME_DATE] = pd.to_datetime(self.prices_df[self._COLNAME_DATE])
    self.prices_df[self._COLNAME_DAILY_CHANGE] = self.prices_df[self._COLNAME_CLOSE].pct_change(periods=1)
    self.prices_df[self._COLNAME_PREV_DAY] = pd.to_datetime(self.prices_df[self._COLNAME_DATE].shift(1))
    self.prices_df[self._COLNAME_IS_EARNINGS] = self.prices_df[self._COLNAME_DATE].isin(self.past_earnings_dates) | self.prices_df[self._COLNAME_PREV_DAY].isin(self.past_earnings_dates)
 
    # Use mask to include/exclude price movements on earnings dates.
    self.avoid_earnings_mask = [True] * len(self.prices_df)
    if avoid_earnings:
      self.avoid_earnings_mask = ~self.prices_df[self._COLNAME_IS_EARNINGS]

    # Save some key stats.
    self.daily_mean = self.prices_df[self.avoid_earnings_mask][self._COLNAME_DAILY_CHANGE].mean()
    self.daily_stdev = self.prices_df[self.avoid_earnings_mask][self._COLNAME_DAILY_CHANGE].std()

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

  def predict_price(self, days, tscore=None, zscore=None, from_price=None):
    if from_price is None:
      from_price = self.get_latest_price()
    mu = self.get_daily_mean()
    sigma = self.get_daily_stdev()
    target_price = calc_expected_price(from_price, mu, sigma, days, tscore=tscore, zscore=zscore)
    return target_price

  def __str__(self):
    latest_price = self.get_latest_price() 
    latest_change = self.get_latest_change()
    s = '\n'.join([
      strformat(self.symbol, f"${latest_price}, {round(latest_change * 100, 2)}%"),
      strformat(self.symbol, f"{MU}={self.daily_mean:.4f} {SIGMA_LOWER}={self.daily_stdev:.4f}"),
      strformat(self.symbol, f"Next earnings={self.next_earnings_date.strftime(DATE_FORMAT)}"),
    ])
    return s

  def graph_historical_returns(self, periods):
    graph_df = self.prices_df[self.avoid_earnings_mask]
    
    graph_df['returns'] = graph_df[self._COLNAME_CLOSE].pct_change(periods=periods)

    x_min = graph_df['returns'].min()
    x_max = graph_df['returns'].max()
    x_interval = .05

    x = np.arange(x_min, x_max, x_interval)

    fig = plt.figure(2)
    plt.hist(graph_df['returns'], bins=x)
    plt.legend(title=f"Periods={periods}")
    print('Rendering plot in Output tab...')
    plt.tight_layout()
    plt.show()

  def graph_intraquarter_returns(self, periods, fig_num=2):
    assert periods < 60
    graph_df = self.prices_df[self.avoid_earnings_mask]

    returns = []

    for i, this_earnings_date in enumerate(self.past_earnings_dates[:-1]):
      prev_earnings_date = self.past_earnings_dates[i + 1]

      mask = graph_df['date'].between(prev_earnings_date, this_earnings_date)
      quarter_df = graph_df[mask]
      period_returns = quarter_df['close'].pct_change(periods).dropna()
      returns = np.concatenate([returns, period_returns])

    print(f"Period={periods}: mean={returns.mean()} sigma={returns.std()}")

    x_min = returns.min()
    x_max = returns.max()
    x_interval = .01

    x = np.arange(x_min, x_max, x_interval)

    fig = plt.figure(fig_num)
    plt.hist(returns, bins=x)
    plt.legend(title=f"Periods={periods}")

  def calc_intraquarter_predict_price_accuracy(self, days, zscore, is_under=True):
    # TODO(vjw): replace zscore with tscore?
    assert days < 60
    
    df = self.prices_df[self.avoid_earnings_mask]

    over_count = 0
    under_count = 0
    for i, this_earnings_date in enumerate(self.past_earnings_dates[:-1]):
      prev_earnings_date = self.past_earnings_dates[i + 1]

      quarter_mask = df['date'].between(prev_earnings_date, this_earnings_date)
      mask = quarter_mask & (df['date'] + timedelta(days=days*7/5) < this_earnings_date)
      quarter_df = df[mask]

      pred_df = pd.DataFrame()
      pred_df['date'] = (quarter_df['date'] + timedelta(days=days*7/5)).dt.date
      # Axis=1 to apply to each row.
      pred_df['predicted'] = quarter_df.apply(lambda row: self.predict_price(days, zscore, row['close']), axis=1)
      
      compare_df = df[quarter_mask].set_index('date').join(pred_df.set_index('date'))

      over_count += sum(compare_df['predicted'] < compare_df['close'])
      under_count += sum(compare_df['predicted'] >= compare_df['close'])

    total = over_count + under_count
    return under_count / total if is_under else over_count / total


if __name__ == '__main__':

  model = PriceModel('NVDA')
  model.graph_intraquarter_returns(20, fig_num=1)
  model.calc_intraquarter_predict_price_accuracy(20, 1)
#  model.graph_intraquarter_returns(30, fig_num=2)
#  model.calc_intraquarter_predict_price_accuracy(30, 1)
#  model.graph_intraquarter_returns(40, fig_num=3)
#  model.calc_intraquarter_predict_price_accuracy(40, 1)

  print('Rendering plot in Output tab...')
  plt.tight_layout()
#  plt.show()

