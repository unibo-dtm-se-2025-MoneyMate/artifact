import os
import sys
import random
from datetime import datetime, timedelta

# Ensure the MoneyMate package is found
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from MoneyMate.data_layer.api import (
    set_db_path,
    api_register_user,
    api_add_category,
    api_get_categories,
    api_add_contact,
    api_get_contacts,
    api_add_expense,
    api_add_transaction
)

# --- Configuration ---
DB_PATH = os.path.join("MoneyMate", "data", "moneymate_gui.db")

# Added your custom user here
USERS = [
    ("Cristian Romeo", "dtmunibo"),
    ("alice", "password"),
    ("bob", "password"),
    ("charlie", "password"),
    ("dave", "password")
]
ADMIN = ("admin", "12345")

CATEGORIES = [
    ("Food", "Groceries and dining out"),
    ("Transport", "Bus, train, fuel"),
    ("Housing", "Rent and utilities"),
    ("Entertainment", "Movies, games, subscriptions"),
    ("Health", "Gym, pharmacy, doctors"),
    ("Tech", "Gadgets and software")
]

EXPENSE_TITLES = {
    "Food": ["Lunch", "Dinner", "Groceries", "Coffee", "Snacks", "Restaurant"],
    "Transport": ["Bus Ticket", "Uber", "Gas", "Train Pass", "Parking"],
    "Housing": ["Rent", "Electric Bill", "Water Bill", "Internet", "Repairs"],
    "Entertainment": ["Netflix", "Cinema", "Concert", "Video Game", "Spotify"],
    "Health": ["Pharmacy", "Gym Membership", "Doctor Visit", "Vitamins"],
    "Tech": ["AWS Bill", "New Mouse", "Software License", "Phone Bill"]
}

def random_date(days_back=90):
    """Generate a random date string (YYYY-MM-DD) within the last N days."""
    end = datetime.now()
    start = end - timedelta(days=days_back)
    random_date = start + (end - start) * random.random()
    return random_date.strftime("%Y-%m-%d")

def populate():
    print(f"--- Initializing Database: {DB_PATH} ---")
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    set_db_path(DB_PATH)

    # 1. Create Users
    user_ids = {}
    all_users = USERS + [ADMIN]
    
    print("\n--- Creating Users ---")
    for username, pwd in all_users:
        role = "admin" if username == "admin" else "user"
        res = api_register_user(username, pwd, role=role)
        if res['success']:
            uid = res['data']['user_id']
            user_ids[username] = uid
            print(f"Created user: {username} (ID: {uid}, Role: {role})")
        else:
            print(f"User '{username}' could not be created: {res.get('error')}")

    if not user_ids:
        print("No users created. Please delete the old .db file and retry for a clean population.")
        return

    # 2. Populate Data for Each User
    for username, uid in user_ids.items():
        print(f"\n--- Populating data for {username} ---")

        # A. Categories
        cat_map = {} # Name -> ID
        for cat_name, cat_desc in CATEGORIES:
            api_add_category(uid, cat_name, description=cat_desc)
        
        # Retrieve valid categories to use their IDs
        res_cats = api_get_categories(uid)
        if res_cats['success']:
            for c in res_cats['data']:
                cat_map[c['name']] = c['id']

        # B. Expenses (50 per user)
        print(f"  -> Adding 50 random expenses...")
        for _ in range(50):
            cat_name = random.choice(list(EXPENSE_TITLES.keys()))
            title = random.choice(EXPENSE_TITLES[cat_name])
            price = round(random.uniform(5.0, 150.0), 2)
            date = random_date()
            cat_id = cat_map.get(cat_name)
            
            api_add_expense(title, price, date, cat_name, uid, category_id=cat_id)

        # C. Contacts (Add other users as contacts)
        print(f"  -> Adding contacts...")
        for other_name, other_uid in user_ids.items():
            if other_uid != uid:
                # Add contact
                contact_name = other_name.title()
                api_add_contact(contact_name, uid)

    # 3. Create Transactions between users
    print("\n--- Creating Transactions ---")
    
    for sender_name, sender_id in user_ids.items():
        # Get sender's contacts
        res_contacts = api_get_contacts(sender_id)
        if not res_contacts['success']: continue
        
        contacts = res_contacts['data'] # [{'id': X, 'name': 'Bob'}, ...]
        
        for _ in range(5): # 5 transactions per user
            if not contacts: break
            
            contact = random.choice(contacts)
            c_id = contact['id']
            c_name_lower = contact['name'].lower()
            
            # Find the target user ID based on contact name match (simple check)
            # We iterate because casing might differ ("Alice" vs "alice")
            target_id = None
            for u_name, u_id in user_ids.items():
                if u_name.lower() == c_name_lower:
                    target_id = u_id
                    break
            
            if not target_id: continue

            trans_type = random.choice(["credit", "debit"])
            amount = round(random.uniform(10.0, 500.0), 2)
            date = random_date()
            desc = f"{trans_type.capitalize()} for {random.choice(['Lunch', 'Trip', 'Concert', 'Rent Share'])}"

            api_add_transaction(
                from_user_id=sender_id,
                to_user_id=target_id,
                type_=trans_type,
                amount=amount,
                date=date,
                description=desc,
                contact_id=c_id
            )
            print(f"  Transaction: {sender_name} -> {contact['name']} ({trans_type} {amount}€)")

    print("\n\nDatabase population complete! Run 'python -m MoneyMate' to view.")

if __name__ == "__main__":
    # Optional: Remove existing DB to start fresh
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print("Removed existing database for fresh start.")
        except Exception:
            pass
            
    populate()