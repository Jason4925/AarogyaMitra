from __future__ import annotations
from datetime import datetime


def build_care_plan(payload: dict, risk: dict, pathway: dict) -> dict:
    level = str(risk.get('level') or 'Low').title()
    severity = payload.get('severity') or risk.get('severity') or ''
    steps = []
    if level in {'High', 'Critical'}:
        steps = [
            {'when': 'Now', 'title': 'Seek urgent professional evaluation', 'detail': 'Use emergency services for life-threatening symptoms; do not delay care for additional AI questions.'},
            {'when': 'At care', 'title': 'Share your AarogyaMitra handoff', 'detail': 'Take the structured summary, symptom timing, severity, history, medicines and red-flag checks.'},
            {'when': 'After evaluation', 'title': 'Follow the clinician plan', 'detail': 'Medication, investigations and treatment changes should be decided by a qualified clinician.'},
            {'when': 'Follow-up', 'title': 'Record whether symptoms improve or worsen', 'detail': 'Use the follow-up check-in so the next risk assessment can consider the trend.'},
        ]
    elif level == 'Moderate':
        steps = [
            {'when': 'Today / soon', 'title': 'Arrange professional assessment', 'detail': 'Persistent or concerning symptoms should be reviewed by a qualified healthcare professional.'},
            {'when': 'Before visit', 'title': 'Prepare your summary', 'detail': 'Bring your symptom description, duration, severity, relevant history, medicines and allergies.'},
            {'when': 'During care', 'title': 'Discuss investigations and treatment', 'detail': 'A clinician can decide whether tests or treatment are appropriate for your situation.'},
            {'when': 'Next check-in', 'title': 'Compare your symptoms', 'detail': 'Record better, same or worse and the new severity score.'},
        ]
    else:
        steps = [
            {'when': 'Now', 'title': 'Monitor symptoms', 'detail': 'Track duration, severity and new warning signs.'},
            {'when': 'Today', 'title': 'Use relevant preventive guidance', 'detail': 'Choose practical self-care and public-health advice appropriate to your concern.'},
            {'when': 'If persistent', 'title': 'Arrange routine professional care', 'detail': 'Seek a qualified clinician if symptoms persist, worsen or remain unexplained.'},
            {'when': 'Follow-up', 'title': 'Check your trend', 'detail': 'Use the follow-up check-in to record whether you are better, the same or worse.'},
        ]
    return {
        'generated_at': datetime.utcnow().isoformat(timespec='seconds'),
        'risk_level': level,
        'risk_score': int(risk.get('score') or 0),
        'severity': severity,
        'steps': steps,
        'pathway_mode': pathway.get('routing_mode', 'routine-monitoring'),
        'safety_note': 'This care plan is decision-support guidance, not a diagnosis or prescription.'
    }
