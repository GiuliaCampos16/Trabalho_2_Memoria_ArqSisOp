"""Modelos e tipos compartilhados pelo simulador de memória virtual."""

from dataclasses import dataclass
from typing import Literal, TypeAlias


PageReplacementPolicyName: TypeAlias = Literal["fifo", "second_chance"]
TlbReplacementPolicyName: TypeAlias = Literal["fifo"]


# Usamos @dataclass porque estas classes existem principalmente para representar dados
# e estados do simulador. O decorador gera __init__, __repr__ e comparação, evitando o
# código repetitivo de uma classe comum e deixando os campos esperados visíveis. O uso
# de slots=True impede atributos criados por engano e reduz o espaço de cada instância.
@dataclass(slots=True)
class PageTableEntry:
    """Representa o estado de uma página virtual na tabela de páginas."""

    physical_frame_number: int | None = None
    is_loaded_in_physical_memory: bool = False
    reference_bit: bool = False


# frozen=True é adequado porque o resultado representa uma fotografia de uma tradução
# já concluída. Torná-lo imutável impede que a saída deixe de corresponder ao evento que
# efetivamente ocorreu no gerenciador de memória.
@dataclass(slots=True, frozen=True)
class TranslationResult:
    """Reúne os dados e passos produzidos por uma tradução de endereço."""

    logical_address: int
    virtual_page_number: int
    page_offset: int
    physical_frame_number: int
    physical_address: int
    unsigned_byte_value: int
    signed_byte_value: int
    was_tlb_hit: bool
    was_page_fault: bool
    evicted_virtual_page_number: int | None
    translation_steps: tuple[str, ...]


@dataclass(slots=True)
class SimulationStatistics:
    """Mantém os contadores acumulados durante uma execução do simulador."""

    translated_address_count: int = 0
    page_fault_count: int = 0
    tlb_hit_count: int = 0
