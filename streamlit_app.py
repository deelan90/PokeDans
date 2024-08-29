import streamlit as st
import requests
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Custom CSS for styling
st.markdown("""
    <style>
    /* General body and card styles */
    body {
        font-family: 'Franklin Gothic Medium', 'Arial Narrow', Arial, sans-serif;
        background-color: #1e1e1e;
        color: #ffffff;
    }
    .card-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 20px;
    }
    .card-image {
        border-radius: 8px;
    }
    .grading-card {
        background-color: #000000;
        color: #ffffff;
        padding: 10px;
        border-radius: 8px;
        margin-top: 10px;
        text-align: center;
        width: 90%;
    }
    /* Adjustments for mobile view */
    @media (max-width: 768px) {
        .card-container {
            width: 100%;
        }
    }
    /* Adjustments for desktop view */
    @media (min-width: 769px) {
        .card-container {
            width: 48%;
            margin-right: 2%;
            float: left;
        }
        .card-container:nth-child(2n) {
            margin-right: 0;
        }
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
                grading_element = offer.find_all('td')[2]  # Assuming grading names are in column 3
                grading_name = grading_element.text.strip() if grading_element else "No Grading"
                
                # Card value
                price_element = offer.find('span', class_='js-price')
                card_value_usd = price_element.text.strip() if price_element else "Unknown Value"
                
                # Convert the value to AUD and JPY
                try:
                    usd_value = float(card_value_usd.replace('$', '').replace(',', ''))
                    card_value_aud = f"${usd_value * 1.5:.2f} AUD"
                    card_value_jpy = f"¥{usd_value * 150:.2f} JPY"
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
        for card_name, card in cards.items():
            st.markdown(f"<div class='card-container'><div class='card-image'><img src='{card['image']}' style='width:100%;' alt='{card_name}'/></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='grading-card'><h3>{card_name}</h3>", unsafe_allow_html=True)
            for grading in card['gradings']:
                st.markdown(f"<p>{grading['grading_name']}</p><p>AUD: {grading['value_aud']}</p><p>JPY: {grading['value_jpy']}</p></div>", unsafe_allow_html=True)
            if card['link']:
                st.markdown(f"<p><a href='{card['link']}' target='_blank'>View on PriceCharting</a></p></div>", unsafe_allow_html=True)

# Streamlit app setup
st.markdown("<h1 style='font-family: Flexo, sans-serif; color: #FFCB05;'>PokéDan</h1>", unsafe_allow_html=True)

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
