import math
import numpy
import random


Nt = 252
Np = 10_000
mu = .06 / Nt
sigma = .40 / math.sqrt(Nt)
s0 = 100


def mc_sim():
  
  paths = []
  for _ in range(Np):
    
    path = []
    for i in range(Nt):
      next_val = mu + sigma * int(bool(random.uniform(-1, 1) > 0))
      path.append(next_val)

    paths.append(path)

  terminals = s0*numpy.exp(numpy.array([path[-1] for path in paths]))
  print(terminals[:10])
  print('mean =', terminals.mean(), 'std =', terminals.std())


mc_sim()
