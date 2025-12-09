import requests
from core.config_loader import settings
from typing import List, Optional

import requests
from sqlalchemy.orm import Session

from core.config_loader import settings
from chem.models.generation import Generation
from chem.schemas.generate import MolGenerateRequest
from chem.schemas.generate import AnalyzeResponse


def call_nvidia_molmim(payload: dict) -> dict:
    url = f"{settings.NVIDIA_BASE_URL}"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
    }

    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()  # kalau mau langsung raise kalau 4xx/5xx

    return resp.json()

def create_generation(
    db: Session,
    user_id: int,
    body: MolGenerateRequest,
    result: AnalyzeResponse,
) -> Generation:
    gen = Generation(
        user_id=user_id,
        smi_string=body.smi_string,
        num_molecules=body.num_molecules,
        algorithm=body.algorithm,
        property_to_optimize=body.property_to_optimize,
        min_similarity=body.min_similarity,
        particles=body.particles,
        iterations=body.iterations,
        minimize=body.minimize,
        result=result,   # simpan sebagai JSONB
    )
    db.add(gen)
    db.commit()
    db.refresh(gen)
    return gen


def get_generations_by_user(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 50,
) -> List[Generation]:
    return (
        db.query(Generation)
        .filter(Generation.user_id == user_id)
        .order_by(Generation.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_generation_by_id_for_user(
    db: Session,
    user_id: int,
    generation_id: int,
) -> Optional[Generation]:
    return (
        db.query(Generation)
        .filter(
            Generation.id == generation_id,
            Generation.user_id == user_id,
        )
        .first()
    )
