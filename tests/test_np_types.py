import numpy as np
import pandas as pd
import datetime
import math

print(f"np.int64 is int: {isinstance(np.int64(5), int)}")
print(f"np.float64 is float: {isinstance(np.float64(5.5), float)}")

def safe_float(v):
    if pd.isna(v): return None
    try:
        return float(v)
    except:
        return None

def safe_int(v):
    if pd.isna(v): return None
    try:
        return int(v)
    except:
        return None

print(f"np.int64 via float(): {type(safe_float(np.int64(5)))}")
print(f"np.float64 via float(): {type(safe_float(np.float64(5.5)))}")
print(f"np.int64 via int(): {type(safe_int(np.int64(5)))}")

print(f"float(nan): {safe_float(math.nan)}")
print(f"float(np.nan): {safe_float(np.nan)}")
