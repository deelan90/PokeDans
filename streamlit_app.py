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
                # Card name
                card_name_element = offer.find('td', class_='meta')
                if not card_name_element:
                    st.error("Card name element not found.")
                    continue
                
                card_name_tag = card_name_element.find('p', class_='title').find('a')
                if not card_name_tag:
                    st.error("Card name tag not found.")
                    continue
                
                card_name = card_name_tag.text.strip()

                # Card value in USD
                card_value_element = offer.find('td', class_='price').find('span', class_='js-price')
                if not card_value_element:
                    st.error(f"Card value element not found for {card_name}.")
                    continue
                
                card_value_usd = card_value_element.text.strip()

                # Convert the value to AUD and JPY
                conversion_rate_aud = 1.5  # Placeholder conversion rate, update to current rate
                conversion_rate_jpy = 150  # Placeholder conversion rate, update to current rate
                card_value_aud = f"${float(card_value_usd.replace('$', '').replace(',', '')) * conversion_rate_aud:.2f} AUD"
                card_value_jpy = f"¥{float(card_value_usd.replace('$', '').replace(',', '')) * conversion_rate_jpy:.2f} JPY"

                # Card link
                card_link_element = offer.find('td', class_='photo').find('div').find('a')
                if not card_link_element:
                    st.error(f"Card link element not found for {card_name}.")
                    continue
                
                card_link = card_link_element.get('href')

                # Fetch the high-resolution image
                card_image_url = get_high_res_image(card_link) if card_link else None

                # Extract the selected grading option from the dropdown
                grading_element = offer.find('td', class_='includes').find('select')
                if not grading_element:
                    st.error(f"Grading element not found for {card_name}.")
                    continue

                selected_option = grading_element.find('option', selected=True)
                grading_name = selected_option.text.strip() if selected_option else "Ungraded"

                # Organize data
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

# Function to fetch high-resolution images
def get_high_res_image(card_link):
    try:
        card_page_response = requests.get(f"https://www.pricecharting.com{card_link}")
        card_page_response.raise_for_status()
        card_page_soup = BeautifulSoup(card_page_response.content, 'html.parser')

        # Find the highest resolution image available
        card_image_element = card_page_soup.find('img', {'src': lambda x: x and ('jpeg' in x.lower() or 'jpg' in x.lower())})
        return card_image_element.get('src') if card_image_element else None
    except Exception as e:
        st.error(f"Error fetching high-resolution image: {e}")
        return None

# Function to fetch wishlist items
def get_wishlist_items(wishlist_url):
    try:
        response = requests.get(wishlist_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        table = soup.find('table', id='games_table')
        if not table:
            st.error("Could not find the wishlist data table.")
            return None

        wishlist_items = []
        for row in table.find_all('tr'):
            try:
                WL_item_name_element = row.find('td', class_='console')
                if not WL_item_name_element:
                    continue

                WL_item_name = WL_item_name_element.text.strip()

                WL_item_link_element = row.find('td').find('a')
                if not WL_item_link_element:
                    continue

                WL_item_link = WL_item_link_element.get('href')
                WL_item_image_url = get_high_res_image(WL_item_link)

                # Adding grading information with placeholders for now
                wishlist_items.append({
                    'name': WL_item_name,
                    'image': WL_item_image_url,
                    'gradings': [
                        {'grading_name': '9', 'value_aud': '$XX.XX AUD', 'value_jpy': '¥XXXXX JPY', 'link': WL_item_link},
                        {'grading_name': '10', 'value_aud': '$XX.XX AUD', 'value_jpy': '¥XXXXX JPY', 'link': WL_item_link},
                        {'grading_name': 'Ungraded', 'value_aud': '$XX.XX AUD', 'value_jpy': '¥XXXXX JPY', 'link': WL_item_link}
                    ]
                })

            except Exception as e:
                st.error(f"An unexpected error occurred while processing {WL_item_name}: {e}")
                continue

        return wishlist_items
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching wishlist data: {e}")
        return None

# Function to display the cards
def display_cards(cards, title):
    if not cards:
        st.warning(f"No {title.lower()} to display.")
        return

    st.subheader(title)
    st.markdown('<div class="card-container">', unsafe_allow_html=True)

    for card in cards:
        st.markdown(f"### {card['name']}")
        st.markdown('<div class="card-container">', unsafe_allow_html=True)

        # Display card image once
        st.markdown(f"""
            <div class="card">
                <img src="{card['image']}" class="card-image" alt="{card['name']}">
            </div>
        """, unsafe_allow_html=True)

        # Display gradings
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

    st.markdown('</div>', unsafe_allow_html=True)

# Streamlit app setup
st.title("PokéDan")

collection_link = st.text_input("Enter the collection link:")
if collection_link:
    st.success(f"Your saved collection link: {collection_link}")
    cards = get_pokemon_cards(collection_link)
    if cards:
        display_cards(cards, "Collection")
    st.text_input("Enter the collection link:", value="", key="hidden", label_visibility="hidden")
else:
    st.warning("Please enter a collection link to proceed.")

# Display Wishlist
wishlist_link = "https://www.pricecharting.com/wishlist?user=ym3hqoown5rn5kk7vymq5bjvfq"  # Replace with actual URL
wishlist_items = get_wishlist_items(wishlist_link)
if wishlist_items:
    display_cards(wishlist_items, "Wishlist")
