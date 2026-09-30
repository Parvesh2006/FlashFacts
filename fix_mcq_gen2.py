# -*- coding: utf-8 -*-
import re

with open('apps/api/app/services/ai_assistant.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find('def _synthesize_deterministic_answer')
if start_idx != -1:
    end_idx = content.find('def _synthesize_ai_answer', start_idx)
    func_body = content[start_idx:end_idx]
    
    new_func = '''def _synthesize_deterministic_answer(
        self, events: List[Event], filters: Dict[str, Any]
    ) -> str:
        """Construct structured exam-oriented answer directly from retrieved events."""
        exam_code = filters.get("exam_code") or "Competitive Exams"
        date_label = (filters.get("date_label") or "Current").capitalize()
        location_label = filters.get("location_name")

        header_title = f"{date_label} Current Affairs"
        if location_label:
            header_title += f" | {location_label}"
        if exam_code:
            header_title += f" ({exam_code})"

        lines = [f"### {header_title}\\n"]

        if filters.get("output_format") == "mcq":
            lines.append("### Current Affairs Practice Quiz\\n")
            mcq_events = events[:5]
            for idx, event in enumerate(mcq_events, 1):
                from app.utils.hashing import fix_mojibake
                q_text = f"**Q{idx}. Which of the following statements accurately reflects recent developments regarding {fix_mojibake(event.title)}?**"
                lines.append(q_text)
                
                lines.append(f"A) {fix_mojibake(event.summary)}")
                lines.append(f"B) The event was cancelled due to international pressure.")
                lines.append(f"C) It was entirely unrelated to the current affairs domain.")
                lines.append(f"D) None of the above.")
                lines.append(f"**Correct Answer: A**")
                lines.append(f"**Explanation:** {fix_mojibake(event.why_it_matters or event.summary)}\\n")
        else:
            # High priority events
            high_events = [e for e in events if (e.importance_score or 50) >= 60][:3]
            if not high_events and events:
                high_events = events[:2]

            if high_events:
                lines.append("🔴 **HIGH PRIORITY**\\n")
                for idx, e in enumerate(high_events, 1):
                    from app.utils.hashing import fix_mojibake
                    lines.append(f"**{idx}. {fix_mojibake(e.title)}**")
                    lines.append(f"**What happened:** {fix_mojibake(e.summary)}")
                    if e.why_it_matters:
                        lines.append(f"**Why it matters:** {fix_mojibake(e.why_it_matters)}")

                    # Exam fact extraction
                    fact = f"Domain: {e.domain} | Category: {e.event_type or 'General'}"
                    lines.append(f"**Exam Fact:** {fact}")

                    # Relevant exams
                    rel = self.exam_service.get_event_exam_relevance(e.id)
                    relevant_codes = [r["exam_code"] for r in rel.get("relevant_exams", [])[:3]]
                    if not relevant_codes:
                        relevant_codes = [exam_code, "UPSC"]
                    lines.append(f"**Relevant exams:** {', '.join(relevant_codes)}")

                    source_name = getattr(e, "source", "") or "FlashFacts Network"
                    if hasattr(source_name, "name"):
                        source_name = source_name.name
                    date_str = e.event_date.isoformat() if e.event_date else ""
                    lines.append(f"**Source:** {source_name} ({date_str})\\n")

            # Remaining important events
            remaining = [e for e in events if e not in high_events][:3]
            if remaining:
                lines.append("🟠 **IMPORTANT DEVELOPMENTS**\\n")
                for idx, e in enumerate(remaining, 1):
                    from app.utils.hashing import fix_mojibake
                    lines.append(f"**{idx}. {fix_mojibake(e.title)}**")
                    lines.append(f"{fix_mojibake(e.summary[:200])}...")
                    lines.append(f"*Category: {e.domain} | Date: {e.event_date}*\\n")

        return "\\n".join(lines)
    
    '''
    content = content[:start_idx] + new_func + content[end_idx:]
    with open('apps/api/app/services/ai_assistant.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replaced whole function.")
