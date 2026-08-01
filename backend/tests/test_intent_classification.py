"""
Unit tests for Day 64 Part A1 — Intent Classification Engine.
"""
import pytest
from app.ai.models.mentor_intent import MentorIntent, IntentResult
from app.ai.classifiers.intent_classifier import IntentClassifier
from app.ai.classifiers.intent_config import IntentClassificationConfig
from app.ai.services.intent_classification_service import IntentClassificationService


class TestIntentClassifier:

    def setup_method(self):
        self.classifier = IntentClassifier()

    def test_empty_message_returns_unknown(self):
        result = self.classifier.classify("")
        assert result.intent == MentorIntent.UNKNOWN
        assert result.confidence == 0.0

        result_space = self.classifier.classify("   ")
        assert result_space.intent == MentorIntent.UNKNOWN

    def test_explain_concept_intent(self):
        result = self.classifier.classify("Can you explain how recursion works?")
        assert result.intent == MentorIntent.EXPLAIN_CONCEPT
        assert result.confidence >= 0.80

    def test_learning_progress_intent(self):
        result = self.classifier.classify("How many sessions have I completed in my learning progress?")
        assert result.intent == MentorIntent.LEARNING_PROGRESS
        assert result.confidence >= 0.85

    def test_session_summary_intent(self):
        result = self.classifier.classify("Can you summarize my last session?")
        assert result.intent == MentorIntent.SESSION_SUMMARY
        assert result.confidence >= 0.85

    def test_learning_journey_intent(self):
        result = self.classifier.classify("What is my current roadmap and learning journey milestone?")
        assert result.intent == MentorIntent.LEARNING_JOURNEY
        assert result.confidence >= 0.85

    def test_profile_information_intent(self):
        result = self.classifier.classify("Show me my strong topics and weak topics from my profile")
        assert result.intent == MentorIntent.PROFILE_INFORMATION
        assert result.confidence >= 0.85

    def test_learning_analytics_intent(self):
        result = self.classifier.classify("Show my learning statistics and weekly activity analytics")
        assert result.intent == MentorIntent.LEARNING_ANALYTICS
        assert result.confidence >= 0.85

    def test_learning_recommendation_intent(self):
        result = self.classifier.classify("What should I learn next? Recommend a topic.")
        assert result.intent == MentorIntent.LEARNING_RECOMMENDATION
        assert result.confidence >= 0.85

    def test_practice_question_intent(self):
        result = self.classifier.classify("Give me a practice exercise or coding challenge")
        assert result.intent == MentorIntent.PRACTICE_QUESTION
        assert result.confidence >= 0.85

    def test_quiz_intent(self):
        result = self.classifier.classify("Quiz me on binary search trees to test my knowledge")
        assert result.intent == MentorIntent.QUIZ
        assert result.confidence >= 0.85

    def test_debug_code_intent(self):
        result = self.classifier.classify("Help me debug this error in my code traceback")
        assert result.intent == MentorIntent.DEBUG_CODE
        assert result.confidence >= 0.80

    def test_general_chat_intent(self):
        result = self.classifier.classify("Hello! How are you doing today?")
        assert result.intent == MentorIntent.GENERAL_CHAT
        assert result.confidence >= 0.80

    def test_priority_resolution_specific_over_general(self):
        # Matches both EXPLAIN_CONCEPT ("explain") and LEARNING_PROGRESS ("learning progress")
        result = self.classifier.classify("Explain my learning progress")
        assert result.intent == MentorIntent.LEARNING_PROGRESS

    def test_threshold_fallback(self):
        config = IntentClassificationConfig(confidence_threshold=0.99)
        strict_classifier = IntentClassifier(config=config)
        result = strict_classifier.classify("Describe trees")
        assert result.intent == MentorIntent.UNKNOWN


class TestIntentClassificationService:

    def setup_method(self):
        self.service = IntentClassificationService()

    def test_service_classify_and_metrics(self):
        res1 = self.service.classify(user_id=1, conversation_id=10, message="Hello mentor")
        assert res1.intent == MentorIntent.GENERAL_CHAT

        res2 = self.service.classify(user_id=1, conversation_id=10, message="How many sessions completed?")
        assert res2.intent == MentorIntent.LEARNING_PROGRESS

        metrics = self.service.get_metrics()
        assert metrics["total_classifications"] == 2
        assert metrics["intent_frequency"]["GENERAL_CHAT"] == 1
        assert metrics["intent_frequency"]["LEARNING_PROGRESS"] == 1
        assert metrics["unknown_count"] == 0

    def test_service_error_handling(self):
        # Service should handle exception in classifier gracefully
        class BrokenClassifier:
            def classify(self, msg):
                raise RuntimeError("Classifier crashed")

        service = IntentClassificationService()
        service._classifier = BrokenClassifier()

        res = service.classify(user_id=1, conversation_id=None, message="Test message")
        assert res.intent == MentorIntent.UNKNOWN
        assert res.confidence == 0.0
        assert "Classifier error" in res.reason
