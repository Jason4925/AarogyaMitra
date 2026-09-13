"""Deterministic AI response safety/quality checks."""
import re

DIAGNOSIS_PATTERNS = [
    r"\byou (definitely|certainly) have\b",
    r"\bdiagnosis (is|:|for you)\b",
]
DOSAGE_PATTERNS = [
    r"\btake\s+\d+\s*(mg|ml|tablet|tablets|capsule|capsules)\b",
    r"\b\d+\s*(mg|ml)\s+(once|twice|daily)\b",
]
DANGEROUS_STOP_PATTERNS = [r"\bstop (your|taking)\b", r"\bdiscontinue (your|the)\b"]

def validate_response(text: str):
    raw = str(text or "").strip()
    low = raw.lower()
    issues = []
    if any(re.search(p, low) for p in DIAGNOSIS_PATTERNS): issues.append("diagnostic_certainty")
    if any(re.search(p, low) for p in DOSAGE_PATTERNS): issues.append("medication_dosage")
    if any(re.search(p, low) for p in DANGEROUS_STOP_PATTERNS): issues.append("treatment_change")
    if len(raw) > 5000: issues.append("excessive_length")
    safe = raw
    if issues:
        # Do not expose the unsafe draft. Replace it with a constrained safe response.
        safe = ("I can provide general health information, but I can't confirm a diagnosis or prescribe treatment. "
                "For medication changes, doses, or treatment decisions, please speak with a qualified healthcare professional. "
                "For severe or rapidly worsening symptoms, seek urgent medical care.")
    return {"text": safe, "issues": list(dict.fromkeys(issues)), "confidence": "high" if not issues else "low", "passed": not issues}
