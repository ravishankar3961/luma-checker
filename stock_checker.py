import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import json
import os

# --- Configuration ---
# This is the user-facing page, not the API URL
AMUL_URL = "https://shop.amul.com/en/browse/protein"

# --- Get secrets from GitHub Actions environment variables ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- Add the full names of the products you want to track ---
# Be specific, as the script will look for these exact names.
PRODUCTS_TO_TRACK = [
    "Amul Whey Protein, 32 g | Pack of 30 Sachets",
    "Amul Whey Protein, 32 g | Pack of 60 Sachets",
    "Amul Chocolate Whey Protein, 34 g | Pack of 30 sachets",
    "Amul Chocolate Whey Protein, 34 g | Pack of 60 sachets"
]

# the SKUs you want to track
PRODUCT_SKUS = [
    "WPCCP01_01",
    "WPCCP02_01",
    "WPCCP03_01",
    "WPCCP05_02"
]  

# --- End Configuration ---

# --- Helper function to send Telegram message (no changes here) ---
def send_telegram_message(message):
    import requests
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.get(url, params=params)
        print(f"Telegram notification sent: {message}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Telegram message: {e}")


def check_stock_with_selenium():
    # Set up Chrome options for Selenium
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Optional: Run Chrome in the background without a visible window
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")

    print("Starting browser...")
    # Automatically downloads and manages the correct driver for Chrome
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    try:
        print(f"Navigating to {AMUL_URL}...")
        # Use a script to fetch the API data after the page has loaded
        # This lets the browser handle all the headers and cookies.
        api_url = 'https://shop.amul.com/api/1/entity/ms.products?fields[name]=1&fields[brand]=1&fields[categories]=1&fields[collections]=1&fields[alias]=1&fields[sku]=1&fields[price]=1&fields[compare_price]=1&fields[original_price]=1&fields[images]=1&fields[metafields]=1&fields[discounts]=1&fields[catalog_only]=1&fields[is_catalog]=1&fields[seller]=1&fields[available]=1&fields[inventory_quantity]=1&fields[net_quantity]=1&fields[num_reviews]=1&fields[avg_rating]=1&fields[inventory_low_stock_quantity]=1&fields[inventory_allow_out_of_stock]=1&fields[default_variant]=1&fields[variants]=1&fields[lp_seller_ids]=1&filters[0][field]=categories&filters[0][value][0]=protein&filters[0][operator]=in&filters[0][original]=1&facets=true&facetgroup=default_category_facet&limit=32&total=1&start=0&cdc=1m&substore=66506004aa64743ceefbed25'
        
        # We need to navigate to the base page first to get the right session/cookies
        driver.get(AMUL_URL)
        print("Page loaded. Waiting a few seconds for all data to load...")
        time.sleep(15) # Wait for the page's JavaScript to make the API calls

        print("Executing script to fetch API data from within the browser...")
        # This JavaScript will run inside the browser and fetch the API data with the correct, valid headers
        script = f"return await fetch('{api_url}').then(response => response.json());"
        api_response = driver.execute_script(script)
        
        products = api_response.get("data", [])
        
        if not products:
            print("Could not find product data in the API response.")
            return

        print(f"Found {len(products)} products in the 'protein' category.")
        
        # --- Check for stock ---
        for product in products:
            # product_sku = product.get("sku")
            if product.get("sku") in PRODUCT_SKUS:
                product_name = product.get("name", "").strip()
                is_available = product.get("available", False)
                inventory_qty = product.get("inventory_quantity", 0)

                price = product.get("price")
                qty = product.get("inventory_quantity")

                print(f"Checking: '{product_name}' | Available: {is_available} | Quantity: {inventory_qty}")

                if is_available and inventory_qty > 0:
                    message = f"✅ *In Stock*: {product_name}\n💰 Price: ₹{price}\n📦 Qty: {qty}\n🔗 [Buy Now](https://shop.amul.com/en/browse/protein)"
                    send_telegram_message(message)
                else:
                    print(f"-> '{product_name}' is out of stock.")


    except Exception as e:
        print(f"An error occurred with Selenium: {e}")
        send_telegram_message(f"⚠️ Script Error: {e}")
    finally:
        print("Closing browser.")
        driver.quit()


if __name__ == "__main__":
    check_stock_with_selenium()
    print("\n--- Script finished successfully. ---")
