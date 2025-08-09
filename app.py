import streamlit as st
import requests
from datetime import datetime
import pytz
import pandas as pd

WIKI_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"

# Custom CSS styling for UI
st.set_page_config(
    page_title="🌍 Country Info Explorer",
    page_icon="🌎",
    layout="centered",
)

st.markdown(
    """
    <style>
    .title {
        font-size: 3rem;
        font-weight: 700;
        color: #0072B5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        font-size: 1.25rem;
        color: #555555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .info-label {
        font-weight: 600;
        color: #003459;
    }
    .footer {
        text-align: center;
        color: #888888;
        margin-top: 3rem;
        font-size: 0.9rem;
    }
    .landmark-img {
        border-radius: 10px;
        box-shadow: 2px 2px 10px #888888;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(f'<div class="title">🌍 Country Info Explorer</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">Discover details, weather, travel tips & fun facts about any country</div>', unsafe_allow_html=True)


def get_country_by_name(name):
    url = f"https://restcountries.com/v3.1/name/{name}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()[0]
    else:
        return None


def get_country_by_code(code):
    url = f"https://restcountries.com/v3.1/alpha/{code}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()[0]
    else:
        return None


def fetch_wikipedia_summary(page_title):
    try:
        url = WIKI_API_URL + page_title
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            extract = data.get("extract")
            image_url = None
            if "originalimage" in data:
                image_url = data["originalimage"]["source"]
            elif "thumbnail" in data:
                image_url = data["thumbnail"]["source"]
            if extract and len(extract) > 20:
                return extract, image_url
    except Exception:
        pass
    return None, None


def fetch_landmarks_and_culture(country_name):
    culture_page = f"Culture_of_{country_name.replace(' ', '_')}"
    landmarks_page = f"{country_name.replace(' ', '_')}_landmarks"

    culture_summary, culture_img = fetch_wikipedia_summary(culture_page)
    landmarks_summary, landmarks_img = fetch_wikipedia_summary(landmarks_page)

    if not culture_summary:
        culture_summary, culture_img = fetch_wikipedia_summary(country_name)
    if not landmarks_summary:
        landmarks_summary, landmarks_img = fetch_wikipedia_summary(country_name)

    return {
        "culture": (culture_summary, culture_img),
        "landmarks": (landmarks_summary, landmarks_img)
    }


def fetch_weather(city):
    # Use wttr.in for simple weather info by city (no API key needed)
    try:
        url = f"https://wttr.in/{city}?format=j1"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            current = data.get("current_condition", [{}])[0]
            temp_c = current.get("temp_C")
            desc = current.get("weatherDesc", [{}])[0].get("value")
            humidity = current.get("humidity")
            return f"{temp_c}°C, {desc}, Humidity: {humidity}%"
    except Exception:
        pass
    return "Weather data not available."


def get_travel_tips(country_name):
    # Simple predefined tips for some popular countries; fallback generic tip
    tips = {
        "France": "Visit the Eiffel Tower and try authentic French pastries.",
        "Japan": "Explore Tokyo's vibrant culture and beautiful cherry blossoms.",
        "Brazil": "Don't miss the Amazon rainforest and lively Rio Carnival.",
        "India": "Experience the diverse cultures and historic monuments like the Taj Mahal.",
        "USA": "Explore national parks and iconic cities like New York and San Francisco."
    }
    return tips.get(country_name, "Remember to check local customs and travel advisories before your trip.")


def get_fun_facts(country_name):
    fact, _ = fetch_wikipedia_summary(country_name)
    if fact and len(fact) > 200:
        # Pick first 3 sentences approx
        return " ".join(fact.split(". ")[:3]) + "."
    else:
        return "No fun facts available."


country_input = st.text_input("Enter a country name")

if country_input:
    country = get_country_by_name(country_input)
    if not country:
        st.error("Country not found. Please try another name.")
    else:
        # Basic Info
        st.subheader(f"Name: {country.get('name', {}).get('common', '')}")
        official_name = country.get('name', {}).get('official')
        if official_name:
            st.write(f"**Official Name:** {official_name}")

        flag_url = country.get('flags', {}).get('png')
        if flag_url:
            st.image(flag_url, width=160)

        st.write(f"**Population:** {country.get('population', 'N/A'):,}")
        st.write(f"**Area:** {country.get('area', 'N/A'):,} km²")

        languages = country.get('languages')
        if languages:
            lang_list = ", ".join(languages.values())
            st.write(f"**Languages:** {lang_list}")

        # Neighboring countries
        st.subheader("Neighboring Countries")
        borders = country.get("borders")
        if borders:
            neighbors = [get_country_by_code(code).get('name', {}).get('common', code) for code in borders]
            st.write(", ".join(neighbors))
        else:
            st.write("No neighboring countries or island nation.")

        # Map
        st.subheader("Location Map")
        latlng = country.get("latlng")
        if latlng and len(latlng) == 2:
            st.map(pd.DataFrame({"lat": [latlng[0]], "lon": [latlng[1]]}))
        else:
            st.write("No location data available.")

        # Local timezones
        st.subheader("Local Time & Timezones")
        timezones = country.get("timezones")
        if timezones:
            for tz in timezones:
                try:
                    now = datetime.now(pytz.timezone(tz))
                    st.write(f"{tz}: {now.strftime('%Y-%m-%d %H:%M:%S')}")
                except Exception:
                    st.write(f"{tz}: Timezone data not available.")
        else:
            st.write("Timezone data not available.")

        # Famous Landmarks & Culture
        st.subheader("Famous Landmarks & Photos")
        data = fetch_landmarks_and_culture(country.get('name', {}).get('common', ''))
        landmarks_summary, landmarks_img = data["landmarks"]
        if landmarks_summary:
            if landmarks_img:
                st.image(landmarks_img, width=400, caption="Famous Landmarks")
            st.write(landmarks_summary)
        else:
            st.write("No landmark data found.")

        st.subheader("Cultural Highlights")
        culture_summary, culture_img = data["culture"]
        if culture_summary:
            if culture_img:
                st.image(culture_img, width=400, caption="Cultural Highlights")
            st.write(culture_summary)
        else:
            st.write("No cultural data found.")

        # Weather info
        st.subheader("Current Weather in Capital")
        capital = country.get("capital")
        if capital and len(capital) > 0:
            weather = fetch_weather(capital[0])
            st.write(f"{capital[0]}: {weather}")
        else:
            st.write("Capital city not found, cannot fetch weather.")

        # Travel Tips
        st.subheader("Travel Tips")
        travel_tips = get_travel_tips(country.get('name', {}).get('common', ''))
        st.write(travel_tips)

        # Fun Facts
        st.subheader("Fun Facts")
        fun_facts = get_fun_facts(country.get('name', {}).get('common', ''))
        st.write(fun_facts)

st.markdown('<div class="footer">Made with ❤️ by Your Friendly AI Assistant</div>', unsafe_allow_html=True)
