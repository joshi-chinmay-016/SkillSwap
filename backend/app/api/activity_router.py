"""
Activity Router module. Re-exports router from learning_activities.py.
"""
from app.api.learning_activities import router, activities_router

__all__ = ["router", "activities_router"]
