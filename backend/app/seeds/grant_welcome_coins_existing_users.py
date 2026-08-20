"""
Script to grant 5 Welcome Bonus coins to all existing database users (Idempotent)
"""
from app.core.database import SessionLocal
from app.models.user import User
from app.services.wallet_service import grant_welcome_bonus


def grant_welcome_coins_to_existing_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"Found {len(users)} existing users in database.")
        granted_count = 0

        for user in users:
            wallet = grant_welcome_bonus(db, user.id)
            print(f"Granted/Verified wallet for User #{user.id} ({user.name}): Balance = {wallet.balance}")
            granted_count += 1

        print(f"Successfully processed {granted_count} existing users!")
    except Exception as e:
        print(f"Error granting welcome coins: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    grant_welcome_coins_to_existing_users()
