"""Contrato da Translation Look-aside Buffer (TLB)."""


class TranslationLookasideBuffer:
    """Define a interface da cache de traduções página-quadro.

    O armazenamento e a política FIFO serão implementados na Etapa 7.
    """

    def __init__(self, entry_capacity: int) -> None:
        self._entry_capacity: int = entry_capacity

    def lookup(self, virtual_page_number: int) -> int | None:
        """Busca o quadro de uma página ou devolve None em caso de TLB miss."""

        raise NotImplementedError("A TLB será implementada na Etapa 7.")

    def insert(
        self, virtual_page_number: int, physical_frame_number: int
    ) -> None:
        """Insere ou atualiza uma tradução de página virtual para quadro físico."""

        raise NotImplementedError("A TLB será implementada na Etapa 7.")

    def invalidate(self, virtual_page_number: int) -> None:
        """Remove uma tradução que não é mais válida."""

        raise NotImplementedError("A TLB será implementada na Etapa 7.")

    def clear(self) -> None:
        """Remove todas as traduções armazenadas."""

        raise NotImplementedError("A TLB será implementada na Etapa 7.")
