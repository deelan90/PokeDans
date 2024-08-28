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
                        st.write(f"HTML for the current offer:\n{offer.prettify()}")
                        continue  # Move on to the next offer


                    # Find the card value
                    card_value_element = offer.find('td', class_='price').find('span', class_='js-price')
                    if card_value_element:
                        card_value = card_value_element.text
                    else:
                        st.error(f"Could not find card value for this offer.")
                        st.write(f"HTML for the current offer:\n{offer.prettify()}")
                        continue  # Move on to the next offer


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
                        <p>**Card Name:** {card_name}</p>
                        <p>**Value:** {card_value}</p>
                        """

                        cards.append(card_display)
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
        for card in cards:
            st.markdown(card, unsafe_allow_html=True)

# Get the Pokémon card data
cards = get_pokemon_cards()

# Display the cards
display_cards(cards) 