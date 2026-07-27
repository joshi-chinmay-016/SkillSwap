import logging
from sqlalchemy.orm import Session
from app.models.achievement import Achievement

logger = logging.getLogger(__name__)

INITIAL_ACHIEVEMENTS = [
    {
        "name": "First Lesson",
        "description": "Complete your first learning activity",
        "category": "Learning",
        "badge_tier": "Bronze",
        "badge_name": "Bronze Learner",
        "icon": "book-open",
        "requirement_type": "activity_count",
        "requirement_value": 1,
        "xp_reward": 50
    },
    {
        "name": "First Session",
        "description": "Complete your first mentor/peer session",
        "category": "Participation",
        "badge_tier": "Bronze",
        "badge_name": "Bronze Participant",
        "icon": "users",
        "requirement_type": "session_count",
        "requirement_value": 1,
        "xp_reward": 50
    },
    {
        "name": "7-Day Streak",
        "description": "Maintain a continuous learning streak for 7 days",
        "category": "Streak",
        "badge_tier": "Silver",
        "badge_name": "Silver Streaker",
        "icon": "flame",
        "requirement_type": "streak_days",
        "requirement_value": 7,
        "xp_reward": 100
    },
    {
        "name": "Reach 90% Consistency",
        "description": "Achieve a 90% or higher learning consistency score",
        "category": "Consistency",
        "badge_tier": "Diamond",
        "badge_name": "Diamond Consistent",
        "icon": "target",
        "requirement_type": "consistency_score",
        "requirement_value": 90,
        "xp_reward": 300
    },
    {
        "name": "Complete 100 Activities",
        "description": "Complete 100 total learning activities on the platform",
        "category": "Milestone",
        "badge_tier": "Gold",
        "badge_name": "Gold Centurion",
        "icon": "award",
        "requirement_type": "activity_count",
        "requirement_value": 100,
        "xp_reward": 250
    },
    {
        "name": "Complete 10 Journeys",
        "description": "Successfully complete 10 full learning journeys",
        "category": "Journey",
        "badge_tier": "Legendary",
        "badge_name": "Legendary Voyager",
        "icon": "compass",
        "requirement_type": "journey_count",
        "requirement_value": 10,
        "xp_reward": 500
    }
]


def seed_initial_achievements(db: Session) -> list[Achievement]:
    """
    Seeds initial reusable master achievements if they don't already exist.
    """
    created = []
    for item in INITIAL_ACHIEVEMENTS:
        existing = db.query(Achievement).filter(Achievement.name == item["name"]).first()
        if not existing:
            ach = Achievement(**item)
            db.add(ach)
            created.append(ach)
    if created:
        db.commit()
        logger.info(f"Seeded {len(created)} initial achievements.")
    return created
