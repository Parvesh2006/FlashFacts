with open('apps/api/app/services/exam_classification_service.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update _determine_exam_importance call
t1 = "exam_importance = self._determine_exam_importance(imp_score, combined_text, event_type)"
r1 = "exam_importance = self._determine_exam_importance(imp_score, combined_text, event_type, domain=domain)"
assert t1 in text, "t1 not found"
text = text.replace(t1, r1, 1)

# 2. Update _determine_exam_importance definition
t2 = "    def _determine_exam_importance(\n        self, imp_score: int, text_lower: str, event_type: str\n    ) -> str:"
r2 = """    def _determine_exam_importance(
        self, imp_score: int, text_lower: str, event_type: str, domain: str = ""
    ) -> str:
        if domain == "Crime":
            landmark_legal_words = [
                "supreme court", "high court", "constitution bench", "constitutional bench",
                "landmark judgment", "law commission", "criminal law reform",
                "bharatiya nyaya sanhita", "bns", "ipc amendment",
                "உச்ச நீதிமன்றம்", "உயர் நீதிமன்றம்", "அரசியலமைப்பு", "நீதிபதிகள் அமர்வு",
                "வரலாற்று சிறப்புமிக்க தீர்ப்பு", "சட்டத்திருத்தம்", "சட்ட திருத்தம்"
            ]
            if not any(w in text_lower for w in landmark_legal_words):
                return "BACKGROUND" """

if t2 not in text and t2.replace('\n', '\r\n') in text:
    t2 = t2.replace('\n', '\r\n')
    r2 = r2.replace('\n', '\r\n')
assert t2 in text, "t2 not found"
text = text.replace(t2, r2, 1)

# 3. Update _evaluate_exam_relevance
t3 = """    def _evaluate_exam_relevance(
        self,
        exam_type: str,
        domain: str,
        event_type: str,
        geo_level: str,
        state: Optional[str],
        text_lower: str,
        imp_score: int,
    ) -> Tuple[int, str, str]:
        \"\"\"Return (score 0-100, level string, explanation string).\"\"\"
        score = 40  # baseline"""

r3 = """    def _evaluate_exam_relevance(
        self,
        exam_type: str,
        domain: str,
        event_type: str,
        geo_level: str,
        state: Optional[str],
        text_lower: str,
        imp_score: int,
    ) -> Tuple[int, str, str]:
        \"\"\"Return (score 0-100, level string, explanation string).\"\"\"
        if domain == "Crime":
            landmark_legal_words = [
                "supreme court", "high court", "constitution bench", "constitutional bench",
                "landmark judgment", "law commission", "criminal law reform",
                "bharatiya nyaya sanhita", "bns", "ipc amendment",
                "உச்ச நீதிமன்றம்", "உயர் நீதிமன்றம்", "அரசியலமைப்பு", "நீதிபதிகள் அமர்வு",
                "வரலாற்று சிறப்புமிக்க தீர்ப்பு", "சட்டத்திருத்தம்", "சட்ட திருத்தம்"
            ]
            has_landmark_legal = any(w in text_lower for w in landmark_legal_words)
            if not has_landmark_legal:
                return 10, "NOT_RELEVANT", f"Routine local incident/crime without broader {exam_type} competitive exam or syllabus applicability."

        score = 40  # baseline"""

if t3 not in text and t3.replace('\n', '\r\n') in text:
    t3 = t3.replace('\n', '\r\n')
    r3 = r3.replace('\n', '\r\n')
assert t3 in text, "t3 not found"
text = text.replace(t3, r3, 1)

with open('apps/api/app/services/exam_classification_service.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated exam_classification_service.py successfully")
