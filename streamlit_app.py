import streamlit as st
import requests
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

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
                    card_name_element = offer.find('td', class_='meta')
                    if card_name_element:
                        title_element = card_name_element.find('p', class_='title')
                        if title_element:
                            card_name = title_element.find('a').text.strip() if title_element.find('a') else "Unknown Name"
                        else:
                            logging.warning("Title element not found")
                            continue
                    else:
                        logging.warning("Meta element not found")
                        continue

                    # Grading name
                    description_element = offer.find('td', class_='description')
                    if description_element:
                        grading_element = description_element.find('p', class_='header')
                        grading_name = grading_element.text.strip() if grading_element else "No Grading"
                    else:
                        logging.warning("Description element not found")
                        continue

                    # Card value in USD
                    price_element = offer.find('td', class_='price')
                    if price_element:
                        card_value_element = price_element.find('span', class_='js-price')
                        card_value_usd = card_value_element.text.strip() if card_value_element else "Unknown Value"
                    else:
                        logging.warning("Price element not found")
                        continue

                    # Convert the value to AUD and JPY
                    try:
                        usd_value = float(card_value_usd.replace('$', '').replace(',', ''))
                        card_value_aud = f"{usd_value * 1.5:.2f} AUD"  # Update conversion rate as needed
                        card_value_jpy = f"{usd_value * 150:.2f} JPY"  # Update conversion rate as needed
                    except ValueError:
                        logging.warning(f"Could not convert price for {card_name}")
                        card_value_aud = "Unknown Value"
                        card_value_jpy = "Unknown Value"

                    # Card link and image
                    photo_element = offer.find('td', class_='photo')
                    if photo_element:
                        card_link_element = photo_element.find('div').find('a')
                        card_link = card_link_element.get('href') if card_link_element else None
                        if card_link:
                            card_page_response = requests.get(f"https://www.pricecharting.com{card_link}")
                            card_page_response.raise_for_status()
                            card_page_soup = BeautifulSoup(card_page_response.content, 'html.parser')
                            card_image_element = card_page_soup.find('img', {'src': lambda x: x and ('jpeg' in x.lower() or 'jpg' in x.lower())})
                            card_image_url = card_image_element.get('src') if card_image_element else None
                            if not card_image_url:
                                card_image_url = photo_element.find('div').find('a').find('img').get('src')
                        else:
                            logging.warning(f"Could not find card link for {card_name}")
                            continue
                    else:
                        logging.warning("Photo element not found")
                        continue

                    # Update or create card entry
                    if card_name in cards:
                        cards[card_name]['gradings'].append({
                            'grading_name': grading_name,
                            'value_aud': card_value_aud,
                            'value_jpy': card_value_jpy
                        })
                    else:
                        cards[card_name] = {
                            'image': card_image_url,
                            'gradings': [{
                                'grading_name': grading_name,
                                'value_aud': card_value_aud,
                                'value_jpy': card_value_jpy
                            }],
                            'link': f"https://www.pricecharting.com{card_link}"
                        }

                except Exception as e:
                    logging.error(f"An error occurred processing card {card_name}: {e}")
                    continue
            return cards
        else:
            logging.error("Could not find the card data table.")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None

# Fetch and display the data in a grid layout
def display_cards(cards):
    if cards:
        cols = st.columns(2)  # Create two columns for the grid layout
        for idx, (card_name, card) in enumerate(cards.items()):
            col = cols[idx % 2]  # Alternate between columns
            with col:
                st.markdown(f"<h3 class='pokemon-font'>{card_name}</h3>", unsafe_allow_html=True)
                st.image(card['image'], caption=card_name, use_column_width=True)
                for grading in card['gradings']:
                    st.write(f"**{grading['grading_name']}:** {grading['value_aud']} | {grading['value_jpy']}")
                st.markdown(f"[View on PriceCharting]({card['link']})")

# Custom CSS for Pokémon-style font
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');

.pokemon-font {
    font-family: 'Press Start 2P', cursive;
    color: #FFCB05;
    text-shadow: 2px 2px #3C5AA6;
}
</style>
""", unsafe_allow_html=True)

# Streamlit app setup
st.markdown("<h1 class='pokemon-font'>Pokémon Card Tracker</h1>", unsafe_allow_html=True)

# Input for the collection URL
collection_link = st.text_input("Enter the collection link:")
if collection_link:
    st.success(f"Your saved collection link: {collection_link}")
    cards = get_pokemon_cards(collection_link)
    if cards:
        display_cards(cards)
    else:
        st.error("No cards found or an error occurred. Please check the logs for more information.")
else:
    st.warning("Please enter a collection link to proceed.")

# Hide the input field after submission
if collection_link:
    st.text_input("Enter the collection link:", value=collection_link, key="hidden", label_visibility="hidden")
