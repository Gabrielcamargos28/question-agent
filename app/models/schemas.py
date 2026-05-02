from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class FileModel(BaseModel):
    id: Optional[int] = Field(0, description="Unique identifier for the file")
    nome: str = Field(..., description="Name of the file")
    url: str = Field(..., description="Public URL or path to the file")

class Alternative(BaseModel):
    id: Optional[int] = Field(0, description="Unique identifier for the alternative")
    corpo: str = Field(..., description="Text content of the alternative")
    correta: bool = Field(..., description="Indicates if this is the correct answer")
    posicao: int = Field(..., description="The order position of the alternative (1, 2, 3...)")
    arquivos: List[FileModel] = Field([], description="List of files/images attached to this alternative")

class Origin(BaseModel):
    id: Optional[int] = Field(0, description="Unique identifier for the origin")
    label: Optional[str] = Field(None, description="Short label for the origin")
    descricao: Optional[str] = Field(None, description="Full description of the source")
    valor: Optional[int] = Field(0, description="Internal value for sorting or categorization")
    grupoFluxo: str = Field("BASE", description="Workflow group classification")

class QuestionBase(BaseModel):
    corpo: str = Field(..., description="Main text of the question")
    fonte: Optional[str] = Field(None, description="Source of the question (e.g., Exam name)")
    titulo: Optional[str] = Field(None, description="Title or short identifier")
    alternativas: List[Alternative] = Field(..., description="List of possible answers")
    alternativaCorreta: int = Field(..., description="Index or ID of the correct alternative")
    dificuldade: Optional[str] = Field("MEDIA", description="Difficulty level (FACIL, MEDIA, DIFICIL)")
    aprovada: bool = Field(True, description="Approval status of the question")
    assuntos: List[int] = Field([], description="List of subject IDs")
    assuntosInterdisciplinares: List[int] = Field([], description="List of interdisciplinary subject IDs")
    area: Optional[int] = Field(None, description="Technical area ID")
    disciplinas: List[int] = Field([], description="List of discipline IDs")
    ano: Optional[int] = Field(None, description="Year the question was created/used")
    origem: Optional[Origin] = Field(Origin(
        id=22,
        label="QUESTION_AGENT",
        descricao="Agente de cadastro de questões antigas",
        valor=0,
        grupoFluxo="PLATAFORMA"), description="Information about the source of the question")
    arquivos: List[FileModel] = Field([], description="List of files/images attached to the main question body")
    introducaoAlternativa: Optional[str] = Field(None, description="Introductory text before alternatives")
    linguagem: Optional[str] = Field("PT_BR", description="Language of the question")

class QuestionCreate(QuestionBase):
    """Schema for creating a new question."""
    pass

class Status(BaseModel):
    id: Optional[int] = Field(0, description="Unique identifier for the status record")
    questaoId: Optional[int] = Field(0, description="Related question ID")
    questaoTitulo: Optional[str] = Field(None, description="Title of the related question")
    classificacaoId: Optional[int] = Field(0, description="Classification ID")
    classificacaoLabel: Optional[str] = Field(None, description="Label for the classification")
    classificacaoDescricao: Optional[str] = Field(None, description="Description for the classification")
    grupoFluxo: Optional[str] = Field(None, description="Workflow group")
    atual: bool = Field(True, description="Whether this is the current status")
    dataCriacao: Optional[str] = Field(None, description="Date the status was recorded")

class AreaUpdate(BaseModel):
    id: int = Field(..., description="Unique identifier for the area")
    nome: Optional[str] = Field(None, description="Name of the area")
    descricao: Optional[str] = Field(None, description="Description of the area")
    codigo: Optional[str] = Field(None, description="Code for the area")

class QuestionUpdate(QuestionBase):
    id: int = Field(..., description="Unique identifier for the question to update")
    status: List[Status] = Field([], description="Current status history")
    area: Optional[AreaUpdate] = Field(None, description="Updated area information")
    rascunho: bool = Field(False, description="Whether the question is a draft")
    criada: bool = Field(True, description="Whether the question has been successfully created")

class ExtractionResponse(BaseModel):
    """Schema for the extraction result response."""
    total_extracted: int = Field(..., description="Total number of questions successfully extracted")
    questions: List[QuestionBase] = Field(..., description="List of extracted questions with their details")
    api_registration_success: bool = Field(..., description="Indicates if all questions were successfully registered in the target API")
    registration_details: List[bool] = Field(..., description="Individual success status for each question registration")
