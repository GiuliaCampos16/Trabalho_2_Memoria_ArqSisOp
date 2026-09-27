"""Contratos das políticas de substituição de páginas.

As implementações concretas serão adicionadas nas Etapas 5 e 6: FIFO na Etapa 5 e
Segunda Chance na Etapa 6.
"""

from collections.abc import Sequence
from typing import Protocol

from models import PageTableEntry


class PageReplacementPolicy(Protocol):
    """Define as operações comuns a qualquer política de substituição.

    Protocol é usado para manter MemoryManager independente de FIFO e Segunda Chance,
    preservando a verificação dos type hints. Ele aplica tipagem estrutural: uma classe
    será compatível quando implementar estes métodos com as assinaturas esperadas, sem
    precisar herdar explicitamente de PageReplacementPolicy.

    Sem este contrato, o gerenciador teria que depender das classes concretas, usar uma
    união de todas as políticas ou aceitar Any e perder segurança de tipos. As classes
    concretas que atenderão ao protocolo serão implementadas nas Etapas 5 e 6.
    """

    def on_page_loaded(self, loaded_virtual_page_number: int) -> None:
        """Registra que uma página virtual acabou de ocupar um quadro físico."""

        ...

    def on_page_accessed(self, accessed_virtual_page_number: int) -> None:
        """Registra uma referência a uma página que está na memória física."""

        ...

    def select_victim(
        self, page_table_entries: Sequence[PageTableEntry]
    ) -> int:
        """Seleciona e devolve o número da página virtual que deve sair."""

        ...
