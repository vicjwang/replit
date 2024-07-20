import matplotlib.dates as mdates
import numpy as np
import pandas as pd

import config

from analysis.models import PriceModel
from constants import (
  COVERED_CALLS,
  DATE_FORMAT,
  DELTA_UPPER,
  PHI_ZSCORE,
  MU,
  SIDE_SHORT,
  SIGMA_LOWER,
  MAX_STRIKE,
  WIN_PROBA_ZSCORE,
  WORTHY_MIN_BID,
  WORTHY_MIN_ROI,
)
from analysis.derivative_strategy import DerivativeStrategyBase


def sell_intraquarter_derivatives(symbol):
  if symbol in COVERED_CALLS:
    option_type = 'call'
  else:
    option_type = 'put'

  side = SIDE_SHORT

  deriv_strat = DerivativeStrategyBase(symbol, side=side)
  print(deriv_strat)
  price_model = deriv_strat.get_price_model()

  latest_price = price_model.get_latest_price()
  latest_change = price_model.get_latest_change()

  if (option_type == 'call' and latest_change < 0) or (option_type == 'put' and latest_change > 0):
    raise ValueError(f'{symbol} {option_type} move threshold not met. ${latest_price}, {round(latest_change * 100, 2)}%')

  next_earnings_date = price_model.get_next_earnings_date()

  return deriv_strat.build_snapshot(option_type, expiry_before=next_earnings_date)


def sell_LTDITM_puts(symbol):
  # Look at far away deep ITM Puts.
  side = SIDE_SHORT
  option_type = 'put'

  deriv_strat = DerivativeStrategyBase(symbol, side=side)
  print(deriv_strat)
  return deriv_strat.build_snapshot(option_type, expiry_after=config.MIN_EXPIRY_DATESTR)


def sell_LTDOTM_calls(symbol):
  # NOTE: YoY ROI generally not worth it (<.05)
  side = SIDE_SHORT
  option_type = 'call'

  deriv_strat = DerivativeStrategyBase(symbol, side=side)
  print(deriv_strat)
  return deriv_strat.build_snapshot(option_type, expiry_after=config.MIN_EXPIRY_DATESTR)
