from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.syllabus import SyllabusTopic, UserSyllabusProgress
from app.schemas.syllabus import (
    SyllabusTopicResponse,
    SyllabusUnitGroup,
    SyllabusSubjectGroup,
    ExamSyllabusResponse,
    TopicProgressResponse,
)


OFFICIAL_SYLLABUS_SEEDS = [
    # ── TNPSC Group 4 ──────────────────────────────────────────
    {
        "exam_name": "TNPSC Group 4",
        "subject": "General Science",
        "unit_number": 1,
        "unit_name": "Unit I: General Science",
        "topic_name": "Physics — Scientific Laws, Mechanics, Electricity and Magnetism",
        "subtopics": ["Nature of Universe", "General Scientific Laws", "Mechanics and properties of matter", "Electricity, Magnetism, Heat, Light, Sound"],
        "order_index": 1,
    },
    {
        "exam_name": "TNPSC Group 4",
        "subject": "General Science",
        "unit_number": 1,
        "unit_name": "Unit I: General Science",
        "topic_name": "Chemistry — Elements, Compounds, Acids, Bases and Salts",
        "subtopics": ["Elements and Compounds", "Acids, Bases, Salts", "Petroleum products", "Fertilizers, pesticides"],
        "order_index": 2,
    },
    {
        "exam_name": "TNPSC Group 4",
        "subject": "General Science",
        "unit_number": 1,
        "unit_name": "Unit I: General Science",
        "topic_name": "Biology — Human Physiology, Diseases, Genetics and Nutrition",
        "subtopics": ["Main concepts of Life Science", "Classification of living organisms", "Nutrition, health and hygiene", "Human diseases and prevention"],
        "order_index": 3,
    },
    {
        "exam_name": "TNPSC Group 4",
        "subject": "Geography",
        "unit_number": 3,
        "unit_name": "Unit III: Geography of India and Tamil Nadu",
        "topic_name": "Physical Geography — Monsoon, Weather and Climate",
        "subtopics": ["Earth and Universe", "Monsoon, rainfall, weather & climate", "Water resources and rivers in India", "Soil, minerals and natural resources"],
        "order_index": 4,
    },
    {
        "exam_name": "TNPSC Group 4",
        "subject": "Geography",
        "unit_number": 3,
        "unit_name": "Unit III: Geography of India and Tamil Nadu",
        "topic_name": "Human and Economic Geography — Forests, Wildlife and Transport",
        "subtopics": ["Forest and wildlife", "Agricultural pattern", "Transport and communication", "Natural calamities and disaster management"],
        "order_index": 5,
    },
    {
        "exam_name": "TNPSC Group 4",
        "subject": "History",
        "unit_number": 4,
        "unit_name": "Unit IV: History and Culture of India and Tamil Nadu",
        "topic_name": "Ancient and Medieval India — Indus Valley to Mughals",
        "subtopics": ["Indus Valley Civilization", "Guptas, Delhi Sultans, Mughals, Marathas", "Age of Vijayanagaram and Bahmani Kingdoms", "South Indian History"],
        "order_index": 6,
    },
    {
        "exam_name": "TNPSC Group 4",
        "subject": "Indian Polity",
        "unit_number": 5,
        "unit_name": "Unit V: Indian Polity",
        "topic_name": "Constitutional Framework — Preamble, Fundamental Rights and Duties",
        "subtopics": ["Constitution of India", "Preamble to the Constitution", "Salient features of Constitution", "Fundamental Rights, Fundamental Duties, DPSP"],
        "order_index": 7,
    },
    {
        "exam_name": "TNPSC Group 4",
        "subject": "Indian Polity",
        "unit_number": 5,
        "unit_name": "Unit V: Indian Polity",
        "topic_name": "Union, State Government and Local Self Governance",
        "subtopics": ["Union Executive & Parliament", "State Executive & State Legislature", "Local Governments and Panchayat Raj", "Judiciary in India — Supreme Court and High Courts"],
        "order_index": 8,
    },
    {
        "exam_name": "TNPSC Group 4",
        "subject": "Indian Economy",
        "unit_number": 6,
        "unit_name": "Unit VI: Indian Economy",
        "topic_name": "Economic Planning, Finance and Banking",
        "subtopics": ["Nature of Indian economy", "Five year plan models and NITI Aayog", "Sources of revenue and Reserve Bank of India", "Fiscal Policy and Monetary Policy", "Finance Commission and GST"],
        "order_index": 9,
    },
    {
        "exam_name": "TNPSC Group 4",
        "subject": "Indian National Movement",
        "unit_number": 7,
        "unit_name": "Unit VII: Indian National Movement",
        "topic_name": "National Renaissance and Freedom Struggle in Tamil Nadu",
        "subtopics": ["National Renaissance", "Early uprising against British rule", "Indian National Congress", "Role of Tamil Nadu in freedom struggle — VO Chidambaram, Subramania Bharati, Rajaji, Kamaraj"],
        "order_index": 10,
    },
    {
        "exam_name": "TNPSC Group 4",
        "subject": "Tamil Nadu Heritage & Culture",
        "unit_number": 8,
        "unit_name": "Unit VIII: History, Culture, Heritage and Socio-Political Movements in TN",
        "topic_name": "Thirukkural and Socio-Political Movements in Tamil Nadu",
        "subtopics": ["History of Tamil Society and related archaeological discoveries", "Thirukkural as a secular literature and moral philosophy", "Evolution of 19th & 20th century socio-political movements in TN", "Self Respect Movement, Justice Party, Dravidian Movement"],
        "order_index": 11,
    },
    {
        "exam_name": "TNPSC Group 4",
        "subject": "Development Administration",
        "unit_number": 9,
        "unit_name": "Unit IX: Development Administration in Tamil Nadu",
        "topic_name": "Human Development and Social Welfare Schemes of Tamil Nadu",
        "subtopics": ["Human Development Indicators in Tamil Nadu", "Social Welfare Schemes for women, children, and underprivileged", "Social Justice and Social Harmony as foundations of economic development", "Education and Health Systems in Tamil Nadu", "e-Governance in Tamil Nadu"],
        "order_index": 12,
    },

    # ── UPSC Civil Services ────────────────────────────────────
    {
        "exam_name": "UPSC CSE",
        "subject": "Polity & Governance",
        "unit_number": 1,
        "unit_name": "Polity & Constitutional Governance",
        "topic_name": "Indian Constitution — Historical Underpinnings, Evolution, Amendments",
        "subtopics": ["Basic Structure Doctrine", "Federalism & Center-State Relations", "Parliament & State Legislatures", "Emergency Provisions", "Statutory, Regulatory & Quasi-Judicial Bodies"],
        "order_index": 1,
    },
    {
        "exam_name": "UPSC CSE",
        "subject": "Economy & Development",
        "unit_number": 2,
        "unit_name": "Economic & Social Development",
        "topic_name": "Macroeconomics, Public Finance and Inclusive Growth",
        "subtopics": ["National Income Accounting", "Monetary Policy & Inflation Targeting", "Government Budgeting & Fiscal Deficit", "Banking Reforms & Insolvency Code", "External Sector & BoP"],
        "order_index": 2,
    },
    {
        "exam_name": "UPSC CSE",
        "subject": "Environment & Ecology",
        "unit_number": 3,
        "unit_name": "Environment, Ecology and Climate Change",
        "topic_name": "Biodiversity Conservation and Environmental Legislation",
        "subtopics": ["Ecosystem Dynamics & Biodiversity Hotspots", "Protected Area Network: National Parks, Wildlife Sanctuaries", "Climate Change Treaties: UNFCCC, Paris Agreement, COP Decisions", "Pollution Control & Environmental Impact Assessment"],
        "order_index": 3,
    },
    {
        "exam_name": "UPSC CSE",
        "subject": "Science & Technology",
        "unit_number": 4,
        "unit_name": "Science, Space and Innovation",
        "topic_name": "Frontier Technologies — Space, Biotech, AI and Defense",
        "subtopics": ["ISRO Space Missions: Gaganyaan, Chandrayaan, Aditya-L1", "Biotechnology & Genome Editing (CRISPR)", "Artificial Intelligence, Quantum Computing, Semiconductor Mission", "Indigenous Defense Platforms & DRDO Developments"],
        "order_index": 4,
    },

    # ── SSC CGL ───────────────────────────────────────────────
    {
        "exam_name": "SSC CGL",
        "subject": "General Awareness",
        "unit_number": 1,
        "unit_name": "General Awareness Core",
        "topic_name": "Indian Polity, Articles and Constitutional Amendments",
        "subtopics": ["Important Articles of the Constitution", "Constitutional Bodies & Writs", "Panchayati Raj & Local Administration"],
        "order_index": 1,
    },
    {
        "exam_name": "SSC CGL",
        "subject": "General Awareness",
        "unit_number": 1,
        "unit_name": "General Awareness Core",
        "topic_name": "Physical and Indian Geography",
        "subtopics": ["River Systems & Dams in India", "Mountain Ranges & Passes", "National Parks & Biosphere Reserves", "Minerals & Industries"],
        "order_index": 2,
    },
    {
        "exam_name": "SSC CGL",
        "subject": "General Awareness",
        "unit_number": 1,
        "unit_name": "General Awareness Core",
        "topic_name": "Indian History and National Movement",
        "subtopics": ["Indus Valley & Vedic Period", "Medieval Dynasties & Architecture", "Governor Generals & Viceroy Era", "Important Battles & Treaties"],
        "order_index": 3,
    },
]


class SyllabusService:
    def __init__(self, db: Session):
        self.db = db
        self._ensure_seeds()

    def _ensure_seeds(self):
        count = self.db.query(SyllabusTopic).count()
        if count == 0:
            for item in OFFICIAL_SYLLABUS_SEEDS:
                topic = SyllabusTopic(
                    exam_name=item["exam_name"],
                    subject=item["subject"],
                    unit_number=item["unit_number"],
                    unit_name=item["unit_name"],
                    topic_name=item["topic_name"],
                    subtopics=item["subtopics"],
                    order_index=item["order_index"],
                )
                self.db.add(topic)
            self.db.commit()

    def get_exam_syllabus(self, user_id: str, exam_name: str) -> ExamSyllabusResponse:
        self._ensure_seeds()

        # Match exam by prefix or substring
        all_topics = (
            self.db.query(SyllabusTopic)
            .filter(SyllabusTopic.exam_name.ilike(f"%{exam_name}%"))
            .order_by(SyllabusTopic.subject, SyllabusTopic.unit_number, SyllabusTopic.order_index)
            .all()
        )

        if not all_topics:
            # Fall back to TNPSC Group 4 if unknown exam
            all_topics = (
                self.db.query(SyllabusTopic)
                .filter(SyllabusTopic.exam_name == "TNPSC Group 4")
                .order_by(SyllabusTopic.subject, SyllabusTopic.unit_number, SyllabusTopic.order_index)
                .all()
            )

        # Fetch user progress for these topics
        topic_ids = [t.id for t in all_topics]
        progress_rows = (
            self.db.query(UserSyllabusProgress)
            .filter(
                UserSyllabusProgress.user_id == user_id,
                UserSyllabusProgress.topic_id.in_(topic_ids),
            )
            .all()
        )
        progress_map = {p.topic_id: p for p in progress_rows}

        # Structure subjects -> units -> topics
        subjects_dict: Dict[str, Dict[str, List[SyllabusTopicResponse]]] = {}

        total_topics = len(all_topics)
        completed_topics = 0
        in_progress_topics = 0
        needs_revision_topics = 0

        for t in all_topics:
            p = progress_map.get(t.id)
            status = p.status if p else "not_started"
            notes = p.notes if p else None
            last_studied = p.last_studied_at if p else None

            if status == "completed":
                completed_topics += 1
            elif status == "in_progress":
                in_progress_topics += 1
            elif status == "needs_revision":
                needs_revision_topics += 1

            topic_resp = SyllabusTopicResponse(
                id=t.id,
                exam_name=t.exam_name,
                subject=t.subject,
                unit_number=t.unit_number,
                unit_name=t.unit_name,
                topic_name=t.topic_name,
                subtopics=t.subtopics or [],
                order_index=t.order_index,
                status=status,
                notes=notes,
                last_studied_at=last_studied,
            )

            if t.subject not in subjects_dict:
                subjects_dict[t.subject] = {}
            if t.unit_name not in subjects_dict[t.subject]:
                subjects_dict[t.subject][t.unit_name] = []
            subjects_dict[t.subject][t.unit_name].append(topic_resp)

        # Assemble hierarchy
        subject_groups: List[SyllabusSubjectGroup] = []
        for subj_name, units_dict in subjects_dict.items():
            unit_groups: List[SyllabusUnitGroup] = []
            subj_total = 0
            subj_completed = 0

            for u_name, topics in units_dict.items():
                u_tot = len(topics)
                u_comp = sum(1 for top in topics if top.status == "completed")
                u_pct = int((u_comp / u_tot) * 100) if u_tot > 0 else 0

                subj_total += u_tot
                subj_completed += u_comp

                unit_groups.append(
                    SyllabusUnitGroup(
                        unit_number=topics[0].unit_number if topics else None,
                        unit_name=u_name,
                        subject=subj_name,
                        topics=topics,
                        completed_count=u_comp,
                        total_count=u_tot,
                        completion_percentage=u_pct,
                    )
                )

            subj_pct = int((subj_completed / subj_total) * 100) if subj_total > 0 else 0
            subject_groups.append(
                SyllabusSubjectGroup(
                    subject=subj_name,
                    units=unit_groups,
                    completed_count=subj_completed,
                    total_count=subj_total,
                    completion_percentage=subj_pct,
                )
            )

        overall_pct = int((completed_topics / total_topics) * 100) if total_topics > 0 else 0

        return ExamSyllabusResponse(
            exam_name=exam_name,
            overall_completion_percentage=overall_pct,
            total_topics=total_topics,
            completed_topics=completed_topics,
            in_progress_topics=in_progress_topics,
            needs_revision_topics=needs_revision_topics,
            subjects=subject_groups,
        )

    def update_progress(
        self, user_id: str, topic_id: int, status: str, notes: Optional[str] = None
    ) -> TopicProgressResponse:
        topic = self.db.query(SyllabusTopic).filter(SyllabusTopic.id == topic_id).first()
        if not topic:
            raise ValueError("Syllabus topic not found")

        progress = (
            self.db.query(UserSyllabusProgress)
            .filter(
                UserSyllabusProgress.user_id == user_id,
                UserSyllabusProgress.topic_id == topic_id,
            )
            .first()
        )

        now = datetime.now(timezone.utc)
        if progress:
            progress.status = status
            if notes is not None:
                progress.notes = notes
            progress.last_studied_at = now
            progress.updated_at = now
        else:
            progress = UserSyllabusProgress(
                user_id=user_id,
                topic_id=topic_id,
                status=status,
                notes=notes,
                last_studied_at=now,
            )
            self.db.add(progress)

        self.db.commit()
        self.db.refresh(progress)

        return TopicProgressResponse(
            topic_id=topic_id,
            status=progress.status,
            notes=progress.notes,
            last_studied_at=progress.last_studied_at,
            message="Syllabus progress updated successfully",
        )
