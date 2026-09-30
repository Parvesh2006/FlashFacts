import re

with open('apps/api/app/services/ai_assistant.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update parse_query to handle output_format and mcq_count
def replace_parse_query(content):
    target_start = content.find('def parse_query(')
    target_end = content.find('    def answer_question(')
    if target_start == -1 or target_end == -1: return content
    
    original_block = content[target_start:target_end]
    
    new_block = """    def parse_query(
        self, question: str, history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        \"\"\"Convert natural language question into structured filters.\"\"\"
        import re
        from datetime import datetime, timezone, timedelta
        
        q_lower = question.lower()
        filters: Dict[str, Any] = {}
        
        # MCQ Intent and Count Extraction
        if "mcq" in q_lower or "quiz" in q_lower or "multiple choice" in q_lower:
            filters["output_format"] = "mcq"
            # Default count
            filters["mcq_count"] = 5
            # Extract requested count (e.g., "5 mcqs", "10 questions")
            match = re.search(r'\\b(\\d+)\\b', q_lower)
            if match:
                filters["mcq_count"] = int(match.group(1))

        today = datetime.now(timezone.utc)
        
        # Inherit context from history if available
        if history:
            last_filters = None
            for item in reversed(history):
                if isinstance(item, dict) and "filters" in item:
                    last_filters = item["filters"]
                    break
            if last_filters:
                if last_filters.get("domain") and "domain" not in q_lower:
                    filters["domain"] = last_filters["domain"]
                if last_filters.get("date_range") and "today" not in q_lower and "yesterday" not in q_lower:
                    filters["date_label"] = last_filters.get("date_label", "inherited")
                if last_filters.get("exam_id"):
                    filters["exam_id"] = last_filters["exam_id"]
                    filters["exam_code"] = last_filters.get("exam_code")
                if last_filters.get("location_name"):
                    filters["location_name"] = last_filters["location_name"]

        # Date extraction
        if "today" in q_lower:
            filters["start_date"] = today
            filters["end_date"] = today
            filters["date_label"] = "today"
        elif "yesterday" in q_lower:
            yesterday = today - timedelta(days=1)
            filters["start_date"] = yesterday
            filters["end_date"] = yesterday
            filters["date_label"] = "yesterday"
        elif any(w in q_lower for w in ["this week", "past 7 days", "last 7 days"]):
            filters["start_date"] = today - timedelta(days=7)
            filters["end_date"] = today
            filters["date_label"] = "this week"
        elif any(w in q_lower for w in ["last week", "past fortnight"]):
            filters["start_date"] = today - timedelta(days=14)
            filters["end_date"] = today - timedelta(days=7)
            filters["date_label"] = "last week"
        elif any(w in q_lower for w in ["this month", "past 30 days"]):
            filters["start_date"] = today - timedelta(days=30)
            filters["end_date"] = today
            filters["date_label"] = "this month"

        # Location extraction
        for kw, canonical_name in INDIAN_STATES_MAP.items():
            if re.search(rf"\\b{re.escape(kw)}\\b", q_lower):
                filters["location_name"] = canonical_name
                break

        if "india" in q_lower and not filters.get("location_name"):
            filters["location_name"] = "India"

        # Exam extraction
        for kw, exam_id in EXAM_KEYWORDS.items():
            if re.search(rf"\\b{re.escape(kw)}\\b", q_lower):
                filters["exam_id"] = exam_id
                defn = EXAM_DEFINITIONS.get(exam_id)
                if defn:
                    filters["exam_code"] = defn["code"]
                break

        # Domain extraction
        for kw, domain_name in DOMAIN_KEYWORDS.items():
            if re.search(rf"\\b{re.escape(kw)}\\b", q_lower):
                filters["domain"] = domain_name
                break

        # Importance extraction
        if any(w in q_lower for w in ["important", "high priority", "major", "top"]):
            filters["importance"] = "high"

        # Clean search keywords
        clean_words = []
        ignore_words = {
            "what", "happened", "today", "current", "affairs", "the", "in", "for", "give", "me", 
            "show", "tell", "explain", "is", "of", "and", "some", "mcq", "mcqs", "about", "on", 
            "quiz", "multiple", "choice", "questions", "generate", "create", "make", "from", 
            "please", "can", "you", "a", "an", "any"
        }
        
        words = q_lower.replace("?", "").replace(".", "").split()
        for word in words:
            # Skip words in ignore list and skip raw numbers (to avoid poisoning topic search)
            if word not in ignore_words and not word.isdigit():
                clean_words.append(word)

        filters["query_text"] = " ".join(clean_words[:6])
        return filters

"""
    return content[:target_start] + new_block + content[target_end:]

content = replace_parse_query(content)
with open('apps/api/app/services/ai_assistant.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated parse_query!")
