import requests
from bs4 import BeautifulSoup
import logging

def get_pokemon_cards(collection_url):
    try:
        response = requests.get(collection_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        table = soup.find('table', id='active')
        if not table:
            logging.error("Could not find the card data table.")
            return None
        
        cards = {}
        for offer in table.find_all('tr'):
            try:
                # Card name
                card_name_element = offer.find('p', class_='title')
                if not card_name_element:
                    logging.warning("Title element not found, skipping this entry")
                    continue
                card_name = card_name_element.text.strip()
                
                # Grading name
                grading_element = offer.find('p', class_='header')
                grading_name = grading_element.text.strip() if grading_element else "No Grading"
                
                # Card value
                price_element = offer.find('span', class_='js-price')
                card_value_usd = price_element.text.strip() if price_element else "Unknown Value"
                
                # Convert the value to AUD and JPY
                try:
                    usd_value = float(card_value_usd.replace('$', '').replace(',', ''))
                    card_value_aud = f"{usd_value * 1.5:.2f} AUD"  # Update conversion rate as needed
                    card_value_jpy = f"{usd_value * 150:.2f} JPY"  # Update conversion rate as needed
                except ValueError:
                    logging.warning(f"Could not convert price for {card_name}")
                    card_value_aud = "Unknown Value"
                    card_value_jpy = "Unknown Value"
                
                # Card link and high-resolution image
                card_link_element = offer.find('a', class_='item-link')
                if card_link_element:
                    card_link = f"https://www.pricecharting.com{card_link_element['href']}"
                    # Visit the individual card page to get the high-res image
                    card_page_response = requests.get(card_link)
                    card_page_response.raise_for_status()
                    card_page_soup = BeautifulSoup(card_page_response.content, 'html.parser')
                    card_image_element = card_page_soup.find('img', class_='product-thumbnail')
                    card_image_url = card_image_element['src'] if card_image_element else None
                else:
                    card_link = None
                    card_image_url = None
                
                # Update or create card entry
                if card_name in cards:
                    cards[card_name]['gradings'].append({
                        'grading_name': grading_name,
                        'value_aud': card_value_aud,
                        'value_jpy': card_value_jpy
                    })
                else:
                    cards[card_name] = {
                        'image': card_image_url,
                        'gradings': [{
                            'grading_name': grading_name,
                            'value_aud': card_value_aud,
                            'value_jpy': card_value_jpy
                        }],
                        'link': card_link
                    }
                
                logging.info(f"Successfully processed card: {card_name}")
            
            except Exception as e:
                logging.error(f"An error occurred processing a card: {e}")
                continue
        
        if not cards:
            logging.warning("No cards were found in the collection.")
        return cards
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None
