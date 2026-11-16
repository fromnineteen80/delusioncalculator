# Download every public input for the family floor model into raw/. Run from this folder: python3 fetch.py ../../index.html
import sys, os, re, json, csv, subprocess, zipfile, io, urllib.request
os.makedirs('raw', exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36', 'Accept-Language': 'en-US,en;q=0.9'}
def get(url, path=None):
    data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180).read()
    if path: open(path, 'wb').write(data)
    return data
# The calculator's own area list (codes and names), from the page's embedded D constant
page = open(sys.argv[1] if len(sys.argv) > 1 else '../../index.html', encoding='utf-8').read()
line = next(l for l in page.split('\n') if l.startswith('const D = '))
d = line[len('const D = '):].rstrip().rstrip(';'); open('raw/d.json', 'w').write(d[:d.rfind('}') + 1])
Z = 'https://files.zillowstatic.com/research/public_csvs/zhvi/'
get(Z + 'Metro_zhvi_bdrmcnt_4_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv', 'raw/z4.csv')
get(Z + 'State_zhvi_bdrmcnt_4_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv', 'raw/z4state.csv')
for t in ('b25103', 'b25077'):
    for y in (2026, 2025, 2024):
        try: get(f'https://www2.census.gov/programs-surveys/acs/summary_file/{y}/table-based-SF/data/5YRData/acsdt5y{y}-{t}.dat', f'raw/{t}.dat'); print(t, y); break
        except Exception: pass
for f, url in (('marpp', 'https://apps.bea.gov/regional/zip/MARPP.zip'), ('sarpp', 'https://apps.bea.gov/regional/zip/SARPP.zip')):
    zipfile.ZipFile(io.BytesIO(get(url))).extractall('raw/' + f)
# Rename the BEA files to stable names
for f, pat in (('marpp', 'MARPP_MSA_'), ('sarpp', 'SARPP_STATE_')):
    src = next(x for x in os.listdir('raw/' + f) if x.startswith(pat)); os.replace(f'raw/{f}/{src}', f'raw/{f}/{pat[:-1]}.csv')
for y in (2026, 2025):
    try: get(f'https://www2.census.gov/programs-surveys/popest/datasets/2020-{y}/metro/totals/cbsa-est{y}-alldata.csv', 'raw/cbsapop.csv'); print('pop', y); break
    except Exception: pass
get('https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2023/delineation-files/list1_2023.xlsx', 'raw/list1.xlsx')
get('https://www.eia.gov/electricity/sales_revenue_price/xls/table_5A.xlsx', 'raw/t5a.xlsx')
aaa = get('https://gasprices.aaa.com/state-gas-price-averages/').decode('utf-8', 'ignore')
gas = {n.strip(): float(p) for _, n, p in re.findall(r'state=(\w\w)">\s*([A-Za-z .]+?)\s*</a>\s*</td>\s*<td class="regular"[^>]*>\$([\d.]+)', aaa)}
import openpyxl
ws = openpyxl.load_workbook('raw/t5a.xlsx', data_only=True).active
elec = {' '.join(r[0].split()): float(r[-1]) for r in ws.iter_rows(values_only=True) if r and isinstance(r[0], str) and isinstance(r[-1], (int, float))}
assert len(gas) == 51 and 'U.S. Total' in elec, (len(gas), len(elec))
json.dump({'gas': gas, 'elec': elec, 'gas_date': re.search(r'Price as of ([\d/]+)', aaa).group(1)}, open('raw/gas_elec.json', 'w'))
# Child Care Aware price table (embedded chart data)
fl = get('https://flo.uri.sh/visualisation/28688197/embed').decode('utf-8', 'ignore')
txt = fl[fl.index('_Flourish_data = ') + 17:]; depth = 0
for i, ch in enumerate(txt):
    depth += ch == '{'; depth -= ch == '}'
    if depth == 0: txt = txt[:i + 1]; break
json.dump(json.loads(txt), open('raw/fl_28688197.json', 'w'))
# Metro -> principal county (for Indiana and Maryland county taxes in PolicyEngine)
ws = openpyxl.load_workbook('raw/list1.xlsx', data_only=True).active
cb = {}
for r in ws.iter_rows(values_only=True):
    if r[0] and str(r[0]).isdigit():
        cb.setdefault(r[0], {'title': r[3], 'kind': r[4], 'counties': []})['counties'].append(dict(county=r[7], state=r[8], central=r[11]))
AB = {'Maryland': 'MD', 'Indiana': 'IN'}; FIX = {'Indianapolis': 'MARION_COUNTY_IN', 'Baltimore': 'BALTIMORE_CITY_MD'}
keys = set()
for code, c in cb.items():
    city, sts = c['title'].split(', '); st1 = sts.split('-')[0]; first = city.split('-')[0]
    if st1 not in ('MD', 'IN'): continue
    if first in FIX: name = FIX[first]
    else:
        cs = [x for x in c['counties'] if AB.get(x['state']) == st1]; cen = [x for x in cs if x['central'] == 'Central'] or cs
        pick = next((x for x in cen if x['county'].split(' County')[0].split(' city')[0] in first), cen[0])
        name = re.sub(r'[^A-Z ]', '', pick['county'].upper().replace("'", '').replace('.', '')).strip().replace(' ', '_') + '_' + st1
    keys.add(name); c['pe_county'] = name
json.dump(cb, open('raw/cbsa_counties.json', 'w')); open('raw/pe_counties.txt', 'w').write(' '.join(sorted(keys)))
print('fetched', len(gas), 'gas states;', len(keys), 'counties')
