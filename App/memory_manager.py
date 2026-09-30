"""Estado da memória física e operações básicas de paginação."""

from collections import deque

import config
from models import PageTableEntry, TranslationResult
from policies import PageReplacementPolicy
from tlb import TranslationLookasideBuffer


class MemoryManager:
    """Mantém páginas virtuais, quadros físicos e seus mapeamentos.

    A Etapa 3 carrega páginas somente em quadros livres. O fluxo completo de tradução,
    com TLB e substituição de páginas, será implementado na Etapa 4.
    """

    def __init__(
        self,
        backingStoreBytes: bytes,
        pageReplacementPolicy: PageReplacementPolicy,
        translationLookasideBuffer: TranslationLookasideBuffer,
    ) -> None:
        """Prepara as estruturas usadas para relacionar páginas e quadros.

        backingStoreBytes contém todo o espaço virtual, lido do arquivo binário.
        pageReplacementPolicy escolherá a página a remover quando a RAM estiver cheia.
        translationLookasideBuffer guardará traduções recentes de página para quadro.
        As duas últimas dependências serão usadas no fluxo completo da Etapa 4.
        """

        if len(backingStoreBytes) != config.virtualMemorySizeBytes:
            raise ValueError(
                "O backing store deve ter "
                f"{config.virtualMemorySizeBytes} bytes para a configuração atual."
            )

        # Fonte permanente dos bytes das páginas, mesmo após saírem da memória física.
        self.backingStoreBytes: bytes = backingStoreBytes

        # Regra que escolherá uma página vítima quando não restarem quadros livres.
        self.pageReplacementPolicy: PageReplacementPolicy = (
            pageReplacementPolicy
        )

        # Cache dos mapeamentos página virtual -> quadro físico mais recentes.
        self.translationLookasideBuffer: TranslationLookasideBuffer = (
            translationLookasideBuffer
        )

        # Uma entrada por página virtual; todas começam ausentes da memória física.
        self.pageTableEntryLista: list[PageTableEntry] = self.InitializePageTableEntryLista()

        # Simula os bytes da RAM, divididos em quadros do tamanho de uma página.
        self.physicalMemoryBytes: bytearray = self.InitializePhysicalMemoryBytes()

        # Mantém os números dos quadros disponíveis, começando pelo quadro zero.
        self.freePhysicalFrameQueue: deque[int] = self.InitializeFreePhysicalFrameQueue()

        # Mapa inverso: em cada posição de quadro, guarda a página ocupante ou None.
        self.virtualPageByPhysicalFrameLista: list[int | None] = (
            self.InitializeVirtualPageByPhysicalFrameLista()
        )

    def InitializePageTableEntryLista(self) -> list[PageTableEntry]:
        """Cria uma entrada inicialmente ausente para cada página virtual."""

        pageTableEntryLista: list[PageTableEntry] = []
        for virtualPageNumber in range(config.virtualPageCount):
            pageTableEntry = PageTableEntry()
            pageTableEntryLista.append(pageTableEntry)
        return pageTableEntryLista

    def InitializePhysicalMemoryBytes(self) -> bytearray:
        """Reserva a RAM simulada; cada quadro começa preenchido com zeros."""

        physicalMemoryBytes = bytearray(config.physicalMemorySizeBytes)
        return physicalMemoryBytes

    def InitializeFreePhysicalFrameQueue(self) -> deque[int]:
        """Ordena os quadros livres para que sejam ocupados do zero em diante."""

        freePhysicalFrameQueue: deque[int] = deque()
        for physicalFrameNumber in range(config.physicalFrameCount):
            freePhysicalFrameQueue.append(physicalFrameNumber)
        return freePhysicalFrameQueue

    def InitializeVirtualPageByPhysicalFrameLista(self) -> list[int | None]:
        """Marca cada quadro como vazio no mapa inverso quadro-página."""

        virtualPageByPhysicalFrameLista: list[int | None] = []
        for physicalFrameNumber in range(config.physicalFrameCount):
            virtualPageByPhysicalFrameLista.append(None)
        return virtualPageByPhysicalFrameLista

    def DecomposeLogicalAddress(self, logicalAddress: int) -> tuple[int, int]:
        """Separa um endereço lógico em número de página e deslocamento."""

        if logicalAddress < 0 or logicalAddress > config.maximumLogicalAddress:
            raise ValueError(
                f"Endereço lógico {logicalAddress} fora da faixa "
                f"0 a {config.maximumLogicalAddress}."
            )

        virtualPageNumber = logicalAddress // config.pageSizeBytes
        pageOffset = logicalAddress % config.pageSizeBytes
        return virtualPageNumber, pageOffset

    def LoadVirtualPageIntoFreeFrame(self, virtualPageNumber: int) -> int:
        """Copia uma página ausente do backing store para o próximo quadro livre."""

        if virtualPageNumber < 0 or virtualPageNumber >= config.virtualPageCount:
            raise ValueError(f"Página virtual inválida: {virtualPageNumber}.")

        pageTableEntry = self.pageTableEntryLista[virtualPageNumber]
        if pageTableEntry.isLoadedInPhysicalMemory:
            raise ValueError(f"A página virtual {virtualPageNumber} já está carregada.")

        if not self.freePhysicalFrameQueue:
            raise RuntimeError(
                "Não há quadros físicos livres. A substituição de páginas "
                "será implementada na Etapa 4."
            )

        physicalFrameNumber = self.freePhysicalFrameQueue.popleft()
        sourceStart = virtualPageNumber * config.pageSizeBytes
        sourceEnd = sourceStart + config.pageSizeBytes
        destinationStart = physicalFrameNumber * config.pageSizeBytes
        destinationEnd = destinationStart + config.pageSizeBytes

        # O arquivo contém bytes individuais. Copiar a fatia inteira preserva todos os
        # deslocamentos da página, independentemente do padrão de quatro bytes visto no
        # backing store fornecido.
        pageBytes = self.backingStoreBytes[sourceStart:sourceEnd]
        self.physicalMemoryBytes[destinationStart:destinationEnd] = pageBytes

        pageTableEntry.physicalFrameNumber = physicalFrameNumber
        pageTableEntry.isLoadedInPhysicalMemory = True
        self.virtualPageByPhysicalFrameLista[physicalFrameNumber] = (
            virtualPageNumber
        )
        return physicalFrameNumber

    def ComposePhysicalAddress(
        self, physicalFrameNumber: int, pageOffset: int
    ) -> int:
        """Combina um quadro físico e o deslocamento original da página."""

        if physicalFrameNumber < 0 or physicalFrameNumber >= config.physicalFrameCount:
            raise ValueError(f"Quadro físico inválido: {physicalFrameNumber}.")
        if pageOffset < 0 or pageOffset >= config.pageSizeBytes:
            raise ValueError(f"Deslocamento inválido: {pageOffset}.")

        frameStartAddress = physicalFrameNumber * config.pageSizeBytes
        physicalAddress = frameStartAddress + pageOffset
        return physicalAddress

    def ReadByteAtPhysicalAddress(self, physicalAddress: int) -> tuple[int, int]:
        """Lê um byte físico e devolve suas interpretações sem sinal e com sinal."""

        if physicalAddress < 0 or physicalAddress >= config.physicalMemorySizeBytes:
            raise ValueError(f"Endereço físico inválido: {physicalAddress}.")

        unsignedByteValue = self.physicalMemoryBytes[physicalAddress]
        if unsignedByteValue < 128:
            signedByteValue = unsignedByteValue
        else:
            # Um byte com o bit mais alto ligado representa um número negativo na
            # interpretação com sinal, sem alterar o byte armazenado na memória.
            signedByteValue = unsignedByteValue - 256

        return unsignedByteValue, signedByteValue

    def Translate(self, logicalAddress: int) -> TranslationResult:
        """Traduz um endereço lógico e devolve o registro completo da operação."""

        raise NotImplementedError(
            "O fluxo completo de tradução será implementado na Etapa 4."
        )
