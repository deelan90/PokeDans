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

        # Extract only the relevant part of the HTML
        # Get the table with the card data
        table = soup.find('table', id='active')

        if table:
            cards = []
            for offer in table.find_all('tr', class_='offer'):
                try:
                    # Find the card name
                    card_name_element = offer.find('td', class_='meta').find('p', class_='title').find('a')
                    if card_name_element:
                        card_name = card_name_element.text
                    else:
                        st.error(f"Could not find card name for this offer.")
                        continue  # Move on to the next offer

                    # Find the card value
                    card_value_element = offer.find('td', class_='price').find('span', class_='js-price')
                    if card_value_element:
                        card_value = card_value_element.text
                    else:
                        st.error(f"Could not find card value for this offer.")
                        continue  # Move on to the next offer

                    # Find the card link
                    card_link_element = offer.find('td', class_='photo').find('div').find('a')
                    if card_link_element:
                        card_link = card_link_element.get('href')
                    else:
                        st.error(f"Could not find card link for this offer.")
                        continue  # Move on to the