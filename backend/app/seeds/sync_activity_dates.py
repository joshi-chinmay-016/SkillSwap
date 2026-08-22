import logging
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.models.learning_activity import LearningActivity
from app.models.journey import JourneyTask, JourneyMilestone, LearningJourney
from app.models.session import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("skillswap.sync_activity_dates")


def sync_activity_dates():
    db = SessionLocal()
    try:
        activities = db.query(LearningActivity).all()
        logger.info(f"Syncing timestamps for {len(activities)} learning activities...")

        updated_count = 0
        for act in activities:
            old_time = act.created_at
            new_time = None

            if act.entity_type in ("journey_task", "task"):
                task = db.query(JourneyTask).filter(JourneyTask.id == act.entity_id).first()
                if task and task.completed_at:
                    new_time = task.completed_at

            elif act.entity_type in ("journey_milestone", "milestone"):
                milestone = db.query(JourneyMilestone).filter(JourneyMilestone.id == act.entity_id).first()
                if milestone:
                    latest_task = (
                        db.query(JourneyTask)
                        .filter(JourneyTask.milestone_id == milestone.id, JourneyTask.completed_at.isnot(None))
                        .order_by(JourneyTask.completed_at.desc())
                        .first()
                    )
                    if latest_task and latest_task.completed_at:
                        new_time = latest_task.completed_at
                    elif getattr(milestone, "updated_at", None):
                        new_time = milestone.updated_at
                    elif getattr(milestone, "created_at", None):
                        new_time = milestone.created_at

            elif act.entity_type in ("learning_journey", "journey"):
                journey = db.query(LearningJourney).filter(LearningJourney.id == act.entity_id).first()
                if journey:
                    new_time = journey.created_at or getattr(journey, "updated_at", None)

            elif act.entity_type == "session":
                sess = db.query(Session).filter(Session.id == act.entity_id).first()
                if sess:
                    new_time = getattr(sess, "completed_at", None) or getattr(sess, "scheduled_at", None) or getattr(sess, "created_at", None)

            if new_time and new_time != old_time:
                act.created_at = new_time
                updated_count += 1
                logger.info(f"Activity ID {act.id} ({act.activity_type}) for user {act.user_id}: {old_time} -> {new_time}")

        db.commit()
        logger.info(f"Successfully synchronized {updated_count} activity timestamps.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error during activity synchronization: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    sync_activity_dates()
