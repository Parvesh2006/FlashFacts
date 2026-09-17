from fastapi import APIRouter

router = APIRouter(prefix="/exams", tags=["exams"])


EXAMS = [
    {
        "id": "tnpsc-group-4",
        "name": "TNPSC Group 4",
        "code": "TNPSC-G4",
        "description": "Tamil Nadu Public Service Commission Group 4 examination.",
        "category": "tnpsc",
    },
    {
        "id": "tnpsc-group-2",
        "name": "TNPSC Group 2",
        "code": "TNPSC-G2",
        "description": "Tamil Nadu Public Service Commission Group 2 examination.",
        "category": "tnpsc",
    },
    {
        "id": "ssc-cgl",
        "name": "SSC CGL",
        "code": "SSC-CGL",
        "description": "Staff Selection Commission Combined Graduate Level examination.",
        "category": "ssc",
    },
    {
        "id": "ssc-chsl",
        "name": "SSC CHSL",
        "code": "SSC-CHSL",
        "description": "Staff Selection Commission Combined Higher Secondary Level examination.",
        "category": "ssc",
    },
    {
        "id": "upsc-cse",
        "name": "UPSC Civil Services",
        "code": "UPSC-CSE",
        "description": "Union Public Service Commission Civil Services examination.",
        "category": "upsc",
    },
    {
        "id": "rrb-ntpc",
        "name": "RRB NTPC",
        "code": "RRB-NTPC",
        "description": "Railway Recruitment Board Non-Technical Popular Categories examination.",
        "category": "rrb",
    },
    {
        "id": "banking",
        "name": "Banking",
        "code": "BANK",
        "description": "Competitive banking examinations including IBPS and SBI.",
        "category": "banking",
    },
]


@router.get("")
def get_exams():
    return EXAMS