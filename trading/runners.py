import traceback

import config

from utils import strformat


class Runner:
  def __init__(self, build, figman, *args, win_proba=config.MY_WIN_PROBA):
    self.figman = figman
    self.build = build
    self.win_proba = win_proba

    self.figman.add_empty_figure(build.__name__)

  def run(self, build):
    pass


class Scanner(Runner):
  
  def __init__(self, *args, symbols=None, **kwargs):
    self.symbols = symbols
    super().__init__(*args, **kwargs)

  def run(self):
    
    for symbol in self.symbols:
      try:
        snapshot = self.build(symbol, self.win_proba).create_snapshot()
        if snapshot:
          self.figman.add_graph_as_ax(snapshot.graph_roi_vs_expiry)
          print(strformat(snapshot.symbol, f"Adding subplot (WORTHY_MIN_BID={config.WORTHY_MIN_BID}, WORTHY_MIN_ROI={config.WORTHY_MIN_ROI})\n \"{snapshot.title}\"\n"))
      
      except Exception as e:
        print(strformat(symbol, f"Skipping - {e}"))
        if config.IS_DEBUG:
          traceback.print_exc()
          raise e


class Diver(Runner):
  pass
