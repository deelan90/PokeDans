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
                    card_name_element = offer.find('td', class_='meta')
                    if not card_name_element:
                        st.error("Card name element not found.")
                        continue

                    card_name = card_name_element.find('p', class_='title').find('a').text.strip()

                    card_value_element = offer.find('td', class_='price').find('span', class_='js-price')
                    if not card_value_element:
                        st.error("Card value element not found.")
                        continue

                    card_value_usd = card_value_element.text.strip()

                    conversion_rate_aud = 1.5  # Replace with real-time conversion from xe.com
                    conversion_rate_jpy = 150  # Replace with real-time conversion from xe.com
                    card_value_aud = f"${float(card_value_usd.replace('$', '').replace(',', '')) * conversion_rate_aud:.2f} AUD"
                    card_value_jpy = f"¥{float(card_value_usd.replace('$', '').replace(',', '')) * conversion_rate_jpy:.2f} JPY"

                    card_link_element = offer.find('td', class_='photo').find('div').find('a')
                    card_link = card_link_element.get('href') if card_link_element else None

                    card_image_url = get_high_res_image(card_link) if card_link else None

                    grading_element = offer.find('td', class_='grade')
                    grading_name = grading_element.text.strip() if grading_element else "Ungraded"

                    if card_name not in cards:
                        cards[card_name] = {
                            'name': card_name,
                            'image': card_image_url,
                            'gradings': []
                        }

                    cards[card_name]['gradings'].append({
                        'grading_name': grading_name,
                        'value_aud': card_value_aud,
                        'value_jpy': card_value_jpy,
                        'link': f"https://www.pricecharting.com{card_link}" if card_link else None
                    })

                except Exception as e:
                    st.error(f"An error occurred processing a card: {e}")
                    continue

            return list(cards.values())
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
        num_columns = 8 if st.experimental_user_info().screen_width >= 1024 else 2
        st.markdown("<style>.card-image-container { text-align: center; }</style>", unsafe_allow_html=True)
        for card in cards:
            st.markdown(f"### {card['name']}")
            cols = st.columns(num_columns)
            for idx, grading in enumerate(card['gradings']):
                with cols[idx % num_columns]:
                    st.markdown("<div class='card-image-container'>", unsafe_allow_html=True)
                    if card['image']:
                        st.image(card['image'], use_column_width=True)
                    else:
                        st.write("Image not available")
                    st.markdown(
                        f"<div style='text-align: center; padding: 8px; border-radius: 8px; margin-top: 10px;'>"
                        f"<b style='font-size: 1.1em;'>{grading['grading_name']}</b><br>"
                        f"AUD: {grading['value_aud']}<br>"
                        f"JPY: {grading['value_jpy']}<br>"
                        f"<a href='{grading['link']}' style='color: lightblue;'>View on PriceCharting</a>"
                        f"</div></div>", 
                        unsafe_allow_html=True
                    )

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
    # Clear the input field after processing
    st.text_input("Enter the collection link:", value="", key="hidden", label_visibility="hidden")
else:
    st.warning("Please enter a collection link to proceed.")
