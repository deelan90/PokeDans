import requests
from bs4 import BeautifulSoup
import streamlit as st
from forex_python.converter import CurrencyRates
from datetime import datetime, timedelta
import time

# Function to fetch and convert currency
def fetch_and_convert_currency(usd_value):
    c = CurrencyRates()
    try:
        rate_aud = c.get_rate('USD', 'AUD')
        rate_yen = c.get_rate('USD', 'JPY')
        aud_value = usd_value * rate_aud
        yen_value = usd_value * rate_yen
        return aud_value, yen_value
    except requests.exceptions.SSLError:
        st.error("SSL error occurred while fetching currency rates.")
        return None, None

# Function to fetch total collection value and card count
def fetch_total_value(soup):
    try:
        summary_table = soup.find('table', id='summary')
        total_value_usd = summary_table.find('td', class_='js-value js-price').text.strip().replace('$', '').replace(',', '')
        total_count = summary_table.find_all('td', class_='number')[1].text.strip()
        return float(total_value_usd), int(total_count)
    except AttributeError:
        st.error("Error fetching total value and count: 'NoneType' object has no attribute 'text'")
        return None, None

# Function to fetch high-resolution images
def get_high_res_image(card_link):
    try:
        card_page_response = requests.get(f"https://www.pricecharting.com{card_link}")
        card_page_response.raise_for_status()
        card_page_soup = BeautifulSoup(card_page_response.content, 'html.parser')

        # Find the highest resolution image available
        card_image_element = card_page_soup.find('img', {'src': lambda x: x and ('jpeg' in x.lower() or 'jpg' in x.lower())})
        return card_image_element.get('src') if card_image_element else None
    except Exception as e:
        st.error(f"Error fetching high-resolution image: {e}")
        return None

# Function to display card information
def display_card_info(soup, rate_aud, rate_yen):
    cards = soup.find_all('tr', class_='offer')
    card_data = {}
    
    for card in cards:
        try:
            card_name = card.find('p', class_='title').find('a').text.strip()
            card_grade = card.find('td', class_='includes').text.strip()
            card_price_usd = card.find('span', class_='js-price').text.strip().replace('$', '').replace(',', '')

            if card_name not in card_data:
                card_data[card_name] = []
            card_data[card_name].append((card_grade, float(card_price_usd), card.find('a')['href']))

        except AttributeError:
            st.warning("Card name tag not found, skipping entry.")
            continue

    for card_name, grades in card_data.items():
        st.markdown(f"### {card_name}")  # Card name larger size
        card_image = get_high_res_image(grades[0][2])

        col1, col2 = st.columns([1, 3])
        if card_image:
            col1.image(card_image, use_column_width=True)

        with col2:
            for grade, price_usd, _ in grades:
                if rate_aud is None or rate_yen is None:
                    st.markdown(f"**{grade}:** ${price_usd:.2f} USD")
                else:
                    price_aud = price_usd * rate_aud
                    price_yen = price_usd * rate_yen
                    st.markdown(f"**{grade}:** ${price_usd:.2f} USD / ${price_aud:.2f} AUD / ¥{price_yen:.0f} Yen")

# Main function to run the app
def main():
    st.markdown("<h1 style='text-align: center; font-family: Pokémon, sans-serif; color: #FFCB05;'>PokéDan</h1>", unsafe_allow_html=True)

    try:
        collection_url = "https://www.pricecharting.com/offers?status=collection&seller=yx5zdzzvnnhyvjeffskx64pus4&sort=name&category=all&folder-id=&condition-id=all"
        response = requests.get(collection_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        rate_aud, rate_yen = fetch_and_convert_currency(1.0)
        total_value_usd, total_count = fetch_total_value(soup)

        if total_value_usd and total_count:
            if rate_aud is None or rate_yen is None:
                st.markdown(f"### Total Collection Value: ${total_value_usd:.2f} USD")
            else:
                total_value_aud = total_value_usd * rate_aud
                total_value_yen = total_value_usd * rate_yen
                st.markdown(f"### Total Collection Value: ${total_value_aud:.2f} AUD / ¥{total_value_yen:.0f} Yen")
            st.markdown(f"<p style='font-size: small;'>Total Cards: {total_count}</p>", unsafe_allow_html=True)
        else:
            st.markdown("### Total Collection Value: Not available")

        display_card_info(soup, rate_aud, rate_yen)

        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.markdown(f"<p style='font-size: x-small;'>Last updated: {last_updated}</p>", unsafe_allow_html=True)

    except requests.exceptions.SSLError:
        st.error("SSL error occurred while fetching the collection data.")
    except Exception as e:
        st.error(f"An error occurred: {e}")

    st.stop()

# Schedule auto-refresh every 3 hours
if __name__ == "__main__":
    while True:
        main()
        time.sleep(10800)  # 3 hours in seconds
