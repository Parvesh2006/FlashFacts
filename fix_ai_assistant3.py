import re

with open('apps/api/app/services/ai_assistant.py', 'r', encoding='utf-8') as f:
    content = f.read()

def replace_deterministic_answer(content):
    target_start = content.find('    def _synthesize_deterministic_answer(')
    target_end = content.find('    def _synthesize_ai_answer(')
    if target_start == -1 or target_end == -1: return content
    
    new_block = """    def _synthesize_deterministic_answer(
        self, events: List[Event], filters: Dict[str, Any]
    ) -> str:
        \"\"\"Construct structured exam-oriented answer directly from retrieved events.\"\"\"
        from app.utils.hashing import fix_mojibake
        
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
            mcq_count = filters.get("mcq_count", 5)
            mcq_events = events[:mcq_count]
            
            all_titles = [e.title for e in events if e.title]
            
            for idx, e in enumerate(mcq_events, 1):
                domain_str = e.domain or 'Current Affairs'
                lines.append(f"**Q{idx}. Regarding recent developments in {domain_str}, which of the following is correct?**")
                
                correct_ans = fix_mojibake(e.title)
                
                distractors = []
                for other in all_titles:
                    other_clean = fix_mojibake(other)
                    if other_clean != correct_ans and other_clean not in distractors:
                        distractors.append(other_clean)
                        if len(distractors) == 3:
                            break
                            
                while len(distractors) < 3:
                    distractors.append(f"A significant policy update in {domain_str}.")
                    distractors.append(f"A new development affecting {domain_str} stakeholders.")
                    distractors.append(f"An international agreement regarding {domain_str}.")
                    
                options = [correct_ans, distractors[0], distractors[1], distractors[2]]
                
                correct_pos = idx % 4
                options[0], options[correct_pos] = options[correct_pos], options[0]
                
                labels = ['A', 'B', 'C', 'D']
                for i, opt in enumerate(options):
                    lines.append(f"{labels[i]}) {opt}")
                    
                lines.append(f"**Correct Answer: {labels[correct_pos]}**")
                lines.append(f"**Explanation:** {fix_mojibake(e.summary)}\\n")
        else:
            # High priority events
            high_events = [e for e in events if (e.importance_score or 50) >= 60][:3]
            if not high_events and events:
                high_events = events[:2]

            if high_events:
                lines.append("🌟 **HIGH PRIORITY**\\n")
                for idx, e in enumerate(high_events, 1):
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
                    lines.append(f"**Relevant exams:** {' • '.join(relevant_codes)}")

                    source_name = getattr(e, "source", "") or "FlashFacts Network"
                    if hasattr(source_name, "name"):
                        source_name = source_name.name
                    date_str = e.event_date.isoformat() if e.event_date else ""
                    lines.append(f"**Source:** {source_name} ({date_str})\\n")

            # Remaining important events
            remaining = [e for e in events if e not in high_events][:3]
            if remaining:
                lines.append("📰 **IMPORTANT DEVELOPMENTS**\\n")
                for idx, e in enumerate(remaining, 1):
                    lines.append(f"**{idx}. {fix_mojibake(e.title)}**")
                    lines.append(f"{fix_mojibake(e.summary[:200])}...")
                    lines.append(f"*Category: {e.domain} | Date: {e.event_date}*\\n")

        return "\\n".join(lines)

"""
    return content[:target_start] + new_block + content[target_end:]

content = replace_deterministic_answer(content)
with open('apps/api/app/services/ai_assistant.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated _synthesize_deterministic_answer!")
