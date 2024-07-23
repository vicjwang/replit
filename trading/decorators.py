import functools
import os
import pickle
import subprocess

import config

from utils import printout


def cached(force_refresh=False, use_time=False):
  """
  A function that creates a decorator which will use "cache_filepath" for caching the results of the decorated function "fn".
  """
  def decorator(fn):  # define a decorator for a function "fn"

    @functools.wraps(fn)
    def wrapped(*args, **kwargs):   # define a wrapper that will finally call "fn" with all arguments

      # Create cache folder if not exist.
      today_datestr = config.NOW.strftime('%Y%m%d')
      cache_dir = os.path.join(config.CACHE_DIR, today_datestr)
      if not os.path.exists(cache_dir):
        subprocess.run(['mkdir', cache_dir])

      # if cache exists -> load it and return its content
      argstr = '_'.join([str(arg) for arg in args])
      kwstr = '_'.join([str(v) for v in kwargs.values()])
      filename_parts = [part for part in [fn.__name__, argstr, kwstr] if part]
      if use_time:
        now_timestr = config.NOW.strftime('%H%M')
        filename_parts = [now_timestr, *filename_parts]

      cache_filename = '-'.join(filename_parts) + '.pkl'
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
