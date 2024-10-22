



class Signal:
  def __init__(self, *args, weight=1, **kwargs):
    self.weight = weight


class SupportSignal(Signal):

  def calc_win_adv(self, build, strike):
    price = build.price_model.get_latest_price()
    return self.weight * self.max_proba * (price - self.support_price) / (price - strike)


class MovingAverageSupportSignal(SupportSignal):
  def __init__(self, n, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.n = n

  def calc_win_adv(self, build, strike):
    self.support_price = build.price_model.get_ma(self.n)
    return super().calc_win_adv(build, strike)


class SignalAggregator:
  
  def __init__(self, build, max_proba):
    self.build = build
    self.max_proba = max_proba
    self.signals = []

  def add_signal(self, signal):
    self.signals.append(signal)

  def calc_win_adv(self):
    adv = 0
    signal_max_proba = self.max_proba / len(self.signals)
    for signal in self.signals:
      adv += signal.calc_win_adv(self.build, )
    return adv

