import re
from bs4 import BeautifulSoup

def extract_reservation_info(html):
    """Extracts reservation information from OpenTable confirmation HTML.

    Args:
        html (str): The HTML content of the OpenTable confirmation page.

    Returns:
        tuple: A tuple containing the following information:
            - restaurant_name (str): The name of the restaurant.
            - reservation_status (str): The status of the reservation (e.g., "confirmed").
            - party_size (int): The number of people in the reservation.
            - reservation_datetime (str): The date and time of the reservation.
            - user_first_name (str): The user's first name.
            - user_last_name (str): The user's last name.
    """

    soup = BeautifulSoup(html, 'html.parser')

    # Extract restaurant name
    restaurant_name = soup.find('h2', {'data-test': 'restaurant-name'}).text.strip()

    # Extract reservation status
    reservation_status = soup.find('div', {'data-test': 'reservation-state'}).find('h1').text.strip().lower()

    # Extract party size
    party_size_text = soup.find('section', {'data-test': 'reservation-party-size'}).text.strip()
    party_size = int(re.search(r'^(\d+)', party_size_text).group(1))

    # Extract reservation date and time
    reservation_datetime = soup.find('section', {'data-test': 'reservation-date-time'}).text.strip()

    # Extract user information
    user_name = soup.find('div', {'class': '_6MqxdoCn1NE-'}).find(
      'div', {'class': 'nLQ-7r8IvOk-'}).text.strip()
    user_first_name, user_last_name = user_name.split(' ')  # Assuming first and last name
    return (
        restaurant_name,
        reservation_status,
        party_size,
        reservation_datetime,
        user_first_name,
        user_last_name,
    )

# Example usage:from evaluation_harness.evaluators.base import evaluator_router
html_content = """
(Insert the provided HTML content here)
"""

restaurant_name, reservation_status, party_size, reservation_datetime, user_first_name, user_last_name = extract_reservation_info(html_content)

print(f"Restaurant: {restaurant_name}")
print(f"Status: {reservation_status}")
print(f"Party size: {party_size}")
print(f"Date and time: {reservation_datetime}")
print(f"User: {user_first_name} {user_last_name}")