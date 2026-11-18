# Write budgets.json into the page as the FFD constant, with the top-200 flags and the population-weighted median.
import sys, csv, json, datetime
page_path = sys.argv[1] if len(sys.argv) > 1 else '../../index.html'
B = json.load(open('budgets.json')); I = json.load(open('inputs.json'))
pop = {r['CBSA']: int(r[[k for k in r if k.startswith('POPESTIMATE')][-1]]) for r in csv.DictReader(open('raw/cbsapop.csv', encoding='latin-1')) if r['LSAD'] in ('Metropolitan Statistical Area', 'Micropolitan Statistical Area')}
top = sorted([o for o in B if not o['micro']], key=lambda o: -pop.get(o['code'], 0))[:200]; ts = {o['code'] for o in top}
s = sorted((o['total'], pop.get(o['code'], 0)) for o in top); half = sum(w for _, w in s) / 2; acc = 0
for v, w in s:
    acc += w
    if acc >= half: wmed = v; break
KEYS = list(B[0]['lines'])
rows = [[o['total'], o['price'], int(o['code'] in ts), int(o['psrc'] != 'zillow_metro')] + [o['lines'][k] for k in KEYS] for o in B]
names = ['Poughkeepsie, NY' if o['name'] == 'Kiryas Joel, NY' else o['name'] for o in B]
n_est = sum(o['psrc'] != 'zillow_metro' for o in B)
ffd = dict(asof=datetime.date.today().isoformat(), wmed=wmed, zdate=I['zdate'], keys=KEYS, cols=['total', 'price', 'top200', 'priceEst'], rows=rows, names=names, t19=[o['total19'] for o in B], z19=I['z19'])
lines = open(page_path, encoding='utf-8').read().split('\n')
k = next(i for i, l in enumerate(lines) if l.startswith('const FFD = '))
lines[k] = 'const FFD = ' + json.dumps(ffd, separators=(',', ':')) + ';'
out = '\n'.join(lines)
import re
month = datetime.date.fromisoformat(I['zdate']).strftime('%B %Y')
out = re.sub(r'(Zillow Home Value Index, 4-bedroom homes, metro and state, )[A-Z][a-z]+ \d{4}', r'\g<1>' + month, out)
out = re.sub(r'for \d+ areas Zillow doesn’t cover', f'for {n_est} areas Zillow doesn’t cover', out)
open(page_path, 'w', encoding='utf-8').write(out)
print('packed', len(rows), 'areas; top-200 under $250k:', sum(o['total'] < 250000 for o in top), '; weighted median', wmed)
