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
                    # Try to find the elements using a more flexible approach
                    card_name = offer.find('td', class_='meta').find('p', class_='title').find('a').text
                    card_value = offer.find('td', class_='price').find('span', class_='js-price').text
                    card_image_url = offer.find('td', class_='photo').find('div').find('a').find('img').get('src')
                    card_link = offer.find('td', class_='photo').find('div').find('a').get('href')

                    # Fetch the image from the individual card page
                    card_response = requests.get(f"https://www.pricecharting.com{card_link}")
                    card_response.raise_for_status()
                    card_soup = BeautifulSoup(card_response.content, 'html.parser')
                    try:
                        card_image = card_soup.find('img', class_='card-image').get('src')
                    except AttributeError:
                        # If 'card-image' class is not found, try another approach
                        card_image = card_soup.find('img', class_='image-rotate-canvas').get('src') 

                    # Build the card display with a pop-up link
                    card_display = f"""
                    <a href="{card_link}" target="_blank">
                        <img src="{card_image}" alt="{card_name}" style="width: 200px; height: auto;">
                    </a>
                    <p>**Card Name:** {card_name}</p>
                    <p>**Value:** {card_value}</p>
                    """

                    cards.append(card_display)
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
        for card in cards:
            st.markdown(card, unsafe_allow_html=True)

# Get the Pokémon card data
cards = get_pokemon_cards()

# Display the cards
display_cards(cards) 
