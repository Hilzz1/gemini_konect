import pandas as pd
import numpy as np
import pytest

from src.force_indicators import elder_force_index, force_slope, signal


@pytest.fixture
def sample_df():
    n   = 50
    rng = np.random.default_rng(42)
    closes  = 30000 + np.cumsum(rng.normal(0, 100, n))
    volumes = rng.uniform(100, 500, n)
    return pd.DataFrame({"close": closes, "volume": volumes})


def test_force_length(sample_df):
    f = elder_force_index(sample_df)
    assert len(f) == len(sample_df)


def test_force_slope_type(sample_df):
    f = elder_force_index(sample_df)
    assert isinstance(force_slope(f), float)


def test_signal_valid(sample_df):
    f = elder_force_index(sample_df)
    s = signal(f)
    assert s in {"BULLISH_PRESSURE", "BEARISH_PRESSURE", "BULL_FADING", "BEAR_FADING"}


def test_insufficient_data():
    tiny = pd.DataFrame({"close": [100.0, 101.0], "volume": [10.0, 12.0]})
    f    = elder_force_index(tiny, period=13)
    assert force_slope(f, lookback=10) == 0.0
