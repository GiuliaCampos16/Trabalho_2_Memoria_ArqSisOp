"""Contrato da saída didática do simulador."""

from pathlib import Path

from models import SimulationStatistics, TranslationResult


class SimulationReporter:
    """Publica traduções e estatísticas no terminal e em arquivo."""

    def __init__(self, outputFilePath: Path) -> None:
        self.outputFilePath: Path = outputFilePath

    def PublishTranslation(self, translationResult: TranslationResult) -> None:
        """Publica os passos e o resultado de uma tradução."""

        raise NotImplementedError("A saída didática será implementada na Etapa 7.")

    def PublishStatistics(
        self, simulationStatistics: SimulationStatistics
    ) -> None:
        """Publica os totais e taxas calculados ao final da execução."""

        raise NotImplementedError("As estatísticas serão implementadas na Etapa 7.")

    def Close(self) -> None:
        """Libera os recursos mantidos pelo reporter."""

        raise NotImplementedError("O fechamento do reporter será implementado na Etapa 7.")
