import mplcursors
import matplotlib.dates as mdates
import pandas as pd

import config

from strategy.base import DerivativeStrategyBase, DerivativeStrategySnapshot

from constants import (
  DATE_FORMAT,
  T_SIG_LEVELS,
  MU,
  SIGMA_LOWER,
  DELTA_UPPER,
)

from utils import (
  calc_annual_roi,
  calc_spread,
  count_trading_days,
  get_sig_level,
  get_win_proba,
  get_target_colname,
  get_tscore,
)


class CreditSpreadStrategy(DerivativeStrategyBase):

  def get_snapshot_class(self):
    return CreditSpreadSnapshot

  def _get_long_row_index(self, group_df, short_strike, short_premium, win_proba):

    mid_bid_ask = (group_df['bid'] + group_df['ask']) / 2

    ev = (
      # win case
      (win_proba * (short_premium - mid_bid_ask))
      # TODO: vjw case where short leg itm but long leg otm
      # "lose" case (value already negative)
      + (1 - win_proba) * ((short_premium - mid_bid_ask) - (short_strike - group_df['strike']))
    ).round(4)

    group_df['ev'] = ev
    ev_argsort = ev.argsort()
    return ev_argsort[-1:]

  def _find_best_strikes(self, group_df, short_target_colname, win_proba):

    short_leg_row = group_df.iloc[(abs(group_df['strike'] - group_df[short_target_colname])).argsort()[:1]]

    short_strike = short_leg_row['strike'].values[0]
    short_premium = (short_leg_row['bid'] + short_leg_row['ask']).values[0] / 2

    long_df = group_df[group_df['strike'] < short_strike]
    long_leg_row = long_df.iloc[self._get_long_row_index(long_df, short_strike, short_premium, win_proba)]

    ret = pd.concat([short_leg_row.reset_index(drop=True), long_leg_row.reset_index(drop=True)])
    return ret

  def _prepare_df(self, sig_level, option_type):
    target_colname = get_target_colname(sig_level)
    win_proba = get_win_proba('short', option_type, sig_level)

    option_type_mask = (self.df['option_type'] == option_type)
    grouped_df = self.df[option_type_mask].groupby(by='expiration_date')

    graph_df = grouped_df.apply(lambda x: self._find_best_strikes(x, target_colname, win_proba))
    return graph_df


class CreditSpreadSnapshot(DerivativeStrategySnapshot):

  def _get_tooltip_map(self, xs, ys):
    tooltip_map = super()._get_tooltip_map(xs, ys)
    evs = self.df['ev']

    for i, xy in enumerate(zip(xs, ys)):
      expiry, roi = xy
      expiry_at = expiry.strftime(DATE_FORMAT)

      ev = evs.iloc[i].round(4)

      key = (expiry_at, roi)
      tooltip_map[key]['ev'] = ev

    return tooltip_map

  def _make_tooltip_text(self, tooltip_map, key):
    ev = tooltip_map[key]['ev']
    text = super()._make_tooltip_text(tooltip_map, key)
    text = '\n'.join([
      text,
      f"ev={ev}",
    ])
    return text
