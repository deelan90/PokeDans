import streamlit as st
import requests
from bs4 import BeautifulSoup

# Function to fetch and extract data from PriceCharting
def get_pokemon_cards(collection_url):
    try:
        response = requests.get(collection_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')  # Corrected parser

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

                    # Convert the value to AUD and JPY using xe.com API or similar for real-time conversion
                    conversion_rate_aud = 1.5  # Replace with actual conversion rate
                    conversion_rate_jpy = 150  # Replace with actual conversion rate
                    card_value_aud = f"${float(card_value_usd.replace('$', '').replace(',', '')) * conversion_rate_aud:.2f} AUD"
                    card_value_jpy = f"¥{float(card_value_usd.replace('$', '').replace(',', '')) * conversion_rate_jpy:.2f} JPY"

                    # Card link
                    card_link_element = offer.find('td', class_='photo').find('div').find('a')
                    card_link = card_link_element.get('href') if card_link_element else None

                    # Fetch the high-resolution image
                    card_image_url = get_high_res_image(card_link) if card_link else None

                    # Grading name
                    grading_name_element = offer.find_all('td', class_='grade')[2] if len(offer.find_all('td', class_='grade')) > 2 else None
                    grading_name = grading_name_element.text.strip() if grading_name_element else "Ungraded"

                    # Create the card display dictionary, aggregating multiple gradings under one card
                    if card_name not in cards:
                        cards[card_name] = {
                            'name': card_name,
                            'image': card_image_url,
                            'grades': []
                        }
                    cards[card_name]['grades'].append({
                        'grading_name': grading_name,
                        'value_aud': card_value_aud,
                        'value_jpy': card_value_jpy,
                        'link': f"https://www.pricecharting.com{card_link}" if card_link else None
                    })

                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
                    continue

            return list(cards.values())
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

# Define the card display box size and styling
card_container_style = """
    .card-container {
        width: 100%;
        max-width: 250px;
        margin: 10px;
        padding: 10px;
        border-radius: 15px;
        background-color: #111;
        box-shadow: 0px 0px 15px rgba(0, 0, 0, 0.2);
    }
    .card-image {
        width: 100%;
        height: auto;
        border-radius: 15px;
    }
    .grading-name {
        font-size: 1.2em;
        font-weight: bold;
        margin-top: 10px;
    }
    .card-value {
        font-size: 1em;
        margin-top: 5px;
    }
"""
st.markdown(f"<style>{card_container_style}</style>", unsafe_allow_html=True)

# Display cards dynamically based on window size
def display_cards(cards):
    if cards:
        cols = st.columns(3)  # Adjusts the layout dynamically
        for idx, card in enumerate(cards):
            col = cols[idx % len(cols)]  # Dynamically assigns cards to columns
            with col:
                st.markdown(f"<div class='card-container'>", unsafe_allow_html=True)
                st.image(card['image'], use_column_width=True, class_="card-image")
                st.markdown(f"<div class='grading-name'>{card['grading_name']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='card-value'>AUD: {card['value_aud']}<br>JPY: {card['value_jpy']}</div>", unsafe_allow_html=True)
                st.markdown(f"<a href='{card['link']}' target='_blank'>View on PriceCharting</a>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

# Streamlit app setup
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
