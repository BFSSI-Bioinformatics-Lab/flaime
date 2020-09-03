import pytest
from django.urls import reverse, resolve

pytestmark = pytest.mark.django_db


def test_data_quality():
    assert (
        reverse("data:data_quality")
        == f"/data/quality/"
    )
    assert resolve(f"/data/quality/").view_name == "data:data_quality"
