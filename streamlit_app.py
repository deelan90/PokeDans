import streamlit as st
import requests
from bs4 import BeautifulSoup

# Set the page configuration
st.set_page_config(page_title="PokéDan", page_icon=":zap:", layout="wide")

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
                card_name_element = offer.find('td', class_='meta')
                if not card_name_element:
                    st.error("Card name element not found.")
                    continue
                
                card_name_tag = card_name_element.find('p', class_='title').find('a')
                if not card_name_tag:
                    st.error("Card name tag not found.")
                    continue
                
                card_name = card_name_tag.text.strip()

                card_value_element = offer.find('td', class_='price').find('span', class_='js-price')
                if not card_value_element:
                    st.error(f"Card value element not found for {card_name}.")
                    continue
                
                card_value_usd = card_value_element.text.strip()

                conversion_rate_aud = 1.5  # Placeholder conversion rate, update to current rate
                conversion_rate_jpy = 150  # Placeholder conversion rate, update to current rate
                card_value_aud = f"${float(card_value_usd.replace('$', '').replace(',', '')) * conversion_rate_aud:.2f} AUD"
                card_value_jpy = f"¥{float(card_value_usd.replace('$', '').replace(',', '')) * conversion_rate_jpy:.2f} JPY"

                card_link_element = offer.find('td', class_='photo').find('div').find('a')
                if not card_link_element:
                    st.error(f"Card link element not found for {card_name}.")
                    continue
                
                card_link = card_link_element.get('href')

                card_image_url = get_high_res_image(card_link) if card_link else None

                grading_element = offer.find('td', class_='includes').find('select')
                if not grading_element:
                    st.error(f"Grading element not found for {card_name}.")
                    continue

                selected_option = grading_element.find('option', selected=True)
                grading_name = selected_option.text.strip() if selected_option else "Ungraded"

                if card_name not in cards:
                    cards[card_name] = {
                        'name': card_name,
                        'image': card_image_url,
                        'gradings': []
                    }
                
                cards[card_name]['gradings'].append({
                    'grading_name': grading_name,
                    'value_aud': card_value_aud,
                    'value_jpy': card_value_jpy,
                    'link': f"https://www.pricecharting.com{card_link}" if card_link else None
                })

            except Exception as e:
                st.error(f"An unexpected error occurred while processing {card_name}: {e}")
                continue

        return sorted(list(cards.values()), key=lambda x: x['name'])
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None

def get_high_res_image(card_link):
    try:
        card_page_response = requests.get(f"https://www.pricecharting.com{card_link}")
        card_page_response.raise_for_status()
        card_page_soup = BeautifulSoup(card_page_response.content, 'html.parser')
        card_image_element = card_page_soup.find('img', {'src': lambda x: x and ('jpeg' in x.lower() or 'jpg' in x.lower())})
        return card_image_element.get('src') if card_image_element else None
    except Exception as e:
        st.error(f"Error fetching high-resolution image: {e}")
        return None

def display_cards(cards):
    if not cards:
        st.warning("No cards to display.")
        return

    desktop_mode = st.sidebar.checkbox("Desktop View", value=True)
    num_columns = 8 if desktop_mode else 2

    st.markdown("""
        <style>
            .card-container {
                display: flex;
                flex-wrap: wrap;
                justify-content: space-around;
            }
            .card {
                flex: 1 0 21%;
                margin: 10px;
                text-align: center;
            }
            .card-image {
                max-width: 100%;
                border-radius: 10px;
            }
            .grading-container {
                background-color: transparent;
                padding: 8px;
                border-radius: 8px;
                margin-top: 10px;
            }
            @media (max-width: 1200px) {
                .card {
                    flex: 1 0 45%;
                }
            }
        </style>
    """, unsafe_allow_html=True)

    for card in cards:
        st.markdown(f"### {card['name']}")
        st.markdown('<div class="card-container">', unsafe_allow_html=True)

        st.markdown(f"""
            <div class="card">
                <img src="{card['image']}" class="card-image" alt="{card['name']}">
            </div>
        """, unsafe_allow_html=True)

        for grading in card['gradings']:
            st.markdown(f"""
                <div class="card">
                    <div class="grading-container">
                        <h4 style="font-size: 18px;">{grading['grading_name']}</h4>
                        <p style="font-size: 16px;">AUD: {grading['value_aud']}</p>
                        <p style="font-size: 16px;">JPY: {grading['value_jpy']}</p>
                        <a href="{grading['link']}" target="_blank">View on PriceCharting</a>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<hr>', unsafe_allow_html=True)

# Function to fetch wishlist items
def get_wishlist_items(wishlist_url):
    try:
        response = requests.get(wishlist_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        wishlist_items = []
        table = soup.find('table', id='games_table')
        if not table:
            st.error("Could not find the wishlist data table.")
            return None

        for row in table.find_all('tr')[1:]:
            try:
                item_name_element = row.find('td', class_='console')
                item_link_element = row.find('a')
                if not item_name_element or not item_link_element:
                    continue

                item_name = item_name_element.text.strip()
                item_link = item_link_element.get('href')

                wishlist_items.append({
                    'name': item_name,
                    'link': item_link
                })
            except Exception as e:
                st.error(f"An error occurred processing a wishlist item: {e}")
                continue

        return wishlist_items
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching wishlist data: {e}")
        return None

def display_wishlist_items(wishlist_items):
    if not wishlist_items:
        st.warning("No wishlist items to display.")
        return

    st.markdown("## Wishlist")
    st.markdown('<div class="card-container">', unsafe_allow_html=True)

    for item in wishlist_items:
        st.markdown(f"### {item['name']}")
        st.markdown('<div class="card-container">', unsafe_allow_html=True)

        item_page = requests.get(f"https://www.pricecharting.com{item['link']}")
        item_page_soup = BeautifulSoup(item_page.content, 'html.parser')

        # Get image
        item_image_element = item_page_soup.find('img', {'src': lambda x: x and ('jpeg' in x.lower() or 'jpg' in x.lower())})
        item_image_url = item_image_element.get('src') if item_image_element else None

        # Display image
        if item_image_url:
            st.markdown(f"""
                <div class="card">
                    <img src="{item_image_url}" class="card-image" alt="{item['name']}">
                </div>
            """, unsafe_allow_html=True)

        # Display grades 9, 10, and ungraded
        grades = ['9', '10', 'Ungraded']
        for grade in grades:
            st.markdown(f"""
                <div class="card">
                    <div class="grading-container">
                        <h4 style="font-size: 18px;">{grade}</h4>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)

# Streamlit app setup
st.title("PokéDan")

collection_link = st.text_input("Enter the collection link:")
if collection_link:
    st.success(f"Your saved collection link: {collection_link}")
    cards = get_pokemon_cards(collection_link)
    if cards:
        display_cards(cards)
    st.text_input("Enter the collection link:", value="", key="hidden", label_visibility="hidden")
else:
    st.warning("Please enter a collection link to proceed.")
