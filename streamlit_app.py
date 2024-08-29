import streamlit as st
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

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
                    card_name_element = offer.find('td', class_='meta').find('p', class_='title').find('a')
                    card_name = card_name_element.text.strip() if card_name_element else "Unknown Name"

                    card_value_element = offer.find('td', class_='price').find('span', class_='js-price')
                    card_value_usd = card_value_element.text.strip() if card_value_element else "Unknown Value"

                    conversion_rate_aud = 1.5  # Replace with real-time conversion from xe.com
                    conversion_rate_jpy = 150  # Replace with real-time conversion from xe.com
                    card_value_aud = f"${float(card_value_usd.replace('$', '').replace(',', '')) * conversion_rate_aud:.2f} AUD"
                    card_value_jpy = f"¥{float(card_value_usd.replace('$', '').replace(',', '')) * conversion_rate_jpy:.2f} JPY"

                    card_link_element = offer.find('td', class_='photo').find('div').find('a')
                    card_link = card_link_element.get('href') if card_link_element else None

                    card_image_url = get_high_res_image(card_link) if card_link else None

                    grading_element = offer.find('td', class_='grade')
                    grading_name = grading_element.text.strip() if grading_element else "Ungraded"

                    card_display = {
                        'name': card_name,
                        'value_aud': card_value_aud,
                        'value_jpy': card_value_jpy,
                        'image': card_image_url,
                        'grading_name': grading_name,
                        'link': f"https://www.pricecharting.com{card_link}" if card_link else None
                    }
                    cards.append(card_display)

                except Exception as e:
                    st.error(f"An error occurred processing a card: {e}")
                    continue

            return cards
        else:
            st.error("Could not find the card data table.")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None

# Function to fetch high-resolution images
def get_high_res_image(card_link):
    try:
        card_page_response = requests.get(f"https://www.pricecharting.com{card_link}")
        card_page_response.raise_for_status()
        card_page_soup = BeautifulSoup(card_page_response.content, 'html.parser')
        card_image_element = card_page_soup.find('img', {'src': lambda x: x and ('jpeg' in x.lower() or 'jpg' in x.lower())})
        if card_image_element:
            return card_image_element.get('src')
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching high-resolution image: {e}")
        return None

# Function to display cards in a dynamic layout
def display_cards(cards):
    if cards:
        cols = st.columns(8)  # Create 8 columns for the grid layout
        for idx, card in enumerate(cards):
            col = cols[idx % 8]  # Alternate between columns
            with col:
                st.image(card['image'], caption=card['name'], use_column_width=True)
                st.write(f"**{card['grading_name']}**")
                st.write(f"AUD: {card['value_aud']}")
                st.write(f"JPY: {card['value_jpy']}")
                st.markdown(f"[View on PriceCharting]({card['link']})")

# Streamlit app setup
st.set_page_config(page_title="PokéDan", page_icon=":zap:", layout="wide")
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
