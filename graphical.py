
import json
import pandas as pd

from utils import calc_annual_roi

from constants import (
  DELTA_UPPER,
  WORTHY_MIN_BID,
  WORTHY_MIN_ROI,
)


def render_roi_vs_expiry(symbol, df, target_colname, ax=None, params=None):
  if not ax:
    raise ValueError('No ax to graph on.')

  rois = df['yoy_roi']
  expirations = df['expiration_date']
  strikes = df['strike']
  bids = df['bid']
  deltas = df['delta']
  target_strikes = df[target_colname].round(2)

  for e, t in sorted(set(zip(expirations, target_strikes))):
    print(f'{symbol}: {e} target=${t:.2f}')

  if len(expirations) == 0:
    raise ValueError(f'No eligible options for graph found for {symbol}.')

  # Graph of ROI vs Expirations.
  print(f'{symbol}: Adding subplot (WORTHY_MIN_BID={WORTHY_MIN_BID}, WORTHY_MIN_ROI={WORTHY_MIN_ROI})')
  ax.plot(expirations, rois)
  for x, y, strike, bid, delta in zip(expirations, rois, strikes, bids, deltas):
    label = f'K=\${strike}; \${bid} ({DELTA_UPPER}={round(delta, 2)})'
    ax.text(x, y, label, fontsize=8)#, ha='right', va='bottom')

  # Custom xticks.
  xticks = expirations
  xticklabels = [f'{e}\n(t=${t})' for e,t in zip(expirations, target_strikes)]
  ax.set_xticks(xticks)
  ax.set_xticklabels(xticklabels, rotation=30)

  if params:
    if 'title' in params:
      title = params['title']
      ax.set_title(title)
    if 'text' in params:
      text = params['text']
      bbox_props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
      ax.text(0.75, 0.95, text, transform=ax.transAxes, fontsize=10,
              verticalalignment='top', bbox=bbox_props)
    if 'ylabel' in params:
      ylabel = params['ylabel']
      ax.set_ylabel(ylabel)

