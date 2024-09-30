import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from collections import defaultdict
import pickle
import time

CACHE_FILE = "cache.pkl"

# API keys list
API_KEYS = [
    "06d2909fdfd0f16758ebd7daf503cb6b",
    "6c10340d78e80946bc5d7d9167069540"
]

# Load cache from file
def load_cache():
    try:
        with open(CACHE_FILE, "rb") as f:
            return pickle.load(f)
    except (FileNotFoundError, EOFError):
        return {}

# Save cache to file
def save_cache(cache):
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(cache, f)

# Function to fetch and convert currency using real-time rates from Fixer API
def fetch_and_convert_currency(usd_value, cache):
    try:
        rate_aud = cache.get('rate_aud')
        rate_yen = cache.get('rate_yen')

        if rate_aud is None or rate_yen is None:
            st.error("Exchange rates are not available. Conversion cannot be performed.")
            return 0.0, 0.0

        value_usd = float(usd_value.replace('$', '').replace(',', '').strip())
        value_aud = value_usd * rate_aud
        value_yen = value_usd * rate_yen

        return value_aud, value_yen
    except ValueError as e:
        st.error(f"Error in currency conversion: {e}")
        return 0.0, 0.0

# Function to fetch exchange rates from Fixer API and update the cache
def update_exchange_rates(cache):
    for api_key in API_KEYS:
        url = f"http://data.fixer.io/api/latest?access_key={api_key}&symbols=USD,AUD,JPY&format=1"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success'):
                rate_usd = data['rates'].get('USD')
                rate_aud = data['rates'].get('AUD')
                rate_yen = data['rates'].get('JPY')

                if rate_usd and rate_aud and rate_yen:
                    cache['rate_aud'] = rate_aud / rate_usd
                    cache['rate_yen'] = rate_yen / rate_usd
                    cache['last_update'] = datetime.now()
                    save_cache(cache)
                    return
        except requests.exceptions.RequestException as e:
            st.error(f"Exchange rate update failed: {e}")
        except Exception as e:
            st.error(f"Unexpected error during exchange rate update: {e}")

    st.error("Failed to update exchange rates from all provided API keys.")

# Function to fetch total value and card count
def fetch_total_value_and_count(soup):
    try:
        summary_table = soup.find('table', id='summary')
        total_value_usd = summary_table.find('td', class_='js-value js-price').text.strip()
        total_count = summary_table.find_all('td', class_='number')[-1].text.strip()
        return total_value_usd, total_count
    except AttributeError:
        return None, None

# Function to fetch high-resolution images
def get_high_res_image(card_link):
    try:
        card_page_response = requests.get(f"https://www.pricecharting.com{card_link}")
        card_page_response.raise_for_status()
        card_page_soup = BeautifulSoup(card_page_response.content, 'html.parser')
        card_image_element = card_page_soup.find('img', {'src': lambda x: x and ('jpeg' in x.lower() or 'jpg' in x.lower())})
        return card_image_element.get('src') if card_image_element else None
    except Exception as e:
        st.error(f"Error fetching high-resolution image: {e}")
        return None

# Scrape all cards by simulating scrolling behavior
def fetch_all_cards(base_url):
    all_cards = []
    seen_cards = set()  # Track unique cards to avoid duplicates
    page_number = 1
    
    while True:
        url = f"{base_url}&page={page_number}"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract card data from current page
        card_rows = soup.find_all('tr', class_='offer')
        if not card_rows:
            break  # No more cards to load
        
        for card in card_rows:
            card_name_tag = card.find('p', class_='title')
            if not card_name_tag:
                continue
            card_name = card_name_tag.text.strip()
            card_link = card.find('a')['href']
            grading = card.find('td', class_='includes').text.strip()
            price_usd = card.find('span', class_='js-price').text.strip()

            # Check if the card and grading already exist
            card_identifier = f"{card_name}-{grading}"
            if card_identifier in seen_cards:
                continue  # Skip duplicate cards
            seen_cards.add(card_identifier)

            all_cards.append({
                'name': card_name,
                'link': card_link,
                'grading': grading,
                'price_usd': price_usd
            })
        
        page_number += 1
        time.sleep(1)  # Pause slightly to avoid overloading the server
    
    return all_cards

# Function to display card information
def display_card_info(cards, cache):
    card_groups = defaultdict(list)

    # Group cards by name
    for card in cards:
        card_groups[card['name']].append(card)

    # Display grouped cards
    cols = st.columns(4)  # Create 4 columns
    for index, (card_name, card_list) in enumerate(card_groups.items()):
        try:
            # Fetch high-resolution image (using the link of the first card in the group)
            image_url = get_high_res_image(card_list[0]['link'])

            # Display the card in the appropriate column
            with cols[index % 4]:
                st.markdown(f"<h5 style='text-align:center; color: white;'>{card_name}</h5>", unsafe_allow_html=True)
                st.image(image_url, caption="", use_column_width=True)
                for card in card_list:
                    # Convert currency
                    price_aud, price_yen = fetch_and_convert_currency(card['price_usd'], cache)
                    if price_aud != 0.0 and price_yen != 0.0:
                        # Use custom HTML for displaying the card information
                        st.markdown(f"""
                        <div style="background-color: #333; padding: 10px; border-radius: 5px; text-align: center;">
                            <h6 style="color: white; font-family: 'Arial'; margin-bottom: 5px; font-size: 16px;">{card['grading']}</h6>
                            <p style="color: white; font-size: 13px; margin: 5px 0;">AUD $ {price_aud:.2f}</p>
                            <p style="color: white; font-size: 13px; margin: 5px 0;">YEN ¥ {price_yen:.2f}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.write("Conversion failed. Check rates or values.")
        except Exception as e:
            st.error(f"An error occurred while displaying the card: {e}")

def main():
    # Load cache
    cache = load_cache()

    # Check if we need to update the exchange rates (twice a day)
    last_update = cache.get('last_update')
    if not last_update or datetime.now() - last_update > timedelta(hours=12):
        update_exchange_rates(cache)

    # Set the page to dark mode
    st.markdown(
        """
        <style>
        body {
            background-color: #0E1117;
            color: #C9D1D9;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Set the title and subtitle
    st.markdown("<h1 style='text-align: center; color: #FFCC00; font-family: \"Pokemon Solid\";'>PokéDan</h1>", unsafe_allow_html=True)

    # Link to collection page
    url = "https://www.pricecharting.com/offers?status=collection&seller=yx5zdzzvnnhyvjeffskx64pus4&sort=name&category=all&folder-id=&condition-id=all"
    
    # Fetch all cards by simulating infinite scrolling
    with st.spinner("Fetching all cards..."):
        all_cards = fetch_all_cards(url)

    # Display card info
    display_card_info(all_cards, cache)

    # Last updated time
    st.markdown(f"**Last updated:** {datetime.now()}", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
