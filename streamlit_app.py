import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Function to fetch and convert currency
def fetch_and_convert_currency(usd_value, rate_aud, rate_yen):
    try:
        value_usd = float(usd_value.replace('$', '').replace(',', '').strip())
        value_aud = value_usd * rate_aud
        value_yen = value_usd * rate_yen
        return value_aud, value_yen
    except ValueError:
        return None, None

# Function to scrape exchange rates from XE.com
def get_exchange_rates():
    try:
        # Scrape AUD/USD
        aud_response = requests.get("https://www.xe.com/currencycharts/?from=USD&to=AUD")
        aud_soup = BeautifulSoup(aud_response.content, 'html.parser')
        aud_row = aud_soup.find('tr', {'data-sleek-node-id': '240706'})
        print("AUD row:", aud_row)  # Debugging line
        aud_rate = float(aud_row.find_all('td')[1].text.strip()) if aud_row else None

        # Scrape USD/JPY
        yen_response = requests.get("https://www.xe.com/currencycharts/?from=USD&to=JPY")
        yen_soup = BeautifulSoup(yen_response.content, 'html.parser')
        yen_row = yen_soup.find('tr', {'data-sleek-node-id': 'e604a2'})
        print("JPY row:", yen_row)  # Debugging line
        yen_rate = float(yen_row.find_all('td')[1].text.strip()) if yen_row else None

        if not aud_rate or not yen_rate:
            raise ValueError("Could not fetch one or both currency rates.")

        return aud_rate, yen_rate
    except Exception as e:
        st.error(f"Error fetching currency rates: {e}")
        return None, None

# Function to fetch total value and card count
def fetch_total_value_and_count(soup):
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
def display_card_info(soup, rate_aud, rate_yen):
    card_rows = soup.find_all('tr', class_='offer')
    for card in card_rows:
        try:
            card_name_tag = card.find('p', class_='title')
            if not card_name_tag:
                raise ValueError("Card title tag not found.")
            card_name = card_name_tag.text.strip()
            card_link = card.find('a')['href']
            grading = card.find('td', class_='includes').text.strip()
            price_usd = card.find('span', class_='js-price').text.strip()

            # Fetch high-resolution image
            image_url = get_high_res_image(card_link)

            # Convert currency
            price_aud, price_yen = fetch_and_convert_currency(price_usd, rate_aud, rate_yen)

            # Display the card
            st.image(image_url, caption=card_name)
            st.write(f"Grading: **{grading}**")
            st.write(f"Value: ${price_aud:.2f} AUD / ¥{price_yen:.2f} Yen")
        except Exception as e:
            st.error(f"An error occurred while processing a card: {e}")

def main():
    # Set the title and subtitle
    st.markdown("<h1 style='text-align: center; color: #FFCC00; font-family: \"Pokemon Solid\";'>PokéDan</h1>", unsafe_allow_html=True)
    
    # Link to collection page
    url = "https://www.pricecharting.com/offers?status=collection&seller=yx5zdzzvnnhyvjeffskx64pus4&sort=name&category=all&folder-id=&condition-id=all"

    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Fetch exchange rates
    rate_aud, rate_yen = get_exchange_rates()

    if rate_aud is None or rate_yen is None:
        st.error("Currency rates could not be fetched.")
        return

    # Fetch total value and count
    total_value_usd, total_count = fetch_total_value_and_count(soup)

    if total_value_usd:
        total_value_aud, total_value_yen = fetch_and_convert_currency(total_value_usd, rate_aud, rate_yen)
        st.write(f"Total Collection Value: **${total_value_aud:.2f} AUD / ¥{total_value_yen:.2f} Yen**", unsafe_allow_html=True)
    else:
        st.write("Total Collection Value: Not available", unsafe_allow_html=True)

    if total_count:
        st.write(f"Total Cards: **{total_count}**", unsafe_allow_html=True)
    else:
        st.write("Total Cards: Not available", unsafe_allow_html=True)

    # Display card info
    display_card_info(soup, rate_aud, rate_yen)

    # Last updated time
    st.markdown(f"**Last updated:** {datetime.now()}")

if __name__ == "__main__":
    main()
