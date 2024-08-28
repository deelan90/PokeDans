import streamlit as st
import requests
from bs4 import BeautifulSoup

st.title("Pokémon Card Tracker")

# Define the PriceCharting URL
priceChartingUrl = 'https://www.pricecharting.com/offers?seller=ym3hqoown5rn5kk7vymq5bjvfq&status=collection'

# Function to fetch and extract data from PriceCharting
def get_pokemon_cards():
    try:
        response = requests.get(priceChartingUrl)
        response.raise_for_status()  # Raise an exception for bad responses
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract the table with the card data
        table = soup.find('table', id='active')

        if table:
            cards = []
            for offer in table.find_all('tr', class_='offer'):
                try:
                    # Extract card details
                    card_name_element = offer.find('td', class_='meta').find('p', class_='title').find('a')
                    card_value_element = offer.find('td', class_='price').find('span', class_='js-price')
                    card_image_url_element = offer.find('td', class_='photo').find('div').find('a').find('img')
                    
                    if not (card_name_element and card_value_element and card_image_url_element):
                        st.error("Incomplete data found, skipping this offer.")
                        continue

                    card_name = card_name_element.text
                    card_value = card_value_element.text
                    card_image_url = card_image_url_element.get('src')
                    card_link = card_name_element.get('href')

                    # Build the card display
                    card_display = f"""
                    <a href="https://www.pricecharting.com{card_link}" target="_blank">
                        <img src="{card_image_url}" alt="{card_name}" style="width: 200px; height: auto;">
                    </a>
                    <p><strong>Card Name:</strong> {card_name}</p>
                    <p><strong>Value:</strong> {card_value}</p>
                    """

                    cards.append(card_display)
                except Exception as e:
                    st.error(f"Error extracting data: {e}")
                    continue

            return cards
        else:
            st.error("Could not find the card data table.")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None

# Fetch and display the data
def display_cards(cards):
    if cards:
        for card in cards:
            st.markdown(card, unsafe_allow_html=True)

# Get the Pokémon card data
cards = get_pokemon_cards()

# Display the cards
display_cards(cards)