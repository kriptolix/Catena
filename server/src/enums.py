# enums.py
import enum

class EstadoEquipamento(str, enum.Enum):
    FUNCIONAL = "funcional"
    DEFEITUOSO = "defeituoso"
    DEVOLVIDO = "devolvido"

class TipoHistorico(str, enum.Enum):
    CADASTRO = "cadastro"
    ALTERACAO_HARDWARE = "alteracao_hardware"
    MUDANCA_LOCALIZACAO = "mudanca_localizacao"
    MUDANCA_ESTADO = "mudanca_estado"
    ALTERACAO_GARANTIA = "alteracao_garantia"
    ALTERACAO_PATRIMONIAL = "alteracao_patrimonial"

class TipoValorControlado(str, enum.Enum):
    FABRICANTE = "fabricante"
    MODELO = "modelo"
    TIPO_MEMORIA = "tipo_memoria"
    FABRICANTE_DISCO = "fabricante_disco"