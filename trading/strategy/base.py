import mplcursors
import matplotlib.dates as mdates
import pandas as pd

import config

from datetime import datetime

from analysis.models import PriceModel
from constants import (
  DATE_FORMAT,
  DELTA_UPPER,
  MU,
  SIGMA_LOWER,
  T_SIG_LEVELS,
)
from utils import (
  count_trading_days,
  calc_annual_roi,
  get_win_proba,
  get_target_colname,
  get_tscore,
  get_zscore,
)
from vendors.tradier import (
  fetch_options_expirations,
  fetch_options_chain,
)


class DerivativeStrategyBase:
  INCLUDE_COLUMNS = [
    'description',
    'expiration_date',
    'option_type',
    'strike',
    'bid',
    'ask',
    'volume',
    'greeks',
  ]
  
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

  def _load(self):
  
    self.df = None
    
    chain_dfs = []
    # Target strikes depend on expiry dates so concat by expiry date groups.
    for expiry_date in self.expiry_dates:

      chain = fetch_options_chain(self.symbol, expiry_date.strftime(DATE_FORMAT))
      # Drop column if all values = nan.
      chain_df = pd.DataFrame.from_records(chain, columns=self.INCLUDE_COLUMNS).dropna(axis=1, how='all')
#      chain_df = pd.DataFrame.from_records(chain).dropna(axis=1, how='all')

      if chain_df.empty:
        continue

      trading_dte = count_trading_days(expiry_date)
      dof = trading_dte - 1
      for sig_level in sorted(T_SIG_LEVELS):
        # T-score does not exist for dof = 0 so default to Normal since sigma is 1 day move anyways.
        xscore = get_tscore(sig_level, dof) or get_zscore(sig_level)
        target_strike = self.price_model.predict_price(trading_dte, xscore)
        colname = get_target_colname(sig_level)
        chain_df[colname] = target_strike

      chain_dfs.append(chain_df)
      
    # Optimization - concat just once at end, otherwise copy created per loop.
    self.df = pd.concat(chain_dfs, axis=0)

    # Helper columns including unnested greek columns.
    greeks = pd.json_normalize(self.df['greeks']).set_index(self.df.index)
    self.df = pd.concat([self.df.drop(columns=['greeks']), greeks], axis=1)

    self.df['yoy_roi'] = self.df.apply(calc_annual_roi, axis=1)
    self.df['expiration_date'] = pd.to_datetime(self.df['expiration_date'])

  # TODO (vjw): use @property?
  def get_price_model(self):
    return self.price_model

  def get_snapshot_class(self):
    return DerivativeStrategySnapshot

  def _prepare_df(self, sig_level, option_type):
    # Capture closest 2 strikes.
    target_colname = get_target_colname(sig_level)
    graph_df = self.df.groupby(by='expiration_date').apply(lambda x: x.iloc[(abs(x['strike'] - x[target_colname])).argsort()[:2]])
    return graph_df

  def _apply_filters(self, graph_df, option_type, expiry_after, expiry_before):

    strike_mask = (graph_df['strike'] < config.MAX_STRIKE)

    option_type_mask = (graph_df['option_type'] == option_type)

    # ROI needs to be worth it plus ROI becomes linear when too itm so remove.
    roi_mask = (graph_df['yoy_roi'] > config.WORTHY_MIN_ROI)
    otm_only_mask = (graph_df['yoy_roi'] < 1)

    # Cash needs to be worth it per contract.
    cash_mask = (graph_df['bid'] > config.WORTHY_MIN_BID)

    mask = option_type_mask & strike_mask & cash_mask & roi_mask & otm_only_mask

    if expiry_after:
      start_mask = (graph_df['expiration_date'].dt.date > expiry_after.date())
      mask &= start_mask
    
    if expiry_before:
      end_mask = (graph_df['expiration_date'].dt.date < expiry_before.date())
      mask &= end_mask

    graph_df = graph_df[mask].reset_index(drop=True)

    if len(graph_df) == 0:
      error_msg = f"""
        No eligible options to graph (option_type={option_type}, expiry_after={expiry_after}, expiry_before={expiry_before}).
        any(strike_mask)={any(strike_mask)}
        any(otm_only_mask)={any(otm_only_mask)}
        any(mask)={any(mask)}
      """
      raise ValueError(error_msg)

    return graph_df

  def make_snapshot(self, option_type, sig_level, expiry_after=None, expiry_before=None):

    if option_type not in ('call', 'put'):
      raise ValueError("Invalid option_type: {option_type}")

    # Prepare dataframe by finding best strikes.
    graph_df = self._prepare_df(sig_level, option_type)

    # Apply filters.
    graph_df = self._apply_filters(graph_df, option_type, expiry_after, expiry_before)

    # Return snapshot.
    mu = self.price_model.get_daily_mean()
    sigma = self.price_model.get_daily_stdev()
    latest_price = self.price_model.get_latest_price()
    latest_change = self.price_model.get_latest_change()
    next_earnings = self.price_model.get_next_earnings_date()

    win_proba = get_win_proba(self.side, option_type, sig_level)
    title = f"{self.symbol}: {self.side.title()} {option_type.title()} Strikes @ {win_proba * 100:.1f}% Win Proba"
    text = '\n'.join((
      f'${latest_price}, {latest_change * 100:.2f}%',
      f'Next earnings: {next_earnings.strftime(DATE_FORMAT)}',
      f'{MU}={mu * 100:.2f}%',
      f'{SIGMA_LOWER}={sigma * 100:.2f}%',
    ))
    snapshot_class = self.get_snapshot_class()
    return snapshot_class(self.symbol, graph_df, self.side, option_type,
                          sig_level, title=title, text=text, next_earnings=next_earnings)


class DerivativeStrategySnapshot:
  
  def __init__(self, symbol, df, side, option_type, sig_level, title=None, text=None, next_earnings=None):
    self.symbol = symbol
    self.df = df
    self.title = title
    self.text = text
    self.side = side
    self.option_type = option_type
    self.sig_level = sig_level
    self.next_earnings = next_earnings

  def _get_tooltip_map(self, xs, ys):

    target_colname = get_target_colname(self.sig_level)

    strikes = self.df['strike']
    bids = self.df['bid']
    deltas = self.df['delta']
    target_strikes = self.df[target_colname].round(2)

    dtes = self.df['expiration_date'].dt.tz_localize(config.EASTERN_TIMEZONE).apply(lambda d: (d - config.NOW).days + 1)
    vols = self.df['smv_vol']
    volumes = self.df['volume']
    thetas = self.df['theta']
    gammas = self.df['gamma']
    vegas = self.df['vega']
    move_edges = self.df['move_edge']
    delta_edges = self.df['delta_edge']
    low_52_edges = self.df['52_low_edge']
    ma_200_edges = self.df['200_ma_edge']

    tooltip_map = dict()

    for i, xy in enumerate(zip(xs, ys)):
      expiry, roi = xy
      expiry_at = expiry.strftime(DATE_FORMAT)
      dte = dtes.iloc[i]
      target_strike = target_strikes.iloc[i]
      strike = strikes.iloc[i]
      bid = bids.iloc[i]
      volume = volumes.iloc[i]
      vol = vols.iloc[i].round(4)
      delta = deltas.iloc[i].round(4)
      theta = thetas.iloc[i].round(4)
      gamma = gammas.iloc[i].round(4)
      vega = vegas.iloc[i].round(4)
      move_edge = move_edges.iloc[i].round(4)
      delta_edge = delta_edges.iloc[i].round(4)
      low_52_edge = low_52_edges.iloc[i].round(4)
      ma_200_edge = ma_200_edges.iloc[i].round(4)
      key = (expiry_at, roi)

      tooltip_map[key] = dict(
        dte=dte,
        target_strike=target_strike,
        strike=strike,
        bid=bid,
        volume=volume,
        vol=vol,
        delta=delta,
        theta=theta,
        gamma=gamma,
        vega=vega,
        move_edge=move_edge,
        delta_edge=delta_edge,
        low_52_edge=low_52_edge,
        ma_200_edge=ma_200_edge
      )

    return tooltip_map

  def _make_tooltip_text(self, tooltip_map, key):
      expiry_at, roi = key
      tooltip_item = tooltip_map[key]
      move_edge = tooltip_item['move_edge']
      delta_edge = tooltip_item['delta_edge']
      low_52_edge = tooltip_item['low_52_edge']
      ma_200_edge = tooltip_item['ma_200_edge']
      total_edge = round(move_edge + delta_edge + low_52_edge + ma_200_edge, 4)

      text = '\n'.join([
        f"expiry={expiry_at}",
        f"dte={tooltip_item['dte']}",
        f"target=${tooltip_item['target_strike']}",
        f"strike=${tooltip_item['strike']}",
        f"bid=${tooltip_item['bid']}",
        f"volume={tooltip_item['volume']}",
        f"vol={tooltip_item['vol']}",
        f"delta={tooltip_item['delta']}",
        f"theta={tooltip_item['theta']}",
        f"gamma={tooltip_item['gamma']}",
        f"vega={tooltip_item['vega']}",
        f"move edge={move_edge}",
        f"delta edge={delta_edge}",
        f"52 low edge={low_52_edge}",
        f"200 ma edge={ma_200_edge}",
        f"total edge={total_edge}",
      ])
      return text

  def _add_tooltip(self, cursor, tooltip_map):
    @cursor.connect('add')
    def on_add(sel):
      expiry_at = mdates.num2date(sel.target[0]).strftime(DATE_FORMAT)
      roi = sel.target[1]
      key = (expiry_at, roi)

      text = self._make_tooltip_text(tooltip_map, key)

      sel.annotation.set(text=text)

  def graph_roi_vs_expiry(self, ax):
    target_colname = get_target_colname(self.sig_level)

    # Graph of ROI vs Expirations.
    xs = self.df['expiration_date']
    ys = self.df['yoy_roi']

    strikes = self.df['strike']
    bids = self.df['bid']
    deltas = self.df['delta']
    target_strikes = self.df[target_colname].round(2)

    if len(xs) == 0 or len(ys) == 0:
      raise RuntimeError('No data to graph')

#    ax.plot(xs, ys, linestyle='-', marker='o')
    scatter = ax.scatter(xs, ys)
    for x, y, strike, bid, delta in zip(xs, ys, strikes, bids, deltas):
      label = f'K=${strike}; ${bid} ({DELTA_UPPER}={delta:.2f})'
      ax.text(x, y, label, fontsize=8)#, ha='right', va='bottom')

    # Custom xticks.
    xticks = xs
    xticklabels = [f'{e.strftime(DATE_FORMAT)}\n(t=${t})' for e,t in zip(xs, target_strikes)]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, rotation=30)

    cursor = mplcursors.cursor(scatter, hover=True)
    tooltip_map = self._get_tooltip_map(xs, ys)
    self._add_tooltip(cursor, tooltip_map)
    
    yticks = [i/10 for i in range(0, 11)]
    ax.set_yticks(yticks)

    ax.set_title(self.title)

    bbox_props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.75, 0.95, self.text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=bbox_props)

    ylabel= 'ROI (YoY)'
    ax.set_ylabel(ylabel)

    ax.axvline(x=self.next_earnings, color='b')

