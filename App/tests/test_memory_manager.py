"""Testes da memória física e da tradução básica da Etapa 3."""

import unittest
from unittest.mock import Mock

from test_support import AddAppDirectoryToImportPath


AddAppDirectoryToImportPath()

import config  # noqa: E402  # App não é um pacote; o caminho é ajustado acima.
from io_utils import ReadBackingStore  # noqa: E402
from memory_manager import MemoryManager  # noqa: E402
from policies import PageReplacementPolicy  # noqa: E402
from tlb import TranslationLookasideBuffer  # noqa: E402


def InitializeExpectedAddressPartsMap() -> dict[int, tuple[int, int]]:
    """Define as fronteiras que comprovam a separação de página e deslocamento."""

    expectedPartsMap: dict[int, tuple[int, int]] = {}
    expectedPartsMap[0] = (0, 0)
    expectedPartsMap[255] = (0, 255)
    expectedPartsMap[256] = (1, 0)
    expectedPartsMap[65_535] = (255, 255)
    return expectedPartsMap


def InitializeExpectedByteValues(
    unsignedByteValue: int, signedByteValue: int
) -> tuple[int, int]:
    """Agrupa as duas interpretações esperadas do mesmo byte."""

    expectedByteValues = (unsignedByteValue, signedByteValue)
    return expectedByteValues


def InitializePhysicalMemoryPrefixLista(physicalMemoryBytes: bytearray) -> list[int]:
    """Copia os oito bytes iniciais para comparar seu conteúdo individualmente."""

    physicalMemoryPrefixLista: list[int] = []
    for physicalAddress in range(8):
        byteValue = physicalMemoryBytes[physicalAddress]
        physicalMemoryPrefixLista.append(byteValue)
    return physicalMemoryPrefixLista


def InitializeExpectedMemoryPrefixLista() -> list[int]:
    """Registra os primeiros bytes do backing store fornecido como referência."""

    expectedMemoryPrefixLista: list[int] = []
    for zeroByteIndex in range(7):
        expectedMemoryPrefixLista.append(0)
    expectedMemoryPrefixLista.append(1)
    return expectedMemoryPrefixLista


class MemoryManagerStageThreeTests(unittest.TestCase):
    """Confere os mapeamentos e a leitura de bytes sem substituição ou TLB."""

    def setUp(self) -> None:
        backingStoreBytes = ReadBackingStore(
            config.backingStoreFilePath,
            config.virtualMemorySizeBytes,
        )
        unusedPolicy = Mock(spec=PageReplacementPolicy)
        unusedTlb = TranslationLookasideBuffer(config.tlbEntryCapacity)
        self.manager = MemoryManager(backingStoreBytes, unusedPolicy, unusedTlb)

    def test_initial_memory_state(self) -> None:
        self.assertEqual(len(self.manager.pageTableEntryLista), 256)
        self.assertEqual(len(self.manager.physicalMemoryBytes), 32_768)
        self.assertEqual(len(self.manager.freePhysicalFrameQueue), 128)
        self.assertTrue(all(page is None for page in self.manager.virtualPageByPhysicalFrameLista))
        self.assertTrue(
            all(
                not entry.isLoadedInPhysicalMemory
                and entry.physicalFrameNumber is None
                for entry in self.manager.pageTableEntryLista
            )
        )

    def test_logical_address_boundaries(self) -> None:
        expectedPartsMap = InitializeExpectedAddressPartsMap()

        for logicalAddress, expected in expectedPartsMap.items():
            with self.subTest(logicalAddress=logicalAddress):
                actualParts = self.manager.DecomposeLogicalAddress(logicalAddress)
                self.assertEqual(actualParts, expected)

    def test_loading_maps_page_to_first_free_frame(self) -> None:
        physicalFrameNumber = self.manager.LoadVirtualPageIntoFreeFrame(71)
        pageTableEntry = self.manager.pageTableEntryLista[71]

        self.assertEqual(physicalFrameNumber, 0)
        self.assertTrue(pageTableEntry.isLoadedInPhysicalMemory)
        self.assertEqual(pageTableEntry.physicalFrameNumber, 0)
        self.assertEqual(self.manager.virtualPageByPhysicalFrameLista[0], 71)
        self.assertEqual(self.manager.freePhysicalFrameQueue[0], 1)

        virtualPageNumber, pageOffset = self.manager.DecomposeLogicalAddress(18_295)
        self.assertEqual(virtualPageNumber, 71)
        physicalAddress = self.manager.ComposePhysicalAddress(
            physicalFrameNumber, pageOffset
        )
        self.assertEqual(physicalAddress, pageOffset)
        self.assertEqual(
            self.manager.ReadByteAtPhysicalAddress(physicalAddress),
            InitializeExpectedByteValues(221, -35),
        )

    def test_page_boundary_reads_individual_bytes(self) -> None:
        firstFrame = self.manager.LoadVirtualPageIntoFreeFrame(0)
        secondFrame = self.manager.LoadVirtualPageIntoFreeFrame(1)

        lastAddressOfFirstPage = self.manager.ComposePhysicalAddress(
            firstFrame, 255
        )
        firstAddressOfSecondPage = self.manager.ComposePhysicalAddress(
            secondFrame, 0
        )

        self.assertEqual(
            self.manager.ReadByteAtPhysicalAddress(lastAddressOfFirstPage),
            InitializeExpectedByteValues(63, 63),
        )
        self.assertEqual(
            self.manager.ReadByteAtPhysicalAddress(firstAddressOfSecondPage),
            InitializeExpectedByteValues(0, 0),
        )
        self.assertEqual(
            InitializePhysicalMemoryPrefixLista(self.manager.physicalMemoryBytes),
            InitializeExpectedMemoryPrefixLista(),
        )

    def test_no_free_frame_has_clear_error_and_keeps_mapping(self) -> None:
        for virtualPageNumber in range(config.physicalFrameCount):
            loadedFrame = self.manager.LoadVirtualPageIntoFreeFrame(
                virtualPageNumber
            )
            self.assertEqual(loadedFrame, virtualPageNumber)

        with self.assertRaisesRegex(RuntimeError, "Não há quadros físicos livres"):
            self.manager.LoadVirtualPageIntoFreeFrame(config.physicalFrameCount)

        self.assertFalse(self.manager.freePhysicalFrameQueue)
        self.assertFalse(
            self.manager.pageTableEntryLista[config.physicalFrameCount]
            .isLoadedInPhysicalMemory
        )
        self.assertEqual(
            self.manager.virtualPageByPhysicalFrameLista[0], 0
        )

    def test_invalid_or_repeated_requests_do_not_change_state(self) -> None:
        with self.assertRaisesRegex(ValueError, "fora da faixa"):
            self.manager.DecomposeLogicalAddress(-1)
        with self.assertRaisesRegex(ValueError, "Página virtual inválida"):
            self.manager.LoadVirtualPageIntoFreeFrame(config.virtualPageCount)

        self.manager.LoadVirtualPageIntoFreeFrame(0)
        with self.assertRaisesRegex(ValueError, "já está carregada"):
            self.manager.LoadVirtualPageIntoFreeFrame(0)

        self.assertEqual(len(self.manager.freePhysicalFrameQueue), 127)


if __name__ == "__main__":
    unittest.main()
