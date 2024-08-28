import streamlit as st
import requests
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Custom CSS for Pokémon-style font and Franklin Gothic for body text
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Flexo:wght@700&display=swap');

body {
    font-family: 'Franklin Gothic Medium', 'Arial Narrow', Arial, sans-serif;
}

.pokemon-title {
    font-family: 'Flexo', sans-serif;
    font-size: 48px;
    font-weight: 700;
    color: #FFCB05;
    letter-spacing: 2px;
    padding: 20px;
    text-align: center;
    margin-bottom: 20px;
}

.pokemon-font {
    font-family: 'Flexo', sans-serif;
    color: #FFCB05;
    font-size: 18px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

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

# Function to fetch and extract data from PriceCharting
def get_pokemon_cards(collection_url):
    try:
        response = requests.get(collection_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        table = soup.find('table', id='active')
        if not table:
            logging.error("Could not find the card data table.")
            return None
        
        cards = {}
        for offer in table.find_all('tr', class_='offer'):
            try:
                # Card name
                card_name_element = offer.find('p', class_='title')
                if not card_name_element:
                    continue
                card_name = card_name_element.text.strip()
                
                # Grading name
                grading_element = offer.find('p', class_='header')
                grading_name = grading_element.text.strip() if grading_element else "No Grading"
                
                # Card value
                price_element = offer.find('span', class_='js-price')
                card_value_usd = price_element.text.strip() if price_element else "Unknown Value"
                
                # Convert the value to AUD and JPY
                try:
                    usd_value = float(card_value_usd.replace('$', '').replace(',', ''))
                    card_value_aud = f"{usd_value * 1.5:.2f} AUD"
                    card_value_jpy = f"{usd_value * 150:.2f} JPY"
                except ValueError:
                    card_value_aud = "Unknown Value"
                    card_value_jpy = "Unknown Value"
                
                # Card link
                card_link_element = offer.find('a', class_='item-link')
                card_link = f"https://www.pricecharting.com{card_link_element['href']}" if card_link_element else None
                
                # Update or create card entry
                if card_name in cards:
                    cards[card_name]['gradings'].append({
                        'grading_name': grading_name,
                        'value_aud': card_value_aud,
                        'value_jpy': card_value_jpy
                    })
                else:
                    cards[card_name] = {
                        'image': None,  # We'll fetch this later
                        'gradings': [{
                            'grading_name': grading_name,
                            'value_aud': card_value_aud,
                            'value_jpy': card_value_jpy
                        }],
                        'link': card_link
                    }
                
                logging.info(f"Successfully processed card: {card_name}")
            
            except Exception as e:
                logging.error(f"An error occurred processing a card: {e}")
                continue
        
        if not cards:
            logging.warning("No cards were found in the collection.")
        return cards
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None

# Function to display the cards in Streamlit
def display_cards(cards):
    if cards:
        cols = st.columns(2)  # Create two columns for the grid layout
        for idx, (card_name, card) in enumerate(cards.items()):
            col = cols[idx % 2]  # Alternate between columns
            with col:
                st.markdown(f"<h3 class='pokemon-font'>{card_name}</h3>", unsafe_allow_html=True)
                if card['image']:
                    st.image(card['image'], caption=card_name, use_column_width=True)
                else:
                    st.write("Image not available")
                for grading in card['gradings']:
                    st.write(f"**{grading['grading_name']}:** {grading['value_aud']} | {grading['value_jpy']}")
                if card['link']:
                    st.markdown(f"[View on PriceCharting]({card['link']})")

# Streamlit app setup
st.markdown("<h1 class='pokemon-title'>Pokémon Card Tracker</h1>", unsafe_allow_html=True)

# Input for the collection URL
collection_link = st.text_input("Enter the collection link:")
if collection_link:
    st.success(f"Your saved collection link: {collection_link}")
    cards = get_pokemon_cards(collection_link)
    if cards:
        # Fetch high-res images
        for card_name, card_data in cards.items():
            if card_data['link']:
                card_data['image'] = get_high_res_image(card_data['link'])
        display_cards(cards)
    else:
        st.error("No cards found or an error occurred. Please check the logs for more information.")
else:
    st.warning("Please enter a collection link to proceed.")

# Hide the input field after submission
if collection_link:
    st.text_input("Enter the collection link:", value=collection_link, key="hidden", label_visibility="hidden")
