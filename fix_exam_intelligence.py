import re

with open('apps/api/app/services/exam_intelligence.py', 'r', encoding='utf-8') as f:
    content = f.read()

def replace_ai_mcqs(content):
    target_start = content.find('        system_prompt = (')
    target_end = content.find('        try:', target_start)
    if target_start == -1 or target_end == -1: return content
    
    new_block = """        system_prompt = (
            f"You are an expert MCQ generator for competitive exam preparation{exam_context}. "
            f"Generate exactly {count} multiple-choice questions based ONLY on the provided event information. "
            "CRITICAL MCQ RULES:\\n"
            "1. Fact-based: Test specific factual claims, not generic summaries.\\n"
            "2. Concise Options: Every option must be a concise factual statement or answer phrase. Do not copy the entire summary into an option.\\n"
            "3. Plausible Distractors: Distractors must be plausible alternatives from the same subject/domain, with similar length and specificity to the correct answer. Every option must be independently plausible to a student who knows the subject.\\n"
            "4. Answer Distribution: Across a multi-question quiz, vary the correct option position among A/B/C/D rather than always placing it at A.\\n"
            "5. Explanations: Briefly state WHY the answer is correct based on the specific facts in the event.\\n"
            "Do NOT invent facts not present in the source.\\n"
            "Return valid JSON: {\\"mcqs\\": [{\\"question\\": \\"...\\", \\"options\\": [\\"A. ...\\", \\"B. ...\\", \\"C. ...\\", \\"D. ...\\"], "
            "\\"correct_answer\\": \\"A\\", \\"explanation\\": \\"...\\"}]}"
        )

"""
    return content[:target_start] + new_block + content[target_end:]

content = replace_ai_mcqs(content)
with open('apps/api/app/services/exam_intelligence.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated _generate_ai_mcqs!")
