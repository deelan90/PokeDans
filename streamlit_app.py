import streamlit as st
import requests
from bs4 import BeautifulSoup

# Function to fetch and extract data from PriceCharting
def get_pokemon_cards(collection_url):
    try:
        response = requests.get(collection_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        table = soup.find('table', id='active')
        if table:
            cards = []
            for offer in table.find_all('tr', class_='offer'):
                try:
                    # Card name
                    card_name_element = offer.find('td', class_='meta').find('p', class_='title').find('a')
                    card_name = card_name_element.text.strip() if card_name_element else "Unknown Name"

                    # Card value in USD
                    card_value_element = offer.find('td', class_='price').find('span', class_='js-price')
                    card_value_usd = card_value_element.text.strip() if card_value_element else "Unknown Value"

                    # Convert the value to AUD (example conversion, update as needed)
                    conversion_rate = 1.5  # Example conversion rate, update to current rate
                    card_value_aud = f"{float(card_value_usd.replace('$', '').replace(',', '')) * conversion_rate:.2f} AUD"

                    # Japanese price placeholder (replace with actual scraping logic if available)
                    card_value_jpy = f"{float(card_value_usd.replace('$', '').replace(',', '')) * 150:.2f} JPY"

                    # Card link
                    card_link_element = offer.find('td', class_='photo').find('div').find('a')
                    card_link = card_link_element.get('href') if card_link_element else None

                    # Grading name
                    grading_name_element = offer.find_all('td')[2]
                    grading_name = grading_name_element.text.strip() if grading_name_element else "No Grading"

                    # Fetch the high-resolution image
                    card_image_url = get_high_res_image(card_link) if card_link else None

                    # Create the card display
                    card_display = {
                        'name': card_name,
                        'grading_name': grading_name,
                        'value_aud': card_value_aud,
                        'value_jpy': card_value_jpy,
                        'image': card_image_url,
                        'link': f"https://www.pricecharting.com{card_link}" if card_link else None
                    }
                    cards.append(card_display)

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

# Function to fetch high-resolution images
def get_high_res_image(card_link):
    try:
        card_page_response = requests.get(f"https://www.pricecharting.com{card_link}")
        card_page_response.raise_for_status()
        card_page_soup = BeautifulSoup(card_page_response.content, 'html.parser')

        # Find the highest resolution image available
        card_image_element = card_page_soup.find('img', {'src': lambda x: x and ('jpeg' in x.lower() or 'jpg' in x.lower())})
        if card_image_element:
            return card_image_element.get('src')
        else:
            st.error("Could not find high-resolution image.")
            return None
    except Exception as e:
        st.error(f"Error fetching high-resolution image: {e}")
        return None

# Custom CSS to make images the same size and align titles
st.markdown("""
<style>
    .card-container {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .card-image {
        width: 200px;
        height: 200px;
        object-fit: cover;
    }
    .card-title {
        text-align: center;
        font-weight: bold;
        font-size: 20px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Function to display the cards in Streamlit
def display_cards(cards):
    if cards:
        cols = st.columns(2)  # Create two columns for the grid layout
        for idx, card in enumerate(cards):
            col = cols[idx % 2]  # Alternate between columns
            with col:
                st.markdown(f"<div class='card-container'><div class='card-title'>{card['name']}</div>", unsafe_allow_html=True)
                st.image(card['image'], caption=f"{card['grading_name']} - {card['name']}", use_column_width=True, class_="card-image")
                st.write(f"**Value (AUD):** {card['value_aud']}")
                st.write(f"**Value (JPY):** {card['value_jpy']}")
                st.markdown(f"[View on PriceCharting]({card['link']})")
                st.markdown("</div>", unsafe_allow_html=True)

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
