import json
import random

from sqlalchemy import func, select, update

from database.base import get_db
from database.models.combat import CombatLogModel
from database.models.user import UserModel
from domain.events import EventType, Importance


class PvPService:

    def __init__(self, chronicle, user_service):
        self.chronicle = chronicle
        self.user_service = user_service

    async def get_opponents(self, user_id: int) -> list:
        async for db in get_db():
            user = await self.user_service.get(user_id)
            if not user:
                return []

            stmt = (
                select(UserModel)
                .where(UserModel.user_id != user_id, UserModel.is_alive == True)
                .order_by(func.abs(UserModel.pvp_rating - user["pvp_rating"]))
                .limit(10)
            )
            result = await db.execute(stmt)
            rows = result.scalars().all()
            return [self._user_to_dict(r) for r in rows]
        return []

    async def battle(self, user_id: int, target_id: int) -> dict:
        user = await self.user_service.get(user_id)
        target = await self.user_service.get(target_id)

        if not user or not target:
            return {"success": False, "message": "Ошибка."}
        if not user["is_alive"]:
            return {"success": False, "message": "Ты мёртв. Очнись сначала."}
        if not target["is_alive"]:
            return {"success": False, "message": "Противник мёртв."}

        result = {
            "rounds": [],
            "user_hp": user["hp"],
            "target_hp": target["hp"],
            "outcome": None,
            "xp_gained": 0,
            "gold_gained": 0,
        }

        user_hp = user["hp"]
        target_hp = target["hp"]
        round_num = 0

        while user_hp > 0 and target_hp > 0 and round_num < 15:
            round_num += 1
            rd = {"round": round_num}

            user_dmg = max(1, user["attack"] - target["defense"] + random.randint(-2, 4))
            target_hp -= user_dmg
            rd["user_damage"] = user_dmg

            target_dmg = max(1, target["attack"] - user["defense"] + random.randint(-2, 4))
            user_hp -= target_dmg
            rd["target_damage"] = target_dmg

            result["rounds"].append(rd)

        result["user_hp"] = max(0, user_hp)
        result["target_hp"] = max(0, target_hp)

        async for db in get_db():
            old_user_rating = user["pvp_rating"]
            old_target_rating = target["pvp_rating"]

            if target_hp <= 0 and user_hp > 0:
                result["outcome"] = "victory"
                result["xp_gained"] = 15 + target["level"] * 3
                result["gold_gained"] = 5 + target["level"] * 2

                rating_change = max(10, (old_target_rating - old_user_rating) // 5 + 15)
                new_user_rating = old_user_rating + rating_change
                new_target_rating = max(100, old_target_rating - rating_change)

                new_xp = user["xp"] + result["xp_gained"]
                new_level = user["level"]
                leveled = False
                while new_xp >= new_level * 100:
                    new_level += 1
                    new_xp -= (new_level - 1) * 100
                    leveled = True
                if leveled:
                    await self._apply_level_up(user_id, new_level, db)

                await db.execute(
                    update(UserModel).where(UserModel.user_id == user_id).values(
                        xp=new_xp, level=new_level,
                        hp=min(user["max_hp"], user_hp + 30),
                        gold=user["gold"] + result["gold_gained"],
                        pvp_wins=user["pvp_wins"] + 1,
                        pvp_rating=new_user_rating,
                    )
                )
                await db.execute(
                    update(UserModel).where(UserModel.user_id == target_id).values(
                        hp=max(1, target_hp),
                        pvp_losses=target["pvp_losses"] + 1,
                        pvp_rating=new_target_rating,
                    )
                )
                await db.commit()

                await self.chronicle.publish(
                    EventType.PVP_WIN,
                    f"Победа в PvP над {target['display_name']}",
                    player_id=user_id,
                    importance=Importance.NOTABLE,
                    metadata={"target": target_id, "xp": result["xp_gained"], "gold": result["gold_gained"]},
                )

            elif user_hp <= 0:
                result["outcome"] = "defeat"

                rating_change = max(10, (old_user_rating - old_target_rating) // 5 + 15)
                new_user_rating = max(100, old_user_rating - rating_change)
                new_target_rating = old_target_rating + rating_change

                await db.execute(
                    update(UserModel).where(UserModel.user_id == user_id).values(
                        hp=0, is_alive=False,
                        pvp_losses=user["pvp_losses"] + 1,
                        pvp_rating=new_user_rating,
                    )
                )
                await db.execute(
                    update(UserModel).where(UserModel.user_id == target_id).values(
                        pvp_wins=target["pvp_wins"] + 1,
                        pvp_rating=new_target_rating,
                    )
                )
                await db.commit()

                await self.chronicle.publish(
                    EventType.PVP_LOSS,
                    f"Поражение в PvP от {target['display_name']}",
                    player_id=user_id,
                    importance=Importance.COMMON,
                    metadata={"target": target_id},
                )

            else:
                result["outcome"] = "draw"
                await db.execute(
                    update(UserModel).where(UserModel.user_id == user_id).values(hp=max(1, user_hp))
                )
                await db.execute(
                    update(UserModel).where(UserModel.user_id == target_id).values(hp=max(1, target_hp))
                )
                await db.commit()

            db.add(CombatLogModel(
                user_id=user_id,
                creature_id=f"pvp_{target_id}",
                result=result["outcome"],
                damage_dealt=sum(r.get("user_damage", 0) for r in result["rounds"]),
                damage_taken=sum(r.get("target_damage", 0) for r in result["rounds"]),
                xp_gained=result["xp_gained"],
                loot_dropped=json.dumps([]),
            ))
            await db.commit()
            break

        return result

    async def get_stats(self, user_id: int) -> dict:
        user = await self.user_service.get(user_id)
        if not user:
            return {}

        async for db in get_db():
            stmt = select(func.count()).select_from(CombatLogModel).where(
                CombatLogModel.user_id == user_id,
                CombatLogModel.creature_id.like("pvp_%"),
                CombatLogModel.result == "victory",
            )
            result = await db.execute(stmt)
            total_pvp_wins = result.scalar()

            stmt2 = select(func.count()).select_from(CombatLogModel).where(
                CombatLogModel.user_id == user_id,
                CombatLogModel.creature_id.like("pvp_%"),
            )
            result2 = await db.execute(stmt2)
            total_pvp_fights = result2.scalar()

            return {
                "rating": user["pvp_rating"],
                "wins": user["pvp_wins"],
                "losses": user["pvp_losses"],
                "total_fights": total_pvp_fights,
                "winrate": round(user["pvp_wins"] / max(1, user["pvp_wins"] + user["pvp_losses"]) * 100, 1),
            }
        return {}

    async def get_leaderboard(self, limit: int = 10) -> list:
        async for db in get_db():
            stmt = (
                select(UserModel)
                .where((UserModel.pvp_wins > 0) | (UserModel.pvp_losses > 0))
                .order_by(UserModel.pvp_rating.desc())
                .limit(limit)
            )
            result = await db.execute(stmt)
            rows = result.scalars().all()
            return [self._user_to_dict(r) for r in rows]
        return []

    async def _apply_level_up(self, user_id: int, new_level: int, db):
        new_max_hp = 100 + (new_level - 1) * 15
        new_attack = 10 + (new_level - 1) * 3
        new_defense = 5 + (new_level - 1) * 2
        await db.execute(
            update(UserModel).where(UserModel.user_id == user_id).values(
                level=new_level, max_hp=new_max_hp, attack=new_attack, defense=new_defense,
            )
        )
        await db.commit()

    @staticmethod
    def _user_to_dict(row: UserModel) -> dict:
        return {
            "user_id": row.user_id,
            "username": row.username,
            "display_name": row.display_name,
            "level": row.level,
            "hp": row.hp,
            "max_hp": row.max_hp,
            "attack": row.attack,
            "defense": row.defense,
            "pvp_rating": row.pvp_rating,
            "pvp_wins": row.pvp_wins,
            "pvp_losses": row.pvp_losses,
        }
