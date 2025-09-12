from pathlib import Path

import pytest

from ccu.fancyplots.data import DEFAULT_PARAMETERS
from ccu.fancyplots.data import Annotation
from ccu.fancyplots.data import FEDData
from ccu.fancyplots.data import FormattingParameters
from ccu.fancyplots.plotting import generate_figure


@pytest.fixture(name="diagram_data")
def fixture_diagram_data() -> FEDData:
    energy_data = [[0, 0.5, 0.75, 0.25], [0, 0.25, 0.4, 0.5]]
    mechanism = ["CO2", "*COOH", "*CO", "CO"]
    legend_labels = ["CO", "HCOO-"]
    return FEDData(
        energy_data=energy_data,
        mechanism=mechanism,
        legend_labels=legend_labels,
    )


@pytest.fixture(name="parameters")
def fixture_parameters(tmp_path: Path) -> FormattingParameters:
    parameters = FormattingParameters(**DEFAULT_PARAMETERS)
    parameters["savename"] = str(tmp_path.joinpath(parameters["savename"]))
    return parameters


@pytest.fixture(name="annotations")
def fixture_annotations() -> list[Annotation]:
    return [Annotation("k", 12, "Annotation 1", 4, 4)]


class TestGenerateFigure:
    @staticmethod
    def test_should_generate_figure(
        diagram_data: FEDData,
        parameters: FormattingParameters,
        annotations: list[Annotation],
    ) -> None:
        _ = generate_figure(
            diagram_data=diagram_data,
            parameters=parameters,
            annotations=annotations,
            visual=False,
        )
        assert Path(parameters["savename"]).exists()
