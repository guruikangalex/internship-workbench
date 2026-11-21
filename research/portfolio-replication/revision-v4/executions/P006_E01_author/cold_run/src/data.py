"""Load the processed inputs exported into data/processed_inputs/.

CSVs are written with %.17g and must be read with float_precision='round_trip'
to recover the original float64 values bit-for-bit.
"""
import os
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(HERE, "data", "processed_inputs")


def load_panel(name):
    """Load a processed-input panel by name (e.g. 'factors_main', 'benchmark')."""
    path = os.path.join(DATA_DIR, f"{name}.csv")
    df = pd.read_csv(path, index_col=0, parse_dates=True,
                     float_precision="round_trip")
    df.index.name = "date"
    return df


def align_to_common_index(df1, df2):
    """Reindex both frames to the intersection of their indices."""
    common = df1.index.intersection(df2.index)
    return df1.loc[common], df2.loc[common]
