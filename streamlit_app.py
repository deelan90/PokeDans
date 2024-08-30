import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from collections import defaultdict
import pickle

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
        # Use cached rates
        rate_aud = cache.get('rate_aud')
        rate_yen = cache.get('rate_yen')

        if rate_aud is None or rate_yen is None:
            st.error("Exchange rates are not available. Conversion cannot be performed.")
            return 0.0, 0.0

        # Convert USD to AUD and JPY using cached rates
        value_usd = float(usd_value.replace('$', '').replace(',', '').strip())
        value_aud = value_usd * rate_aud
        value_yen = value_usd * rate_yen

        return value_aud, value_yen
    except ValueError as e:
        st.error(f"Error in currency conversion: {e}")
        return 0.0, 0.0

# Function to fetch exchange rates from Fixer API and update the cache
def update_exchange_rates(cache):
    # Rotate between API keys
    api_key = API_KEYS[len(API_KEYS) % 2]  # Alternates between the two keys
    url = f"http://data.fixer.io/api/latest?access_key={api_key}&symbols=USD,AUD,JPY&format=1"
    
    response = requests.get(url)
    data = response.json()
    
    if response.status_code == 200 and data.get('success'):
        # Conversion rates
        rate_aud = data['rates'].get('AUD') / data['rates'].get('USD')
        rate_yen = data['rates'].get('JPY') / data['rates'].get('USD')

        # Ensure rates are not None
        if rate_aud is None or rate_yen is None:
            st.error("Failed to retrieve valid exchange rates. Please try again later.")
        else:
            # Update cache
            cache['rate_aud'] = rate_aud
            cache['rate_yen'] = rate_yen
            cache['last_update'] = datetime.now()
            save_cache(cache)
    else:
        st.error(f"Could not fetch exchange rates. Error: {data.get('error', 'Unknown error')}")

# Function to fetch total value and card count
def fetch_total_value_and_count(soup, cache):
    try:
        summary_table = soup.find('table', id='summary')
        total_value_usd = summary_table.find('td', class_='js-value js-price').text.strip().replace('$', '').replace(',', '')
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

# Function to display card information
def display_card_info(soup, cache):
    card_groups = defaultdict(list)
    
    # Group cards by name
    card_rows = soup.find_all('tr', class_='offer')
    for card in card_rows:
        try:
            card_name_tag = card.find('p', class_='title')
            if not card_name_tag:
                continue
            card_name = card_name_tag.text.strip()
            card_link = card.find('a')['href']
            grading = card.find('td', class_='includes').text.strip()
            price_usd = card.find('span', class_='js-price').text.strip()
            card_groups[card_name].append({
                'link': card_link,
                'grading': grading,
                'price_usd': price_usd,
            })
        except Exception as e:
            st.error(f"An error occurred while processing a card: {e}")
    
    # Display grouped cards
    cols = st.columns(4)  # Create 4 columns
    for index, (card_name, cards) in enumerate(card_groups.items()):
        try:
            # Fetch high-resolution image (using the link of the first card in the group)
            image_url = get_high_res_image(cards[0]['link'])
            
            # Display the card in the appropriate column
            with cols[index % 4]:
                st.markdown(f"<h5 style='text-align:center;'>{card_name}</h5>", unsafe_allow_html=True)
                st.image(image_url, caption="", use_column_width=True)
                for card in cards:
                    # Convert currency
                    price_aud, price_yen = fetch_and_convert_currency(card['price_usd'], cache)
                    if price_aud != 0.0 and price_yen != 0.0:
                        # Use custom HTML for displaying the card information
                        st.markdown(f"""
                        <div style="background-color: #333; padding: 10px; border-radius: 5px; text-align: center;">
                            <h4 style="color: #FFCC00; font-family: 'Arial'; margin-bottom: 5px;">{card['grading']}</h4>
                            <p style="color: white; font-size: 14px; margin: 5px 0;">AUD $ {price_aud:.2f}</p>
                            <p style="color: white; font-size: 14px; margin: 5px 0;">YEN ¥ {price_yen:.2f}</p>
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

    # Set the title and subtitle
    st.markdown("<h1 style='text-align: center; color: #FFCC00; font-family: \"Pokemon Solid\";'>PokéDan</h1>", unsafe_allow_html=True)
    
    # Link to collection page
    url = "https://www.pricecharting.com/offers?status=collection&seller=yx5zdzzvnnhyvjeffskx64pus4&sort=name&category=all&folder-id=&condition-id=all"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Fetch total value and count
    total_value_usd, total_count = fetch_total_value_and_count(soup, cache)
    if total_value_usd:
        total_value_aud, total_value_yen = fetch_and_convert_currency(total_value_usd, cache)
        st.write(f"Total Collection Value: **${total_value_aud:.2f} AUD / ¥{total_value_yen:.2f} Yen**", unsafe_allow_html=True)
    else:
        st.write("Total Collection Value: Not available", unsafe_allow_html=True)

    if total_count:
        st.write(f"Total Cards: **{total_count}**", unsafe_allow_html=True)
    else:
        st.write("Total Cards: Not available", unsafe_allow_html=True)

    # Display card info
    display_card_info(soup, cache)

    # Last updated time
    st.markdown(f"**Last updated:** {datetime.now()}")

if __name__ == "__main__":
    main()
