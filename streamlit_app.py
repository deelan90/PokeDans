import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# Function to load the cards using AJAX directly
def load_cards_via_ajax(base_url):
    all_cards = []
    page = 0
    while True:
        # Constructing the AJAX URL for each subsequent page of results
        ajax_url = f"{base_url}&internal=true&page={page}"
        response = requests.get(ajax_url)
        
        # Check if the response is OK and attempt to decode JSON
        if response.status_code == 200:
            try:
                data = response.json()  # Attempt to get JSON data
                # Break if no more data is returned
                if not data['cards']:
                    break
                all_cards.extend(data['cards'])
                page += 1
                st.write(f"Fetched {len(data['cards'])} cards from page {page}")
            except ValueError:
                # If JSON decoding fails
                st.error("Failed to decode JSON response.")
                st.write("Response content:", response.text[:500])  # Print first 500 characters of the response
                break
        else:
            # If the response has an error status code
            st.error(f"Failed to fetch data: {response.status_code}")
            st.write("Response content:", response.text[:500])
            break
    
    return all_cards

def main():
    # Your base URL might need to be updated to the AJAX endpoint used on the site
    base_url = "https://www.pricecharting.com/offers?status=collection&seller=yx5zdzzvnnhyvjeffskx64pus4&sort=name&category=all&folder-id=&condition-id=all"
    st.markdown("<h1 style='text-align: center;'>PokéDan Card Collection</h1>", unsafe_allow_html=True)
    
    # Load all cards via AJAX
    cards = load_cards_via_ajax(base_url)
    
    # Display the cards
    if cards:
        for card in cards:
            st.image(card['image_url'], caption=f"{card['name']} - ${card['price']}")
    else:
        st.error("Failed to load cards.")

if __name__ == "__main__":
    main()
