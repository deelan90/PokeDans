import streamlit as st
import requests
import json
from datetime import datetime, timedelta

CACHE_FILE = "cache.pkl"

# Initialize Streamlit app settings
st.set_page_config(page_title="PokéDan Card Collection", layout="wide")

# API keys list (if needed for currency conversion, etc.)
API_KEYS = [
    "06d2909fdfd0f16758ebd7daf503cb6b",
    "6c10340d78e80946bc5d7d9167069540"
]

# Load cache from file
def load_cache():
    try:
        with open(CACHE_FILE, "rb") as f:
            return json.load(f)
    except (FileNotFoundError, EOFError, json.JSONDecodeError):
        return {}

# Save cache to file
def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

# Function to load the cards using AJAX directly
def load_cards_via_ajax(base_url):
    all_cards = []
    page = 0
    while True:
        ajax_url = f"{base_url}&internal=true&page={page}"
        response = requests.get(ajax_url)

        if response.status_code == 200:
            try:
                data = response.json()
                if not data.get('cards'):
                    break
                all_cards.extend(data['cards'])
                page += 1
                st.write(f"Fetched {len(data['cards'])} cards from page {page}")
            except json.JSONDecodeError:
                st.error("Failed to decode JSON response.")
                st.text(response.text[:500])  # Print part of the response to help debugging
                break
        else:
            st.error(f"HTTP Error {response.status_code} while fetching data.")
            break
    
    return all_cards

# Update exchange rates (if using API to convert prices)
def update_exchange_rates(cache):
    # Dummy function for updating exchange rates
    # You'll need to implement this based on your actual rate fetching logic
    cache['last_update'] = datetime.now().isoformat()
    save_cache(cache)
    st.write("Exchange rates updated")

def main():
    st.title("PokéDan Card Collection")

    # Your base URL needs to be updated if the endpoint is different
    base_url = "https://www.pricecharting.com/offers?status=collection&seller=yx5zdzzvnnhyvjeffskx64pus4&sort=name&category=all&folder-id=&condition-id=all"
    
    # Load cache and check for rate updates
    cache = load_cache()

    # Check and convert `last_update` to datetime; initialize if missing
    last_update = cache.get('last_update', None)
    if last_update:
        last_update = datetime.fromisoformat(last_update)
    else:
        last_update = datetime.min  # Set to earliest possible date if no update found

    # Check if we need to update exchange rates (every 12 hours)
    if datetime.now() - last_update > timedelta(hours=12):
        update_exchange_rates(cache)

    # Fetch all cards by AJAX
    cards = load_cards_via_ajax(base_url)
    
    # Display cards
    if cards:
        for card in cards:
            st.image(card['image_url'], caption=f"{card['name']} - ${card['price']}", width=200)
    else:
        st.write("No cards found or failed to load cards.")

if __name__ == "__main__":
    main()
