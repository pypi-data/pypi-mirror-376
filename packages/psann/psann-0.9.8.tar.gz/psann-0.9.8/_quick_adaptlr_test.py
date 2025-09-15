import sys, pathlib, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / 'src'))
from psann import PSANNRegressor

np.random.seed(0)
T,M=80,2
prices=np.cumprod(1+0.001*np.random.randn(T,M),axis=0).astype(np.float32)
model=PSANNRegressor(hidden_layers=1, hidden_width=16, epochs=5, extras=1, activation_type='relu')
model.fit(prices, y=None, hisso=True, hisso_window=8, hisso_trans_cost=1e-3, noisy=0.01, verbose=0, lr_max=1e-2, lr_min=1e-4)
print('trained hisso OK, history len:', len(getattr(model,'history_',[])))
alloc, ex = model.hisso_infer_series(prices)
print('alloc/ex:', alloc.shape, ex.shape)

# Supervised branch sanity
X = np.random.randn(200, 4).astype(np.float32)
y = (X.sum(axis=1, keepdims=True) + 0.1*np.random.randn(200,1)).astype(np.float32)
reg = PSANNRegressor(hidden_layers=1, hidden_width=16, epochs=5, lr=1e-3)
reg.fit(X, y, verbose=0, lr_max=1e-2, lr_min=1e-4)
print('supervised OK')
