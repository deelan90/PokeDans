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
                    card_name = offer.find('td', class_='meta').find('p', class_='title').find('a').text
                    card_value = offer.find('td', class_='price').find('span', class_='js-price').text
                    card_image_url = offer.find('td', class_='photo').find('div').find('a').find('img').get('src')
                    card_link = offer.find('td', class_='photo').find('div').find('a').get('href')

                    # Create a table to display the card information
                    card_table = f"""
                    <table style="width:100%">
                        <tr>
                            <td>**Card Name:**</td>
                            <td>{card_name}</td>
                        </tr>
                        <tr>
                            <td>**Value:**</td>
                            <td>{card_value}</td>
                        </tr>
                        <tr>
                            <td>**Image URL:**</td>
                            <td>{card_image_url}</td>
                        </tr>
                        <tr>
                            <td>**Card Link:**</td>
                            <td>{card_link}</td>
                        </tr>
                    </table>
                    """
                    cards.append(card_table)
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