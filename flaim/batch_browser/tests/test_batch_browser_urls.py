import pytest
from django.urls import reverse, resolve

pytestmark = pytest.mark.django_db


def test_index():
    assert (
        reverse("batch_browser:index")
        == f"/tools/batch_browser/"
    )
    assert resolve(f"/tools/batch_browser/").view_name == "batch_browser:index"


def test_detail(pk: int = 1):
    assert (
        reverse("batch_browser:batch_view", kwargs={"pk": pk})
        == f"/tools/batch_browser/{pk}"
    )
    assert resolve(f"/tools/batch_browser/{pk}").view_name == "batch_browser:batch_view"
