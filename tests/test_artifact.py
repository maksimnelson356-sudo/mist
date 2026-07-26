import pytest
from unittest.mock import AsyncMock, MagicMock

from services.artifact_service import ArtifactService


class MockChronicle:
    async def publish(self, *a, **kw):
        pass


def test_artifact_service_init():
    svc = ArtifactService(MockChronicle())
    assert svc is not None


def test_artifact_service_has_create_method():
    svc = ArtifactService(MockChronicle())
    assert hasattr(svc, 'create_artifact')


def test_artifact_service_has_get_method():
    svc = ArtifactService(MockChronicle())
    assert hasattr(svc, 'get')


def test_artifact_service_has_get_by_owner():
    svc = ArtifactService(MockChronicle())
    assert hasattr(svc, 'get_by_owner')


def test_artifact_service_has_use_method():
    svc = ArtifactService(MockChronicle())
    assert hasattr(svc, 'use_artifact')


def test_artifact_service_has_discover_method():
    svc = ArtifactService(MockChronicle())
    assert hasattr(svc, 'discover_artifact')


def test_artifact_service_has_get_all_method():
    svc = ArtifactService(MockChronicle())
    assert hasattr(svc, 'get_all_artifacts')


def test_artifact_service_has_stats_method():
    svc = ArtifactService(MockChronicle())
    assert hasattr(svc, 'get_artifact_stats')


def test_artifact_method_signatures_are_async():
    import inspect
    svc = ArtifactService(MockChronicle())
    for method in ['create_artifact', 'get', 'get_by_owner', 'use_artifact', 'discover_artifact', 'get_all_artifacts', 'get_artifact_stats']:
        assert inspect.iscoroutinefunction(getattr(svc, method)), f"{method} should be async"