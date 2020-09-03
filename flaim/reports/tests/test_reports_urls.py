import pytest
from django.urls import reverse, resolve

pytestmark = pytest.mark.django_db


def test_category_report():
    assert (
        reverse("reports:category_report", kwargs={"category": "Beverages"})
        == f"/reports/category/Beverages/"
    )
    assert resolve(f"/reports/category/Beverages/").view_name == "reports:category_report"


def test_store_report():
    assert (
        reverse("reports:store_report", kwargs={"store": "Loblaws"})
        == f"/reports/store/Loblaws/"
    )
    assert resolve(f"/reports/store/Loblaws/").view_name == "reports:store_report"
