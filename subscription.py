import os, json
from datetime import datetime, timedelta

USERS_FILE = "data/users.json"
os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)

class SubscriptionManager:
    PLANS = {
        "Silver": {"days": 30, "price": "$20"},
        "Gold": {"days": 90, "price": "$50"},
        "Platinum": {"days": 365, "price": "$150"},
    }

    def __init__(self):
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE,'r') as f:
                self.users = json.load(f)
        else:
            self.users = {}
            self._save()

    def _save(self):
        with open(USERS_FILE,'w') as f:
            json.dump(self.users, f, default=str, indent=2)

    def ensure_user(self, user_id, username=None):
        uid = str(user_id)
        if uid not in self.users:
            expiry = (datetime.utcnow() + timedelta(days=3)).isoformat()
            self.users[uid] = {"username": username, "expiry": expiry, "plan": "Trial"}
            self._save()

    def is_active(self, user_id):
        uid = str(user_id)
        if uid not in self.users:
            return False
        expiry = datetime.fromisoformat(self.users[uid]["expiry"])
        return datetime.utcnow() <= expiry

    def activate_plan(self, user_id, plan_key):
        uid = str(user_id)
        plan = self.PLANS.get(plan_key)
        if not plan:
            raise ValueError("Plan not found")
        expiry = (datetime.utcnow() + timedelta(days=plan["days"])).isoformat()
        self.users[uid] = {"username": self.users.get(uid,{}).get("username"), "expiry": expiry, "plan": plan_key}
        self._save()

    def days_left(self, user_id):
        uid = str(user_id)
        if uid not in self.users:
            return 0
        expiry = datetime.fromisoformat(self.users[uid]["expiry"])
        return max(0, (expiry - datetime.utcnow()).days)

    def status_text(self, user_id):
        uid = str(user_id)
        if uid not in self.users:
            return "No account found. Use /start to begin."
        plan = self.users[uid].get("plan","Trial")
        days = self.days_left(user_id)
        return f"Plan: {plan}\nDays left: {days}"