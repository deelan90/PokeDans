import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import os

# Define the file where user data will be stored
DATA_FILE = 'user_data.json'

# Function to load user data from the JSON file
def load_user_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        else:
            return {} 
    except Exception as e:
        st.error(f"Error loading user data: {e}")
        return {}

# Function to save user data to the JSON file
def save_user_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

# Function to fetch and extract data from PriceCharting
def get_pokemon_cards(collection_link):
    try:
        response = requests.get(collection_link)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        table = soup.find('table', id='active')
        if not table:
            st.error("Could not find the card data table.")
            return None

        cards = {}
        for offer in table.find_all('tr', class_='offer'):
            try:
                card_name = None  # Ensure card_name is initialized

                # Card name
                card_name_element = offer.find('td', class_='meta').find('p', class_='title').find('a')
                card_name = card_name_element.text.strip() if card_name_element else "Unknown Name"

                # Card value
                card_value_element = offer.find('td', class_='price').find('span', class_='js-price')
                card_value_text = card_value_element.text.strip() if card_value_element else "0"
                card_value = float(card_value_text.replace('$', '').replace(',', ''))

                # Card link
                card_link_element = offer.find('td', class_='photo').find('div').find('a')
                card_link = card_link_element.get('href') if card_link_element else None

                # Fetch image from card page
                card_image_url = None
                if card_link:
                    card_page_response = requests.get(f"https://www.pricecharting.com{card_link}")
                    card_page_response.raise_for_status()
                    card_page_soup = BeautifulSoup(card_page_response.content, 'html.parser')
                    card_image_element = card_page_soup.find('img', {'src': lambda x: x and ('jpeg' in x.lower() or 'jpg' in x.lower())})
                    card_image_url = card_image_element.get('src') if card_image_element else None

                if not card_image_url:
                    card_image_url = offer.find('td', class_='photo').find('div').find('a').find('img').get('src')

                if card_name not in cards:
                    cards[card_name] = {'AUD': card_value, 'JPY': card_value * 100, 'image_url': card_image_url, 'link': card_link}
                else:
                    # If the card already exists, sum the values
                    cards[card_name]['AUD'] += card_value
                    cards[card_name]['JPY'] += card_value * 100

            except Exception as e:
                st.error(f"An unexpected error occurred while processing {card_name}: {e}")
                continue

        return cards

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None

# Fetch and display the data
def display_cards(cards):
    if cards:
        col1, col2 = st.columns(2)
        idx = 0
        for card_name, details in cards.items():
            with (col1 if idx % 2 == 0 else col2):
                st.markdown(f"""
                <a href="{details['link']}" target="_blank">
                    <img src="{details['image_url']}" alt="{card_name}" style="width: 200px; height: auto;">
                </a>
                <p><strong>Card Name:</strong> {card_name}</p>
                <p><strong>Price:</strong> AU${details['AUD']:.2f} / ¥{details['JPY']:.0f}</p>
                """, unsafe_allow_html=True)
            idx += 1
    else:
        st.warning("No cards found or there was an error retrieving the cards.")

# Streamlit app starts here
st.title('Pokémon Card Tracker')

user_email = st.text_input("Enter your email to log in:")

if user_email:
    st.success(f'Logged in as {user_email}')
    user_data = load_user_data()

    if user_email in user_data:
        collection_link = user_data[user_email]
        st.write(f"Your saved collection link: {collection_link}")
    else:
        collection_link = st.text_input('Paste your collection link here:')

    if st.button('Save Link'):
        user_data[user_email] = collection_link
        save_user_data(user_data)
        st.success('Collection link saved!')

    if collection_link:
        if st.button('Refresh'):
            # Instead of using st.experimental_rerun, reset the app state manually
            st.experimental_set_query_params(refresh=True)
            st.experimental_rerun()

        cards = get_pokemon_cards(collection_link)
        display_cards(cards)