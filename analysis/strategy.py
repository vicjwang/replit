import numpy as np
import pandas as pd
import sys

from analysis.models import PriceModel

from constants import (
  COVERED_CALLS,
  DATE_FORMAT,
  DELTA_UPPER,
  PHI_ZSCORE,
  MIN_EXPIRY_DATESTR,
  MU,
  SIDE_SHORT,
  SIGMA_LOWER,
  MY_WIN_PROBA,
  WIN_PROBA_ZSCORE,
  WORTHY_MIN_BID,
  WORTHY_MIN_ROI,
)

from vendors.tradier import (
  fetch_options_expirations,
  fetch_options_chain,
)

from utils import (
  count_trading_days,
  calc_annual_roi,
  get_win_proba,
  get_target_colname,
  strformat,
)


class DerivativeStrategySnapshot:
  
  def __init__(self, symbol, df, side, option_type, zscore, title=None, text=None):
    self.symbol = symbol
    self.df = df
    self.title = title
    self.text = text
    self.side = side
    self.option_type = option_type
    self.zscore = zscore

  def graph_roi_vs_expiry(self, ax):
    target_colname = get_target_colname(self.zscore)

    rois = self.df['yoy_roi']
    expirations = self.df['expiration_date']
    strikes = self.df['strike']
    bids = self.df['bid']
    deltas = self.df['delta']
    target_strikes = self.df[target_colname].round(2)

    if len(expirations) == 0:
      raise RuntimeError('No data to graph')

    """
    # Print target strikes.
    for e, t in sorted(set(zip(expirations, target_strikes))):
      trading_dte = count_trading_days(e)
      self._print(f"{e.date()} ({trading_dte} trading days away) {target_colname}=${t:.2f}")

      try:
        is_under = option_type == 'call'
        accuracy = self.price_model.calc_intraquarter_predict_price_accuracy(trading_dte, zscore, is_under)
        self._print(f" historical win rate for {trading_dte} trading days away={accuracy:.2f}")
      except:
        continue
    """

    # Graph of ROI vs Expirations.
    xs = expirations.dt.strftime(DATE_FORMAT)
    ys = rois
    ax.plot(xs, ys)
    for x, y, strike, bid, delta in zip(xs, ys, strikes, bids, deltas):
      label = f'K=\${strike}; \${bid} ({DELTA_UPPER}={delta:.2f})'
      ax.text(x, y, label, fontsize=8)#, ha='right', va='bottom')

    # Custom xticks.
    xticks = xs
    xticklabels = [f'{e}\n(t=${t})' for e,t in zip(xs, target_strikes)]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, rotation=30)

    win_proba = get_win_proba(self.side, self.option_type, self.zscore)
    ax.set_title(self.title)

    bbox_props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.75, 0.95, self.text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=bbox_props)

    ylabel= 'ROI (YoY)'
    ax.set_ylabel(ylabel)



class DerivativeStrategyBase:
  
  def __init__(self, symbol, side=None):
    self.symbol = symbol
    self.price_model = PriceModel(symbol)
    self.side = side
  
    self.expiry_dates = pd.to_datetime(fetch_options_expirations(symbol))
    self._load()

  def __repr__(self):
    return f"DerivativeStrategyBase(symbol={self.symbol}, side={self.side})"

  def __str__(self):
    return str(self.price_model)

  # TODO (vjw): use_cache from pkl?
  def _load(self, use_cache=True):
  
    self.df = None
    
    # Target strikes depend on expiry dates so concat by expiry date groups.
    for expiry_date in self.expiry_dates:

      chain = fetch_options_chain(self.symbol, expiry_date.strftime(DATE_FORMAT))
      # Drop column if all values = nan.
      chain_df = pd.DataFrame.from_records(chain).dropna(axis=1, how='all')

      if chain_df.empty:
        continue

      trading_dte = count_trading_days(expiry_date)
      for zscore in sorted(PHI_ZSCORE.values()):
        target_strike = self.price_model.predict_price(trading_dte, zscore)
        colname = f"{zscore}_sigma_target"
        chain_df[colname] = target_strike

      if self.df is None:
        self.df = chain_df
      else:
        self.df = pd.concat([self.df, chain_df], axis=0)

    # Helper columns including unnested greek columns.
    self.df = pd.concat([self.df, self.df['greeks'].apply(pd.Series)], axis=1)
    del self.df['greeks']
    self.df['yoy_roi'] = self.df.apply(calc_annual_roi, axis=1)
    self.df['expiration_date'] = pd.to_datetime(self.df['expiration_date'])

  # TODO (vjw): use @property?
  def get_price_model(self):
    return self.price_model

  def build_snapshot(self, option_type, zscore=None, expiry_after=None, expiry_before=None):

    if option_type not in ('call', 'put'):
      raise ValueError("Invalid option_type: {option_type}")

    if zscore is None:
      zscore = WIN_PROBA_ZSCORE[self.side][option_type][MY_WIN_PROBA]
      win_proba = MY_WIN_PROBA
    else:
      win_proba = get_win_proba(self.side, option_type, zscore)

    # Capture closest 2 strikes.
    target_colname = get_target_colname(zscore)
    graph_df = self.df.groupby(by='expiration_date').apply(lambda x: x.iloc[(abs(x['strike'] - x[target_colname])).argsort()[:2]])

    option_type_mask = (graph_df['option_type'] == option_type)

    # ROI needs to be worth it plus ROI becomes linear when too itm so remove.
    roi_mask = (graph_df['yoy_roi'] > WORTHY_MIN_ROI)
    otm_only_mask = (graph_df['yoy_roi'] < 1)

    # Cash needs to be worth it per contract.
    cash_mask = (graph_df['bid'] > WORTHY_MIN_BID) 

    mask = option_type_mask & cash_mask & roi_mask & otm_only_mask

    if expiry_after:
      start_mask = (graph_df['expiration_date'] > expiry_after)
      mask &= start_mask

    if expiry_before:
      end_mask = (graph_df['expiration_date'] < expiry_before)
      mask &= end_mask

    graph_df = graph_df[mask]

    if len(graph_df) == 0:
      raise ValueError(f"No eligible options to graph (option_type={option_type}, expiry_after={expiry_after}, expiry_before={expiry_before}).")

    mu = self.price_model.get_daily_mean()
    sigma = self.price_model.get_daily_stdev()
    latest_price = self.price_model.get_latest_price()
    latest_change = self.price_model.get_latest_change()

    title = f"{self.symbol}: {self.side.title()} {option_type.title()} Strikes @ Z-Score={zscore} ({win_proba}% Win Proba)"
    text = '\n'.join((
      f'\${latest_price}, {latest_change * 100:.2f}%',
      f'Next earnings: {self.price_model.get_next_earnings_date().date()}',
      f'{MU}={mu * 100:.2f}%',
      f'{SIGMA_LOWER}={sigma * 100:.2f}%',
    ))
    return DerivativeStrategySnapshot(self.symbol, graph_df, self.side, option_type,
                                      zscore, title=title, text=text)


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
  return deriv_strat.build_snapshot(option_type, expiry_after=MIN_EXPIRY_DATESTR)


def sell_LTDOTM_calls(symbol):
  # NOTE: YoY ROI generally not worth it (<.05)
  side = SIDE_SHORT
  option_type = 'call'

  deriv_strat = DerivativeStrategyBase(symbol, side=side)
  print(deriv_strat)
  return deriv_strat.build_snapshot(option_type, expiry_after=MIN_EXPIRY_DATESTR)
