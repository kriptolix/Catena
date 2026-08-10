from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from enums import EstadoEquipamento, TipoHistorico, TipoValorControlado

# Schemas para ValorControlado
class ValorControladoBase(BaseModel):
    tipo: TipoValorControlado
    valor: str

class ValorControladoCreate(ValorControladoBase):
    pass

class ValorControlado(ValorControladoBase):
    id: int
    criado_por_admin: bool

    model_config = ConfigDict(from_attributes=True)

# Schemas para Equipamento
class EquipamentoBase(BaseModel):
    tombo: Optional[str] = None  # Se não fornecido, gerado automaticamente
    uuid: Optional[str] = None
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    localizacao: str  # obrigatório
    estado: EstadoEquipamento = EstadoEquipamento.FUNCIONAL
    inicio_garantia: Optional[datetime] = None
    duracao_garantia: Optional[int] = None

class EquipamentoCreate(EquipamentoBase):
    pass

class EquipamentoUpdate(BaseModel):
    uuid: Optional[str] = None
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    localizacao: Optional[str] = None
    estado: Optional[EstadoEquipamento] = None
    inicio_garantia: Optional[datetime] = None
    duracao_garantia: Optional[int] = None

class Equipamento(EquipamentoBase):
    id: int
    criado_em: datetime
    atualizado_em: Optional[datetime]
    fabricante: Optional[ValorControlado] = None
    modelo: Optional[ValorControlado] = None

    model_config = ConfigDict(from_attributes=True)

# Schemas para Defeito
class DefeitoBase(BaseModel):
    componente: str
    descricao: Optional[str] = None
    resolvido: bool = False

class DefeitoCreate(DefeitoBase):
    equipamento_id: int

class Defeito(DefeitoBase):
    id: int
    equipamento_id: int
    data: datetime

    model_config = ConfigDict(from_attributes=True)

# Schemas para InventarioHardware
class InventarioHardwareBase(BaseModel):
    cpu: Optional[str] = None
    memoria: Optional[str] = None
    armazenamento: Optional[str] = None
    gpu: Optional[str] = None
    placa_mae: Optional[str] = None
    bios: Optional[str] = None
    sistema_operacional: Optional[str] = None
    json_original: Optional[Dict[str, Any]] = None

class InventarioHardwareCreate(InventarioHardwareBase):
    equipamento_id: int

class InventarioHardware(InventarioHardwareBase):
    id: int
    equipamento_id: int
    data_coleta: datetime

    model_config = ConfigDict(from_attributes=True)

# Schemas para Historico
class HistoricoBase(BaseModel):
    tipo: TipoHistorico
    valor_anterior: Optional[str] = None
    valor_novo: Optional[str] = None

class HistoricoCreate(HistoricoBase):
    equipamento_id: int
    usuario: str

class Historico(HistoricoBase):
    id: int
    equipamento_id: int
    usuario: str
    data: datetime

    model_config = ConfigDict(from_attributes=True)

# Schemas para Anotacao
class AnotacaoBase(BaseModel):
    texto: str

class AnotacaoCreate(AnotacaoBase):
    equipamento_id: int
    usuario: str

class Anotacao(AnotacaoBase):
    id: int
    equipamento_id: int
    usuario: str
    data: datetime

    model_config = ConfigDict(from_attributes=True)

# Schemas para Usuario
class UsuarioBase(BaseModel):
    fullname: str
    username: str

class UsuarioCreate(UsuarioBase):
    password: str
    is_admin: bool = False

class UsuarioUpdate(BaseModel):
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    ativo: Optional[bool] = None

class Usuario(UsuarioBase):
    id: int
    is_admin: bool
    ativo: bool
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)

# Schemas para Autenticação
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# Schemas para recebimento de inventário (POST /api/v1/inventario)
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class Identificacao(BaseModel):
    uuid: Optional[str] = None


class EquipamentoInventario(BaseModel):
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    numeroSerie: Optional[str] = None


class BiosInventario(BaseModel):
    fabricante: Optional[str] = None
    versao: Optional[str] = None
    data: Optional[str] = None


class PlacaMaeInventario(BaseModel):
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    numeroSerie: Optional[str] = None


class SistemaInventario(BaseModel):
    nome: Optional[str] = None
    versao: Optional[str] = None
    arquitetura: Optional[str] = None


class ProcessadorInventario(BaseModel):
    modelo: Optional[str] = None
    fabricante: Optional[str] = None
    nucleos: Optional[int] = None
    threads: Optional[int] = None
    clockMaximoMHz: Optional[int] = None


class ModuloMemoria(BaseModel):
    fabricante: Optional[str] = None
    capacidadeGB: Optional[float] = None
    velocidadeMHz: Optional[int] = None
    tipo: Optional[str] = None
    partNumber: Optional[str] = None
    numeroSerie: Optional[str] = None
    slot: Optional[str] = None


class MemoriaInventario(BaseModel):
    totalGB: Optional[float] = None
    modulos: List[ModuloMemoria] = []


class DiscoInventario(BaseModel):
    modelo: Optional[str] = None
    fabricante: Optional[str] = None
    interface: Optional[str] = None
    tamanhoGB: Optional[float] = None
    serial: Optional[str] = None
    tipo: Optional[str] = None


class VideoInventario(BaseModel):
    modelo: Optional[str] = None
    memoriaGB: Optional[float] = None


class RedeInventario(BaseModel):
    modelo: Optional[str] = None
    mac: Optional[str] = None
    velocidadeMbps: Optional[int] = None

class InventarioRecebido(BaseModel):
    identificacao: Optional[Identificacao] = None
    equipamento: Optional[EquipamentoInventario] = None
    bios: Optional[BiosInventario] = None
    placaMae: Optional[PlacaMaeInventario] = None
    sistema: Optional[SistemaInventario] = None
    processador: Optional[ProcessadorInventario] = None
    memoria: Optional[MemoriaInventario] = None
    discos: List[DiscoInventario] = []
    video: List[VideoInventario] = []
    rede: List[RedeInventario] = []

    tombo: Optional[str] = None
    localizacao: Optional[str] = None
    observacoes: Optional[str] = None
    dataInventario: Optional[str] = None
