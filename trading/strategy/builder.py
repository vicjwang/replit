import matplotlib.dates as mdates
import numpy as np
import pandas as pd

import config

from analysis.models import PriceModel
from constants import COVERED_CALLS, SIDE_SHORT
from strategy.credit_spreads import CreditSpreadStrategy
from utils import get_sig_level


class Build:
  
  def __init__(self, symbol, win_proba=config.MY_WIN_PROBA):
    self.symbol = symbol
    self.win_proba = win_proba
  
  def validate_conditions(self):
    pass

  def create_snapshot(self):
    pass


class SellSimpleCreditSpreadBuild(Build):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.side = SIDE_SHORT
    self.strategy = CreditSpreadStrategy(self.symbol, side=self.side)
    self.price_model = self.strategy.get_price_model()
    self.option_type = 'put'

    self.validate_conditions()

  def validate_conditions(self):

    latest_price = self.price_model.get_latest_price()
    latest_change = self.price_model.get_latest_change()

    sigma = self.price_model.get_daily_stdev()
    min_change = sigma * config.MIN_ZSCORE_THRESHOLD

    if latest_change > min_change:
      raise ValueError(f'{self.symbol} {self.option_type} move threshold not met. ${latest_price}, {round(latest_change * 100, 2)}%')

  def create_snapshot(self):
    sig_level = get_sig_level(self.side, self.option_type, self.win_proba)
    next_earnings_date = self.price_model.get_next_earnings_date()
    return self.strategy.make_snapshot(self.option_type, sig_level, expiry_before=next_earnings_date)
  









def sell_intraquarter_derivatives(symbol, win_proba=config.MY_WIN_PROBA):
  if symbol in COVERED_CALLS:
    option_type = 'call'
  else:
    option_type = 'put'

  side = SIDE_SHORT

  deriv_strat = CreditSpreadStrategy(symbol, side=side)
  print(deriv_strat)
  price_model = deriv_strat.get_price_model()

  latest_price = price_model.get_latest_price()
  latest_change = price_model.get_latest_change()

  sigma = price_model.get_daily_stdev()
  min_change = sigma * config.MIN_ZSCORE_THRESHOLD

  if (option_type == 'call' and latest_change < min_change) or (option_type == 'put' and latest_change > -1*min_change):
    raise ValueError(f'{symbol} {option_type} move threshold not met. ${latest_price}, {round(latest_change * 100, 2)}%')

  next_earnings_date = price_model.get_next_earnings_date()

  sig_level = get_sig_level(side, option_type, win_proba)
  return deriv_strat.build_snapshot(option_type, sig_level, expiry_before=next_earnings_date)


def sell_LTDITM_puts(symbol, win_proba=config.MY_WIN_PROBA):
  # Look at far away deep ITM Puts.
  side = SIDE_SHORT
  option_type = 'put'

  deriv_strat = CreditSpreadStrategy(symbol, side=side)
  print(deriv_strat)
  return deriv_strat.build_snapshot(option_type, 0.15, expiry_after=config.MIN_EXPIRY_DATESTR)


def sell_LTDOTM_calls(symbol, win_proba=config.MY_WIN_PROBA):
  # NOTE: YoY ROI generally not worth it (<.05)
  side = SIDE_SHORT
  option_type = 'call'

  deriv_strat = CreditSpreadStrategy(symbol, side=side)
  print(deriv_strat)
  return deriv_strat.build_snapshot(option_type, 0.85, expiry_after=config.MIN_EXPIRY_DATESTR)
