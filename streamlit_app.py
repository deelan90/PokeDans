import streamlit as st
import requests
from bs4 import BeautifulSoup
from collections import defaultdict

st.title("Pokémon Card Tracker")

# Input for collection link
collection_link = st.text_input("Enter your collection link:", "")

if collection_link:
    # Save and hide the collection link after entering
    st.session_state.collection_link = collection_link

if 'collection_link' in st.session_state:
    priceChartingUrl = st.session_state.collection_link
    st.markdown(f"**Collection link saved**")

    # Function to fetch and extract data from PriceCharting
    def get_pokemon_cards():
        try:
            response = requests.get(priceChartingUrl)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            table = soup.find('table', id='active')

            if table:
                cards = defaultdict(lambda: {"image": "", "AUD": 0, "JPY": 0})

                for offer in table.find_all('tr', class_='offer'):
                    try:
                        # Initialize card_name to prevent the error
                        card_name = "Unknown Name"

                        card_name_element = offer.find('td', class_='meta').find('p', class_='title').find('a')
                        card_name = card_name_element.text.strip() if card_name_element else card_name

                        card_value_element = offer.find('td', class_='price').find('span', class_='js-price')
                        card_value = card_value_element.text.strip() if card_value_element else "Unknown Value"

                        card_currency = "AUD" if "AU$" in card_value else "JPY" if "¥" in card_value else ""

                        card_value = float(card_value.replace("AU$", "").replace("¥", "").replace(",", "").strip())

                        card_link_element = offer.find('td', class_='photo').find('div').find('a')
                        card_link = card_link_element.get('href') if card_link_element else None

                        if card_link:
                            card_page_response = requests.get(f"https://www.pricecharting.com{card_link}")
                            card_page_response.raise_for_status()
                            card_page_soup = BeautifulSoup(card_page_response.content, 'html.parser')

                            card_image_element = card_page_soup.find('img', {'src': lambda x: x and ('jpeg' in x.lower() or 'jpg' in x.lower())})
                            card_image_url = card_image_element.get('src') if card_image_element else None

                            if not card_image_url:
                                card_image_url = offer.find('td', class_='photo').find('div').find('a').find('img').get('src')

                            cards[card_name]["image"] = card_image_url or cards[card_name]["image"]
                            if card_currency == "AUD":
                                cards[card_name]["AUD"] += card_value
                            elif card_currency == "JPY":
                                cards[card_name]["JPY"] += card_value

                    except Exception as e:
                        st.error(f"An unexpected error occurred while processing {card_name}: {e}")
                        continue

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

    def display_cards(cards):
        if cards:
            cols = st.columns(2)
            index = 0
            for card_name, details in cards.items():
                with cols[index % 2]:
                    st.markdown(
                        f"""
                        <img src="{details['image']}" alt="{card_name}" style="width: 200px; height: auto;">
                        <p><strong>{card_name}</strong></p>
                        <p><strong>Price:</strong> ${details['AUD']:.2f} / ¥{details['JPY']:.0f}</p>
                        """,
                        unsafe_allow_html=True
                    )
                index += 1

    cards = get_pokemon_cards()
    display_cards(cards)