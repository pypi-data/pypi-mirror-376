import json, io, sys
p = 'PSANN_yfinance.ipynb'
nb = json.load(open(p,'r',encoding='utf-8'))
for i,cell in enumerate(nb.get('cells', [])):
    if cell.get('cell_type')=='code':
        src = ''.join(cell.get('source', []))
        hdr = src.strip().splitlines()[:1]
        print(f'--- Cell {i} ---', hdr[0] if hdr else '')
        if any(k in src for k in ['PSANNRegressor','PredictiveExtrasTrainer','portfolio_log_return_reward','hisso','buy','hold','equity_curve']):
            print(src)
            print('')
