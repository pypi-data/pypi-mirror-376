import json
nb=json.load(open('PSANN_yfinance.ipynb','r',encoding='utf-8'))
for i,cell in enumerate(nb.get('cells', [])):
    if cell.get('cell_type')=='code':
        src=''.join(cell.get('source', []))
        if 'PSANNRegressor(' in src or 'psann.fit(' in src:
            print('--- Cell', i, '---')
            print(src)
            print()
