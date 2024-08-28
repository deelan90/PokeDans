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
        cards = []
        for offer in soup.find_all('tr', class_='offer'):
            try:
                # Extract card details
                card_name_element = offer.find('td', class_='meta').find('p', class_='title').find('a')
                card_value_element = offer.find('td', class_='price').find('span', class_='js-price')
                card_image_element = offer.find('td', class_='photo').find('div').find('a').find('img')
                card_link_element = offer.find('td', class_='photo').find('div').find('a')

                if card_name_element and card_value_element and card_image_element and card_link_element:
                    card_name = card_name_element.text.strip()
                    card_value = card_value_element.text.strip()
                    card_image_url = card_image_element.get('src')
                    card_link = card_link_element.get('href')

                    # Fetch the high-resolution image from the individual card page
                    card_response = requests.get(f"https://www.pricecharting.com{card_link}")
                    card_response.raise_for_status()
                    card_soup = BeautifulSoup(card_response.content, 'html.parser')
                    
                    # Find the higher resolution image, fallback to original if not found
                    card_image_high_res = card_soup.find('img', class_='card-image') or card_soup.find('img', class_='image-rotate-canvas')
                    card_image = card_image_high_res.get('src') if card_image_high_res else card_image_url

                    # Build the card display with a pop-up link
                    card_display = f"""
                    <a href="{card_link}" target="_blank">
                        <img src="{card_image}" alt="{card_name}" style="width: 200px; height: auto;">
                    </a>
                    <p><strong>Card Name:</strong> {card_name}</p>
                    <p><strong>Value:</strong> {card_value}</p>
                    """

                    cards.append(card_display)
                else:
                    st.error("One or more elements were not found for this offer.")
                    st.write(f"HTML for the current offer:\n{offer.prettify()}")

            except AttributeError as e:
                st.error(f"Error extracting data: {e}")
                # Print the HTML for the current offer to help with debugging
                st.write(f"HTML for the current offer:\n{offer.prettify()}")
                continue  # Move on to the next offer
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                return None

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
            st.markdown(card, unsafe_allow_html=True)

# Get the Pokémon card data
cards = get_pokemon_cards()

# Display the cards
display_cards(cards)
