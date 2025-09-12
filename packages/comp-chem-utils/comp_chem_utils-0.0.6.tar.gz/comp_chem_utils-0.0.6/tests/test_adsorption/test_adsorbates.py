import pytest

from ccu.adsorption.adsorbates import ALL_ADSORBATES
from ccu.adsorption.adsorbates import get_adsorbate


# pylint:disable=too-few-public-methods
class TestGetAdsorbates:
    @staticmethod
    @pytest.mark.parametrize("adsorbate_name", ALL_ADSORBATES.keys())
    def test_should_return_defined_adsorbates(adsorbate_name: str):
        _ = get_adsorbate(adsorbate_name)
        assert True
