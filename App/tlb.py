"""Contrato da Translation Look-aside Buffer (TLB)."""


class TranslationLookasideBuffer:
    """Define a interface da cache de traduções página-quadro.

    O armazenamento e a política FIFO serão implementados na Etapa 7.
    """

    def __init__(self, entryCapacity: int) -> None:
        self.entryCapacity: int = entryCapacity

    def Lookup(self, virtualPageNumber: int) -> int | None:
        """Busca o quadro de uma página ou devolve None em caso de TLB miss."""

        raise NotImplementedError("A TLB será implementada na Etapa 7.")

    def Insert(
        self, virtualPageNumber: int, physicalFrameNumber: int
    ) -> None:
        """Insere ou atualiza uma tradução de página virtual para quadro físico."""

        raise NotImplementedError("A TLB será implementada na Etapa 7.")

    def Invalidate(self, virtualPageNumber: int) -> None:
        """Remove uma tradução que não é mais válida."""

        raise NotImplementedError("A TLB será implementada na Etapa 7.")

    def Clear(self) -> None:
        """Remove todas as traduções armazenadas."""

        raise NotImplementedError("A TLB será implementada na Etapa 7.")
