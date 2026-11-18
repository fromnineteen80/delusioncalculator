import csv, json, re
D=json.load(open('raw/d.json'))
codes=D['codes']; cbsa=D['cbsa']
FIPS={'01':'AL','02':'AK','04':'AZ','05':'AR','06':'CA','08':'CO','09':'CT','10':'DE','11':'DC','12':'FL','13':'GA','15':'HI','16':'ID','17':'IL','18':'IN','19':'IA','20':'KS','21':'KY','22':'LA','23':'ME','24':'MD','25':'MA','26':'MI','27':'MN','28':'MS','29':'MO','30':'MT','31':'NE','32':'NV','33':'NH','34':'NJ','35':'NM','36':'NY','37':'NC','38':'ND','39':'OH','40':'OK','41':'OR','42':'PA','44':'RI','45':'SC','46':'SD','47':'TN','48':'TX','49':'UT','50':'VT','51':'VA','53':'WA','54':'WV','55':'WI','56':'WY'}
NAME={'AL':'Alabama','AK':'Alaska','AZ':'Arizona','AR':'Arkansas','CA':'California','CO':'Colorado','CT':'Connecticut','DE':'Delaware','DC':'District of Columbia','FL':'Florida','GA':'Georgia','HI':'Hawaii','ID':'Idaho','IL':'Illinois','IN':'Indiana','IA':'Iowa','KS':'Kansas','KY':'Kentucky','LA':'Louisiana','ME':'Maine','MD':'Maryland','MA':'Massachusetts','MI':'Michigan','MN':'Minnesota','MS':'Mississippi','MO':'Missouri','MT':'Montana','NE':'Nebraska','NV':'Nevada','NH':'New Hampshire','NJ':'New Jersey','NM':'New Mexico','NY':'New York','NC':'North Carolina','ND':'North Dakota','OH':'Ohio','OK':'Oklahoma','OR':'Oregon','PA':'Pennsylvania','RI':'Rhode Island','SC':'South Carolina','SD':'South Dakota','TN':'Tennessee','TX':'Texas','UT':'Utah','VT':'Vermont','VA':'Virginia','WA':'Washington','WV':'West Virginia','WI':'Wisconsin','WY':'Wyoming'}
def rd(f): return {l.split('|')[0]:float(l.split('|')[1].replace('$','').replace(',','')) for l in open(f).read().splitlines() if l.strip() and not l.startswith('#')}
cbc=json.load(open('raw/cbsa_counties.json'))
# Zillow 4-bedroom typical value, latest month
def zread(f,col):
    r=list(csv.reader(open(f))); h=r[0]; i=h.index(col)
    return {x[i]:float(x[-1]) for x in r[1:] if x[-1]}, h[-1]
zmet,zdate=zread('raw/z4.csv','RegionName'); zst,_=zread('raw/z4state.csv','RegionName')
# Same month in 2019, for the "since 2019" comparison
Z19=str(int(zdate[:4])-7)+zdate[4:7]
def zread19(f,col):
    r=list(csv.reader(open(f))); h=r[0]; i=h.index(col); j=next(k for k,x in enumerate(h) if x.startswith(Z19))
    return {x[i]:float(x[j]) for x in r[1:] if x[j]}
zmet19=zread19('raw/z4.csv','RegionName'); zst19=zread19('raw/z4state.csv','RegionName')
# ACS 2020-2024 medians
def acs(f):
    o={}
    for l in open(f).read().splitlines()[1:]:
        p=l.split('|'); o[p[0]]=p[1]
    return o
tax=acs('raw/b25103.dat'); val=acs('raw/b25077.dat')
def num(x):
    try: v=float(x); return v if v>0 else None
    except: return None
# BEA goods RPP 2024
rpp_m={}; rpp_s={}
for f,dst in [('raw/marpp/MARPP_MSA.csv',rpp_m),('raw/sarpp/SARPP_STATE.csv',rpp_s)]:
    for r in csv.reader(open(f,encoding='latin-1')):
        if len(r)>8 and 'Goods' in r[6]: dst[r[0].strip().strip('"')]=float(r[-1])
# state tables
ge=json.load(open('raw/gas_elec.json')); GAS=ge['gas']; ELEC=ge['elec']
AUTO=rd('static/auto_ins_monthly.txt')
HINS=rd('static/home_ins_annual.txt')
cc={}
for r in json.load(open('raw/fl_28688197.json'))['rows']:
    c=r['columns']; cc[c[0].rstrip('*')]=c[4]
CC_NOTE={}
for st,v in {'Colorado':35779,'South Carolina':20166,'District of Columbia':47174}.items():
    if not cc.get(st): cc[st]=v; CC_NOTE[st]='2024'
vals=sorted(v for v in cc.values() if v)
if not cc.get('New Mexico'): cc['New Mexico']=vals[len(vals)//2]; CC_NOTE['New Mexico']='median of states'
ZALIAS={'30500':'California, MD'}   # Lexington Park, MD is still listed under its old name
areas=[]
miss={'zillow':0}
for code,c in zip(codes,cbsa):
    st=FIPS[c['s']]; nm=c['n'].replace(' (micro)','')
    title=cbc[code]['title']; cities=re.split(r'[-/]',title.split(', ')[0]); st1=title.split(', ')[1].split('-')[0]
    key=f'{cities[0]}, {st1}'
    # Zillow names a metro by one of its principal cities; try each, plus known old names
    p=None; psrc='zillow_metro'; p19=None
    for nm in [ZALIAS.get(code)]+[f'{c}, {st1}' for c in cities]:
        if nm and nm in zmet: p=zmet[nm]; p19=zmet19.get(nm); break
    tx=num(tax.get('310M700US'+code)); mv=num(val.get('310M700US'+code))
    if p is None:
        sv=num(val.get('0400000US'+[k for k,v in FIPS.items() if v==st1][0]))
        p=zst.get(NAME[st1])*(mv/sv if mv and sv else 1); psrc='zillow_state_scaled'; miss['zillow']+=1
    if p19 is None: p19=p*zst19[NAME[st1]]/zst[NAME[st1]]   # no 2019 metro value: move with the state
    ptax=tx/mv if tx and mv else None
    g=rpp_m.get(code); gsrc='msa'
    if g is None: g=rpp_s[[k for k,v in FIPS.items() if v==st1][0]+'000']; gsrc='state'
    areas.append(dict(code=code,name=key,micro=' (micro)' in c['n'],st=st1,lat=c['la'],lon=c['lo'],price=round(p),price19=round(p19),psrc=psrc,ptax=ptax,rpp=g,rsrc=gsrc,pe_county=cbc[code].get('pe_county')))
print(len(areas), miss, 'zillow month', zdate, 'no ptax', sum(a['ptax'] is None for a in areas))
json.dump(dict(areas=areas,GAS=GAS,ELEC=ELEC,AUTO=AUTO,HINS=HINS,CC=cc,CC_NOTE=CC_NOTE,zdate=zdate,z19=Z19,NAME=NAME),open('inputs.json','w'))
