from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime


class ScoreHistoryPoint(BaseModel):
    attempt_id: str
    test_id: str
    exam_name: str
    score: float
    accuracy: int
    total_answered: int
    total_questions: int
    time_taken_seconds: int
    submitted_at: datetime


class SubjectPerformance(BaseModel):
    subject: str
    total_questions: int
    correct_count: int
    accuracy: int


class StudyRecommendation(BaseModel):
    subject: str
    topic: str
    reason: str
    action: str
    priority: str  # "high", "medium", "normal"


class PerformanceAnalyticsResponse(BaseModel):
    total_tests_completed: int
    total_questions_attempted: int
    overall_accuracy: int
    average_score: float
    total_correct: int
    total_incorrect: int
    total_unanswered: int
    average_time_per_question_seconds: float
    revision_pending_count: int
    strong_topics: List[str]
    weak_topics: List[str]
    scores_over_time: List[ScoreHistoryPoint]
    subject_performance: List[SubjectPerformance]
    recommendations: List[StudyRecommendation]
