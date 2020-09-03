import pytest
from django.urls import reverse, resolve

pytestmark = pytest.mark.django_db


def test_index():
    assert (
        reverse("product_curator:index")
        == f"/tools/product_curator/"
    )
    assert resolve(f"/tools/product_curator/").view_name == "product_curator:index"
