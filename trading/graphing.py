import math
import matplotlib.pyplot as plt
import os

import config

from collections import OrderedDict

from constants import (
  FIG_WIDTH,
  FIG_HEIGHT,
  FIG_NCOLS,
)


class FigureManager:
  
  def __init__(self):
    self.figures = OrderedDict()
    self.current_figure = None

  def add_graph_as_ax(self, graph_fn, *args, **kwargs):
    self.current_figure.append((graph_fn, args, kwargs))

  def add_empty_figure(self, title):
    self.figures[title] = []
    self.current_figure = self.figures[title]

  def render(self):
    
    if config.SKIP_GRAPHS:
      print(f"Disabled render (config.SKIP_GRAPHS={config.SKIP_GRAPHS}).")
      return

    for fig_title, graphs in self.figures.items():
      if len(graphs) == 0:
        print('Skipping', fig_title, '- no graphs to render.')
        continue
      
      nrows = math.ceil(len(graphs) / FIG_NCOLS)
      ncols = FIG_NCOLS
      fig, axes = plt.subplots(nrows, ncols, figsize=(FIG_WIDTH, FIG_HEIGHT))

      fig.canvas.manager.set_window_title(fig_title)

      for i, graph in enumerate(graphs):
        graph_fn, args, kwargs = graph

        if nrows == 1 or ncols == 1:
          ax = axes[i]
        else:
          row_index = i // 2
          col_index = i % 2
          ax = axes[row_index, col_index]

        print()
        graph_fn(ax, *args, **kwargs)

      fig.subplots_adjust()
      plt.tight_layout()

    if config.SHOW_GRAPHS:
      print('Rendering in Output tab...')
      plt.show()
