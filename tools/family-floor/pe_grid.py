# State + local income tax for a married couple with two kids (ages 1 and 4), wages split evenly, 2026 rules, by AGI.
import json, sys, openpyxl
from policyengine_us import Simulation
N, LO, HI = 41, 60000, 900000
def sim(state, county=None):
    people={"you":{"age":{"2026":36}},"spouse":{"age":{"2026":35}},"k1":{"age":{"2026":1}},"k2":{"age":{"2026":4}}}
    hh={"members":list(people),"state_name":{"2026":state}}
    if county: hh["county_str"]={"2026":county}
    sit={"people":people,"families":{"f":{"members":list(people)}},"marital_units":{"m":{"members":["you","spouse"]},"a":{"members":["k1"]},"b":{"members":["k2"]}},
         "tax_units":{"t":{"members":list(people)}},"spm_units":{"s":{"members":list(people)}},"households":{"h":hh},
         "axes":[[{"name":"employment_income","count":N,"min":LO/2,"max":HI/2,"period":"2026","index":0},{"name":"employment_income","count":N,"min":LO/2,"max":HI/2,"period":"2026","index":1}]]}
    s=Simulation(situation=sit)
    return dict(agi=[float(x) for x in s.calculate("adjusted_gross_income","2026")],
                st=[float(x) for x in s.calculate("state_income_tax","2026")],
                loc=[float(x) for x in s.calculate("local_income_tax","2026")])
ST=['AL','AK','AZ','AR','CA','CO','CT','DE','DC','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']
out={'state':{}, 'county':{}}
for st in ST:
    out['state'][st]=sim(st); print(st, round(out['state'][st]['st'][10]), flush=True)
for key in sys.argv[1:]:   # county keys like MARION_COUNTY_IN
    st=key[-2:]
    try: out['county'][key]=sim(st,key); print(key, round(out['county'][key]['loc'][10]), flush=True)
    except Exception as e: print('ERR',key,str(e)[:100], flush=True)
json.dump(out,open('raw/pe_grid.json','w'))
