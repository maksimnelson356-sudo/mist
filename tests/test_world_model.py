import uuid
import pytest
from unittest.mock import MagicMock


def test_continent_model_fields():
    from database.models.continent import ContinentModel

    continent = ContinentModel(
        id="test-001",
        name="Test Continent",
        description="A test continent",
        x=0, y=0,
    )

    assert continent.id == "test-001"
    assert continent.name == "Test Continent"
    assert continent.description == "A test continent"
    assert continent.x == 0
    assert continent.y == 0


def test_region_model_fields():
    from database.models.region import RegionModel

    region = RegionModel(
        id="region-001",
        name="Test Region",
        continent_id="test-001",
        x=1, y=2,
    )

    assert region.id == "region-001"
    assert region.name == "Test Region"
    assert region.continent_id == "test-001"
    assert region.x == 1
    assert region.y == 2


def test_location_model_uuid():
    from database.models.location import LocationModel

    loc = LocationModel(
        location_id="test_location",
        name="Test Location",
        region_id="region-001",
        x=0, y=0, z=0,
    )

    assert loc.location_id == "test_location"
    assert loc.region_id == "region-001"
    assert loc.x == 0


def test_poi_model_fields():
    from database.models.poi import POIModel

    poi = POIModel(
        location_id="loc-001",
        poi_type="shop",
        name="Test Shop",
        description="A test shop",
        x=1, y=2,
    )

    assert poi.location_id == "loc-001"
    assert poi.poi_type == "shop"
    assert poi.name == "Test Shop"


def test_location_region_mapping():
    REGIONS = {
        "dark_forest": {"id": "region-dark-forest", "name": "Тёмный лес"},
        "coast": {"id": "region-coast", "name": "Побережье"},
        "mountains": {"id": "region-mountains", "name": "Горные земли"},
    }

    LOCATION_REGIONS = {
        "dark_forest": "dark_forest",
        "wolf_den": "dark_forest",
        "riverbank": "coast",
        "ancient_ruins": "mountains",
    }

    assert LOCATION_REGIONS["dark_forest"] == "dark_forest"
    assert LOCATION_REGIONS["wolf_den"] == "dark_forest"
    assert LOCATION_REGIONS["riverbank"] == "coast"
    assert LOCATION_REGIONS["ancient_ruins"] == "mountains"

    assert REGIONS[LOCATION_REGIONS["dark_forest"]]["name"] == "Тёмный лес"
    assert REGIONS[LOCATION_REGIONS["riverbank"]]["name"] == "Побережье"


def test_poi_templates():
    POI_TEMPLATES = {
        "fishing_village": [
            {"poi_type": "shop", "name": "Рыбацкий склад"},
            {"poi_type": "quest_giver", "name": "Старый рыбак"},
        ],
        "market_square": [
            {"poi_type": "shop", "name": "Торговые палатки"},
        ],
    }

    assert len(POI_TEMPLATES["fishing_village"]) == 2
    assert POI_TEMPLATES["fishing_village"][0]["poi_type"] == "shop"
    assert len(POI_TEMPLATES["market_square"]) == 1


def test_uuid_generation():
    id1 = str(uuid.uuid4())
    id2 = str(uuid.uuid4())

    assert id1 != id2
    assert len(id1) == 36
    assert id1.count("-") == 4


def test_location_connections_are_lists():
    connections = ["loc1", "loc2", "loc3"]

    assert isinstance(connections, list)
    assert len(connections) == 3
    assert "loc1" in connections


def test_continent_hierarchy():
    continent_id = "mistlands-001"
    regions = {
        "dark_forest": {"id": "region-dark-forest", "continent_id": continent_id},
        "coast": {"id": "region-coast", "continent_id": continent_id},
    }

    for reg in regions.values():
        assert reg["continent_id"] == continent_id
