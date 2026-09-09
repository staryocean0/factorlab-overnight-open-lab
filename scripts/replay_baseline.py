#!/usr/bin/env python3
from pathlib import Path
import json
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
rec = json.loads((ROOT / "docs/governance/baseline_receipt.json").read_text())
panel = pd.read_parquet(ROOT / "data/development/csi1000_open_pit_panel.parquet")
cols = rec["features"]
train = panel.loc[panel["trading_day"] <= "2018-12-31"]
hold = panel.loc[panel["trading_day"] >= "2019-01-01"]
x_tr, y_tr = train[cols].apply(pd.to_numeric, errors="coerce"), pd.to_numeric(train["gap"], errors="coerce")
x_te, y_te = hold[cols].apply(pd.to_numeric, errors="coerce"), pd.to_numeric(hold["gap"], errors="coerce")
m_tr = x_tr.notna().all(axis=1) & y_tr.notna()
m_te = x_te.notna().all(axis=1) & y_te.notna()
pipe = Pipeline([("sc", StandardScaler()), ("m", Ridge(alpha=1.0))])
pipe.fit(x_tr.loc[m_tr], y_tr.loc[m_tr])
pred = pipe.predict(x_te.loc[m_te])
y = y_te.loc[m_te].to_numpy()
ic = float(np.corrcoef(y, pred)[0, 1])
print({"ic": ic, "receipt_ic": rec["metrics"]["ridge_ic"]})
assert abs(ic - rec["metrics"]["ridge_ic"]) < 1e-6
