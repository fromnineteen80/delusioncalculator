# Family-of-four budget model (same structure as the "Few Men Secure the Family of Four American Dream" deck), run for every area.
import json, numpy as np
I=json.load(open('inputs.json')); PE=json.load(open('raw/pe_grid.json'))
FED=[(24800,.10),(100800,.12),(211400,.22),(403550,.24),(512450,.32),(768700,.35),(1e12,.37)]
def prog(x,br):
    t=0;lo=0
    for hi,r in br:
        if x>lo: t+=(min(x,hi)-lo)*r
        lo=hi
    return t
# National items (deck sources): health out of pocket, student loans 2x$503/mo, tech, kids, emergency, Deloitte vacation, wellness, life insurance, NRF celebrations
OTHER=dict(health_oop=4029,loans=12072,tech=3000,kids_misc=8000,emergency=6000,vacation=4069,wellness=5000,life_ins=2000,celebrations=4120)
CAR_BASE=12863-2098-2595; GAL=2595/4.152; PREM=7471; RATE=0.072
def pi(loan): r=RATE/12; return loan*r/(1-(1+r)**-360)*12
US_ELEC=I['ELEC']['U.S. Total']
# Revolving credit card debt for a household: NY Fed Q2 2026 card balances over Census households ($9,370), scaled by the state's
# average card balance (Experian, March 2026) over the national $6,659. Payment: interest at the Fed G.19 rate (22.36%) plus 1% of the balance a month.
CCB={l.split('|')[0]:float(l.split('|')[1]) for l in open('static/cc_state.txt').read().splitlines() if l.strip() and not l.startswith('#')}
def card_pay(N): bal=9370*CCB[N]/6659; return bal*(0.2236/12+0.01)*12
# Local wage taxes at typical statewide rates (one city's rate, like NYC's or Philadelphia's, would not fit metro-wide home values)
DEFAULT={'OH':.02,'PA':.01,'KY':.01}
def grid(a):
    S=PE['state'][a['st']]; C=PE['county'].get(a['pe_county']) if a['pe_county'] else None
    return S, C
# 2019 comparison: the same family in the same month of 2019. Home at its 2019 Zillow value and the 2019 Freddie Mac average rate (3.9%);
# every other cost, and the tax brackets and limits, moved back by CPI-U (October 2019 257.346 over October 2026 337.511).
CPI19=257.346/337.511; RATE19=0.039
def run(a,y19=False):
    st=a['st']; N=I['NAME'][st]; price=a['price19'] if y19 else a['price']; loan=price*0.9
    if y19:   # housing in 2019 dollars, restated in today's dollars so the rest of the model runs unchanged, then scaled back at the end
        r=RATE19/12; pti=loan*r/(1-(1+r)**-360)*12/CPI19; price=price/CPI19; loan=loan/CPI19
    else: pti=pi(loan)
    pmi=loan*0.005; proptax=price*a['ptax']; ins=I['HINS'][N]; child=I['CC'][N]; g=a['rpp']/100
    loc=dict(groceries=311*52*g, dining=5974*g, clothing_household=4000*g, utilities=5062*I['ELEC'][N]/US_ELEC,
             car_own=2*CAR_BASE, auto_ins=24*I['AUTO'][N], gas=2*GAL*I['GAS'][N])
    cards=card_pay(N)
    spend=pti+pmi+proptax+ins+price*0.01+child+sum(OTHER.values())+sum(loc.values())+cards
    interest=loan*(RATE19 if y19 else RATE)*min(1,750000/loan); S,C=grid(a)
    wr=DEFAULT.get(st,0)   # metro-wide home values, so statewide-typical local taxes rather than one city's rate
    def takehome(G):
        kk=min(0.15*G,49000); agi=G-kk-PREM; wages=G-PREM
        ss=2*0.062*min(wages/2,184500); med=0.0145*wages+0.009*max(0,wages-250000)
        stt=float(np.interp(agi,S['agi'],S['st'])); lt=float(np.interp(agi,C['agi'],C['loc'])) if C else 0.0
        if st=='PA': stt=0.0307*wages
        sdi=0.013*wages if st=='CA' else 0
        lt+=wr*wages
        if st=='MD': lt+=0.03*max(0,agi-4*(3200 if agi<=150000 else 1600 if agi<=175000 else 800 if agi<=200000 else 0))   # Maryland county income tax, about 3% statewide
        if a['name']=='Portland, OR': lt+=0.01*max(0,agi-200000)   # Metro supportive housing tax, region-wide
        salt_cap=40400 if agi<=505000 else max(10000,40400-0.3*(agi-505000))
        salt=min(proptax+stt+lt,salt_cap)
        ti=max(0,agi-max(interest+salt,32200))
        ctc=max(0,4400-50*max(0,-(-(agi-400000)//1000)))   # $50 per $1,000 or fraction over $400k
        fed=max(0,prog(ti,FED)-ctc)
        return G-kk-PREM-fed-stt-sdi-lt-ss-med, dict(fed=fed,state=stt+sdi,local=lt,fica=ss+med,k401=kk)
    lo,hi=60000,2500000
    for _ in range(60):
        mid=(lo+hi)/2
        if takehome(mid)[0]>=spend: hi=mid
        else: lo=mid
    th,tx=takehome(hi)
    L=dict(mortgage=pti+pmi,proptax=proptax,home_ins=ins,upkeep=price*0.01,utilities=loc['utilities'],tech=OTHER['tech'],
      groceries=loc['groceries'],dining=loc['dining'],child=child,kids_misc=OTHER['kids_misc'],clothing_household=loc['clothing_household'],
      health=PREM+OTHER['health_oop'],life_ins=OTHER['life_ins'],wellness=OTHER['wellness'],car_own=loc['car_own'],auto_ins=loc['auto_ins'],gas=loc['gas'],
      loans=OTHER['loans'],cards=cards,vacation=OTHER['vacation'],celebrations=OTHER['celebrations'],retire=tx['k401'],emergency=OTHER['emergency'],
      fed_tax=tx['fed'],state_tax=tx['state'],local_tax=tx['local'],fica=tx['fica'])
    if y19: L={k:v*CPI19 for k,v in L.items()}
    L={k:round(v) for k,v in L.items()}
    return sum(L.values()), L
if __name__=='__main__':
    out=[]
    for a in I['areas']:
        t,L=run(a); t19,L19=run(a,True); out.append(dict(a,total=t,lines=L,total19=t19,mort19=L19['mortgage']))
    json.dump(out,open('budgets.json','w'))
    by={o['name']:o for o in out}
    deck={'Huntsville, AL':251729,'Tyler, TX':270832,'Columbus, OH':286381,'Jackson, MS':202633,'Detroit, MI':237086,'Dallas, TX':296533,'Chicago, IL':289339,'Atlanta, GA':300319,'Denver, CO':345640,'Washington, DC':394586,'Boston, MA':416384,'New York, NY':434907,'Los Angeles, CA':446844,'San Francisco, CA':544426,'Santa Cruz, CA':619435,'Milwaukee, WI':249602,'Houston, TX':259483,'Philadelphia, PA':282787}
    for k,v in deck.items():
        o=by[k]; print(f"{k:20} deck {v:>8,}  new {o['total']:>8,}  {o['total']-v:+8,}  price {o['price']:>9,} {o['psrc'][:6]}")
    ts=sorted(o['total'] for o in out); print('min',ts[0],'median',ts[len(ts)//2],'max',ts[-1],'under250k',sum(t<250000 for t in ts))
