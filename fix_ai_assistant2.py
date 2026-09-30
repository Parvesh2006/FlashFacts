import re

with open('apps/api/app/services/ai_assistant.py', 'r', encoding='utf-8') as f:
    content = f.read()

def replace_ai_answer(content):
    target_start = content.find('    def _synthesize_ai_answer(')
    target_end = content.find('    def _retrieve_candidate_events(')
    if target_start == -1 or target_end == -1: return content
    
    original_block = content[target_start:target_end]
    
    new_block = """    def _synthesize_ai_answer(
        self, question: str, events: List[Event], filters: Dict[str, Any]
    ) -> Optional[str]:
        \"\"\"Synthesize answer using OpenAI API formatted strictly over retrieved events.\"\"\"
        from app.core.config import settings

        api_key = getattr(settings, "AI_API_KEY", "")
        model = getattr(settings, "AI_MODEL", "gpt-4o-mini")
        if not api_key:
            return None

        context_blocks = []
        for idx, e in enumerate(events, 1):
            source_name = getattr(e, "source", "") or "FlashFacts Network"
            if hasattr(source_name, "name"):
                source_name = source_name.name
            context_blocks.append(
                f"[{idx}] Title: {e.title}\\n"
                f"Domain: {e.domain} | Date: {e.event_date}\\n"
                f"Summary: {e.summary}\\n"
                f"Why it matters: {e.why_it_matters or 'N/A'}\\n"
                f"Source: {source_name}\\n"
            )

        context_str = "\\n".join(context_blocks)
        
        is_mcq = filters.get("output_format") == "mcq" or "mcq" in question.lower() or "quiz" in question.lower()

        if is_mcq:
            mcq_count = filters.get("mcq_count", 5)
            system_prompt = (
                "You are FlashFacts AI, an expert MCQ generator for competitive exams. "
                "The user has requested MCQs based on current affairs. "
                "Use ONLY the provided retrieved context to generate the questions. "
                "CRITICAL MCQ RULES:\\n"
                "1. Fact-based: Test specific factual claims, not generic summaries.\\n"
                "2. Concise Options: Every option must be a concise factual statement or answer phrase.\\n"
                "3. Plausible Distractors: Distractors must be plausible alternatives from the same subject/domain, with similar length and specificity to the correct answer. Every option must be independently plausible to a student who knows the subject.\\n"
                "4. Answer Distribution: Across a multi-question quiz, vary the correct option position among A/B/C/D rather than always placing it at A.\\n"
                f"5. Count: Generate exactly {mcq_count} questions, using distinct events where possible. If there is insufficient context to generate {mcq_count} questions safely, generate as many as you safely can.\\n"
                "6. Grounding: The correct answer must be supported directly by the retrieved event.\\n"
                "7. Explanations: The explanation must reference the specific factual basis of the correct answer.\\n"
                "Format as a numbered quiz. Use ### Current Affairs Practice Quiz as the title.\\n"
                "Use **Q to denote a question. End each question with **Correct Answer: [Option] and **Explanation:** [Text]."
            )
        else:
            system_prompt = (
                "You are FlashFacts AI, an exam-focused current affairs assistant. "
                "Answer the user's question using ONLY the provided verified FlashFacts event context. "
                "Do NOT invent current affairs not present in the context. "
                "Structure the response clearly with High Priority events, What Happened, Why It Matters, Exam Facts, and Sources."
            )

        try:
            import httpx
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user", 
                        "content": f"Context:\\n{context_str}\\n\\nQuestion: {question}"
                    }
                ],
                "temperature": 0.2
            }
            resp = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=15.0
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                return None
        except Exception:
            return None

"""
    return content[:target_start] + new_block + content[target_end:]

content = replace_ai_answer(content)
with open('apps/api/app/services/ai_assistant.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated _synthesize_ai_answer!")
