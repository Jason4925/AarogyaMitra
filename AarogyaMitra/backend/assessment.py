import json, re
from langchain_groq import ChatGroq
from .config import GROQ_API_KEY
from .risk_engine import calculate_risk

REPORT_PROMPT='''You are the assessment-report engine for AarogyaMitra. Return ONLY valid JSON with keys: problem_summary, key_findings, next_steps, allopathy{overview,medicine_information,investigations}, homeopathy{overview,remedy_information,safety_note}, ayurveda{overview,lifestyle_information,safety_note}, red_flags. Keep medicine information educational only, no dosage or individualized prescription. Do not diagnose with certainty. Severe symptoms must be reflected in red_flags and next_steps. If a preferred language is supplied, write the human-readable report fields in that language while preserving the JSON keys.'''

def _fallback(payload,risk):
    symptoms=payload.get('symptoms') or []
    return {'problem_summary': f"Assessment information was provided for: {payload.get('mainProblem') or 'the reported health concern'}.", 'key_findings': symptoms or ['Main concern recorded'], 'next_steps': risk.get('recommended_action','Discuss persistent or worsening symptoms with a qualified healthcare professional.'), 'allopathy': {'overview':'Informational overview only; the cause should be assessed by a qualified clinician.','medicine_information':['Medication choice depends on the underlying cause, age, allergies, existing conditions and other factors; discuss appropriate options with a clinician or pharmacist.'],'investigations':['A clinician can decide whether an examination or investigations are appropriate based on the symptoms.']}, 'homeopathy': {'overview':'A complementary perspective only; evidence for homeopathy varies and it should not replace necessary medical care.','remedy_information':['Any remedy discussion should be reviewed with a qualified practitioner and should not delay appropriate care.'],'safety_note':'Do not replace urgent or prescribed care with homeopathic products.'}, 'ayurveda': {'overview':'Traditional lifestyle perspective only; use qualified practitioners for individualized advice.','lifestyle_information':['Maintain appropriate hydration, nutrition, sleep and activity as tolerated.'],'safety_note':'Tell your clinician about herbs or traditional products, especially when taking medicines.'}, 'red_flags': risk.get('red_flags',[])}

def _clean_human(v, fallback=''):
    if v is None:
        return fallback
    if isinstance(v, str):
        t=v.strip()
        if not t: return fallback
        if (t.startswith('[') and t.endswith(']')) or (t.startswith('{') and t.endswith('}')):
            try:
                return _clean_human(json.loads(t), fallback)
            except Exception:
                pass
        return t
    if isinstance(v, list):
        return ' · '.join(_clean_human(x, '') for x in v if _clean_human(x, '')) or fallback
    if isinstance(v, dict):
        parts=[]
        for k,val in v.items():
            hv=_clean_human(val,'')
            if hv: parts.append(f"{str(k).replace('_',' ').title()}: {hv}")
        return ' · '.join(parts) or fallback
    return str(v)

def _clean_list(v, fallback):
    if isinstance(v,list):
        out=[]
        for x in v:
            if isinstance(x,dict):
                parts=[]
                for k,val in x.items():
                    if val not in (None,'',[]): parts.append(f'{str(k).replace("_"," ").title()}: {val}')
                if parts: out.append(' · '.join(parts))
            elif str(x).strip(): out.append(str(x))
        return out or fallback
    if isinstance(v,str) and v.strip(): return [v.strip()]
    return fallback

def normalize_report(raw,payload,risk):
    base=_fallback(payload,risk)
    r=raw if isinstance(raw,dict) else {}
    out={'problem_summary':_clean_human(r.get('problem_summary'),base['problem_summary']), 'key_findings':_clean_list(r.get('key_findings'),base['key_findings']), 'next_steps':_clean_human(r.get('next_steps'),base['next_steps']), 'allopathy':{},'homeopathy':{},'ayurveda':{}, 'red_flags':_clean_list(r.get('red_flags'),base['red_flags'])}
    for section in ('allopathy','homeopathy','ayurveda'):
        src=r.get(section) if isinstance(r.get(section),dict) else {}
        out[section]=dict(base[section]); out[section].update({k:src[k] for k in base[section] if src.get(k) not in (None,'',[])})
    out['allopathy']['medicine_information']=_clean_list(out['allopathy'].get('medicine_information'),base['allopathy']['medicine_information'])
    out['allopathy']['investigations']=_clean_list(out['allopathy'].get('investigations'),base['allopathy']['investigations'])
    out['homeopathy']['remedy_information']=_clean_list(out['homeopathy'].get('remedy_information'),base['homeopathy']['remedy_information'])
    out['ayurveda']['lifestyle_information']=_clean_list(out['ayurveda'].get('lifestyle_information'),base['ayurveda']['lifestyle_information'])
    return out

def generate_report(payload):
    risk=calculate_risk(payload)
    raw=None
    if GROQ_API_KEY and not GROQ_API_KEY.startswith('YOUR_'):
        try:
            llm=ChatGroq(model='openai/gpt-oss-120b',temperature=0.2,api_key=GROQ_API_KEY)
            response=llm.invoke([{'role':'system','content':REPORT_PROMPT},{'role':'user','content':json.dumps(payload,ensure_ascii=False)}])
            content=str(response.content).strip(); content=re.sub(r'^```json\s*','',content,flags=re.I); content=re.sub(r'\s*```$','',content)
            raw=json.loads(content)
        except Exception as e:
            print('REPORT AI FALLBACK:',repr(e))
    return normalize_report(raw,payload,risk),risk
