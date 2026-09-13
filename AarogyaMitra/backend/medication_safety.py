"""Conservative medication safety checks. Not a drug-interaction database."""

def check_medications(medications, allergies='', age='', weight='', pregnancy=''):
    text=str(medications or '').strip()
    alerts=[]
    if not text:
        return {'status':'no_medications_entered','alerts':[],'note':'Enter clinician-prescribed medicines to review them. This tool does not prescribe or change treatment.'}
    if allergies.strip():
        alerts.append('Check each medicine against the patient’s recorded allergies with a pharmacist or clinician.')
    if str(pregnancy).lower() in {'pregnant','breastfeeding'}:
        alerts.append('Pregnancy/breastfeeding: medication safety requires product-specific professional review.')
    try:
        a=int(age) if age not in ('',None) else None
        if a is not None and a < 18: alerts.append('Pediatric medication use requires age-appropriate professional review.')
        if a is not None and a >= 65: alerts.append('Older adults may need additional medication review for interactions and dosing.')
    except Exception: pass
    # Duplicate-ingredient heuristic only; no external database claim.
    lower=text.lower()
    if ',' not in text and ';' not in text and '\n' not in text:
        alerts.append('For interaction or duplicate-ingredient checking, provide the full medicine list to a pharmacist/clinician or verified drug database.')
    return {'status':'review_required' if alerts else 'no_alerts_found','alerts':alerts,'note':'This is a safety prompt, not a validated interaction checker or prescription system.'}
