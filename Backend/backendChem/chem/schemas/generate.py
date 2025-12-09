from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from pyparsing import Optional

class MolGenerateRequest(BaseModel):
    smi_string: str              # <- sesuai ML
    num_molecules: int
    algorithm: str               # "CMA-ES" / "none" (kalau ada)
    property_to_optimize: str    # "QED" / "plogP"
    min_similarity: float
    particles: int
    iterations: int
    minimize: bool


# ========== RESPONSE DARI ML ==========
class MetaResponse(BaseModel):
    original_smiles: str
    optimized_property: str
    algorithm: str


class GeneratedMolecule(BaseModel):
    sample: str
    score: float


class AnalyzeResponse(BaseModel):
    status: str
    meta: MetaResponse
    generated_molecules: list[GeneratedMolecule]
    analysis_result: Any


# ========== YANG DIKIRIM BALIK KE FE (dan disimpan di DB) ==========
class GenerationResponse(BaseModel):
    id: int
    user_id: int

    smi_string: str
    num_molecules: int
    algorithm: str
    property_to_optimize: str
    min_similarity: float
    particles: int
    iterations: int
    minimize: bool

    result: AnalyzeResponse | dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)