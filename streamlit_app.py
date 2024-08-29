import streamlit as st
import requests
from bs4 import BeautifulSoup

# Function to fetch detailed grading data from the card's individual page
def fetch_grading_data(card_page_url):
    try:
        card_page_response = requests.get(card_page_url)
        card_page_response.raise_for_status()
        card_page_soup = BeautifulSoup(card_page_response.content, 'html.parser')
        
        # Locate the grading data on the individual card page
        grading_data = {}
        grading_table = card_page_soup.find('table', {'class': 'graded_prices_table'})
        
        if grading_table:
            for row in grading_table.find_all('tr')[1:]:  # Skipping the header
                cells = row.find_all('td')
                if len(cells) >= 2:
                    grading = cells[0].text.strip()
                    price = cells[1].text.strip()
                    grading_data[grading] = price
        return grading_data
    
    except Exception as e:
        st.error(f"Error fetching grading data: {e}")
        return {}

# Function to get Pokémon cards from the collection URL
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
                    continue
                card_name_tag = card_name_element.find('p', class_='title').find('a')
                if not card_name_tag:
                    continue
                card_name = card_name_tag.text.strip()

                card_value_element = offer.find('td', class_='price').find('span', class_='js-price')
                if not card_value_element:
                    continue
                card_value_usd = card_value_element.text.strip()

                conversion_rate_aud = 1.5  # Placeholder
                conversion_rate_jpy = 150  # Placeholder
                card_value_aud = f"${float(card_value_usd.replace('$', '').replace(',', '')) * conversion_rate_aud:.2f} AUD"
                card_value_jpy = f"¥{float(card_value_usd.replace('$', '').replace(',', '')) * conversion_rate_jpy:.2f} JPY"

                card_link_element = offer.find('td', class_='photo').find('div').find('a')
                card_link = card_link_element.get('href') if card_link_element else None
                card_image_url = get_high_res_image(card_link) if card_link else None

                # Updated grading extraction
                grading_element = offer.find('td', class_='grade')
                if grading_element:
                    grading_name = grading_element.text.strip()
                    # Check if it's a graded card
                    if grading_name in ['PSA', 'BGS', 'CGC']:
                        grade_number = offer.find('td', class_='grade-number')
                        if grade_number:
                            grading_name += f" {grade_number.text.strip()}"
                    elif grading_name == '':
                        grading_name = "Ungraded"
                else:
                    grading_name = "Ungraded"

                if card_name not in cards:
                    cards[card_name] = {
                        'name': card_name,
                        'image': card_image_url,
                        'gradings': []
                    }
                
                # Fetch the detailed grading data
                if card_link:
                    grading_data = fetch_grading_data(f"https://www.pricecharting.com{card_link}")
                    for grading, value in grading_data.items():
                        cards[card_name]['gradings'].append({
                            'grading_name': grading,
                            'value_aud': f"${float(value.replace('$', '').replace(',', '')) * conversion_rate_aud:.2f} AUD",
                            'value_jpy': f"¥{float(value.replace('$', '').replace(',', '')) * conversion_rate_jpy:.2f} JPY",
                            'link': f"https://www.pricecharting.com{card_link}" if card_link else None
                        })
                else:
                    cards[card_name]['gradings'].append({
                        'grading_name': grading_name,
                        'value_aud': card_value_aud,
                        'value_jpy': card_value_jpy,
                        'link': f"https://www.pricecharting.com{card_link}" if card_link else None
                    })
            except Exception as e:
                st.error(f"An error occurred processing a card: {e}")
                continue
        return list(cards.values())
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None

# Function to fetch high-resolution images
def get_high_res_image(card_link):
    try:
        if not card_link:
            return None
        card_page_response = requests.get(f"https://www.pricecharting.com{card_link}")
        card_page_response.raise_for_status()
        card_page_soup = BeautifulSoup(card_page_response.content, 'html.parser')
        card_image_element = card_page_soup.find('img', {'src': lambda x: x and ('jpeg' in x.lower() or 'jpg' in x.lower())})
        return card_image_element.get('src') if card_image_element else None
    except Exception as e:
        st.error(f"Error fetching high-resolution image: {e}")
        return None

# Function to display the cards
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
                width: calc(100% / 8 - 20px);
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
                    width: calc(100% / 2 - 20px);
                }
            }
        </style>
    """, unsafe_allow_html=True)

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

# Streamlit app setup
st.set_page_config(page_title="PokéDan", page_icon=":zap:", layout="wide")
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
