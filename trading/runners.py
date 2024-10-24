import traceback

import config

from joblib import Parallel, delayed

from signals import (
  MoveSignal,
  DeltaSignal,
  FiftyTwoLowSupportSignal,
  MovingAverageSupportSignal,
)
from utils import strformat, get_win_proba


class Runner:
  def __init__(self, build, figman, symbols, *args):
    self.figman = figman
    self.build = build
    self.symbols = symbols

    self.figman.add_empty_figure(build.__name__)

  def run(self, side=None):
    pass


class Scanner(Runner):

  def __init__(self, *args, win_proba=config.MY_WIN_PROBA, **kwargs):
    super().__init__(*args, **kwargs)
    self.win_proba = win_proba

  def _run_iter(self, symbol):
    signals = [
      MoveSignal(),
      DeltaSignal(),
      FiftyTwoLowSupportSignal(),
      MovingAverageSupportSignal(200, weight=0.5),
    ]
    try:
      snapshot = self.build(symbol, self.win_proba, signals=signals).create_snapshot()
      if snapshot:
        self.figman.add_graph_as_ax(snapshot.graph_roi_vs_expiry)
        print(strformat(snapshot.symbol, f"Adding subplot (WORTHY_MIN_BID={config.WORTHY_MIN_BID}, WORTHY_MIN_ROI={config.WORTHY_MIN_ROI})\n \"{snapshot.title}\"\n"))

    except Exception as e:
      print(strformat(symbol, f"Skipping - {e}"))
      if config.IS_DEBUG:
        traceback.print_exc()
        raise e

  def run(self, side=None):
    Parallel(n_jobs=config.NUM_PARALLEL_JOBS, require='sharedmem')(delayed(self._run_iter)(symbol) for symbol in self.symbols)


class Diver(Runner):

  def run(self, side=None):
    for symbol in self.symbols:

      self.figman.add_empty_figure(symbol)

      for sig_level in self.sig_levels:
        try:
          win_proba = get_win_proba(side, self.option_type, sig_level)
          snapshot = self.build(symbol, win_proba).create_snapshot()
          self.figman.add_graph_as_ax(snapshot.graph_roi_vs_expiry)
          print(strformat(symbol, f"Adding subplot (WORTHY_MIN_BID={config.WORTHY_MIN_BID}, WORTHY_MIN_ROI={config.WORTHY_MIN_ROI})\n \"{snapshot.title}\""))

        except Exception as e:
          print(strformat(symbol, f"Skipping - {e}"))
          if config.IS_DEBUG:
            traceback.print_exc()
            raise e
          else:
            continue


class PutDiver(Diver):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.sig_levels = [0.15, 0.10, 0.05, 0.01]
    self.option_type = 'put'
