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

                        # Attempt to find the high-res image
                        card_image_element = card_page_soup.find('img', {'class': 'card-image'})
                        card_image_url = card_image_element.get('src') if card_image_element else None

                        if not card_image_url:
                            # Fallback to low-res image
                            card_image_url = offer.find('td', class_='photo').find('div').find('a').find('img').get('src')

                        # Build the card display with a pop-up link
                        card_display = f"""
                        <a href="{card_link}" target="_blank">
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

# Fetch and display the data
def display_cards(cards):
    if cards:
        for card in cards:
            st.markdown(card, unsafe_allow_html=True)

# Get the Pokémon card data
cards = get_pokemon_cards()

# Display the cards
display_cards(cards)
