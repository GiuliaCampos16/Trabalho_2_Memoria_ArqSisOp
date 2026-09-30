"""Testes das dataclasses compartilhadas criadas na Etapa 1."""

import unittest
from dataclasses import FrozenInstanceError

from test_support import AddAppDirectoryToImportPath


AddAppDirectoryToImportPath()

from models import (  # noqa: E402  # Depende do caminho configurado acima.
    PageTableEntry,
    SimulationStatistics,
    TranslationResult,
)


def InitializeTranslationSteps() -> tuple[str, ...]:
    """Prepara os eventos fixos usados para testar a imutabilidade do resultado."""

    translationStepsLista: list[str] = []
    translationStepsLista.append("Falha de página")
    translationStepsLista.append("Página carregada")
    translationSteps = tuple(translationStepsLista)
    return translationSteps


class ModelTests(unittest.TestCase):
    """Verifica valores iniciais, mutabilidade de estado e resultados imutáveis."""

    def test_page_table_entry_starts_as_absent(self) -> None:
        pageTableEntry = PageTableEntry()

        self.assertIsNone(pageTableEntry.physicalFrameNumber)
        self.assertFalse(pageTableEntry.isLoadedInPhysicalMemory)
        self.assertFalse(pageTableEntry.referenceBit)

    def test_page_table_entry_is_mutable_runtime_state(self) -> None:
        pageTableEntry = PageTableEntry()

        pageTableEntry.physicalFrameNumber = 7
        pageTableEntry.isLoadedInPhysicalMemory = True
        pageTableEntry.referenceBit = True

        self.assertEqual(pageTableEntry.physicalFrameNumber, 7)
        self.assertTrue(pageTableEntry.isLoadedInPhysicalMemory)
        self.assertTrue(pageTableEntry.referenceBit)

    def test_translation_result_is_immutable(self) -> None:
        translationResult = TranslationResult(
            logicalAddress=16_916,
            virtualPageNumber=66,
            pageOffset=20,
            physicalFrameNumber=0,
            physicalAddress=20,
            unsignedByteValue=0,
            signedByteValue=0,
            wasTlbHit=False,
            wasPageFault=True,
            evictedVirtualPageNumber=None,
            translationSteps=InitializeTranslationSteps(),
        )

        with self.assertRaises(FrozenInstanceError):
            translationResult.physicalAddress = 21  # type: ignore[misc]

    def test_simulation_statistics_are_mutable_counters(self) -> None:
        simulationStatistics = SimulationStatistics()

        simulationStatistics.translatedAddressCount += 1
        simulationStatistics.pageFaultCount += 1
        simulationStatistics.tlbHitCount += 1

        self.assertEqual(simulationStatistics.translatedAddressCount, 1)
        self.assertEqual(simulationStatistics.pageFaultCount, 1)
        self.assertEqual(simulationStatistics.tlbHitCount, 1)


if __name__ == "__main__":
    unittest.main()
