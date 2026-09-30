"""Estado da memória física e fluxo de tradução por paginação sob demanda."""

from collections import deque

import config
from models import PageTableEntry, SimulationStatistics, TranslationResult
from policies import PageReplacementPolicy
from tlb import TranslationLookasideBuffer


class MemoryManager:
    """Mantém páginas virtuais, quadros físicos e seus mapeamentos."""

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
        As duas últimas dependências são consultadas durante cada tradução.
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

        # Contadores da execução; taxas e apresentação serão feitas na Etapa 7.
        self.simulationStatistics: SimulationStatistics = (
            self.InitializeSimulationStatistics()
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

    def InitializeSimulationStatistics(self) -> SimulationStatistics:
        """Cria contadores zerados para a execução deste gerenciador."""

        simulationStatistics = SimulationStatistics()
        return simulationStatistics

    def InitializeTranslationStepsLista(self) -> list[str]:
        """Prepara o registro ordenado dos eventos de uma tradução."""

        translationStepsLista: list[str] = []
        return translationStepsLista

    def InitializeTranslationSteps(self, translationStepsLista: list[str]) -> tuple[str, ...]:
        """Congela os passos para que o resultado não mude depois da tradução."""

        translationSteps = tuple(translationStepsLista)
        return translationSteps

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
                "Não há quadros físicos livres para este carregamento direto. "
                "Use Translate para aplicar a política de substituição."
            )

        physicalFrameNumber = self.freePhysicalFrameQueue.popleft()
        self.LoadVirtualPageIntoFrame(virtualPageNumber, physicalFrameNumber)
        return physicalFrameNumber

    def LoadVirtualPageIntoFrame(
        self, virtualPageNumber: int, physicalFrameNumber: int
    ) -> None:
        """Copia uma página ausente para um quadro vazio e registra o mapeamento."""

        if virtualPageNumber < 0 or virtualPageNumber >= config.virtualPageCount:
            raise ValueError(f"Página virtual inválida: {virtualPageNumber}.")
        if physicalFrameNumber < 0 or physicalFrameNumber >= config.physicalFrameCount:
            raise ValueError(f"Quadro físico inválido: {physicalFrameNumber}.")

        pageTableEntry = self.pageTableEntryLista[virtualPageNumber]
        if pageTableEntry.isLoadedInPhysicalMemory:
            raise ValueError(f"A página virtual {virtualPageNumber} já está carregada.")
        if self.virtualPageByPhysicalFrameLista[physicalFrameNumber] is not None:
            raise RuntimeError(f"O quadro físico {physicalFrameNumber} já está ocupado.")

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

    def ReplaceVirtualPage(self, requestedVirtualPageNumber: int) -> tuple[int, int]:
        """Escolhe uma vítima e reutiliza seu quadro para a página solicitada."""

        victimVirtualPageNumber = self.pageReplacementPolicy.SelectVictim(
            self.pageTableEntryLista
        )
        if type(victimVirtualPageNumber) is not int:
            raise RuntimeError("A política retornou uma página vítima inválida.")
        if victimVirtualPageNumber < 0 or victimVirtualPageNumber >= config.virtualPageCount:
            raise RuntimeError("A política retornou uma página vítima fora da tabela.")

        victimPageTableEntry = self.pageTableEntryLista[victimVirtualPageNumber]
        physicalFrameNumber = victimPageTableEntry.physicalFrameNumber
        if not victimPageTableEntry.isLoadedInPhysicalMemory or physicalFrameNumber is None:
            raise RuntimeError("A política escolheu uma página que não está na memória física.")
        if physicalFrameNumber < 0 or physicalFrameNumber >= config.physicalFrameCount:
            raise RuntimeError("A página vítima aponta para um quadro físico inválido.")
        if self.virtualPageByPhysicalFrameLista[physicalFrameNumber] != victimVirtualPageNumber:
            raise RuntimeError("O mapa inverso não corresponde à página vítima escolhida.")

        # O quadro só pode receber novos bytes depois que ambos os registros antigos
        # deixarem de apontar para ele; a TLB jamais pode conservar a tradução vítima.
        victimPageTableEntry.isLoadedInPhysicalMemory = False
        victimPageTableEntry.physicalFrameNumber = None
        victimPageTableEntry.referenceBit = False
        self.virtualPageByPhysicalFrameLista[physicalFrameNumber] = None
        self.translationLookasideBuffer.Invalidate(victimVirtualPageNumber)

        self.LoadVirtualPageIntoFrame(requestedVirtualPageNumber, physicalFrameNumber)
        return victimVirtualPageNumber, physicalFrameNumber

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

        virtualPageNumber, pageOffset = self.DecomposeLogicalAddress(logicalAddress)
        translationStepsLista = self.InitializeTranslationStepsLista()
        translationStepsLista.append(
            f"Endereço lógico {logicalAddress}: página {virtualPageNumber}, "
            f"deslocamento {pageOffset}."
        )

        wasTlbHit = False
        wasPageFault = False
        evictedVirtualPageNumber: int | None = None
        cachedPhysicalFrameNumber = self.translationLookasideBuffer.Lookup(
            virtualPageNumber
        )

        if cachedPhysicalFrameNumber is not None:
            wasTlbHit = True
            physicalFrameNumber = cachedPhysicalFrameNumber
            translationStepsLista.append(
                f"TLB hit: página {virtualPageNumber} -> quadro {physicalFrameNumber}."
            )
        else:
            translationStepsLista.append(f"TLB miss: página {virtualPageNumber}.")
            pageTableEntry = self.pageTableEntryLista[virtualPageNumber]

            if pageTableEntry.isLoadedInPhysicalMemory:
                loadedPhysicalFrameNumber = pageTableEntry.physicalFrameNumber
                if loadedPhysicalFrameNumber is None:
                    raise RuntimeError("Página presente sem número de quadro físico.")
                physicalFrameNumber = loadedPhysicalFrameNumber
                translationStepsLista.append(
                    f"Tabela de páginas: página {virtualPageNumber} presente "
                    f"no quadro {physicalFrameNumber}."
                )
            else:
                wasPageFault = True
                translationStepsLista.append(
                    f"Falha de página: página {virtualPageNumber} ausente."
                )

                if self.freePhysicalFrameQueue:
                    physicalFrameNumber = self.LoadVirtualPageIntoFreeFrame(
                        virtualPageNumber
                    )
                    translationStepsLista.append(
                        f"Quadro livre {physicalFrameNumber} selecionado."
                    )
                else:
                    evictedVirtualPageNumber, physicalFrameNumber = (
                        self.ReplaceVirtualPage(virtualPageNumber)
                    )
                    translationStepsLista.append(
                        f"Página vítima {evictedVirtualPageNumber} removida; "
                        f"quadro {physicalFrameNumber} reutilizado."
                    )

                translationStepsLista.append(
                    f"Página {virtualPageNumber} carregada do backing store."
                )
                self.pageReplacementPolicy.OnPageLoaded(virtualPageNumber)

            self.translationLookasideBuffer.Insert(
                virtualPageNumber, physicalFrameNumber
            )
            translationStepsLista.append(
                f"TLB atualizada: página {virtualPageNumber} -> quadro "
                f"{physicalFrameNumber}."
            )

        pageTableEntry = self.pageTableEntryLista[virtualPageNumber]
        pageTableEntry.referenceBit = True
        self.pageReplacementPolicy.OnPageAccessed(virtualPageNumber)

        physicalAddress = self.ComposePhysicalAddress(physicalFrameNumber, pageOffset)
        unsignedByteValue, signedByteValue = self.ReadByteAtPhysicalAddress(
            physicalAddress
        )
        translationStepsLista.append(
            f"Endereço físico {physicalAddress}: byte sem sinal {unsignedByteValue}, "
            f"com sinal {signedByteValue}."
        )

        translationSteps = self.InitializeTranslationSteps(translationStepsLista)
        translationResult = TranslationResult(
            logicalAddress=logicalAddress,
            virtualPageNumber=virtualPageNumber,
            pageOffset=pageOffset,
            physicalFrameNumber=physicalFrameNumber,
            physicalAddress=physicalAddress,
            unsignedByteValue=unsignedByteValue,
            signedByteValue=signedByteValue,
            wasTlbHit=wasTlbHit,
            wasPageFault=wasPageFault,
            evictedVirtualPageNumber=evictedVirtualPageNumber,
            translationSteps=translationSteps,
        )

        # A página pode ter exigido carregamento, mas esta continua sendo uma única
        # referência lógica: contar somente depois de concluir toda a tradução.
        self.simulationStatistics.translatedAddressCount += 1
        if wasPageFault:
            self.simulationStatistics.pageFaultCount += 1
        if wasTlbHit:
            self.simulationStatistics.tlbHitCount += 1

        return translationResult
