import streamlit as st
import requests
from bs4 import BeautifulSoup

# Function to fetch and extract data from PriceCharting
def get_pokemon_cards(collection_url):
    try:
        response = requests.get(collection_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        table = soup.find('table', id='active')
        if table:
            cards = []
            for offer in table.find_all('tr', class_='offer'):
                try:
                    # Card name
                    card_name_element = offer.find('td', class_='meta').find('p', class_='title').find('a')
                    card_name = card_name_element.text.strip() if card_name_element else "Unknown Name"

                    # Card value in USD
                    card_value_element = offer.find('td', class_='price').find('span', class_='js-price')
                    card_value_usd = card_value_element.text.strip() if card_value_element else "Unknown Value"

                    # Currency conversion
                    conversion_rate_aud = get_conversion_rate('USD', 'AUD')
                    conversion_rate_jpy = get_conversion_rate('USD', 'JPY')
                    card_value_aud = f"{float(card_value_usd.replace('$', '').replace(',', '')) * conversion_rate_aud:.2f} AUD"
                    card_value_jpy = f"{float(card_value_usd.replace('$', '').replace(',', '')) * conversion_rate_jpy:.2f} JPY"

                    # Card link
                    card_link_element = offer.find('td', class_='photo').find('div').find('a')
                    card_link = card_link_element.get('href') if card_link_element else None

                    # Fetch the high-resolution image
                    card_image_url = get_high_res_image(card_link) if card_link else None

                    # Create the card display
                    card_display = {
                        'name': card_name,
                        'value_aud': card_value_aud,
                        'value_jpy': card_value_jpy,
                        'image': card_image_url,
                        'link': f"https://www.pricecharting.com{card_link}" if card_link else None
                    }
                    cards.append(card_display)

                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
                    continue

            return cards
        else:
            st.error("Could not find the card data table.")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None

# Function to fetch high-resolution images
def get_high_res_image(card_link):
    try:
        card_page_response = requests.get(f"https://www.pricecharting.com{card_link}")
        card_page_response.raise_for_status()
        card_page_soup = BeautifulSoup(card_page_response.content, 'html.parser')

        # Find the highest resolution image available
        card_image_element = card_page_soup.find('img', {'src': lambda x: x and ('jpeg' in x.lower() or 'jpg' in x.lower())})
        if card_image_element:
            return card_image_element.get('src')
        else:
            st.error("Could not find high-resolution image.")
            return None
    except Exception as e:
        st.error(f"Error fetching high-resolution image: {e}")
        return None

# Function to get real-time currency conversion rates
def get_conversion_rate(from_currency, to_currency):
    try:
        response = requests.get(f"https://api.exchangerate-api.com/v4/latest/{from_currency}")
        data = response.json()
        return data['rates'][to_currency]
    except Exception as e:
        st.error(f"Error fetching conversion rates: {e}")
        return 1  # Fallback to 1 if there's an issue

# Fetch and display the data in a grid layout
def display_cards(cards):
    if cards:
        num_columns = st.columns([1] * min(4, len(cards)))  # Dynamic column count based on window size
        for idx, card in enumerate(cards):
            with num_columns[idx % len(num_columns)]:
                st.markdown(f"""
                    <div style='border-radius: 10px; background-color: #333; padding: 10px;'>
                        <img src='{card['image']}' style='width: 100%; height: auto; border-radius: 10px;'/>
                        <h4 style='text-align: center;'>{card['name']}</h4>
                        <p style='text-align: center; font-weight: bold;'>{card['grading_name']}</p>
                        <p style='text-align: center;'>AUD: {card['value_aud']}</p>
                        <p style='text-align: center;'>JPY: {card['value_jpy']}</p>
                        <a href='{card['link']}' style='color: #4CAF50; text-align: center; display: block;'>View on PriceCharting</a>
                    </div>
                """, unsafe_allow_html=True)

# Streamlit app setup
st.set_page_config(page_title="PokéDan", layout="wide")
st.title("PokéDan")

# Input for the collection URL
collection_link = st.text_input("Enter the collection link:")

if collection_link:
    st.success(f"Your saved collection link: {collection_link}")
    cards = get_pokemon_cards(collection_link)
    if cards:
        display_cards(cards)
else:
    st.warning("Please enter a collection link to proceed.")

# Hide the input field after submission
if collection_link:
    st.text_input("Enter the collection link:", value=collection_link, key="hidden", label_visibility="hidden")
