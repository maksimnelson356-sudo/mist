import json
from sqlalchemy import select

from database.base import get_db
from database.models.continent import ContinentModel
from database.models.region import RegionModel
from database.models.location import LocationModel
from database.models.poi import POIModel


class WorldGenerator:

    @staticmethod
    async def generate_world(world_data: dict) -> dict:
        result = {
            "continents": 0,
            "regions": 0,
            "locations": 0,
            "pois": 0,
        }

        async for db in get_db():
            for continent_data in world_data.get("continents", []):
                continent = ContinentModel(
                    id=continent_data["id"],
                    name=continent_data["name"],
                    description=continent_data.get("description", ""),
                    x=continent_data.get("x", 0),
                    y=continent_data.get("y", 0),
                )
                db.add(continent)
                result["continents"] += 1

                for region_data in continent_data.get("regions", []):
                    region = RegionModel(
                        id=region_data["id"],
                        name=region_data["name"],
                        description=region_data.get("description", ""),
                        continent_id=continent.id,
                        x=region_data.get("x", 0),
                        y=region_data.get("y", 0),
                    )
                    db.add(region)
                    result["regions"] += 1

                    for loc_data in region_data.get("locations", []):
                        location = LocationModel(
                            id=loc_data["id"],
                            location_id=loc_data["location_id"],
                            name=loc_data["name"],
                            description=loc_data.get("description", ""),
                            region_id=region.id,
                            x=loc_data.get("x", 0),
                            y=loc_data.get("y", 0),
                            z=loc_data.get("z", 0),
                            connections=loc_data.get("connections", []),
                            is_secret=loc_data.get("is_secret", False),
                            required_karma=loc_data.get("required_karma", 0),
                            discovered=loc_data.get("discovered", False),
                        )
                        db.add(location)
                        result["locations"] += 1

                        for poi_data in loc_data.get("pois", []):
                            poi = POIModel(
                                id=poi_data["id"],
                                location_id=location.id,
                                poi_type=poi_data["poi_type"],
                                name=poi_data["name"],
                                description=poi_data.get("description", ""),
                                x=poi_data.get("x", 0),
                                y=poi_data.get("y", 0),
                                is_active=poi_data.get("is_active", True),
                                interaction_data=poi_data.get("interaction_data", {}),
                            )
                            db.add(poi)
                            result["pois"] += 1

            await db.commit()

        return result

    @staticmethod
    async def get_map(continent_id: str) -> str:
        async for db in get_db():
            stmt = select(ContinentModel).where(ContinentModel.id == continent_id)
            result = await db.execute(stmt)
            continent = result.scalar_one_or_none()

            if not continent:
                return "Континент не найден."

            stmt_regions = select(RegionModel).where(RegionModel.continent_id == continent_id)
            result_regions = await db.execute(stmt_regions)
            regions = result_regions.scalars().all()

            map_lines = [
                f"🗺 {continent.name}",
                f"   {continent.description or ''}",
                "",
            ]

            for region in regions:
                map_lines.append(f"📍 {region.name}")
                stmt_locs = select(LocationModel).where(LocationModel.region_id == region.id)
                result_locs = await db.execute(stmt_locs)
                locations = result_locs.scalars().all()

                for loc in locations:
                    status = "✅" if loc.discovered else "❓"
                    map_lines.append(f"   {status} {loc.name}")

                map_lines.append("")

            return "\n".join(map_lines)
        return "Ошибка базы данных."

    @staticmethod
    async def get_nearby(location_id: str, radius: int = 1) -> list:
        async for db in get_db():
            stmt = select(LocationModel).where(LocationModel.location_id == location_id)
            result = await db.execute(stmt)
            loc = result.scalar_one_or_none()

            if not loc:
                return []

            connections = loc.connections if isinstance(loc.connections, list) else []
            nearby = []

            for conn_id in connections[:radius]:
                stmt_conn = select(LocationModel).where(LocationModel.location_id == conn_id)
                result_conn = await db.execute(stmt_conn)
                conn_loc = result_conn.scalar_one_or_none()
                if conn_loc:
                    nearby.append({
                        "location_id": conn_loc.location_id,
                        "name": conn_loc.name,
                        "discovered": conn_loc.discovered,
                        "x": conn_loc.x,
                        "y": conn_loc.y,
                    })

            return nearby
        return []

    @staticmethod
    async def get_pois_at(location_id: str) -> list:
        async for db in get_db():
            stmt_loc = select(LocationModel).where(LocationModel.location_id == location_id)
            result_loc = await db.execute(stmt_loc)
            loc = result_loc.scalar_one_or_none()

            if not loc:
                return []

            stmt = select(POIModel).where(
                POIModel.location_id == loc.id,
                POIModel.is_active == True,
            )
            result = await db.execute(stmt)
            pois = result.scalars().all()

            return [
                {
                    "id": poi.id,
                    "poi_type": poi.poi_type,
                    "name": poi.name,
                    "description": poi.description,
                    "x": poi.x,
                    "y": poi.y,
                }
                for poi in pois
            ]
        return []
