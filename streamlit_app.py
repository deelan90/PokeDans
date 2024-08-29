import streamlit as st
import requests
from bs4 import BeautifulSoup
from forex_python.converter import CurrencyRates
import datetime

# Function to fetch and convert currency
def fetch_and_convert_currency(usd_value):
    try:
        c = CurrencyRates()
        rate_aud = c.get_rate('USD', 'AUD')
        rate_yen = c.get_rate('USD', 'JPY')
        print(f"Currency Rates: AUD={rate_aud}, YEN={rate_yen}")
        return usd_value * rate_aud, usd_value * rate_yen
    except requests.exceptions.SSLError as e:
        st.error("SSL error occurred while fetching currency rates.")
        print(f"SSL Error: {e}")
        return None, None

# Function to fetch the total value and card count
def fetch_total_value_and_count(soup):
    try:
        summary_table = soup.find('table', id='summary')
        print(f"Summary Table HTML: {summary_table}")
        total_value_usd = summary_table.find('td', class_='js-value js-price').text.strip().replace('$', '').replace(',', '')
        card_count = summary_table.find_all('td', class_='number')[1].text.strip()
        print(f"Total Value (USD): {total_value_usd}, Card Count: {card_count}")
        return float(total_value_usd), int(card_count)
    except AttributeError as e:
        st.error(f"Error fetching total value and count: {e}")
        print(f"AttributeError: {e}")
        return None, None

# Function to fetch high-resolution images
def get_high_res_image(card_link):
    try:
        card_page_response = requests.get(f"https://www.pricecharting.com{card_link}")
        card_page_response.raise_for_status()
        card_page_soup = BeautifulSoup(card_page_response.content, 'html.parser')

        # Find the highest resolution image available
        card_image_element = card_page_soup.find('img', {'src': lambda x: x and ('jpeg' in x.lower() or 'jpg' in x.lower())})
        image_url = card_image_element.get('src') if card_image_element else None
        print(f"Fetched image URL: {image_url}")
        return image_url
    except Exception as e:
        st.error(f"Error fetching high-resolution image: {e}")
        print(f"Image Fetch Error: {e}")
        return None

# Function to display card information
def display_card_info(soup, rate_aud, rate_yen):
    cards = {}

    for card in soup.find_all('tr', class_='offer'):
        try:
            card_name_tag = card.find('p', class_='title')
            if card_name_tag and card_name_tag.find('a'):
                card_name = card_name_tag.find('a').text.strip()
                print(f"Card Name: {card_name}")
            else:
                st.warning("Card name tag not found, skipping entry.")
                print("Card name tag not found, skipping entry.")
                continue

            card_link = card_name_tag.find('a')['href']
            card_image_url = get_high_res_image(card_link)
            grading = card.find('td', class_='includes').text.strip()
            price = card.find('span', class_='js-price').text.strip().replace('$', '').replace(',', '')

            if card_name not in cards:
                cards[card_name] = {
                    'link': card_link,
                    'image_url': card_image_url,
                    'gradings': {}
                }
            cards[card_name]['gradings'][grading] = float(price)

        except Exception as e:
            st.error(f"An error occurred while processing a card: {e}")
            print(f"Card Processing Error: {e}")
            continue

    if not cards:
        st.warning("No cards were found.")
        print("No cards were found.")
    else:
        for card_name, card_data in cards.items():
            st.markdown(f"### {card_name}")
            if card_data['image_url']:
                st.image(card_data['image_url'], use_column_width=True)
            for grading, price in card_data['gradings'].items():
                st.markdown(f"**{grading}:** ${price:.2f} USD")
        st.markdown(f"<p style='text-align: center; color: lightgray;'>Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>", unsafe_allow_html=True)

def main():
    # App title and heading
    st.markdown("<h1 style='text-align: center; color: #FFCB05; font-family: Pokémon, sans-serif;'>PokéDan</h1>", unsafe_allow_html=True)

    try:
        # Fetch the page content
        url = "https://www.pricecharting.com/offers?status=collection&seller=yx5zdzzvnnhyvjeffskx64pus4&sort=name&category=all&folder-id=&condition-id=all"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        print("Page fetched successfully.")

        # Fetch currency rates
        rate_aud, rate_yen = fetch_and_convert_currency(1.0)

        # Fetch total collection value and count
        total_value_usd, card_count = fetch_total_value_and_count(soup)
        if total_value_usd is not None:
            total_value_aud, total_value_yen = fetch_and_convert_currency(total_value_usd)
            st.markdown(f"<h3 style='text-align: center;'>Total Collection Value: {total_value_aud:.2f} AUD / {total_value_yen:.2f} JPY</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; color: lightgray;'>Card Count: {card_count} | Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>", unsafe_allow_html=True)
        else:
            st.markdown("<h3 style='text-align: center;'>Total Collection Value: Not available</h3>", unsafe_allow_html=True)

        # Display card info
        display_card_info(soup, rate_aud, rate_yen)

    except Exception as e:
        st.error(f"An error occurred: {e}")
        print(f"Main Function Error: {e}")

if __name__ == "__main__":
    main()
