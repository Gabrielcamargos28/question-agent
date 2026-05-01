from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class FileModel(BaseModel):
    id: Optional[int] = 0
    nome: str
    url: str

class Alternative(BaseModel):
    id: Optional[int] = 0
    corpo: str
    correta: bool
    posicao: int
    arquivos: List[FileModel] = []

class Origin(BaseModel):
    id: Optional[int] = 0
    label: Optional[str] = None
    descricao: Optional[str] = None
    valor: Optional[int] = 0
    grupoFluxo: str = "BASE"

class QuestionBase(BaseModel):
    corpo: str
    fonte: Optional[str] = None
    titulo: Optional[str] = None
    alternativas: List[Alternative]
    alternativaCorreta: int
    dificuldade: Optional[str] = "MEDIA"
    aprovada: bool = True
    assuntos: List[int] = []
    assuntosInterdisciplinares: List[int] = []
    area: Optional[int] = None
    disciplinas: List[int] = []
    ano: Optional[int] = None
    origem: Optional[Origin] = Origin(
        id=22,
        label="QUESTION_AGENT",
        descricao="Agente de cadastro de questões antigas",
        valor=0,
        grupoFluxo="PLATAFORMA")
    arquivos: List[FileModel] = []
    introducaoAlternativa: Optional[str] = None
    linguagem: Optional[str] = "PT_BR"

class QuestionCreate(QuestionBase):
    pass

class Status(BaseModel):
    id: Optional[int] = 0
    questaoId: Optional[int] = 0
    questaoTitulo: Optional[str] = None
    classificacaoId: Optional[int] = 0
    classificacaoLabel: Optional[str] = None
    classificacaoDescricao: Optional[str] = None
    grupoFluxo: Optional[str] = None
    atual: bool = True
    dataCriacao: Optional[str] = None

class AreaUpdate(BaseModel):
    id: int
    nome: Optional[str] = None
    descricao: Optional[str] = None
    codigo: Optional[str] = None

class QuestionUpdate(QuestionBase):
    id: int
    status: List[Status] = []
    area: Optional[AreaUpdate] = None
    rascunho: bool = False
    criada: bool = True
