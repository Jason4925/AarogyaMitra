from datetime import date

PUBLIC_HEALTH_CONTENT=[
 {"category":"Prevention","title":"Prevent mosquito-borne illness","text":"Remove standing water, use mosquito protection, and seek professional care for persistent high fever or warning signs.","action":"Prevention","source":{"name":"WHO","url":"https://www.who.int/health-topics/dengue-and-severe-dengue"}},
 {"category":"Nutrition","title":"Build simple healthy meals","text":"Aim for varied meals with vegetables or fruit, protein sources, whole grains where available, and safe drinking water.","action":"Healthy living"},
 {"category":"Respiratory","title":"Reduce respiratory infection spread","text":"Improve ventilation, stay home when unwell, wash hands regularly, and follow local public-health guidance.","action":"Prevention"},
 {"category":"Vaccination","title":"Keep vaccinations up to date","text":"Check the appropriate national or local immunization schedule and confirm due doses with an authorized health facility.","action":"Vaccination","source":{"name":"MoHFW, Government of India","url":"https://www.mohfw.gov.in/pdf/NationalImmunizationSchedule.pdf"}},
 {"category":"Emergency","title":"Know when symptoms are urgent","text":"Severe breathing difficulty, loss of consciousness, major bleeding, severe chest pain, or stroke-like symptoms need immediate emergency medical attention.","action":"Urgent care"},
 {"category":"General","title":"Track changes in your health","text":"Recording symptom duration, severity, medicines and changes over time can make conversations with clinicians more useful.","action":"Health tracking"},
]

def get_daily_awareness(limit=6):
    start=date.today().toordinal()%len(PUBLIC_HEALTH_CONTENT);return [PUBLIC_HEALTH_CONTENT[(start+i)%len(PUBLIC_HEALTH_CONTENT)] for i in range(min(limit,len(PUBLIC_HEALTH_CONTENT)))]

TRANSLATIONS={
 'Hindi':{
  'Prevent mosquito-borne illness':'मच्छर से होने वाली बीमारियों से बचाव','Track changes in your health':'अपने स्वास्थ्य में बदलाव दर्ज करें','Know when symptoms are urgent':'जानें कब लक्षण तुरंत देखभाल मांगते हैं','Keep vaccinations up to date':'टीकाकरण समय पर कराएं'
 },
 'Marathi':{
  'Prevent mosquito-borne illness':'डासांपासून होणाऱ्या आजारांपासून बचाव','Track changes in your health':'आरोग्यातील बदल नोंदवा','Know when symptoms are urgent':'लक्षणे तातडीची कधी आहेत ते ओळखा','Keep vaccinations up to date':'लसीकरण वेळेवर पूर्ण करा'
 }
}

def get_public_health(language='English'):
    items=[]
    for item in PUBLIC_HEALTH_CONTENT:
        x=dict(item); x['title']=TRANSLATIONS.get(language,{}).get(item['title'],item['title']); items.append(x)
    return {"updated":str(date.today()),"language":language,"categories":sorted({x["category"] for x in items}),"items":items}
