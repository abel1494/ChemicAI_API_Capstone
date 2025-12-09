# chem/routes/generate_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from auth.services.auth_service import get_current_user  # sesuaikan path
from chem.schemas.generate import (
    MolGenerateRequest,
    GenerationResponse,
)
from chem.services.generate_services import (
    call_nvidia_molmim,
    create_generation,
    get_generations_by_user,
    get_generation_by_id_for_user,
)

router = APIRouter(
    prefix="/chem",
    tags=["Chemistry"],
)


@router.post(
    "/generate",
    response_model=GenerationResponse,
)
def generate_molecules(
    body: MolGenerateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Ambil user_id dari JWT payload
    user_id = current_user.id
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User id not found in token",
        )

    # Call NVIDIA API via service
    try:
        result = call_nvidia_molmim(body.model_dump())
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )

    # Simpan history ke DB via service
    gen = create_generation(db, user_id=user_id, body=body, result=result)
    return gen


@router.get(
    "/history",
    response_model=list[GenerationResponse],
)
def get_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
):
    user_id = current_user.id
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User id not found in token",
        )

    gens = get_generations_by_user(db, user_id=user_id, skip=skip, limit=limit)
    return gens


@router.get(
    "/history/{generation_id}",
    response_model=GenerationResponse,
)
def get_history_detail(
    generation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = current_user.id
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User id not found in token",
        )

    gen = get_generation_by_id_for_user(
        db, user_id=user_id, generation_id=generation_id
    )
    if not gen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History not found",
        )
    return gen
