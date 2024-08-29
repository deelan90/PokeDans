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
            cards = {}
            for offer in table.find_all('tr', class_='offer'):
                try:
                    # Card name
                    card_name_element = offer.find('td', class_='meta').find('p', class_='title').find('a')
                    card_name = card_name_element.text.strip() if card_name_element else "Unknown Name"

                    # Card value in USD
                    card_value_element = offer.find('td', class_='price').find('span', class_='js-price')
                    card_value_usd = card_value_element.text.strip() if card_value_element else "Unknown Value"

                    # Convert the value to AUD and JPY using live data
                    conversion_rate_aud = 1.5  # Example conversion rate, update to live data as needed
                    conversion_rate_jpy = 150  # Example conversion rate, update to live data as needed
                    card_value_aud = f"${float(card_value_usd.replace('$', '').replace(',', '')) * conversion_rate_aud:.2f} AUD"
                    card_value_jpy = f"¥{float(card_value_usd.replace('$', '').replace(',', '')) * conversion_rate_jpy:.2f} JPY"

                    # Card link
                    card_link_element = offer.find('td', class_='photo').find('div').find('a')
                    card_link = card_link_element.get('href') if card_link_element else None

                    # Fetch the high-resolution image
                    card_image_url = get_high_res_image(card_link) if card_link else None

                    # Grading name
                    grading_name = offer.find_all('td')[2].text.strip()

                    # Collate data under card name
                    if card_name not in cards:
                        cards[card_name] = []
                    cards[card_name].append({
                        'grading_name': grading_name,
                        'value_aud': card_value_aud,
                        'value_jpy': card_value_jpy,
                        'image': card_image_url,
                        'link': f"https://www.pricecharting.com{card_link}" if card_link else None
                    })

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

# Function to display cards
def display_cards(cards):
    if cards:
        cols = st.columns(8)  # Create columns for dynamic layout

        for card_name, card_details in cards.items():
            for idx, card in enumerate(card_details):
                col = cols[idx % 8]  # Alternate between columns
                with col:
                    st.markdown(f"<div style='border-radius: 10px; padding: 5px;'>", unsafe_allow_html=True)
                    if card['image']:
                        st.image(card['image'], caption=card_name, use_column_width=True)
                    else:
                        st.write("Image not available")

                    for detail in card_details:
                        st.markdown(
                            f"<div style='background-color: black; color: white; border-radius: 5px; padding: 10px; margin-top: 5px;'>"
                            f"<b>{detail['grading_name']}</b><br>"
                            f"AUD: {detail['value_aud']}<br>"
                            f"JPY: {detail['value_jpy']}</div>",
                            unsafe_allow_html=True
                        )
                    st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.warning("No cards found or an error occurred. Please check the logs for more information.")

# Streamlit app setup
st.markdown(f"<h1 style='color: #FFCC00;'>PokéDan</h1>", unsafe_allow_html=True)

# Input for the collection URL
collection_link = st.text_input("Enter the collection link:")

if collection_link:
    st.success(f"Your saved collection link: {collection_link}")
    cards = get_pokemon_cards(collection_link)
    if cards:
        display_cards(cards)
else:
    st.warning("Please enter a collection link to proceed.")
