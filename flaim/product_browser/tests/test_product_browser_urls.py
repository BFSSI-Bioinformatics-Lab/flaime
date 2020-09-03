import pytest
from django.urls import reverse, resolve

pytestmark = pytest.mark.django_db


def test_index():
    assert (
        reverse("product_browser:index")
        == f"/tools/product_browser/"
    )
    assert resolve(f"/tools/product_browser/").view_name == "product_browser:index"


def test_detail(pk: int = 1):
    assert (
        reverse("product_browser:product_view", kwargs={"pk": pk})
        == f"/tools/product_browser/{pk}"
    )
    assert resolve(f"/tools/product_browser/{pk}").view_name == "product_browser:product_view"
