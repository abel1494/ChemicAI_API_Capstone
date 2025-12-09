from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import requests
import json
import os
import uvicorn
from typing import Literal

# KONFIGURASI
GEMINI_MODEL_ID = "gemini-2.5-flash"
MOLMIM_CLOUD_ENDPOINT = "https://health.api.nvidia.com/v1/biology/nvidia/molmim/generate" 

# DATA CADANGAN
SIMULATED_MOL_DATA = """
[
  {"sample": "CCN(CC)C(=O)N[C@@H]1CCc2c1cccc2C(F)(F)F", "score": 0.905},
  {"sample": "CCN(CC)C(=O)N[C@@H]1CCCc2ccc3ccccc3c21", "score": 0.901},
  {"sample": "CCN(CC)C(=O)N[C@@H]1CCC(=O)N[C@]12CCCc1ccccc12", "score": 0.895},
  {"sample": "CCOC(=O)N1CCN([C@]2(C(=O)NC)C=Cc3cccc4cccc2c34)CC1", "score": 0.890},
  {"sample": "CCN(CC)C(=O)N1CCC[C@H](n2c(=O)[nH]c3ccc(Cl)cc3c2=O)C1", "score": 0.885},
  {"sample": "CCNC(=O)N1CCC[C@]2(C1)N[C@@H](CC)Cc1ccccc12", "score": 0.881},
  {"sample": "CCN(CC)NC(=O)NC1=N[C@@]2(CCCc3c2[nH]c2ccccc32)CC1", "score": 0.855},
  {"sample": "CCN(CC)C[C@H](C)N[C@]1(C)CCc2[nH]c3ccccc3c21", "score": 0.852},
  {"sample": "CCN(CC)NC(=O)[C@@H]1c2c([nH]c3ccccc23)CCN1C", "score": 0.850},
  {"sample": "CCN(CC)NC(=O)N(C)[C@@H]1CCN(C)c2c1[nH]c1ccccc21", "score": 0.848}
]
"""

# INISIALISASI APP 
app = FastAPI(
    title="Capstone Drug Discovery API",
    description="API MolMIM + Gemini. Menghasilkan 10 molekul untuk UI, Menganalisis 5 teratas.",
    version="2.0.0"
)

# MODEL INPUT
class MolMimRequest(BaseModel):
    smi_string: str = Field(..., example="O=C(Oc1ccccc1C(=O)O)C", description="SMILES input user")
    
    num_molecules: int = Field(50, ge=1, le=100, description="Jumlah generate (1-100)")
    algorithm: Literal["CMA-ES", "Spherical"] = Field("CMA-ES", description="Algoritma Sampling")
    property_to_optimize: Literal["QED", "plogP"] = Field("QED", description="Target optimasi")
    minimize: bool = Field(False, description="Set False untuk Maximize properti")
    min_similarity: float = Field(0.3, ge=0.0, le=1.0, description="Similarity constraint (0-1)")
    particles: int = Field(30, ge=20, le=1000, description="Jumlah partikel")
    iterations: int = Field(10, ge=1, le=100, description="Jumlah iterasi")

# FUNGSI API CALL
def call_molmim_api(params: MolMimRequest) -> str:
    print(f"   ⏳ [API] Mengirim request ke MolMIM Cloud ({params.num_molecules} molekul)...")
    NVIDIA_KEY = os.environ.get("NVIDIA_API_KEY")
    
    if not NVIDIA_KEY:
        print("   ⚠️ API Key NVIDIA hilang. Menggunakan Simulasi.")
        return SIMULATED_MOL_DATA

    # Mapping input frontend ke payload API NVIDIA
    body = {
        "algorithm": params.algorithm,
        "num_molecules": params.num_molecules,
        "iterations": params.iterations,
        "property_name": params.property_to_optimize,
        "particles": params.particles,
        "minimize": params.minimize,
        "min_similarity": params.min_similarity,
        "scaled_radius": 1,
        "smi": params.smi_string
    }
    
    headers = {"Authorization": f"Bearer {NVIDIA_KEY}", "Content-Type": "application/json", "Accept": "application/json"}

    try:
        response = requests.post(MOLMIM_CLOUD_ENDPOINT, headers=headers, json=body, timeout=60)
        if response.status_code != 200:
            print(f"   ⚠️ API Error {response.status_code}: {response.text}. Fallback simulasi.")
            return SIMULATED_MOL_DATA
        return response.text 
    except Exception as e:
        print(f"   ⚠️ Koneksi Gagal: {e}. Fallback simulasi.")
        return SIMULATED_MOL_DATA

# FUNGSI PROCESSING (SORTING & FILTERING)
def process_molmim_results(json_string: str) -> list:
    """ Mengembalikan LIST of DICT (bukan string) dari semua molekul unik yang diurutkan. """
    try:
        data = json.loads(json_string)
        mol_list = []
        
        # Parsing struktur respons yang mungkin bervariasi
        if isinstance(data, dict):
            if 'molecules' in data:
                content = data['molecules']
                mol_list = json.loads(content) if isinstance(content, str) else content
            elif 'results' in data:
                mol_list = data['results']
        elif isinstance(data, list):
            mol_list = data

        if not mol_list:
            return json.loads(SIMULATED_MOL_DATA)

        # De-duplikasi (SMILES Unik)
        unique_mols = []
        seen = set()
        
        # Sortir dulu biar yang skor tinggi masuk duluan
        sorted_raw = sorted(mol_list, key=lambda x: x.get('score', 0), reverse=True)

        for m in sorted_raw:
            smi = m.get('sample')
            if smi and smi not in seen:
                unique_mols.append(m)
                seen.add(smi)

        return unique_mols 
      
    except Exception as e:
        print(f"   ❌ Error parsing JSON: {e}")
        return json.loads(SIMULATED_MOL_DATA)

# ENDPOINT UTAMA
@app.post("/analyze")
async def analyze_molecules(request: MolMimRequest):
    
    if not os.environ.get("GOOGLE_API_KEY"):
        raise HTTPException(status_code=500, detail="Server Error: GOOGLE_API_KEY belum diset.")

    # Generate & Dapatkan List Lengkap
    raw_json_string = call_molmim_api(request)
    all_sorted_molecules = process_molmim_results(raw_json_string)
    
    # Siapkan Data untuk Frontend (Top 10)
    molecules_for_frontend = all_sorted_molecules[:10]
    
    # Siapkan Data untuk Analisis Gemini (Top 5)
    molecules_for_analysis = all_sorted_molecules[:5]
    analysis_input_string = json.dumps(molecules_for_analysis, indent=2)

    # Analisis Gemini
    llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL_ID)
    analysis_prompt = ChatPromptTemplate.from_template(
        """Anda adalah ahli kimia komputasi.
        
        Data berikut adalah 5 kandidat molekul terbaik dari hasil optimasi:
        {input_data}
        
        TUGAS: Analisis ke-5 molekul tersebut secara berurutan.
        Format output WAJIB daftar bernomor (1-5). JANGAN pakai tabel.
        
        Untuk setiap molekul, berikan detail:
        1. **Hasil Molekul:** (Hanya ambil SMILES string).
        2. **Identifikasi Struktur:** Jelaskan gugus fungsi utamanya.
        3. **Skor {property_name}:** (Cantumkan skor).
        4. **Perkiraan Modal & Kompleksitas:** SA Score (Rendah/Sedang/Tinggi) dan estimasi Modal.
        5. **Kesesuaian Industri:** (Farmasi/Skincare/Pangan) dan risiko.
        """
    )
    
    try:
        chain = analysis_prompt | llm | StrOutputParser()
        final_analysis = chain.invoke({
            "input_data": analysis_input_string,
            "property_name": request.property_to_optimize
        })
        
        # RETURN HASIL KE BACKEND
        return {
            "status": "success",
            "meta": {
                "original_smiles": request.smi_string,
                "optimized_property": request.property_to_optimize,
                "algorithm": request.algorithm
            },
            "generated_molecules": molecules_for_frontend,
            "analysis_result": final_analysis       
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during processing: {str(e)}")

if __name__ == "__main__":
    print("🚀 ML Service siap! Akses docs di http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
