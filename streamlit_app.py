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
            # Handle the case where the file doesn't exist
            st.error("Error: User data file not found.")
            return {} 
    except Exception as e:
        # Handle any other errors that might occur during loading
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
        # Get the table with the card data
        table = soup.find('table', id='active')

        if table:
            cards = []
            for offer in table.find_all('tr', class_='offer'):
                try:
                    # Find the card name
                    card_name_element = offer.find('td', class_='meta')
                    if card_name_element:
                        title_element = card_name_element.find('p', class_='title')
                        if title_element:
                            card_name = title_element.text.strip()
                        else:
                            card_name = "Unknown Card"
                    else:
                        st.warning(f"Could not find card name for this offer.")
                        continue  # Move on to the next offer

                    # Find the card value
                    card_value_element = offer.find('td', class_='price')
                    if card_value_element:
                        price_element = card_value_element.find('span', class_='js-price')
                        if price_element:
                            card_value = price_element.text.strip()
                        else:
                            card_value = "Unknown Value"
                    else:
                        st.warning(f"Could not find card value for this offer.")
                        continue  # Move on to the next offer

                    # Find the card link
                    card_link_element = offer.find('td', class_='photo')
                    if card_link_element:
                        link_element = card_link_element.find('a')
                        if link_element:
                            card_link = link_element.get('href')
                        else:
                            card_link = "#"
                    else:
                        st.warning(f"Could not find card link for this offer.")
                        continue  # Move on to the next offer

                    # Find the card image
                    card_image_url = "/api/placeholder/200/300"  # Default placeholder image

                    # Build the card display with a pop-up link
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
                    continue  # Move on to the next offer

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

# Fetch and display the data
def display_cards(cards):
    if cards:
        for card in cards:
            st.markdown(card, unsafe_allow_html=True)
    else:
        st.warning("No cards found or there was an error retrieving the cards.")

# Get the Pokémon card data
def get_collection_data(collection_link):
    cards = get_pokemon_cards(collection_link)
    display_cards(cards)

# Streamlit app starts here
st.title('Pokémon Card Tracker')

# Simulate the login process with an email input
user_email = st.text_input("Enter your email to log in:")

if user_email:
    st.success(f'Logged in as {user_email}')

    # Load existing user data from the JSON file
    user_data = load_user_data()

    # Check if the user already has a saved collection link
    if user_email in user_data:
        collection_link = user_data[user_email]
        st.write(f"Your saved collection link: {collection_link}")
        get_collection_data(collection_link)
    else:
        # If no collection link is found, prompt the user to input one
        collection_link = st.text_input('Paste your collection link here:')

    # Save the collection link when the user clicks the "Save Link" button
    if st.button('Save Link'):
        user_data[user_email] = collection_link
        save_user_data(user_data)
        st.success('Collection link saved!')

    # Add a refresh button
    if st.button('Refresh'):
        # Clear the existing card display
        st.experimental_rerun()
        # Load and display the updated data
        if user_email in user_data:
            collection_link = user_data[user_email]
            get_collection_data(collection_link)
        else:
            # If no collection link is found, display an error message
            st.error("Please save your collection link first.")