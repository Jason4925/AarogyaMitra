from datetime import date, timedelta

# Source: Government of India, Ministry of Health & Family Welfare,
# National Immunization Schedule (UIP).
# See official source linked in the web page.
SCHEDULE = [
    ("Birth", 0, ["BCG", "OPV-0", "Hepatitis B birth dose"]),
    ("6 weeks", 42, ["OPV-1", "Pentavalent-1", "Rotavirus-1", "fIPV-1", "PCV-1"]),
    ("10 weeks", 70, ["OPV-2", "Pentavalent-2", "Rotavirus-2"]),
    ("14 weeks", 98, ["OPV-3", "Pentavalent-3", "fIPV-2", "Rotavirus-3", "PCV-2"]),
    ("9-12 months", 274, ["MR-1", "JE-1 where applicable", "PCV booster", "fIPV-3"]),
    ("16-24 months", 487, ["MR-2", "JE-2 where applicable", "DPT booster-1", "OPV booster"]),
    ("5-6 years", 1826, ["DPT booster-2"]),
    ("10 years", 3652, ["Td"]),
    ("16 years", 5844, ["Td"]),
]


def age_in_days(dob: date, today: date | None = None):
    today = today or date.today()
    return max(0, (today - dob).days)


def calculate_schedule(dob: date, today: date | None = None):
    today = today or date.today()
    age_days = age_in_days(dob, today)
    rows = []
    for label, due_days, vaccines in SCHEDULE:
        due_date = dob + timedelta(days=due_days)
        status = "Upcoming" if due_date > today else "Due / review"
        if abs(age_days - due_days) <= 30:
            status = "Current window"
        rows.append({
            "milestone": label,
            "due_date": due_date.isoformat(),
            "vaccines": vaccines,
            "status": status,
        })
    return rows


def next_milestone(dob: date, today: date | None = None):
    today = today or date.today()
    rows = calculate_schedule(dob, today)
    for row in rows:
        if row["due_date"] >= today.isoformat():
            return row
    return rows[-1] if rows else None
