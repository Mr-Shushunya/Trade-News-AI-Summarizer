import json
import os

SUBSCRIPTIONS_FILE = "subscriptions.json"

def load_subscriptions():
    if not os.path.exists(SUBSCRIPTIONS_FILE):
        return {}
    with open(SUBSCRIPTIONS_FILE, "r") as f:
        return json.load(f)

def save_subscriptions(data):
    with open(SUBSCRIPTIONS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_assets(user_id, assets):
    subs = load_subscriptions()
    user_id = str(user_id)
    
    if user_id not in subs:
        subs[user_id] = {"assets": [], "frequency": None}
    
    current_assets = subs[user_id]["assets"]
    new_assets = [a.strip().upper() for a in assets if a.strip()]
    
    # Добавляем только уникальные активы
    added_assets = []
    for asset in new_assets:
        if asset not in current_assets:
            current_assets.append(asset)
            added_assets.append(asset)
    
    save_subscriptions(subs)
    return added_assets  # Возвращаем список ДОБАВЛЕННЫХ активов