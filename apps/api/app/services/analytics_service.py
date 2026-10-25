from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc

from app.models.mock_test import MockTest, MockTestAttempt, MockTestQuestion
from app.models.revision_item import RevisionItem
from app.schemas.analytics import (
    PerformanceAnalyticsResponse,
    ScoreHistoryPoint,
    SubjectPerformance,
    StudyRecommendation,
)


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_analytics(self, user_id: str) -> PerformanceAnalyticsResponse:
        # 1. Fetch user attempts with test metadata
        stmt = (
            select(MockTestAttempt, MockTest)
            .join(MockTest, MockTest.id == MockTestAttempt.test_id)
            .where(MockTestAttempt.user_id == user_id)
            .order_by(MockTestAttempt.submitted_at.asc())
        )
        attempts_with_tests = self.db.execute(stmt).all()

        total_tests = len(attempts_with_tests)

        if total_tests == 0:
            # Check pending revision items count even for new test-takers
            pending_rev_count = (
                self.db.query(func.count(RevisionItem.id))
                .filter(
                    RevisionItem.user_id == user_id,
                    RevisionItem.is_revised == False,
                )
                .scalar()
                or 0
            )

            return PerformanceAnalyticsResponse(
                total_tests_completed=0,
                total_questions_attempted=0,
                overall_accuracy=0,
                average_score=0.0,
                total_correct=0,
                total_incorrect=0,
                total_unanswered=0,
                average_time_per_question_seconds=0.0,
                revision_pending_count=pending_rev_count,
                strong_topics=[],
                weak_topics=[],
                scores_over_time=[],
                subject_performance=[],
                recommendations=[
                    StudyRecommendation(
                        subject="General Studies",
                        topic="Diagnostic Mock Test",
                        reason="No completed mock test attempts recorded yet.",
                        action="Start your first full-length or topic test to establish your diagnostic performance baseline.",
                        priority="high",
                    )
                ],
            )

        total_answered = 0
        total_correct = 0
        total_incorrect = 0
        total_unanswered = 0
        total_time_taken = 0
        score_sum = 0.0

        scores_over_time: List[ScoreHistoryPoint] = []
        subject_stats: Dict[str, Dict[str, int]] = {}

        for attempt, test in attempts_with_tests:
            total_answered += attempt.total_answered
            total_incorrect += attempt.incorrect_count
            total_unanswered += attempt.unanswered_count
            total_time_taken += attempt.time_taken_seconds
            score_sum += float(attempt.score)

            calc_correct = max(0, attempt.total_answered - attempt.incorrect_count)
            total_correct += calc_correct

            scores_over_time.append(
                ScoreHistoryPoint(
                    attempt_id=attempt.id,
                    test_id=attempt.test_id,
                    exam_name=test.exam_name,
                    score=float(attempt.score),
                    accuracy=attempt.accuracy,
                    total_answered=attempt.total_answered,
                    total_questions=test.total_questions,
                    time_taken_seconds=attempt.time_taken_seconds,
                    submitted_at=attempt.submitted_at,
                )
            )

            # Analyze subject performance
            subj = test.domain or "General Studies"
            if subj not in subject_stats:
                subject_stats[subj] = {"total": 0, "correct": 0}
            subject_stats[subj]["total"] += test.total_questions
            subject_stats[subj]["correct"] += calc_correct

        # Calculate aggregates
        overall_accuracy = (
            int((total_correct / (total_correct + total_incorrect)) * 100)
            if (total_correct + total_incorrect) > 0
            else 0
        )
        avg_score = round(score_sum / total_tests, 2)
        avg_time_per_q = (
            round(total_time_taken / total_answered, 1)
            if total_answered > 0
            else 0.0
        )

        # Subject performance list
        subject_perf_list: List[SubjectPerformance] = []
        strong_topics = []
        weak_topics = []

        for subj, stats in subject_stats.items():
            tot = stats["total"]
            corr = stats["correct"]
            acc = int((corr / tot) * 100) if tot > 0 else 0
            subject_perf_list.append(
                SubjectPerformance(
                    subject=subj,
                    total_questions=tot,
                    correct_count=corr,
                    accuracy=acc,
                )
            )
            if acc >= 70:
                strong_topics.append(subj)
            elif acc < 50:
                weak_topics.append(subj)

        # Fetch revision items breakdown
        pending_rev_count = (
            self.db.query(func.count(RevisionItem.id))
            .filter(
                RevisionItem.user_id == user_id,
                RevisionItem.is_revised == False,
            )
            .scalar()
            or 0
        )

        # Generate targeted recommendations based on real weak areas
        recommendations: List[StudyRecommendation] = []
        for weak in weak_topics:
            recommendations.append(
                StudyRecommendation(
                    subject=weak,
                    topic=f"{weak} Core Revision",
                    reason=f"Accuracy is currently below 50% across attempted {weak} questions.",
                    action=f"Practice 15 dedicated PYQs and review flagged items in your Mistake Book for {weak}.",
                    priority="high",
                )
            )

        if pending_rev_count > 0:
            recommendations.append(
                StudyRecommendation(
                    subject="Smart Revision",
                    topic="Pending Mistake Book Items",
                    reason=f"You have {pending_rev_count} unrevised questions needing spaced-repetition review.",
                    action="Open the Mistake Book and complete your scheduled retry session.",
                    priority="high" if pending_rev_count >= 5 else "medium",
                )
            )

        if not recommendations:
            recommendations.append(
                StudyRecommendation(
                    subject="All Subjects",
                    topic="Comprehensive Mock Drill",
                    reason="High overall accuracy maintained across recent practice tests.",
                    action="Attempt a timed 100-question full-syllabus mock test to test speed and endurance under exam conditions.",
                    priority="normal",
                )
            )

        return PerformanceAnalyticsResponse(
            total_tests_completed=total_tests,
            total_questions_attempted=total_answered,
            overall_accuracy=overall_accuracy,
            average_score=avg_score,
            total_correct=total_correct,
            total_incorrect=total_incorrect,
            total_unanswered=total_unanswered,
            average_time_per_question_seconds=avg_time_per_q,
            revision_pending_count=pending_rev_count,
            strong_topics=strong_topics,
            weak_topics=weak_topics,
            scores_over_time=scores_over_time,
            subject_performance=subject_perf_list,
            recommendations=recommendations,
        )
