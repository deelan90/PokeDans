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
@st.cache_data
def get_pokemon_cards(collection_link):
    try:
        response = requests.get(collection_link)
        response.raise_for_status()  # Raise an exception for bad responses
        soup = BeautifulSoup(response.content, 'html.parser')

        table = soup.find('table', id='active')
        if not table:
            st.error("Could not find the card data table.")
            return None

        cards = {}
        for offer in table.find_all('tr', class_='offer'):
            try:
                # Find the card name
                card_name_element = offer.find('td', class_='meta').find('p', class_='title').find('a')
                if card_name_element:
                    card_name = card_name_element.text.strip()
                else:
                    st.error(f"Could not find card name for this offer.")
                    st.write(f"HTML for the current offer:\n{offer.prettify()}")
                    continue  # Move on to the next offer


                # Find the card value
                card_value_element = offer.find('td', class_='price').find('span', class='js-price')
                if card_value_element:
                    card_value_text = card_value_element.text.strip()
                else:
                    st.error(f"Could not find card value for this offer.")
                    st.write(f"HTML for the current offer:\n{offer.prettify()}")
                    continue  # Move on to the next offer
                
                # Extract the value in AUD and JPY
                try:
                    card_value = float(card_value_text.replace('$', '').replace(',', ''))
                except ValueError:
                    st.error(f"Could not convert card value to float: {card_value_text}")
                    continue


                # Find the card link
                card_link_element = offer.find('td', class_='photo').find('div').find('a')
                if card_link_element:
                    card_link = card_link_element.get('href')
                else:
                    st.error(f"Could not find card link for this offer.")
                    st.write(f"HTML for the current offer:\n{offer.prettify()}")
                    continue  # Move on to the next offer


                # Find the card image
                card_image_url_element = offer.find('td', class_='photo').find('div').find('a').find('img')
                if card_image_url_element:
                    card_image_url = card_image_url_element.get('src')
                else:
                    st.error(f"Could not find card image URL for this offer.")
                    st.write(f"HTML for the current offer:\n{offer.prettify()}")
                    continue  # Move on to the next offer


                # Fetch the image from the individual card page
                try:
                    card_response = requests.get(f"https://www.pricecharting.com{card_link}")
                    card_response.raise_for_status()
                    card_soup = BeautifulSoup(card_response.content, 'html.parser')

                    # Find the image tag by a more robust selector
                    card_image = card_soup.find('img', {'class': 'card-image'})
                    if card_image:
                        card_image = card_image.get('src')
                    else:
                        # Try a different selector for the image tag
                        card_image = card_soup.find('img', {'class': 'card-image'})
                        if card_image:
                            card_image = card_image.get('src')
                        else:
                            # Try to find the image by ID
                            card_image = card_soup.find('img', id='card_image')
                            if card_image:
                                card_image = card_image.get('src')
                            else:
                                st.error(f"Could not find the image tag for {card_name}")
                                st.write(f"HTML for the current card page:\n{card_soup.prettify()}")
                                continue  # Move on to the next offer

                        # Build the card display with a pop-up link
                        card_display = f"""
                        <a href="{card_link}" target="_blank">
                            <img src="{card_image}" alt="{card_name}" style="width: 200px; height: auto;">
                        </a>
                        <p><strong>Card Name:</strong> {card_name}</p>
                        <p><strong>Price:</strong> AU${card_value:.2f} / ¥{card_value * 100:.0f}</p>
                        """

                        cards[card_name] = {'AUD': card_value, 'JPY': card_value * 100, 'image_url': card_image, 'link': card_link}
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error fetching data from card page: {e}")
                        st.write(f"HTML for the current card page:\n{card_soup.prettify()}")
                        continue  # Move on to the next offer
                    except Exception as e:
                        st.error(f"An unexpected error occurred: {e}")
                        return None

                except AttributeError as e:
                    st.error(f"Error extracting data: {e}")
                    # Print the HTML for the current offer to help with debugging
                    st.write(f"HTML for the current offer:\n{offer.prettify()}")
                    continue  # Move on to the next offer
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
                    return None

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
        get_collection_data(collection_link)
    else:
        # If no collection link is found, prompt the user to input one
        collection_link = st.text_input('Paste your collection link here:')

    # Save the collection link when the user clicks the "Save Link" button
    if st.button('Save Link'):
        user_data[user_email] = collection_link
        save_user_data(user_data)
        st.success('Collection link saved!')

    if collection_link:
        if st.button('Refresh'):
            # Clear the cached data when refresh is clicked
            get_pokemon_cards.clear()
            cards = get_pokemon_cards(collection_link)
            display_cards(cards)
        else:
            # Display cards without refreshing the cache
            cards = get_pokemon_cards(collection_link)
            display_cards(cards)



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

    if collection_link:
        if st.button('Refresh'):
            # Clear the cached data when refresh is clicked
            get_pokemon_cards.clear()
            cards = get_pokemon_cards(collection_link)
            display_cards(cards)
        else:
            # Display cards without refreshing the cache
            cards = get_pokemon_cards(collection_link)
            display_cards(cards) 