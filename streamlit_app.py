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
            return None, None

        value_usd = float(usd_value.replace('$', '').replace(',', '').strip())
        value_aud = value_usd * rate_aud
        value_yen = value_usd * rate_yen

        return value_aud, value_yen
    except ValueError as e:
        st.error(f"Error in currency conversion: {e}")
        return None, None

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
                rate_jpy = data['rates'].get('JPY')

                if rate_usd and rate_aud and rate_jpy:
                    cache['rate_aud'] = rate_aud / rate_usd
                    cache['rate_yen'] = rate_jpy / rate_usd
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

# Function to fetch high-resolution images with caching
def get_high_res_image(card_link, cache):
    if 'image_urls' not in cache:
        cache['image_urls'] = {}
    if card_link in cache['image_urls']:
        return cache['image_urls'][card_link]
    try:
        card_page_response = requests.get(f"https://www.pricecharting.com{card_link}")
        card_page_response.raise_for_status()
        card_page_soup = BeautifulSoup(card_page_response.content, 'html.parser')
        card_image_element = card_page_soup.find('img', {'class': 'chart-item-image'})
        image_url = card_image_element['src'] if card_image_element else None
        if image_url:
            cache['image_urls'][card_link] = image_url
            save_cache(cache)
        return image_url
    except Exception as e:
        st.error(f"Error fetching image for {card_link}: {e}")
        return None

# Function to display card information
def display_card_info(soup, cache):
    card_groups = defaultdict(list)
    
    card_rows = soup.find_all('tr', class_='offer')
    for card in card_rows:
        try:
            # Extract card name and link
            card_name_tag = card.find('a', href=True)
            if not card_name_tag:
                continue
            card_name = card_name_tag.text.strip()
            card_link = card_name_tag['href']
            
            # Extract additional info after <br> tag
            additional_info_tag = card_name_tag.find_next_sibling(text=True)
            additional_info = additional_info_tag.strip() if additional_info_tag else ''
            
            # Extract grading and price
            grading = card.find('td', class_='includes').text.strip()
            price_usd = card.find('span', class_='js-price').text.strip()
            
            card_groups[(card_name, card_link, additional_info)].append({
                'grading': grading,
                'price_usd': price_usd
            })
        except Exception as e:
            st.error(f"Error processing card data: {e}")

    # Sort cards alphabetically by name
    sorted_cards = sorted(card_groups.items(), key=lambda x: x[0][0])

    cols = st.columns(4)  # Create 4 columns for layout
    for index, ((card_name, card_link, additional_info), gradings) in enumerate(sorted_cards):
        try:
            image_url = get_high_res_image(card_link, cache)
            
            with cols[index % 4]:
                # Card name as a clickable link
                st.markdown(f"""
                    <h4 style='text-align: center;'>
                        <a href='https://www.pricecharting.com{card_link}' style='text-decoration: none; color: #FFCC00;' target='_blank'>
                            {card_name}
                        </a>
                    </h4>
                """, unsafe_allow_html=True)
                
                # Display card image
                if image_url:
                    st.image(image_url, use_column_width=True)
                else:
                    st.image("https://via.placeholder.com/200x280?text=No+Image", use_column_width=True)
                
                # Display additional info in light gray, small font
                if additional_info:
                    st.markdown(f"""
                        <p style='text-align: center; color: #A0A0A0; font-size: 12px;'>
                            {additional_info}
                        </p>
                    """, unsafe_allow_html=True)
                
                # Display all gradings with converted prices
                for grading_info in gradings:
                    price_aud, price_yen = fetch_and_convert_currency(grading_info['price_usd'], cache)
                    if price_aud is not None and price_yen is not None:
                        st.markdown(f"""
                            <div style="background-color: #1E1E1E; padding: 5px; border-radius: 5px; margin-bottom: 5px;">
                                <p style="color: #FFFFFF; font-size: 14px; margin: 0;"><strong>{grading_info['grading']}</strong></p>
                                <p style="color: #FFFFFF; font-size: 12px; margin: 0;">USD: ${float(grading_info['price_usd'].replace('$','')):,.2f}</p>
                                <p style="color: #FFFFFF; font-size: 12px; margin: 0;">AUD: ${price_aud:,.2f}</p>
                                <p style="color: #FFFFFF; font-size: 12px; margin: 0;">YEN: ¥{price_yen:,.2f}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("<p style='color: red;'>Price conversion failed.</p>", unsafe_allow_html=True)
                
                # Add some spacing between cards
                st.markdown("<hr style='border: none; height: 2px; background-color: #333;'>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error displaying card {card_name}: {e}")

def main():
    cache = load_cache()

    last_update = cache.get('last_update')
    if not last_update or datetime.now() - last_update > timedelta(hours=12):
        with st.spinner("Updating exchange rates..."):
            update_exchange_rates(cache)

    # Set page configuration
    st.set_page_config(page_title="PokéDan Collection", layout="wide")

    # Apply custom CSS for dark mode and fonts
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

            body {
                background-color: #0E1117;
                color: #C9D1D9;
                font-family: 'Roboto', sans-serif;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #FFCC00;
            }
            a {
                color: #FFCC00;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            .stSpinner > div > div {
                border-top-color: #FFCC00;
            }
        </style>
    """, unsafe_allow_html=True)

    # Display title
    st.markdown("<h1 style='text-align: center;'>PokéDan Collection</h1>", unsafe_allow_html=True)

    # Fetch data from PriceCharting
    with st.spinner("Fetching collection data..."):
        try:
            url = "https://www.pricecharting.com/offers?status=collection&seller=yx5zdzzvnnhyvjeffskx64pus4&sort=name&category=all&folder-id=&condition-id=all"
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch collection data: {e}")
            return

    # Fetch and display total collection value and card count
    total_value_usd, total_count = fetch_total_value_and_count(soup)
    if total_value_usd and total_count:
        price_aud, price_yen = fetch_and_convert_currency(total_value_usd, cache)
        if price_aud and price_yen:
            st.markdown(f"""
                <h3 style='text-align: center;'>
                    Total Collection Value:
                </h3>
                <p style='text-align: center; font-size: 18px;'>
                    USD: ${float(total_value_usd.replace('$','')):,.2f} |
                    AUD: ${price_aud:,.2f} |
                    YEN: ¥{price_yen:,.2f}
                </p>
                <p style='text-align: center; font-size: 18px;'>
                    Total Cards: {total_count}
                </p>
                <hr style='border: none; height: 2px; background-color: #333;'>
            """, unsafe_allow_html=True)
        else:
            st.error("Failed to convert total collection value.")
    else:
        st.error("Failed to retrieve total collection value and card count.")

    # Display card information
    display_card_info(soup, cache)

    # Display last updated time
    st.markdown(f"""
        <p style='text-align: center; font-size: 12px; color: #A0A0A0;'>
            Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
