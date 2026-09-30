import os

# 1. FIX AI ASSISTANT
with open("apps/api/app/services/ai_assistant.py", "r", encoding="utf-8") as f:
    content = f.read()

old_words_block = '''        clean_words = []
        for word in q_lower.split():
            if word not in ("what", "happened", "today", "current", "affairs", "the", "in", "for", "give", "me", "show", "tell", "explain", "is", "of", "and"):
                clean_words.append(word)'''

new_words_block = '''        clean_words = []
        ignore_words = {
            "what", "happened", "today", "current", "affairs", "the", "in", "for", "give", "me", 
            "show", "tell", "explain", "is", "of", "and", "some", "mcq", "mcqs", "about", "on", 
            "quiz", "multiple", "choice", "questions", "generate", "create", "make", "from", 
            "please", "can", "you", "a", "an", "any"
        }
        for word in q_lower.split():
            if word not in ignore_words:
                clean_words.append(word)'''

content = content.replace(old_words_block, new_words_block)


old_prompt = '''        system_prompt = (
            "You are FlashFacts AI, an exam-focused current affairs assistant. "
            "Answer the user's question using ONLY the provided verified FlashFacts event context. "
            "Do NOT invent current affairs not present in the context. "
            "Structure the response clearly with High Priority events, What Happened, Why It Matters, Exam Facts, and Sources."
        )'''

new_prompt = '''        is_mcq = "mcq" in question.lower() or "multiple choice" in question.lower() or "quiz" in question.lower()

        if is_mcq:
            system_prompt = (
                "You are FlashFacts AI, an expert MCQ generator for competitive exams. "
                "The user has requested MCQs based on current affairs. "
                "Use ONLY the provided retrieved context to generate the questions. "
                "CRITICAL MCQ RULES:\\n"
                "1. Fact-based: Test specific factual claims, not generic summaries.\\n"
                "2. Plausible Distractors: Options B, C, and D MUST be plausible, domain-relevant alternatives. NEVER use 'The event was cancelled', 'None of the above', or 'It was entirely unrelated'.\\n"
                "3. Concise Options: Options must be short, factual phrases, not entire paragraphs or the whole event description.\\n"
                "4. Distribute Answers: The correct answer must be randomly distributed among A, B, C, D (do not always make A the correct answer).\\n"
                "5. Explanations: The explanation must briefly state WHY the answer is correct based on the specific facts in the event, not a generic template.\\n"
                "6. No Duplicates: Do not ask the same question twice. Use different events for different questions.\\n"
                "Format as a numbered quiz. Use ### Current Affairs Practice Quiz as the title.\\n"
                "Use **Q to denote a question (e.g. **Q1. ). End each question with **Correct Answer: [Option] and **Explanation:** [Text]."
            )
        else:
            system_prompt = (
                "You are FlashFacts AI, an exam-focused current affairs assistant. "
                "Answer the user's question using ONLY the provided verified FlashFacts event context. "
                "Do NOT invent current affairs not present in the context. "
                "Structure the response clearly with High Priority events, What Happened, Why It Matters, Exam Facts, and Sources."
            )'''

content = content.replace(old_prompt, new_prompt)

with open("apps/api/app/services/ai_assistant.py", "w", encoding="utf-8") as f:
    f.write(content)


# 2. FIX EXAM INTELLIGENCE
with open("apps/api/app/services/exam_intelligence.py", "r", encoding="utf-8") as f:
    content2 = f.read()

old_prompt2 = '''        system_prompt = (
            f"You are an expert MCQ generator for competitive exam preparation{exam_context}. "
            f"Generate exactly {count} multiple-choice questions based ONLY on the provided event information. "
            "Each question must have exactly 4 options (A, B, C, D), one correct answer, and a brief explanation. "
            "Do NOT invent facts not present in the source. "
            "Return valid JSON: {\\"mcqs\\": [{\\"question\\": \\"...\\", \\"options\\": [\\"A. ...\\", \\"B. ...\\", \\"C. ...\\", \\"D. ...\\"], "
            "\\"correct_answer\\": \\"A\\", \\"explanation\\": \\"...\\"}]}"
        )'''

new_prompt2 = '''        system_prompt = (
            f"You are an expert MCQ generator for competitive exam preparation{exam_context}. "
            f"Generate exactly {count} multiple-choice questions based ONLY on the provided event information. "
            "CRITICAL MCQ RULES:\\n"
            "1. Fact-based: Test specific factual claims, not generic summaries.\\n"
            "2. Plausible Distractors: Options MUST be plausible, domain-relevant alternatives. NEVER use 'The event was cancelled', 'None of the above', or 'entirely unrelated'.\\n"
            "3. Concise Options: Options must be short factual phrases, not entire paragraphs.\\n"
            "4. Distribute Answers: The correct answer must be randomly distributed among A, B, C, D.\\n"
            "5. Explanations: Briefly state WHY the answer is correct based on the facts.\\n"
            "Do NOT invent facts not present in the source.\\n"
            "Return valid JSON: {\\"mcqs\\": [{\\"question\\": \\"...\\", \\"options\\": [\\"A. ...\\", \\"B. ...\\", \\"C. ...\\", \\"D. ...\\"], "
            "\\"correct_answer\\": \\"A\\", \\"explanation\\": \\"...\\"}]}"
        )'''

content2 = content2.replace(old_prompt2, new_prompt2)

with open("apps/api/app/services/exam_intelligence.py", "w", encoding="utf-8") as f:
    f.write(content2)

print("Updates applied.")
