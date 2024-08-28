import streamlit as st
import requests
from bs4 import BeautifulSoup
from collections import defaultdict

# Function to fetch and extract data from PriceCharting
def get_pokemon_cards(collection_url):
    try:
        response = requests.get(collection_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        table = soup.find('table', id='active')
        if table:
            cards = defaultdict(list)
            for offer in table.find_all('tr', class_='offer'):
                try:
                    # Card name
                    card_name_element = offer.find('td', class_='meta').find('p', class_='title').find('a')
                    card_name = card_name_element.text.strip() if card_name_element else "Unknown Name"

                    # Grading name (using a more reliable path)
                    grading_element = offer.find('td', class_='includes')
                    grading_name = grading_element.text.strip() if grading_element else "Ungraded"

                    # Card value in USD
                    card_value_element = offer.find('td', class_='price').find('span', class_='js-price')
                    card_value_usd = card_value_element.text.strip() if card_value_element else "0.00"

                    # Convert the value to AUD and JPY
                    conversion_rate_aud = 1.5  # Example conversion rate
                    conversion_rate_jpy = 150  # Example conversion rate
                    card_value_aud = f"{float(card_value_usd.replace('$', '').replace(',', '')) * conversion_rate_aud:.2f} AUD"
                    card_value_jpy = f"{float(card_value_usd.replace('$', '').replace(',', '')) * conversion_rate_jpy:.2f} JPY"

                    # Card link and image
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

                        cards[(card_name, card_image_url)].append({
                            'grading_name': grading_name,
                            'value_aud': card_value_aud,
                            'value_jpy': card_value_jpy,
                            'link': f"https://www.pricecharting.com{card_link}"
                        })

                    else:
                        st.error(f"Could not find card link for {card_name}.")
                        continue

                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
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

# Fetch and display the data in a grid layout
def display_cards(cards):
    if cards:
        cols = st.columns(2)  # Create two columns for the grid layout
        for idx, ((card_name, card_image), gradings) in enumerate(cards.items()):
            col = cols[idx % 2]  # Alternate between columns
            with col:
                st.markdown(f"<h3 style='font-family: pokemon; color: #FFCB05;'>{card_name}</h3>", unsafe_allow_html=True)
                st.image(card_image, use_column_width=True)
                for grading in gradings:
                    st.write(f"**{grading['grading_name']}:** {grading['value_aud']} | {grading['value_jpy']}")
                st.markdown(f"[View on PriceCharting]({grading['link']})")

# Streamlit app setup
st.title("Pokémon Card Tracker")

# Input for the collection URL
collection_link = st.text_input("Enter the collection link:")

if collection_link:
    st.success(f"Your saved collection link: {collection_link}")
    cards = get_pokemon_cards(collection_link)
    if cards:
        display_cards(cards)
else:
    st.warning("Please enter a collection link to proceed.")

# Hide the input field after submission
if collection_link:
    st.text_input("Enter the collection link:", value=collection_link, key="hidden", label_visibility="hidden")

# Custom CSS to add a Pokémon-style font
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
    .pokemon-font {
        font-family: 'Press Start 2P', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)
