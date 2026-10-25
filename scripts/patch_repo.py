from pathlib import Path

path = Path("apps/api/app/repositories/event_repository.py")
content = path.read_text(encoding="utf-8")

old_block = """        if exam:
            exam_norm = exam.strip().upper()
            if exam_norm == "TNPSC":
                exam_type_val = "TNPSC"
            elif exam_norm == "UPSC":
                exam_type_val = "UPSC"
            elif exam_norm == "SSC":
                exam_type_val = "SSC"
            elif exam_norm == "BANKING":
                exam_type_val = "BANKING"
            elif exam_norm == "RAILWAY":
                exam_type_val = "RAILWAY"
            else:
                exam_type_val = "GENERAL_GOVT"

            query = query.join(Event.exam_relevances).filter(
                EventExamRelevance.exam_type == exam_type_val,
                EventExamRelevance.relevance_level.in_(["VERY_HIGH", "HIGH", "MEDIUM"])
            )"""

new_block = """        if exam:
            exam_norm = exam.strip().upper()
            if "TNPSC" in exam_norm:
                exam_type_val = "TNPSC"
            elif "UPSC" in exam_norm:
                exam_type_val = "UPSC"
            elif "SSC" in exam_norm:
                exam_type_val = "SSC"
            elif "BANK" in exam_norm:
                exam_type_val = "BANKING"
            elif "RAILWAY" in exam_norm or "RRB" in exam_norm:
                exam_type_val = "RAILWAY"
            else:
                exam_type_val = "GENERAL_GOVT"

            query = query.join(Event.exam_relevances).filter(
                EventExamRelevance.exam_type == exam_type_val,
                EventExamRelevance.relevance_level.in_(["VERY_HIGH", "HIGH", "MEDIUM"])
            )
            non_exam_domains = ["Entertainment", "Crime", "Lifestyle", "Gossip", "Cinema"]
            query = query.filter(~Event.domain.in_(non_exam_domains))"""

old_search_block = """        if exam:
            exam_norm = exam.strip().upper()
            exam_type_val = "TNPSC" if "TNPSC" in exam_norm else ("UPSC" if "UPSC" in exam_norm else ("SSC" if "SSC" in exam_norm else ("BANK" in exam_norm and "BANKING" or ("RAILWAY" if "RAILWAY" in exam_norm else "GENERAL_GOVT"))))
            query = query.join(Event.exam_relevances).filter(
                EventExamRelevance.exam_type == exam_type_val,
                EventExamRelevance.relevance_level.in_(["VERY_HIGH", "HIGH", "MEDIUM"])
            )"""

new_search_block = """        if exam:
            exam_norm = exam.strip().upper()
            exam_type_val = "TNPSC" if "TNPSC" in exam_norm else ("UPSC" if "UPSC" in exam_norm else ("SSC" if "SSC" in exam_norm else ("BANK" in exam_norm and "BANKING" or ("RAILWAY" if "RAILWAY" in exam_norm else "GENERAL_GOVT"))))
            query = query.join(Event.exam_relevances).filter(
                EventExamRelevance.exam_type == exam_type_val,
                EventExamRelevance.relevance_level.in_(["VERY_HIGH", "HIGH", "MEDIUM"])
            )
            non_exam_domains = ["Entertainment", "Crime", "Lifestyle", "Gossip", "Cinema"]
            query = query.filter(~Event.domain.in_(non_exam_domains))"""

if old_block in content and old_search_block in content:
    content = content.replace(old_block, new_block).replace(old_search_block, new_search_block)
    path.write_text(content, encoding="utf-8")
    print("Successfully patched event_repository.py")
else:
    print("Blocks not found in content, checking CRLF vs LF...")
    content_crlf = content.replace("\r\n", "\n")
    old_block_lf = old_block.replace("\r\n", "\n")
    old_search_lf = old_search_block.replace("\r\n", "\n")
    if old_block_lf in content_crlf and old_search_lf in content_crlf:
        content_crlf = content_crlf.replace(old_block_lf, new_block.replace("\r\n", "\n")).replace(old_search_lf, new_search_block.replace("\r\n", "\n"))
        path.write_text(content_crlf, encoding="utf-8")
        print("Successfully patched event_repository.py with LF normalization")
    else:
        print("Failed to find targets.")
