import json
p='''PSANN_yfinance.ipynb'''
nb=json.load(open(p,'r',encoding='utf-8'))
changed=False
for i,cell in enumerate(nb.get('cells', [])):
    if cell.get('cell_type')=='code':
        src=''.join(cell.get('source', []))
        if 'hidden_layers = ' in src and 'PSANNRegressor(' in src and 'psann.fit' in src:
            src = src.replace('hidden_layers = 32','hidden_layers = 2')
            src = src.replace('lr=1e-5','lr=1e-3')
            src = src.replace(
                'psann.fit(train, y=None, hisso=True, hisso_window=episode_length, verbose=1, noisy=.005)',
                'psann.fit(train, y=None, hisso=True, hisso_window=episode_length, verbose=1, noisy=.005, hisso_trans_cost=float(trans_cost))'
            )
            if 'random_state=' not in src:
                src = src.replace('PSANNRegressor(', 'PSANNRegressor(random_state=0, ', 1)
            cell['source'] = src
            changed=True
        if 'psann_extras = PSANNRegressor(' in src and 'psann_extras.fit' in src:
            src = src.replace('lr=1e-5','lr=1e-3')
            if 'random_state=' not in src:
                src = src.replace('PSANNRegressor(', 'PSANNRegressor(random_state=0, ', 1)
            src = src.replace(
                'psann_extras.fit(train, y=None, hisso=True, hisso_window=episode_length, verbose=1, noisy=.005)',
                'psann_extras.fit(train, y=None, hisso=True, hisso_window=episode_length, verbose=1, noisy=.005, hisso_trans_cost=float(trans_cost))'
            )
            cell['source'] = src
            changed=True

if changed:
    with open(p,'w',encoding='utf-8') as f:
        json.dump(nb,f,ensure_ascii=False,indent=1)
    print('Notebook updated')
else:
    print('No changes made')
