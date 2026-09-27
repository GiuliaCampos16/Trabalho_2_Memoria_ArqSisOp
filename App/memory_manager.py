"""Contrato do componente central de gerenciamento de memória virtual."""

from models import TranslationResult
from policies import PageReplacementPolicy
from tlb import TranslationLookasideBuffer


class MemoryManager:
    """Coordena a tradução de endereços e a paginação por demanda.

    O estado da tabela de páginas e da memória física será implementado nas Etapas 3 e
    4. Neste momento, a classe congela apenas as dependências e a assinatura pública.
    """

    def __init__(
        self,
        backing_store_bytes: bytes,
        page_replacement_policy: PageReplacementPolicy,
        translation_lookaside_buffer: TranslationLookasideBuffer,
    ) -> None:
        self._backing_store_bytes: bytes = backing_store_bytes
        self._page_replacement_policy: PageReplacementPolicy = (
            page_replacement_policy
        )
        self._translation_lookaside_buffer: TranslationLookasideBuffer = (
            translation_lookaside_buffer
        )

    def translate(self, logical_address: int) -> TranslationResult:
        """Traduz um endereço lógico e devolve o registro completo da operação."""

        raise NotImplementedError(
            "A tradução de endereços será implementada nas Etapas 3 e 4."
        )
