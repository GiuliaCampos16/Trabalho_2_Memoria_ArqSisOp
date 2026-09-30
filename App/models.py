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

    physicalFrameNumber: int | None = None
    isLoadedInPhysicalMemory: bool = False
    referenceBit: bool = False


# frozen=True é adequado porque o resultado representa uma fotografia de uma tradução
# já concluída. Torná-lo imutável impede que a saída deixe de corresponder ao evento que
# efetivamente ocorreu no gerenciador de memória.
@dataclass(slots=True, frozen=True)
class TranslationResult:
    """Reúne os dados e passos produzidos por uma tradução de endereço."""

    logicalAddress: int
    virtualPageNumber: int
    pageOffset: int
    physicalFrameNumber: int
    physicalAddress: int
    unsignedByteValue: int
    signedByteValue: int
    wasTlbHit: bool
    wasPageFault: bool
    evictedVirtualPageNumber: int | None
    translationSteps: tuple[str, ...]


@dataclass(slots=True)
class SimulationStatistics:
    """Mantém os contadores acumulados durante uma execução do simulador."""

    translatedAddressCount: int = 0
    pageFaultCount: int = 0
    tlbHitCount: int = 0
