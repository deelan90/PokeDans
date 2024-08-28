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

        cards = []
        for offer in soup.find_all('tr', class_='offer'):
            card_name = offer.find('td', class_='meta').find('p', class_='title').find('a').text
            card_value = offer.find('td', class_='price').find('span', class_='js-price').text
            card_image = offer.find('td', class_='photo').find('div').find('a').find('img').get('src')
            cards.append({
                'name': card_name,
                'value': card_value,
                'image': card_image
            })
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
        for card in cards:
            st.image(card['image'])
            st.write(f"**Card Name:** {card['name']}")
            st.write(f"**Value:** {card['value']}")
            st.write("---")

# Get the Pokémon card data
cards = get_pokemon_cards()

# Display the cards
display_cards(cards)
