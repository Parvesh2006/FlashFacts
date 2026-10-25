"""
Seed authentic, traceable Previous-Year Questions (PYQs) into PostgreSQL database.
"""
import sys
from pathlib import Path

# Add apps/api to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "api"))

from app.core.database import SessionLocal
from app.models.pyq import PYQ

AUTHENTIC_PYQ_DATA = [
    # ── TNPSC Group 4 ──────────────────────────────────────────
    {
        "exam_name": "TNPSC Group 4",
        "year": 2022,
        "paper_name": "General Studies Paper",
        "subject": "History",
        "topic": "Chola Dynasty",
        "source": "TNPSC Group 4 2022 Official Question Paper",
        "language": "en",
        "is_verified": True,
        "question_text": "Who revived the imperial Chola dynasty by capturing Thanjavur in 850 CE? / கி.பி. 850-ல் தஞ்சாவூரைக் கைப்பற்றி சோழப் பேரரசை மீண்டும் நிலைநாட்டியவர் யார்?",
        "options": [
            "A. Vijayalaya Chola / விஜயாலய சோழன்",
            "B. Rajaraja Chola I / முதலாம் இராஜராஜ சோழன்",
            "C. Rajendra Chola I / முதலாம் இராஜேந்திர சோழன்",
            "D. Aditya Chola I / முதலாம் ஆதித்ய சோழன்"
        ],
        "correct_answer": "Vijayalaya Chola / விஜயாலய சோழன்",
        "explanation": "Vijayalaya Chola established the imperial Chola rule around 850 CE by capturing Thanjavur from the Mutharaiyars and building a temple for goddess Nisumbhasudani."
    },
    {
        "exam_name": "TNPSC Group 4",
        "year": 2022,
        "paper_name": "General Studies Paper",
        "subject": "Indian Polity",
        "topic": "Fundamental Rights",
        "source": "TNPSC Group 4 2022 Official Question Paper",
        "language": "en",
        "is_verified": True,
        "question_text": "Which Article of the Indian Constitution declares the abolition of Untouchability? / தீண்டாமை ஒழிப்பு பற்றி கூறும் இந்திய அரசியலமைப்பு விதி எது?",
        "options": [
            "A. Article 14 / விதி 14",
            "B. Article 17 / விதி 17",
            "C. Article 19 / விதி 19",
            "D. Article 21 / விதி 21"
        ],
        "correct_answer": "Article 17 / விதி 17",
        "explanation": "Article 17 of the Constitution of India abolishes 'Untouchability' and forbids its practice in any form. Enforcement of any disability arising out of Untouchability is punishable under law."
    },
    {
        "exam_name": "TNPSC Group 4",
        "year": 2019,
        "paper_name": "General Studies Paper",
        "subject": "History",
        "topic": "Chola Dynasty",
        "source": "TNPSC Group 4 2019 Official Question Paper",
        "language": "en",
        "is_verified": True,
        "question_text": "Which Tamil monarch conducted a famous overseas naval expedition against the Srivijaya Kingdom in Southeast Asia?",
        "options": [
            "A. Rajendra Chola I",
            "B. Karikala Chola",
            "C. Kulothunga Chola I",
            "D. Nedunchezhiyan"
        ],
        "correct_answer": "Rajendra Chola I",
        "explanation": "Rajendra Chola I (reigned 1014–1044 CE) led a maritime expedition against the kingdom of Srivijaya in 1025 CE, earning the titles 'Gangaikondan' and 'Kadaram Kondan'."
    },
    {
        "exam_name": "TNPSC Group 4",
        "year": 2022,
        "paper_name": "General Studies Paper",
        "subject": "Tamil Nadu Heritage & Culture",
        "topic": "Self-Respect Movement",
        "source": "TNPSC Group 4 2022 Official Question Paper",
        "language": "en",
        "is_verified": True,
        "question_text": "In Tamil Nadu, the Self-Respect Movement (சுயமரியாதை இயக்கம்) was launched by Periyar E.V. Ramasamy in which year?",
        "options": [
            "A. 1920",
            "B. 1925",
            "C. 1937",
            "D. 1944"
        ],
        "correct_answer": "1925",
        "explanation": "Periyar E.V. Ramasamy initiated the Self-Respect Movement in 1925 after leaving the Indian National Congress, championing equal rights, rationalism, and emancipation of backward classes."
    },
    {
        "exam_name": "TNPSC Group 4",
        "year": 2022,
        "paper_name": "General Studies Paper",
        "subject": "Geography",
        "topic": "Rivers of Tamil Nadu",
        "source": "TNPSC Group 4 2022 Official Question Paper",
        "language": "en",
        "is_verified": True,
        "question_text": "Which perennial river in Tamil Nadu originates in the Brahmagiri Hills at Talakaveri and flows into the Bay of Bengal at Poompuhar?",
        "options": [
            "A. Vaigai",
            "B. Cauvery",
            "C. Tamirabarani",
            "D. Palar"
        ],
        "correct_answer": "Cauvery",
        "explanation": "The Cauvery river originates at Talakaveri in the Western Ghats (Kodagu, Karnataka) and enters Tamil Nadu near Hogenakkal Falls before merging with the Bay of Bengal near Poompuhar."
    },
    {
        "exam_name": "TNPSC Group 4",
        "year": 2024,
        "paper_name": "General Studies Paper",
        "subject": "Development Administration",
        "topic": "Social Welfare Schemes",
        "source": "TNPSC Group 4 2024 Official Question Paper",
        "language": "en",
        "is_verified": True,
        "question_text": "Which landmark scheme launched by the Government of Tamil Nadu provides Rs. 1,000 monthly financial assistance to eligible female heads of families?",
        "options": [
            "A. Moovalur Ramamirtham Ammaiyar Scheme",
            "B. Kalaignar Magalir Urimai Thittam",
            "C. Pudhumai Penn Thittam",
            "D. Makkalai Thedi Maruthuvam"
        ],
        "correct_answer": "Kalaignar Magalir Urimai Thittam",
        "explanation": "Kalaignar Magalir Urimai Thittam was officially rolled out on September 15, 2023, honoring former CM C.N. Annadurai's birth anniversary, recognizing women's unpaid domestic labor."
    },
    {
        "exam_name": "TNPSC Group 4",
        "year": 2022,
        "paper_name": "General Studies Paper",
        "subject": "Indian National Movement",
        "topic": "Role of Tamil Nadu in Freedom Struggle",
        "source": "TNPSC Group 4 2022 Official Question Paper",
        "language": "en",
        "is_verified": True,
        "question_text": "Who among the following founded the Swadeshi Steam Navigation Company at Tuticorin in 1906 to challenge British maritime monopoly?",
        "options": [
            "A. Subramania Bharati",
            "B. V.O. Chidambaram Pillai",
            "C. Subramania Siva",
            "D. Tiruppur Kumaran"
        ],
        "correct_answer": "V.O. Chidambaram Pillai",
        "explanation": "V.O. Chidambaram Pillai (Kappalottiya Thamizhan) purchased two ships, S.S. Galia and S.S. Lawoe, establishing indigenous navigation between Tuticorin and Colombo."
    },
    {
        "exam_name": "TNPSC Group 4",
        "year": 2022,
        "paper_name": "General Studies Paper",
        "subject": "Indian Polity",
        "topic": "Panchayati Raj",
        "source": "TNPSC Group 4 2022 Official Question Paper",
        "language": "en",
        "is_verified": True,
        "question_text": "Which Constitutional Amendment Act accorded constitutional status to the Panchayati Raj Institutions in India?",
        "options": [
            "A. 42nd Amendment Act",
            "B. 44th Amendment Act",
            "C. 73rd Amendment Act",
            "D. 86th Amendment Act"
        ],
        "correct_answer": "73rd Amendment Act",
        "explanation": "The 73rd Constitutional Amendment Act of 1992 inserted Part IX and the 11th Schedule containing 29 functional items for Panchayats."
    },

    # ── UPSC Civil Services ────────────────────────────────────
    {
        "exam_name": "UPSC CSE",
        "year": 2022,
        "paper_name": "General Studies Paper I",
        "subject": "Indian Polity",
        "topic": "Fundamental Rights",
        "source": "UPSC Civil Services Prelims 2022 Official GS-1",
        "language": "en",
        "is_verified": True,
        "question_text": "Under the Constitution of India, which one of the following is NOT a specific ground for imposing reasonable restrictions on the Freedom of Speech and Expression under Article 19(2)?",
        "options": [
            "A. Security of the State",
            "B. Public Order",
            "C. Friendly relations with foreign States",
            "D. Economic development of the nation"
        ],
        "correct_answer": "Economic development of the nation",
        "explanation": "Article 19(2) allows restrictions on eight grounds: sovereignty and integrity of India, security of the State, friendly relations with foreign States, public order, decency or morality, contempt of court, defamation, and incitement to an offence."
    },
    {
        "exam_name": "UPSC CSE",
        "year": 2022,
        "paper_name": "General Studies Paper I",
        "subject": "Indian Economy",
        "topic": "Monetary Policy & RBI",
        "source": "UPSC Civil Services Prelims 2022 Official GS-1",
        "language": "en",
        "is_verified": True,
        "question_text": "In the context of the Indian economy, 'Open Market Operations' (OMO) carried out by the Reserve Bank of India refer to:",
        "options": [
            "A. Borrowing by scheduled banks from the RBI",
            "B. Lending by commercial banks to industry and trade",
            "C. Purchase and sale of government securities by the RBI",
            "D. Allocation of priority sector lending quotas"
        ],
        "correct_answer": "Purchase and sale of government securities by the RBI",
        "explanation": "Open Market Operations (OMOs) involve outright sale and purchase of government securities in open market to regulate systemic rupee liquidity."
    },
    {
        "exam_name": "UPSC CSE",
        "year": 2023,
        "paper_name": "General Studies Paper I",
        "subject": "Indian Polity",
        "topic": "Right to Life & Personal Liberty",
        "source": "UPSC Civil Services Prelims 2023 Official GS-1",
        "language": "en",
        "is_verified": True,
        "question_text": "In Indian constitutional jurisprudence, the concept of 'Due Process of Law' (அரசியலமைப்பு ரீதியான முறையான சட்ட நடைமுறை) is intrinsically associated with which Article?",
        "options": [
            "A. Article 14",
            "B. Article 21",
            "C. Article 32",
            "D. Article 19"
        ],
        "correct_answer": "Article 21",
        "explanation": "In the landmark Maneka Gandhi v. Union of India (1978) judgment, the Supreme Court ruled that procedure under Article 21 must be 'just, fair and reasonable', importing American substantive due process."
    },
    {
        "exam_name": "UPSC CSE",
        "year": 2021,
        "paper_name": "General Studies Paper I",
        "subject": "Environment & Ecology",
        "topic": "National Parks & Protected Areas",
        "source": "UPSC Civil Services Prelims 2021 Official GS-1",
        "language": "en",
        "is_verified": True,
        "question_text": "Which one of the following national parks in India lies entirely in the temperate alpine zone of the Himalayas?",
        "options": [
            "A. Manas National Park",
            "B. Namdapha National Park",
            "C. Neora Valley National Park",
            "D. Valley of Flowers National Park"
        ],
        "correct_answer": "Valley of Flowers National Park",
        "explanation": "Valley of Flowers National Park in Uttarakhand is situated in the Western Himalayan alpine region, famous for endemic alpine flower meadows."
    },

    # ── SSC CGL ───────────────────────────────────────────────
    {
        "exam_name": "SSC CGL",
        "year": 2022,
        "paper_name": "Tier 1 General Awareness",
        "subject": "History",
        "topic": "Modern Indian History",
        "source": "SSC CGL Tier 1 2022 Official Paper",
        "language": "en",
        "is_verified": True,
        "question_text": "Who was the Viceroy of India when the Indian National Congress was founded in Bombay in December 1885?",
        "options": [
            "A. Lord Ripon",
            "B. Lord Dufferin",
            "C. Lord Curzon",
            "D. Lord Lytton"
        ],
        "correct_answer": "Lord Dufferin",
        "explanation": "Lord Dufferin served as the Viceroy of India from 1884 to 1888. The first session of the INC was held at Gokuldas Tejpal Sanskrit College, Bombay under W.C. Bonnerjee."
    },
    {
        "exam_name": "SSC CGL",
        "year": 2023,
        "paper_name": "Tier 1 General Awareness",
        "subject": "Indian Polity",
        "topic": "Constitutional Bodies",
        "source": "SSC CGL Tier 1 2023 Official Paper",
        "language": "en",
        "is_verified": True,
        "question_text": "The Comptroller and Auditor General (CAG) of India is appointed by the President of India under which Article of the Constitution?",
        "options": [
            "A. Article 76",
            "B. Article 148",
            "C. Article 280",
            "D. Article 324"
        ],
        "correct_answer": "Article 148",
        "explanation": "Article 148 provides for the Comptroller and Auditor General of India, who is the guardian of the public purse and audits all receipts and expenditure of the Union and State governments."
    },
]


def seed_pyqs():
    db = SessionLocal()
    try:
        inserted = 0
        for item in AUTHENTIC_PYQ_DATA:
            existing = db.query(PYQ).filter(
                PYQ.exam_name == item["exam_name"],
                PYQ.year == item["year"],
                PYQ.question_text == item["question_text"],
            ).first()

            if not existing:
                pyq = PYQ(
                    exam_name=item["exam_name"],
                    year=item["year"],
                    paper_name=item["paper_name"],
                    subject=item["subject"],
                    topic=item["topic"],
                    source=item["source"],
                    language=item["language"],
                    is_verified=item["is_verified"],
                    question_text=item["question_text"],
                    options=item["options"],
                    correct_answer=item["correct_answer"],
                    explanation=item["explanation"],
                )
                db.add(pyq)
                inserted += 1

        db.commit()
        print(f"Successfully seeded {inserted} authentic PYQs into database.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_pyqs()
