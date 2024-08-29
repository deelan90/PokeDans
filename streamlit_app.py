import streamlit as st
import requests
from bs4 import BeautifulSoup

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

# ... (rest of the code remains the same)

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

def display_cards(cards):
    if cards:
        num_columns = 8 if st.sidebar.checkbox("Desktop View", value=True) else 2
        st.markdown("""
            <style>
                .card-image-container { text-align: center; }
                .card-image { border-radius: 10px; margin-bottom: 15px; max-height: 200px; }
                .grading-container { background-color: rgba(255,255,255,0.1); padding: 8px; border-radius: 8px; margin-top: 10px; }
            </style>
            """, unsafe_allow_html=True)
        
        for card in cards:
            st.markdown(f"### {card['name']}")
            cols = st.columns([2] + [1] * (num_columns - 1))
            
            with cols[0]:
                st.markdown("<div class='card-image-container'>", unsafe_allow_html=True)
                if card['image']:
                    st.image(card['image'], use_column_width=True)
                else:
                    st.write("Image not available")
            
            for idx, grading in enumerate(card['gradings']):
                with cols[(idx % (num_columns - 1)) + 1]:
                    st.markdown(
                        f"<div class='grading-container'>"
                        f"<b style='font-size: 1.1em;'>{grading['grading_name']}</b><br>"
                        f"AUD: {grading['value_aud']}<br>"
                        f"JPY: {grading['value_jpy']}<br>"
                        f"<a href='{grading['link']}' style='color: lightblue;'>View on PriceCharting</a>"
                        f"</div>", 
                        unsafe_allow_html=True
                    )

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