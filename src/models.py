# src/models.py
from pydantic import BaseModel
from typing import List

class Receita(BaseModel):
    categoria: str = ''
    origem: str = ''
    receita_prevista_no_ano: float = 0.0
    receita_arrecadada_no_período: float = 0.0
    receita_recolhida_no_período: float = 0.0
    percentual_realizado: float = 0.0
    detalhamento: str = ''
    
class ResponseSite(BaseModel):
    receitas: List[Receita] = []

class ResponseDefault(BaseModel):
    code: int
    message: str
    datetime: str
    results: List[ResponseSite] = []

class ResponseError(BaseModel):
    code: int
    message: str