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

  def make_snapshot(self, option_type, sig_level, expiry_after=None, expiry_before=None):

    if option_type not in ('call', 'put'):
      raise ValueError("Invalid option_type: {option_type}")

    if option_type == 'call':
      raise NotImplementedError

    # Capture closest strike to short leg.
    target_colname = get_target_colname(sig_level)
    option_type_mask = (self.df['option_type'] == option_type)
    grouped_df = self.df[option_type_mask].groupby(by='expiration_date')
    short_leg_df = grouped_df.apply(lambda x: x.iloc[(abs(x['strike'] - x[target_colname])).argsort()[:1]])

    # Capture closest strike to long leg.
    win_proba = get_win_proba('short', option_type, sig_level)
    long_leg_df = grouped_df.apply(lambda x: x.iloc[(abs(x['strike'] - (x[target_colname] - calc_spread(win_proba, x['bid'])))).dropna().argsort()[:1]])
    graph_df = pd.concat([short_leg_df.reset_index(drop=True), long_leg_df.reset_index(drop=True)])

    strike_mask = (graph_df['strike'] < config.MAX_STRIKE)

    # ROI needs to be worth it plus ROI becomes linear when too itm so remove.
    otm_only_mask = (graph_df['yoy_roi'] < 1)

    mask = strike_mask & otm_only_mask

    if expiry_after:
      start_mask = (graph_df['expiration_date'] > expiry_after)
      mask &= start_mask
    
    if expiry_before:
      end_mask = (graph_df['expiration_date'] < expiry_before)
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
    return CreditSpreadSnapshot(self.symbol, graph_df, self.side, option_type,
                                      sig_level, title=title, text=text, next_earnings=next_earnings)


class CreditSpreadSnapshot(DerivativeStrategySnapshot):
  def graph_roi_vs_expiry(self, ax):
    # TODO: combine legs? color code?
    target_colname = get_target_colname(self.sig_level)
    win_proba = get_win_proba('short', self.option_type, self.sig_level)

    rois = self.df['yoy_roi']
    expirations = self.df['expiration_date']
    strikes = self.df['strike']
    bids = self.df['bid']
    deltas = self.df['delta']
    target_strikes = self.df[target_colname].round(2)

    if len(expirations) == 0:
      raise RuntimeError('No data to graph')

    # Graph of ROI vs Expirations.
    xs = pd.to_datetime(expirations)
    ys = rois
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

    dtes = self.df['expiration_date'].apply(lambda d: (d - config.NOW).days + 1)
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
      tooltip_map[key] = (dte, target_strike, strike, bid, volume, vol, delta, theta, gamma, vega, move_edge, delta_edge, low_52_edge, ma_200_edge)

    @cursor.connect('add')
    def on_add(sel):
      expiry_at = mdates.num2date(sel.target[0]).strftime(DATE_FORMAT)
      roi = sel.target[1]
      key = (expiry_at, roi)
      dte, target_strike, strike, bid, volume, vol, delta, theta, gamma, vega, move_edge, delta_edge, low_52_edge, ma_200_edge = tooltip_map[key]
      text = '\n'.join([
        f"expiry={expiry_at}",
        f"dte={dte}",
        f"target=${target_strike}",
        f"strike=${strike}",
        f"bid=${bid}",
        f"volume={volume}",
        f"vol={vol}",
        f"delta={delta}",
        f"theta={theta}",
        f"gamma={gamma}",
        f"vega={vega}",
        f"move edge={move_edge}",
        f"delta edge={delta_edge}",
        f"52 low edge={low_52_edge}",
        f"200 ma edge={ma_200_edge}",
        f"total edge={move_edge + delta_edge + low_52_edge + ma_200_edge}",
      ])

      sel.annotation.set(text=text)
    
    yticks = [i/10 for i in range(11)]
    ax.set_yticks(yticks)

    ax.set_title(self.title)

    bbox_props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.75, 0.95, self.text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=bbox_props)

    ylabel= 'ROI (YoY)'
    ax.set_ylabel(ylabel)

    ax.axvline(x=self.next_earnings, color='b')

