import sys, pathlib, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / 'src'))
from psann import PSANNRegressor

np.random.seed(0)
T,M=40,2
prices=np.cumprod(1+0.001*np.random.randn(T,M),axis=0).astype(np.float32)
model=PSANNRegressor(hidden_layers=1, hidden_width=8, epochs=1, extras=1, activation_type='relu')
model.fit(prices, y=None, hisso=True, hisso_window=8, hisso_trans_cost=1e-3, noisy=0.01, verbose=0)
print('trained; hisso cfg:', getattr(model,'_hisso_cfg_',None))
print('val reward:', model.hisso_evaluate_reward(prices, n_batches=2))
alloc, ex = model.hisso_infer_series(prices)
print('alloc shape:', alloc.shape, 'extras shape:', ex.shape)
