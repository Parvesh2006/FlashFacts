with open('apps/api/app/services/exam_intelligence.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = """    def score_event_for_exam(self, event: Event, exam_def: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Score a single event's relevance to one exam (0-100).\"\"\"
        score = 0
        reasons: List[str] = []
        text = f"{event.title} {event.summary or ''}".lower()"""

replacement = """    def score_event_for_exam(self, event: Event, exam_def: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Score a single event's relevance to one exam (0-100).\"\"\"
        score = 0
        reasons: List[str] = []
        text = f"{event.title} {event.summary or ''}".lower()

        # Non-exam domains (e.g. routine crime) have no exam relevance unless landmark legal/constitutional
        if event.domain in ("Crime", "Entertainment", "Lifestyle", "Gossip", "Cinema"):
            landmark_legal_words = [
                "supreme court", "high court", "constitution bench", "constitutional bench",
                "landmark judgment", "law commission", "criminal law reform",
                "bharatiya nyaya sanhita", "bns", "ipc amendment",
                "உச்ச நீதிமன்றம்", "உயர் நீதிமன்றம்", "அரசியலமைப்பு", "நீதிபதிகள் அமர்வு",
                "வரலாற்று சிறப்புமிக்க தீர்ப்பு", "சட்டத்திருத்தம்", "சட்ட திருத்தம்"
            ]
            if not any(w in text for w in landmark_legal_words):
                return {
                    "exam_id": exam_def["id"],
                    "exam_name": exam_def["name"],
                    "exam_code": exam_def["code"],
                    "relevance_score": 10,
                    "section": exam_def["section_label"],
                    "reasons": [f"Routine {event.domain.lower()} report without direct syllabus relevance"],
                }"""

if target not in text and target.replace('\n', '\r\n') in text:
    target = target.replace('\n', '\r\n')
    replacement = replacement.replace('\n', '\r\n')

assert target in text, "Target not found in exam_intelligence.py"
text = text.replace(target, replacement, 1)

with open('apps/api/app/services/exam_intelligence.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated exam_intelligence.py successfully")
