import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import os

# Define the file where user data will be stored
DATA_FILE = 'user_data.json'

# Base URL for PriceCharting
BASE_URL = "https://www.pricecharting.com"

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
def get_collection_data(collection_link):
    try:
        response = requests.get(collection_link)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        table = soup.find('table', id='active')

        if table:
            cards = []
            for offer in table.find_all('tr', class_='offer'):
                try:
                    card_name_element = offer.find('td', class_='meta')
                    card_name = card_name_element.find('p', class_='title').text.strip() if card_name_element else "Unknown Card"

                    card_value_element = offer.find('td', class_='price')
                    card_value = card_value_element.find('span', class_='js-price').text.strip() if card_value_element else "Unknown Value"

                    card_link_element = offer.find('td', class_='photo')
                    card_link = card_link_element.find('a')['href'] if card_link_element and card_link_element.find('a') else "#"

                    # Handle relative URLs by appending the base URL
                    if card_link != "#":
                        card_link = BASE_URL + card_link
                        card_response = requests.get(card_link)
                        card_response.raise_for_status()
                        card_soup = BeautifulSoup(card_response.content, 'html.parser')
                        image_element = card_soup.find('img', class_='js-lightbox-content')
                        card_image_url = image_element['src'] if image_element else "/api/placeholder/200/300"
                    else:
                        card_image_url = "/api/placeholder/200/300"

                    card_display = f"""
                    <a href="{card_link}" target="_blank">
                        <img src="{card_image_url}" alt="{card_name}" style="width: 200px; height: auto;">
                    </a>
                    <p><strong>Card Name:</strong> {card_name}</p>
                    <p><strong>Value:</strong> {card_value}</p>
                    """

                    cards.append(card_display)
                except Exception as e:
                    st.error(f"Error processing card: {str(e)}")
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

# Function to display the cards
def display_cards(cards):
    if cards:
        for card in cards:
            st.markdown(card, unsafe_allow_html=True)
    else:
        st.warning("No cards found or there was an error retrieving the cards.")

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
        cards = get_collection_data(collection_link)
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
