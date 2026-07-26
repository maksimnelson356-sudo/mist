import logging
from sqlalchemy import select, update

from database.base import get_db
from database.models.user import UserModel
from domain.events import EventType, Importance

logger = logging.getLogger("MIST.class")

CLASSES = {
    "warrior": {
        "name": "Воин",
        "icon": "⚔️",
        "description": "Мастер ближнего боя. Сильный удар, стойкость, ярость.",
        "base_stats": {"attack": 15, "defense": 12, "max_hp": 120},
        "abilities": [
            {"level": 1, "id": "power_strike", "name": "Мощный удар", "description": "Удар с силой x2", "cooldown": 3},
            {"level": 5, "id": "shield_wall", "name": "Стена щитов", "description": "+10 защита на 3 хода", "cooldown": 5},
            {"level": 10, "id": "berserk", "name": "Берсерк", "description": "+50% атака, -25% защита на 5 ходов", "cooldown": 8},
            {"level": 20, "id": "war_cry", "name": "Боевой клич", "description": "Повреждает всех врагов в области", "cooldown": 12},
        ],
    },
    "mage": {
        "name": "Маг",
        "icon": "🔮",
        "description": "Повелитель стихий. Огненные шары, щиты, исцеление.",
        "base_stats": {"attack": 12, "defense": 8, "max_hp": 80},
        "abilities": [
            {"level": 1, "id": "fireball", "name": "Огненный шар", "description": "Магический урон 25", "cooldown": 2},
            {"level": 5, "id": "arcane_shield", "name": "Магический щит", "description": "Блокирует следующий удар", "cooldown": 4},
            {"level": 10, "id": "heal", "name": "Исцеление", "description": "Восстанавливает 40 HP", "cooldown": 6},
            {"level": 20, "id": "meteor", "name": "Метеор", "description": "Урон 80 по области", "cooldown": 15},
        ],
    },
    "scout": {
        "name": "Разведчик",
        "icon": "🏹",
        "description": "Мастер скрытности. Уклонение, криты, разведка.",
        "base_stats": {"attack": 10, "defense": 8, "max_hp": 90},
        "abilities": [
            {"level": 1, "id": "quick_shot", "name": "Быстрый выстрел", "description": "Двойной выстрел", "cooldown": 2},
            {"level": 5, "id": "dodge", "name": "Уклонение", "description": "Уклоняется от следующей атаки", "cooldown": 3},
            {"level": 10, "id": "stealth", "name": "Скрытность", "description": "Невидимость на 3 хода", "cooldown": 7},
            {"level": 20, "id": "eagle_eye", "name": "Орлиный глаз", "description": "Крит шанс +50% на 5 ходов", "cooldown": 10},
        ],
    },
    "craftsman": {
        "name": "Ремесленник",
        "icon": "⚒️",
        "description": "Мастер на все руки. Крафт, ремонт, лучшее снаряжение.",
        "base_stats": {"attack": 8, "defense": 10, "max_hp": 100},
        "abilities": [
            {"level": 1, "id": "repair", "name": "Починка", "description": "Чинит снаряжение", "cooldown": 1},
            {"level": 5, "id": "fortify", "name": "Укрепить", "description": "+8 защита на 3 хода", "cooldown": 4},
            {"level": 10, "id": "trap", "name": "Ловушка", "description": "Наносит 30 урона при атаке", "cooldown": 5},
            {"level": 20, "id": "golem", "name": "Голем", "description": "Призывает голема на 5 ходов", "cooldown": 12},
        ],
    },
}


class ClassService:

    def __init__(self, chronicle, player):
        self.chronicle = chronicle
        self.player = player

    async def get_class(self, user_id: int) -> dict:
        user = await self.player.get(user_id)
        if not user:
            return CLASSES["warrior"]

        class_id = user.get("player_class", "warrior")
        class_level = user.get("class_level", 1)
        class_def = CLASSES.get(class_id, CLASSES["warrior"])

        unlocked_abilities = [
            a for a in class_def["abilities"]
            if a["level"] <= class_level
        ]

        return {
            "class_id": class_id,
            "name": class_def["name"],
            "icon": class_def["icon"],
            "description": class_def["description"],
            "class_level": class_level,
            "abilities": unlocked_abilities,
            "base_stats": class_def["base_stats"],
        }

    async def select_class(self, user_id: int, class_id: str) -> dict:
        if class_id not in CLASSES:
            return {"success": False, "message": "Класс не найден."}

        user = await self.player.get(user_id)
        if not user:
            return {"success": False, "message": "Пользователь не найден."}

        if user.get("player_class") and user["player_class"] != "warrior":
            return {"success": False, "message": "Ты уже выбрал класс. Нельзя сменить."}

        class_def = CLASSES[class_id]
        stats = class_def["base_stats"]

        async for db in get_db():
            await db.execute(
                update(UserModel)
                .where(UserModel.user_id == user_id)
                .values(
                    player_class=class_id,
                    class_level=1,
                    attack=stats["attack"],
                    defense=stats["defense"],
                    max_hp=stats["max_hp"],
                    hp=stats["max_hp"],
                )
            )
            await db.commit()

        await self.chronicle.publish(
            EventType.PLAYER_LEVEL_UP,
            f"{user.get('display_name', 'Путник')} выбрал класс {class_def['name']}",
            player_id=user_id,
            importance=Importance.COMMON,
        )

        return {
            "success": True,
            "message": f"✨ Ты стал {class_def['name']}!",
            "class": class_id,
        }

    async def level_up_class(self, user_id: int) -> dict:
        user = await self.player.get(user_id)
        if not user:
            return {"success": False, "message": "Пользователь не найден."}

        class_id = user.get("player_class", "warrior")
        class_level = user.get("class_level", 1)
        class_def = CLASSES.get(class_id, CLASSES["warrior"])

        new_level = class_level + 1
        new_ability = None

        for a in class_def["abilities"]:
            if a["level"] == new_level:
                new_ability = a
                break

        async for db in get_db():
            await db.execute(
                update(UserModel)
                .where(UserModel.user_id == user_id)
                .values(class_level=new_level)
            )
            await db.commit()

        msg = f"⬆️ Класс {class_def['name']} повышен до {new_level}!"
        if new_ability:
            msg += f"\n🔓 Новая способность: {new_ability['name']}!"

        return {"success": True, "message": msg, "new_level": new_level, "new_ability": new_ability}

    async def get_all_classes(self) -> list:
        result = []
        for class_id, class_def in CLASSES.items():
            result.append({
                "id": class_id,
                "name": class_def["name"],
                "icon": class_def["icon"],
                "description": class_def["description"],
                "ability_count": len(class_def["abilities"]),
            })
        return result
