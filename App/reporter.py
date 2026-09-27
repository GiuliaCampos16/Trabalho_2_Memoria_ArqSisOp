"""Contrato da saída didática do simulador."""

from pathlib import Path

from models import SimulationStatistics, TranslationResult


class SimulationReporter:
    """Publica traduções e estatísticas no terminal e em arquivo."""

    def __init__(self, output_file_path: Path) -> None:
        self._output_file_path: Path = output_file_path

    def publish_translation(self, translation_result: TranslationResult) -> None:
        """Publica os passos e o resultado de uma tradução."""

        raise NotImplementedError("A saída didática será implementada na Etapa 7.")

    def publish_statistics(
        self, simulation_statistics: SimulationStatistics
    ) -> None:
        """Publica os totais e taxas calculados ao final da execução."""

        raise NotImplementedError("As estatísticas serão implementadas na Etapa 7.")

    def close(self) -> None:
        """Libera os recursos mantidos pelo reporter."""

        raise NotImplementedError("O fechamento do reporter será implementado na Etapa 7.")
