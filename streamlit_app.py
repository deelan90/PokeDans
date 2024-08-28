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
        response.raise_for_status()  # Raise an exception for bad responses
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract only the relevant part of the HTML
        table = soup.find('table', id='active')

        if table:
            cards = []
            for offer in table.find_all('tr', class_='offer'):
                try:
                    # Find the card name
                    card_name_element = offer.find('td', class_='meta').find('p', class_='title').find('a')
                    card_name = card_name_element.text.strip() if card_name_element else "Unknown Name"

                    # Find the card value
                    card_value_element = offer.find('td', class_='price').find('span', class_='js-price')
                    card_value = card_value_element.text.strip() if card_value_element else "Unknown Value"

                    # Find the card link
                    card_link_element = offer.find('td', class_='photo').find('div').find('a')
                    card_link = card_link_element.get('href') if card_link_element else None

                    if card_link:
                        # Fetch the image from the individual card page
                        card_page_response = requests.get(f"https://www.pricecharting.com{card_link}")
                        card_page_response.raise_for_status()
                        card_page_soup = BeautifulSoup(card_page_response.content, 'html.parser')

                        # Look for images with 'jpeg', 'jpg', or 'JPEG' in the src attribute
                        card_image_element = card_page_soup.find('img', {'src': lambda x: x and ('jpeg' in x.lower() or 'jpg' in x.lower())})
                        card_image_url = card_image_element.get('src') if card_image_element else None

                        if not card_image_url:
                            # Fallback to low-res image
                            card_image_url = offer.find('td', class_='photo').find('div').find('a').find('img').get('src')

                        # Build the card display with a pop-up link
                        card_display = f"""
                        <a href="https://www.pricecharting.com{card_link}" target="_blank">
                            <img src="{card_image_url}" alt="{card_name}" style="width: 200px; height: auto;">
                        </a>
                        <p><strong>Card Name:</strong> {card_name}</p>
                        <p><strong>Value:</strong> {card_value}</p>
                        """
                        cards.append(card_display)
                    else:
                        st.error(f"Could not find card link for {card_name}.")
                        continue  # Skip if link is not found

                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
                    continue  # Skip the current offer and continue

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

# Function to display the cards
def display_cards(cards):
    if cards:
        for card in cards:
            st.markdown(card, unsafe_allow_html=True)

# Streamlit app starts here
st.title('Pokémon Card Tracker')

# Simulate the login process with an email input
user_email = st.text_input("Enter your email to log in:")

if user_email:
    st.success(f'Logged in as {user_email}')

    # Load existing user data from the JSON file
    user_data = load_user_data()

    # Check if the user already has a saved collection link
    collection_link = user_data.get(user_email)

    if collection_link:
        st.write(f"Your saved collection link: {collection_link}")

        # Refresh button at the top
        if st.button('Refresh'):
            st.experimental_rerun()

        # Display cards
        cards = get_pokemon_cards(collection_link)
        display_cards(cards)
    else:
        # If no collection link is found, prompt the user to input one
        collection_link = st.text_input('Paste your collection link here:')

        # Save the collection link when the user clicks the "Save Link" button
        if st.button('Save Link') and collection_link:
            user_data[user_email] = collection_link
            save_user_data(user_data)
            st.success('Collection link saved!')

            # Automatically refresh the app to display the saved link and hide the input
            st.experimental_rerun()
