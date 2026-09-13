import re
from datetime import datetime

HIGH_RED_FLAGS={'severe chest pain','difficulty breathing',"can't breathe",'cannot breathe','unconscious','loss of consciousness','not responding','stroke symptoms','signs of stroke','severe bleeding','heavy bleeding','uncontrolled bleeding','seizure','severe injury','fainting'}
SYMPTOM_ALIASES={'chest pain':'Chest pain','chest discomfort':'Chest discomfort','breathlessness':'Breathlessness','difficulty breathing':'Breathing difficulty','shortness of breath':'Breathlessness','dizziness':'Dizziness','fever':'Fever','headache':'Headache','nausea':'Nausea','vomiting':'Vomiting','diarrhea':'Diarrhoea','fatigue':'Fatigue','cough':'Cough','bleeding':'Bleeding','fainting':'Fainting','palpitations':'Palpitations'}
DURATION_SCORES={'Less than 24 hours':0,'1–3 days':0,'4–7 days':1,'1–2 weeks':1,'2–4 weeks':2,'1–3 months':2,'3+ months':2}

def _text_blob(payload):
    pieces=[str(payload.get('mainProblem',''))];pieces.extend(payload.get('symptoms',[]) or []);pieces.extend(payload.get('conditions',[]) or []);pieces.append(str(payload.get('medications','')));pieces.append(str(payload.get('allergies','')));pieces.append(str(payload.get('pregnancy','')))
    for k,v in (payload.get('follow_up_details') or {}).items():pieces.extend([str(k),str(v)])
    pieces.extend(payload.get('follow_up_answers',[]) or [])
    return ' '.join(pieces).lower()

def _match_flags(text):
    flags=[p.title() for p in HIGH_RED_FLAGS if p in text]
    if re.search(r'\b(severe|extreme|unbearable)\b',text) and ('pain' in text or 'bleed' in text):flags.append('Severe or uncontrolled symptom language')
    return list(dict.fromkeys(flags))

def _extract_symptoms(payload):
    found=[str(x) for x in payload.get('symptoms',[]) or [] if x]
    blob=_text_blob(payload)
    for key,label in SYMPTOM_ALIASES.items():
        if key in blob and label not in found:found.append(label)
    return list(dict.fromkeys(found))

def calculate_risk(payload):
    severity=int(payload.get('severity') or 0)
    age=int(payload.get('age') or 0) if str(payload.get('age','')).isdigit() else 0
    duration=str(payload.get('duration') or '')
    conditions=[str(x) for x in payload.get('conditions',[]) or [] if x]
    symptoms=_extract_symptoms(payload);text=_text_blob(payload);red_flags=_match_flags(text)
    answers=payload.get('follow_up_details') or {}
    factors=[];score=0
    if severity>=8:score+=4;factors.append(f'High severity reported ({severity}/10)')
    elif severity>=5:score+=2;factors.append(f'Moderate severity ({severity}/10)')
    elif severity:score+=1;factors.append(f'Mild severity ({severity}/10)')
    if duration in {'4–7 days','1–2 weeks','2–4 weeks','1–3 months','3+ months'}:score+=DURATION_SCORES.get(duration,1);factors.append('Symptoms lasting > 3 days')
    if len(symptoms)>=3:score+=1;factors.append(f'Multiple associated symptoms reported ({len(symptoms)})')
    if age>=65 or (age and age<5):score+=2;factors.append('Age group may require extra clinical caution')
    elif age>=45:score+=1;factors.append('Age may increase the importance of clinical review')
    if conditions:score+=min(2,len(conditions));factors.append('Relevant medical history reported')
    cl=[c.lower() for c in conditions]
    if 'heart disease' in cl and any(s.lower() in {'chest pain','chest discomfort','breathlessness'} for s in symptoms):score+=3;factors.append('Cardiac history with chest/breathing symptoms')
    for key,value in answers.items():
        v=str(value).lower()
        if any(w in v for w in ['yes','worse','present','during activity','increasing']):score+=2;factors.append(f'Follow-up indicates {key.replace("_"," ").lower()}')
        elif v in {'no','none','not present','stable','same'}:factors.append(f'No {key.replace("_"," ")} reported')
    if red_flags:score=max(score,10);level='High';priority='HIGH PRIORITY';action='Seek urgent professional medical evaluation immediately. If symptoms are severe or life-threatening, use local emergency services.'
    elif score>=7:level='High';priority='HIGH PRIORITY';action='Arrange prompt professional medical evaluation, especially if symptoms persist, worsen or new red flags appear.'
    elif score>=4:level='Moderate';priority='MODERATE PRIORITY';action='Consult a healthcare professional, particularly if symptoms persist, worsen or interfere with normal activities.'
    else:level='Low';priority='LOW PRIORITY';action='Monitor your symptoms and seek professional advice if they persist, worsen or new warning signs develop.'
    if not factors:factors.append('Limited information available from the assessment')
    return {'score':score,'level':level,'priority':priority,'risk_indicators':len(factors),'factors':list(dict.fromkeys(factors)),'red_flags':red_flags,'recommended_action':action,'symptoms_considered':symptoms,'calculated_at':datetime.now().isoformat(timespec='seconds')}

def follow_up_questions(payload):
    text=_text_blob(payload);questions=[]
    if not payload.get('duration'):questions.append({'id':'duration','question':'When did the symptoms start?','options':['Today','1–3 days','4–7 days','More than 1 week']})
    if 'chest' in text or 'heart' in text:questions += [{'id':'breathing_difficulty','question':'Is there breathing difficulty?','options':['Yes','No']},{'id':'dizziness','question':'Are you dizzy, faint or unusually weak?','options':['Yes','No']},{'id':'activity_trigger','question':'Does it worsen with activity or exertion?','options':['Yes','No','Not sure']},{'id':'cardiac_history','question':'Any known heart/cardiac history?','options':['Yes','No']}]
    elif 'fever' in text:questions += [{'id':'fever_temperature','question':'Do you know your highest temperature?','options':['Below 38°C','38–39°C','Above 39°C','Not measured']},{'id':'dehydration','question':'Any trouble keeping fluids down or signs of dehydration?','options':['Yes','No']}]
    elif 'headache' in text:questions += [{'id':'sudden_onset','question':'Did the headache start suddenly and become severe?','options':['Yes','No']},{'id':'vision_change','question':'Any new vision change, weakness or confusion?','options':['Yes','No']}]
    else:questions += [{'id':'worsening','question':'Are the symptoms getting worse?','options':['Yes','No','Same']},{'id':'daily_impact','question':'Are the symptoms affecting normal daily activities?','options':['Yes','No']}]
    return questions[:6]
