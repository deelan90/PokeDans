import streamlit as st
import requests
from bs4 import BeautifulSoup

# Custom CSS for Pokémon-style font and subtle bold grading titles
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Flexo:wght@700&display=swap');

body {
    font-family: 'Franklin Gothic Medium', 'Arial Narrow', Arial, sans-serif;
}

.pokemon-title {
    font-family: 'Flexo', sans-serif;
    font-size: 48px;
    font-weight: 700;
    color: #FFCB05;
    letter-spacing: 2px;
    padding: 20px;
    text-align: center;
    margin-bottom: 20px;
}

.pokemon-font {
    font-family: 'Flexo', sans-serif;
    color: #FFCB05;
    font-size: 18px;
    margin-bottom: 10px;
}

.card-container {
    text-align: center;
    margin-bottom: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.card-image {
    max-width: 100%;
    height: auto;
    border-radius: 10px;
}

.grading-card {
    background-color: #000;
    color: #FFF;
    padding: 2px;
    border-radius: 2px;
    margin-bottom: 2px;
    width: 100%;
    box-sizing: border-box;
}

.grading-card h4 {
    font-weight: bold;
    font-size: 12px;
    margin: 0;
    text-align: center;
}

@media screen and (min-width: 768px) {
    .stImage > img {
        object-fit: cover;
        max-width: 100%;
        height: auto;
    }

    .card-container {
        display: flex;
        align-items: flex-start;
    }

    .stColumns {
        display: flex;
        flex-wrap: nowrap;
    }

    .stColumn {
        flex: 1;
    }
}
</style>
""", unsafe_allow_html=True)

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
            return None
    except Exception as e:
        st.error(f"Error fetching high-resolution image: {e}")
        return None

# Function to fetch and extract data from PriceCharting
def get_pokemon_cards(collection_url):
    try:
        response = requests.get(collection_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        table = soup.find('table', id='active')
        if not table:
            st.error("Could not find the card data table.")
            return None

        cards = {}
        for offer in table.find_all('tr', class_='offer'):
            try:
                # Ensure card_name_element exists before accessing
                card_name_element = offer.find('td', class_='meta').find('p', class_='title').find('a')
                if card_name_element:
                    card_name = card_name_element.text.strip()
                else:
                    continue

                # Ensure grading_element exists and has at least 3 elements before accessing
                grading_elements = offer.find('td', class_='meta').find_all('p')
                if len(grading_elements) >= 3:
                    grading_name = grading_elements[2].text.strip()
                else:
                    grading_name = "Ungraded"

                # Ensure price_element exists before accessing
                price_element = offer.find('td', class_='price').find('span', class_='js-price')
                if price_element:
                    card_value_usd = price_element.text.strip()
                else:
                    card_value_usd = "Unknown Value"

                # Convert the value to AUD and JPY
                try:
                    usd_value = float(card_value_usd.replace('$', '').replace(',', ''))
                    card_value_aud = f"${usd_value * 1.5:.2f} AUD"
                    card_value_jpy = f"¥{usd_value * 150:.2f} JPY"
                except ValueError:
                    card_value_aud = "Unknown Value"
                    card_value_jpy = "Unknown Value"

                # Ensure card_link_element exists before accessing
                card_link_element = offer.find('td', class_='photo').find('div').find('a')
                if card_link_element:
                    card_link = card_link_element.get('href')
                else:
                    card_link = None

                # Fetch or update card entry
                if card_name not in cards:
                    cards[card_name] = {
                        'image': get_high_res_image(card_link) if card_link else None,
                        'gradings': []
                    }
                cards[card_name]['gradings'].append({
                    'grading_name': grading_name,
                    'value_aud': card_value_aud,
                    'value_jpy': card_value_jpy,
                    'link': f"https://www.pricecharting.com{card_link}" if card_link else None
                })

            except Exception as e:
                st.error(f"An error occurred processing a card: {e}")
                continue

        return cards
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None

# Function to display the cards in Streamlit
def display_cards(cards):
    if cards:
        cols = st.columns(2)  # Create two columns for the grid layout
        for idx, (card_name, card) in enumerate(cards.items()):
            col = cols[idx % 2]  # Alternate between columns
            with col:
                st.markdown(f"<div class='card-container'><div class='card-image'>", unsafe_allow_html=True)
                if card['image']:
                    st.image(card['image'], caption=f"{card_name}", use_column_width=True)
                else:
                    st.write("Image not available")
                st.markdown("</div>", unsafe_allow_html=True)
                for grading in card['gradings']:
                    st.markdown(f"<div class='grading-card'><h4>{grading['grading_name']}</h4>", unsafe_allow_html=True)
                    st.write(f"AUD: {grading['value_aud']}")
                    st.write(f"JPY: {grading['value_jpy']}")
                    if grading['link']:
                        st.markdown(f"[View on PriceCharting]({grading['link']})")
                    st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

# Streamlit app setup
st.markdown("<h1 class='pokemon-title'>PokéDan</h1>", unsafe_allow_html=True)

# Input for the collection URL
collection_link = st.text_input("Enter the collection link:")
if collection_link:
    st.success(f"Your saved collection link: {collection_link}")
    cards = get_pokemon_cards(collection_link)
    if cards:
        display_cards(cards)
    else:
        st.error("No cards found or an error occurred. Please check the logs for more information.")
else:
    st.warning("Please enter a collection link to proceed.")

# Hide the input field after submission
if collection_link:
    st.text_input("Enter the collection link:", value=collection_link, key="hidden", label_visibility="hidden")
