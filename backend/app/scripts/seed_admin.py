"""
SkillSwap Arena — CLI Admin Bootstrapping Tool

Usage:
    python -m app.scripts.seed_admin --email admin@skillswap.com --name "Platform Admin" --password "AdminPassword123!"
"""
import sys
import argparse
import logging
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User
from app.models.profile import Profile
from app.core.security import hash_password
from app.services.wallet_service import grant_welcome_bonus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("skillswap.seed_admin")


def seed_or_promote_admin(email: str, name: str, password: str | None = None) -> User:
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if user:
            logger.info(f"User {email} already exists (ID: {user.id}). Promoting to ADMIN role...")
            user.role = "ADMIN"
            user.is_active = True
            if password:
                user.password_hash = hash_password(password)
            db.commit()
            db.refresh(user)
            logger.info(f"Successfully promoted user {email} to ADMIN!")
            return user

        if not password:
            raise ValueError("Password is required to create a new admin account.")

        logger.info(f"Creating new ADMIN user: {email} ({name})...")
        user = User(
            name=name.strip(),
            email=email.strip().lower(),
            password_hash=hash_password(password),
            role="ADMIN",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create admin profile
        profile = Profile(
            user_id=user.id,
            avatar_url=f"https://api.dicebear.com/7.x/bottts/svg?seed={user.id}"
        )
        db.add(profile)
        db.commit()

        # Grant initial wallet bonus
        try:
            grant_welcome_bonus(db, user.id)
        except Exception:
            pass

        logger.info(f"Successfully created platform ADMIN account (ID: {user.id}) for {email}!")
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed admin user: {e}")
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="SkillSwap Platform Admin Seed Tool")
    parser.add_argument("--email", required=True, help="Admin email address")
    parser.add_argument("--name", default="Platform Admin", help="Admin display name")
    parser.add_argument("--password", required=False, help="Admin password (required for new accounts)")

    args = parser.parse_args()
    try:
        seed_or_promote_admin(email=args.email, name=args.name, password=args.password)
        sys.exit(0)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
