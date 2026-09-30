"""Testes do fluxo de tradução da Etapa 4 com dependências de teste."""

import unittest
from collections.abc import Sequence

from test_support import AddAppDirectoryToImportPath


AddAppDirectoryToImportPath()

import config  # noqa: E402  # App usa imports locais simples.
from io_utils import ReadBackingStore  # noqa: E402
from memory_manager import MemoryManager  # noqa: E402
from models import PageTableEntry  # noqa: E402
from policies import PageReplacementPolicy  # noqa: E402
from tlb import TranslationLookasideBuffer  # noqa: E402


def InitializePageEventLista() -> list[int]:
    """Cria um registro vazio de páginas observadas pelas dependências de teste."""

    pageEventLista: list[int] = []
    return pageEventLista


def InitializeExpectedPageEventLista(*virtualPageNumbers: int) -> list[int]:
    """Monta a ordem esperada de páginas nos registros dos testes."""

    expectedPageEventLista: list[int] = []
    for virtualPageNumber in virtualPageNumbers:
        expectedPageEventLista.append(virtualPageNumber)
    return expectedPageEventLista


def InitializePageToFrameMap() -> dict[int, int]:
    """Cria o mapa simples usado somente para simular consultas à TLB."""

    pageToFrameMap: dict[int, int] = {}
    return pageToFrameMap


class FakePageReplacementPolicy(PageReplacementPolicy):
    """Registra chamadas e devolve uma vítima definida pelo teste."""

    def __init__(self) -> None:
        self.loadedPageLista: list[int] = InitializePageEventLista()
        self.accessedPageLista: list[int] = InitializePageEventLista()
        self.selectedVictimVirtualPageNumber: int = 0
        self.selectVictimCallCount: int = 0

    def OnPageLoaded(self, loadedVirtualPageNumber: int) -> None:
        self.loadedPageLista.append(loadedVirtualPageNumber)

    def OnPageAccessed(self, accessedVirtualPageNumber: int) -> None:
        self.accessedPageLista.append(accessedVirtualPageNumber)

    def SelectVictim(self, pageTableEntryLista: Sequence[PageTableEntry]) -> int:
        self.selectVictimCallCount += 1
        return self.selectedVictimVirtualPageNumber


class FakeTranslationLookasideBuffer(TranslationLookasideBuffer):
    """Mantém mapeamentos sem política de capacidade para isolar o gerenciador."""

    def __init__(self) -> None:
        super().__init__(config.tlbEntryCapacity)
        self.pageToFrameMap: dict[int, int] = InitializePageToFrameMap()
        self.invalidatedPageLista: list[int] = InitializePageEventLista()
        self.lookupPageLista: list[int] = InitializePageEventLista()

    def Lookup(self, virtualPageNumber: int) -> int | None:
        self.lookupPageLista.append(virtualPageNumber)
        return self.pageToFrameMap.get(virtualPageNumber)

    def Insert(self, virtualPageNumber: int, physicalFrameNumber: int) -> None:
        self.pageToFrameMap[virtualPageNumber] = physicalFrameNumber

    def Invalidate(self, virtualPageNumber: int) -> None:
        self.invalidatedPageLista.append(virtualPageNumber)
        self.pageToFrameMap.pop(virtualPageNumber, None)

    def Clear(self) -> None:
        self.pageToFrameMap.clear()


class MemoryManagerTranslationTests(unittest.TestCase):
    """Confere os caminhos de hit, falha e substituição sem implementações futuras."""

    def setUp(self) -> None:
        backingStoreBytes = ReadBackingStore(
            config.backingStoreFilePath,
            config.virtualMemorySizeBytes,
        )
        self.pageReplacementPolicy = FakePageReplacementPolicy()
        self.translationLookasideBuffer = FakeTranslationLookasideBuffer()
        self.manager = MemoryManager(
            backingStoreBytes,
            self.pageReplacementPolicy,
            self.translationLookasideBuffer,
        )

    def test_first_access_faults_and_second_access_hits_tlb(self) -> None:
        firstResult = self.manager.Translate(0)
        self.assertTrue(firstResult.wasPageFault)
        self.assertFalse(firstResult.wasTlbHit)
        self.assertEqual(firstResult.physicalFrameNumber, 0)
        self.assertEqual(firstResult.physicalAddress, 0)
        self.assertIsNone(firstResult.evictedVirtualPageNumber)
        self.assertTrue(any("Falha de página" in step for step in firstResult.translationSteps))
        self.assertTrue(any("Quadro livre" in step for step in firstResult.translationSteps))

        self.manager.pageTableEntryLista[0].referenceBit = False
        secondResult = self.manager.Translate(255)
        self.assertFalse(secondResult.wasPageFault)
        self.assertTrue(secondResult.wasTlbHit)
        self.assertEqual(secondResult.physicalAddress, 255)
        self.assertEqual(secondResult.unsignedByteValue, 63)
        self.assertEqual(secondResult.signedByteValue, 63)
        self.assertTrue(self.manager.pageTableEntryLista[0].referenceBit)
        self.assertTrue(any("TLB hit" in step for step in secondResult.translationSteps))

        self.assertEqual(
            self.pageReplacementPolicy.loadedPageLista,
            InitializeExpectedPageEventLista(0),
        )
        self.assertEqual(
            self.pageReplacementPolicy.accessedPageLista,
            InitializeExpectedPageEventLista(0, 0),
        )
        self.assertEqual(self.manager.simulationStatistics.translatedAddressCount, 2)
        self.assertEqual(self.manager.simulationStatistics.pageFaultCount, 1)
        self.assertEqual(self.manager.simulationStatistics.tlbHitCount, 1)

    def test_tlb_miss_can_find_page_already_in_physical_memory(self) -> None:
        self.manager.Translate(256)
        self.translationLookasideBuffer.Invalidate(1)

        result = self.manager.Translate(257)

        self.assertFalse(result.wasTlbHit)
        self.assertFalse(result.wasPageFault)
        self.assertEqual(result.physicalFrameNumber, 0)
        self.assertEqual(self.translationLookasideBuffer.pageToFrameMap[1], 0)
        self.assertEqual(
            self.pageReplacementPolicy.loadedPageLista,
            InitializeExpectedPageEventLista(1),
        )
        self.assertEqual(self.manager.simulationStatistics.translatedAddressCount, 2)
        self.assertEqual(self.manager.simulationStatistics.pageFaultCount, 1)
        self.assertEqual(self.manager.simulationStatistics.tlbHitCount, 0)

    def test_translation_reads_individual_signed_byte(self) -> None:
        result = self.manager.Translate(18_295)

        self.assertEqual(result.virtualPageNumber, 71)
        self.assertEqual(result.pageOffset, 119)
        self.assertEqual(result.unsignedByteValue, 221)
        self.assertEqual(result.signedByteValue, -35)

    def test_full_memory_replaces_page_and_invalidates_old_translation(self) -> None:
        for virtualPageNumber in range(config.physicalFrameCount):
            logicalAddress = virtualPageNumber * config.pageSizeBytes
            result = self.manager.Translate(logicalAddress)
            self.assertEqual(result.physicalFrameNumber, virtualPageNumber)

        self.assertEqual(self.pageReplacementPolicy.selectVictimCallCount, 0)
        replacementAddress = config.physicalFrameCount * config.pageSizeBytes
        result = self.manager.Translate(replacementAddress)

        self.assertTrue(result.wasPageFault)
        self.assertEqual(result.evictedVirtualPageNumber, 0)
        self.assertEqual(result.physicalFrameNumber, 0)
        expectedUnsignedByteValue = self.manager.backingStoreBytes[replacementAddress]
        self.assertEqual(result.unsignedByteValue, expectedUnsignedByteValue)
        self.assertEqual(self.pageReplacementPolicy.selectVictimCallCount, 1)
        self.assertEqual(
            self.translationLookasideBuffer.invalidatedPageLista,
            InitializeExpectedPageEventLista(0),
        )
        self.assertEqual(self.pageReplacementPolicy.loadedPageLista[-1], 128)
        self.assertEqual(self.pageReplacementPolicy.accessedPageLista[-1], 128)
        self.assertNotIn(0, self.translationLookasideBuffer.pageToFrameMap)
        self.assertIsNone(self.manager.pageTableEntryLista[0].physicalFrameNumber)
        self.assertFalse(self.manager.pageTableEntryLista[0].isLoadedInPhysicalMemory)
        self.assertFalse(self.manager.pageTableEntryLista[0].referenceBit)
        self.assertEqual(self.manager.virtualPageByPhysicalFrameLista[0], 128)
        self.assertEqual(self.manager.simulationStatistics.translatedAddressCount, 129)
        self.assertEqual(self.manager.simulationStatistics.pageFaultCount, 129)

        occupiedFrameLista = InitializePageEventLista()
        seenFrameLista = InitializePageEventLista()
        for pageTableEntry in self.manager.pageTableEntryLista:
            if pageTableEntry.isLoadedInPhysicalMemory:
                physicalFrameNumber = pageTableEntry.physicalFrameNumber
                if physicalFrameNumber is None:
                    self.fail("Página presente sem número de quadro físico.")
                self.assertNotIn(physicalFrameNumber, seenFrameLista)
                seenFrameLista.append(physicalFrameNumber)
                occupiedFrameLista.append(physicalFrameNumber)
        self.assertEqual(len(occupiedFrameLista), config.physicalFrameCount)

    def test_invalid_address_does_not_change_state(self) -> None:
        with self.assertRaisesRegex(ValueError, "fora da faixa"):
            self.manager.Translate(-1)
        with self.assertRaisesRegex(ValueError, "fora da faixa"):
            self.manager.Translate(config.maximumLogicalAddress + 1)

        self.assertEqual(self.manager.simulationStatistics.translatedAddressCount, 0)
        self.assertEqual(self.manager.simulationStatistics.pageFaultCount, 0)
        self.assertEqual(self.manager.simulationStatistics.tlbHitCount, 0)
        self.assertEqual(
            self.translationLookasideBuffer.lookupPageLista,
            InitializePageEventLista(),
        )
        self.assertEqual(len(self.manager.freePhysicalFrameQueue), config.physicalFrameCount)

    def test_invalid_policy_victim_keeps_memory_mapping_intact(self) -> None:
        for virtualPageNumber in range(config.physicalFrameCount):
            logicalAddress = virtualPageNumber * config.pageSizeBytes
            self.manager.Translate(logicalAddress)

        self.pageReplacementPolicy.selectedVictimVirtualPageNumber = 128
        replacementAddress = config.physicalFrameCount * config.pageSizeBytes
        with self.assertRaisesRegex(RuntimeError, "não está na memória física"):
            self.manager.Translate(replacementAddress)

        self.assertEqual(self.manager.simulationStatistics.translatedAddressCount, 128)
        self.assertEqual(self.manager.simulationStatistics.pageFaultCount, 128)
        self.assertEqual(self.manager.virtualPageByPhysicalFrameLista[0], 0)
        self.assertTrue(self.manager.pageTableEntryLista[0].isLoadedInPhysicalMemory)
        self.assertNotIn(128, self.translationLookasideBuffer.pageToFrameMap)


if __name__ == "__main__":
    unittest.main()
