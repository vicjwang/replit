import functools
import math
import matplotlib.pyplot as plt
import os
import pickle
import subprocess

from constants import (
  CACHE_DIR,
  FIG_HEIGHT,
  FIG_WIDTH,
  FIG_NCOLS,
  SHOW_GRAPHS,
)
from datetime import datetime
from utils import printout


def graph(strategy_fn):
  
  @functools.wraps(strategy_fn)
  def wrapped(*args, **kwargs):
    
    # add some extra rows for visibility on iPad
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))


    strategy_fn(*args, **kwargs)


    for ax in axes.flatten():
      if not ax.has_data():
        fig.delaxes(ax)

    num_axes = len(fig.get_axes())
      
    if SHOW_GRAPHS:
      print('Rendering plot in Output tab...')
      plt.tight_layout()
      fig.subplots_adjust()
      plt.show()


    return

  return wrapped


def cached(force_refresh=False):
  """
  A function that creates a decorator which will use "cache_filepath" for caching the results of the decorated function "fn".
  """
  def decorator(fn):  # define a decorator for a function "fn"

    @functools.wraps(fn)
    def wrapped(*args, **kwargs):   # define a wrapper that will finally call "fn" with all arguments

      # Create cache folder if not exist.
      today_datestr = datetime.now().strftime('%Y%m%d')
      cache_dir = os.path.join(CACHE_DIR, today_datestr)
      if not os.path.exists(cache_dir):
        subprocess.run(['mkdir', cache_dir])

      # if cache exists -> load it and return its content
      argstr = '_'.join([str(arg) for arg in args])
      kwstr = '_'.join([str(v) for v in kwargs.values()])
      filename_parts = [part for part in [fn.__name__, argstr, kwstr] if part]

      cache_filename = '-'.join(filename_parts)
      cache_filepath = os.path.join(cache_dir, cache_filename)
      if os.path.exists(cache_filepath) and not force_refresh:
        with open(cache_filepath, 'rb') as cachehandle:
          printout("Using cached result from '%s'" % cache_filepath)
          return pickle.load(cachehandle)

      # execute the function with all arguments passed
      res = fn(*args, **kwargs)

      # write to cache file
      with open(cache_filepath, 'wb') as cachehandle:
        printout("Saving result to cache '%s'" % cache_filepath)
        pickle.dump(res, cachehandle)

      return res

    return wrapped

  return decorator
