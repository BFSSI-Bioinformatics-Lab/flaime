import pytest
from django.urls import reverse, resolve

pytestmark = pytest.mark.django_db


def test_index():
    assert (
        reverse("product_search:index")
        == f"/tools/product_search/"
    )
    assert resolve(f"/tools/product_search/").view_name == "product_search:index"
