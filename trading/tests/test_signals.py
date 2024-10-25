import pytest

import config

from datetime import datetime
from unittest.mock import patch

from strategy.builds import SellSimplePutBuild
from signals import (
  DeltaSignal,
  MovingAverageSupportSignal,
  FiftyTwoLowSupportSignal,
  MoveSignal,
)


class TestSignalsComputeEdge:

  @pytest.fixture
  def build_ddog(self):
    """
    DDOG
    2024-10-23
    121.52, -2.49%
    52low = 77.81
    52high = 138.61
    50ma = 117.17
    200ma = 121.50
    """

    build = SellSimplePutBuild('DDOG', config.MY_WIN_PROBA)
    max_proba = 1 - config.MY_WIN_PROBA
    return build

  @pytest.fixture
  def build_nvda(self):
    """
    FIXME
    NVDA
    2024-10-23
    139.56, 0%
    52low = 
    52high = 
    50ma = 
    200ma = 
    """

    build = SellSimplePutBuild('NVDA', 0.85)
    max_proba = 1 - config.MY_WIN_PROBA
    return build

  @pytest.fixture
  def build_okta(self):
    """
    OKTA
    2024-10-23
    72.16, -2.53%
    52low = 65.74
    52high = 114.50
    50ma = 79.57 (price is below)
    200ma = 90.15 (price is below)
    """

    build = SellSimplePutBuild('OKTA', config.MY_WIN_PROBA)
    max_proba = 1 - config.MY_WIN_PROBA
    return build

  def test_200ma_nonzero(self, build_ddog, snapshot):
    build_ddog.add_signals([
      MovingAverageSupportSignal(200, weight=0.5)
    ])
    result_df = build_ddog.create_snapshot().df
    result = result_df.iloc[0]['200_ma_edge'].round(4)

    assert result_df.to_csv() == snapshot
    assert result == round(0.0001, 4)

  def test_200ma_zero(self, build_nvda, snapshot):
    build_nvda.add_signals([
      MovingAverageSupportSignal(200, weight=0.5)
    ])
    result_df = build_nvda.create_snapshot().df
    result = result_df.iloc[0]['200_ma_edge'].round(4)

    assert result_df.to_csv() == snapshot
    assert result == 0

  # Okta daily move actually slightly positive.
  @patch('strategy.builds.SellSimplePutBuild.validate_conditions', lambda self: True)
  def test_52_low_nonzero(self, build_okta, snapshot):
    build_okta.add_signals([
      FiftyTwoLowSupportSignal(weight=0.5)
    ])

    result_df = build_okta.create_snapshot().df
    result = result_df.iloc[0]['52_low_edge'].round(4)

    assert result_df.to_csv() == snapshot
    assert result == 0.0448

  def test_52_low_zero(self, build_ddog, snapshot):
    build_ddog.add_signals([
      FiftyTwoLowSupportSignal()
    ])
    result_df = build_ddog.create_snapshot().df
    result = result_df.iloc[0]['52_low_edge'].round(4)

    assert result_df.to_csv() == snapshot
    assert result == 0

  def test_delta_zero(self, build_ddog, snapshot):
    build_ddog.add_signals([
      DeltaSignal(),
    ])
    result_df = build_ddog.create_snapshot().df
    result = result_df.iloc[0]['delta_edge'].round(4)

    assert result_df.to_csv() == snapshot
    assert result == 0

  def test_delta_nonzero(self, build_nvda, snapshot):
    build_nvda.add_signals([
      DeltaSignal(),
    ])
    result_df = build_nvda.create_snapshot().df
    result1 = result_df.iloc[3]['delta_edge'].round(4)  # |delta| = 0.2271
    result2 = result_df.iloc[1]['delta_edge'].round(4)  # |delta| = 0.2968

    assert result_df.to_csv() == snapshot
    assert result1 == 0.0742
    assert result2 == 0.0509

  def test_move_zero(self, build_nvda, snapshot):
    build = build_nvda
    build.add_signals([
      MoveSignal(),
    ])
    result_df = build.create_snapshot().df
    result1 = result_df.iloc[0]['move_edge'].round(4)

    assert result_df.to_csv() == snapshot
    assert result1 == 0.0003

  def test_move_nonzero(self, build_ddog, snapshot):
    build = build_ddog
    build.add_signals([
      MoveSignal(),
    ])
    result_df = build.create_snapshot().df
    result1 = result_df.iloc[0]['move_edge'].round(4)

    assert result_df.to_csv() == snapshot
    assert result1 == 0.001

  def test_many_signals(self, build_nvda, snapshot):
    signals = [
      MoveSignal(),
      DeltaSignal(),
      FiftyTwoLowSupportSignal(),
      MovingAverageSupportSignal(200, weight=0.5),
    ]
    build_nvda.add_signals(signals)

    result_df = build_nvda.create_snapshot().df
    result1 = result_df.loc[3, [str(x) for x in signals]].sum().round(4)

    assert result_df.to_csv() == snapshot
    assert result1 == 0.0186  # Only DeltaSignal is nonzero
