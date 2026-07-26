import pytest

from services.admin_service import ADMIN_IDS, is_admin


def test_admin_ids_empty():
    assert isinstance(ADMIN_IDS, list)


def test_is_admin_no_users():
    assert is_admin(123456) is False


def test_is_admin_empty_list():
    assert is_admin(0) is False
