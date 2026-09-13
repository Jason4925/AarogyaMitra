import ollama
import googlemaps
from twilio.rest import Client
from langchain.tools import tool

from .config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_VOICE_FROM,
    TWILIO_EMERGENCY_CONTACT,
    GOOGLE_MAPS_API_KEY,
)

@tool
def ask_health_specialist(prompt: str) -> str:
    """Answer general public-health questions using the local MedGemma model."""
    system_prompt = """
You are AarogyaMitra's Health Education Specialist.
Provide concise public-health education about diseases, symptoms, prevention,
hygiene, sanitation, vaccination awareness and when to seek care.

Safety:
- Do not diagnose with certainty.
- Do not prescribe prescription medicines or give personalized dosages.
- Do not tell users to stop/change prescribed medicines.
- For serious or emergency symptoms, recommend urgent professional care.
- Keep answers short and easy to understand.
- English is the default; follow the current user's language.
"""
    try:
        response = ollama.chat(
            model="alibayram/medgemma:4b",
            messages=[
                {"role":"system","content":system_prompt},
                {"role":"user","content":prompt},
            ],
            options={"num_predict":120,"temperature":0.3,"top_p":0.8},
        )
        return response["message"]["content"].strip()
    except Exception as e:
        print("MEDGEMMA ERROR:", repr(e))
        return "I’m unable to access the health-information specialist right now. Please try again."

@tool
def find_nearby_healthcare(location: str, service: str = "doctor") -> str:
    """Find up to 3 nearby healthcare resources within 3 km."""
    try:
        gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
        geocode = gmaps.geocode(location)
        if not geocode:
            return f"No location found for: {location}"

        latlng = geocode[0]["geometry"]["location"]
        result = gmaps.places_nearby(
            location=(latlng["lat"], latlng["lng"]),
            radius=3000,
            keyword=service,
        )
        places = result.get("results", [])[:3]
        if not places:
            return f"No nearby {service} found within 3 km of {location}."

        lines = [f"Nearby {service} in {location}", ""]
        for i, place in enumerate(places, 1):
            name = place.get("name", "N/A")
            address = place.get("vicinity", "N/A")
            phone = "N/A"
            if place.get("place_id"):
                details = gmaps.place(
                    place["place_id"],
                    fields=["formatted_phone_number"]
                )
                phone = details.get("result", {}).get("formatted_phone_number", "N/A")
            lines.append(f"{i}. {name}\nAddress: {address}\nPhone: {phone}")
        return "\n".join(lines)
    except Exception as e:
        print("LOCATION TOOL ERROR:", repr(e))
        return f"Unable to find healthcare providers near {location}."

def call_emergency_family(reason: str, contact: str | None = None):
    """Call the family/caregiver. Falls back to configured contact."""
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        destination = contact or TWILIO_EMERGENCY_CONTACT
        call = client.calls.create(
            to=destination,
            from_=TWILIO_VOICE_FROM,
            url="https://webhooks.twilio.com/v1/Voice/Template/voice_text_to_speech",
        )
        print("EMERGENCY CALL CREATED:", call.sid, call.status)
        return {"success": True, "sid": call.sid, "status": call.status}
    except Exception as e:
        print("EMERGENCY CALL ERROR:", repr(e))
        return {"success": False, "sid": None, "status": "failed", "error": str(e)}


def search_nearby_healthcare_structured(location: str, service: str = 'doctor', limit: int = 3, risk_level: str = 'Low'):
    """Return structured, risk-aware nearby healthcare options."""
    import math
    try:
        if not GOOGLE_MAPS_API_KEY:
            return []
        gmaps=googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
        geocode=gmaps.geocode(location)
        if not geocode:return []
        origin=geocode[0]['geometry']['location']
        query_service=service
        if risk_level == 'High' and service in {'doctor','clinic'}: query_service='hospital emergency'
        results=gmaps.places_nearby(location=(origin['lat'],origin['lng']),radius=5000,keyword=query_service).get('results',[])
        def km(lat,lng):
            r=6371;p1,p2=math.radians(origin['lat']),math.radians(lat);d1=math.radians(lat-origin['lat']);d2=math.radians(lng-origin['lng']);a=math.sin(d1/2)**2+math.cos(p1)*math.cos(p2)*math.sin(d2/2)**2;return round(2*r*math.asin(math.sqrt(a)),1)
        rows=[]
        for place in results:
            loc=place.get('geometry',{}).get('location',{})
            distance=km(loc.get('lat',origin['lat']),loc.get('lng',origin['lng'])) if loc else None
            name=place.get('name','Healthcare facility');rating=float(place.get('rating') or 0)
            types=[str(x).lower() for x in place.get('types',[])]
            if 'hospital' in types or 'hospital' in query_service.lower():ptype='Emergency' if risk_level=='High' else 'Hospital'
            elif 'doctor' in query_service.lower() or 'clinic' in query_service.lower():ptype='General'
            else:ptype='Specialist'
            capability=5 if risk_level=='High' and ptype=='Emergency' else 4 if 'specialist' in service.lower() and ptype=='Specialist' else 3
            rating_score=min(5,max(1,round(rating) if rating else 3))
            distance_score=max(0,5-min(5,int(distance or 5)))
            relevance=min(5,max(2,round((capability+rating_score+distance_score)/3)))
            if risk_level=='High' and ptype=='Emergency':relevance=5
            rows.append({'facility':name,'distance_km':distance,'type':ptype,'relevance':relevance,'rating':rating,'address':place.get('vicinity',''),'place_id':place.get('place_id',''),'maps_query':name,'risk_level':risk_level,'routing_reason':'Emergency capability prioritized for high-risk cases.' if risk_level=='High' else 'Ranked by distance, facility type and relevance.'})
        rows.sort(key=lambda x:(-x['relevance'],x['distance_km'] is None,x['distance_km'] or 999))
        return rows[:limit]
    except Exception as e:
        print('STRUCTURED LOCATION ERROR:',repr(e));return []
