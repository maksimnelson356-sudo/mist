import logging
import random

from sqlalchemy import text

from database.base import get_db
from domain.events import EventType, Importance

logger = logging.getLogger("MIST.events")

EVENT_PARTICIPATIONS = {
    "forest_fire": {
        "name": "Помощь при пожаре",
        "description": "Тушить огонь или спасать жителей?",
        "actions": [
            {"id": "fight_fire", "label": "🧯 Тушить огонь", "xp": 15, "gold": 10, "risk": 0.1},
            {"id": "save_people", "label": "🏃 Спасать людей", "xp": 20, "gold": 5, "risk": 0.15},
            {"id": "loot", "label": "💰 Грабить горящие дома", "xp": 5, "gold": 30, "risk": 0.3, "rep_loss": 10},
        ],
    },
    "wolf_pack_migration": {
        "name": "Сдерживание стаи",
        "description": "Стая волков движется через земли. Что будешь делать?",
        "actions": [
            {"id": "hunt_wolves", "label": "🏹 Охотиться на волков", "xp": 20, "gold": 15, "risk": 0.2},
            {"id": "defend_village", "label": "🛡️ Защищать деревню", "xp": 25, "gold": 5, "risk": 0.1},
            {"id": "observe", "label": "👁️ Наблюдать издалека", "xp": 10, "gold": 0, "risk": 0.0},
        ],
    },
    "harvest_festival": {
        "name": "Участие в празднике",
        "description": "Праздник урожая! Как проведёшь время?",
        "actions": [
            {"id": "feast", "label": "🍺 Пировать", "xp": 10, "gold": -5, "risk": 0.0},
            {"id": "dance", "label": "💃 Танцевать", "xp": 15, "gold": 0, "risk": 0.0},
            {"id": "trade", "label": "🛒 Торговать на ярмарке", "xp": 5, "gold": 20, "risk": 0.0},
        ],
    },
    "drought": {
        "name": "Помощь в засухе",
        "description": "Земля горит. Люди страдают. Чем поможешь?",
        "actions": [
            {"id": "find_water", "label": "💧 Искать воду", "xp": 20, "gold": 10, "risk": 0.1},
            {"id": "dig_well", "label": "⛏️ Копать колодец", "xp": 25, "gold": 15, "risk": 0.05},
            {"id": "steal_water", "label": "🚰 Воровать воду", "xp": 10, "gold": 25, "risk": 0.25, "rep_loss": 15},
        ],
    },
    "ancient_altar_discovered": {
        "name": "Исследование алтаря",
        "description": "Древний алтарь пробудился. Что делаешь?",
        "actions": [
            {"id": "study", "label": "📖 Изучать алтарь", "xp": 30, "gold": 0, "risk": 0.1},
            {"id": "pray", "label": "🙏 Молиться", "xp": 20, "gold": 0, "risk": 0.0},
            {"id": "steal_crystal", "label": "💎 Выломать кристалл", "xp": 10, "gold": 50, "risk": 0.3, "rep_loss": 5},
        ],
    },
    "merchant_caravan": {
        "name": "Торговля с караваном",
        "description": "Караван прибыл. Торгуешь?",
        "actions": [
            {"id": "buy_rare", "label": "🛒 Купить редкие товары", "xp": 5, "gold": -30, "risk": 0.0},
            {"id": "sell_crafts", "label": "💰 Продать свои изделия", "xp": 5, "gold": 25, "risk": 0.0},
            {"id": "work_for_caravan", "label": "🤝 Поработать на караван", "xp": 15, "gold": 15, "risk": 0.0},
        ],
    },
    "flood": {
        "name": "Помощь при наводнении",
        "description": "Вода поднимается. Спасаешь?",
        "actions": [
            {"id": "rescue", "label": "🏊 Спасать людей", "xp": 25, "gold": 10, "risk": 0.2},
            {"id": "build_dam", "label": "🪵 Строить плотину", "xp": 20, "gold": 15, "risk": 0.1},
            {"id": "scavenge", "label": "🔍 Искать выброшенные вещи", "xp": 10, "gold": 30, "risk": 0.05},
        ],
    },
    "plague": {
        "name": "Борьба с эпидемией",
        "description": "Чума косит людей. Что делаешь?",
        "actions": [
            {"id": "heal", "label": "💊 Лечить больных", "xp": 30, "gold": 0, "risk": 0.15},
            {"id": "quarantine", "label": "🚧 Оцепить район", "xp": 20, "gold": 5, "risk": 0.05},
            {"id": "flee", "label": "🏃 Бежать из города", "xp": 5, "gold": 0, "risk": 0.0, "rep_loss": 20},
        ],
    },
    "undead_awakening": {
        "name": "Сражение с нежитью",
        "description": "Мертвецы поднимаются. Сражаешься?",
        "actions": [
            {"id": "fight_undead", "label": "⚔️ Сражаться с нежитью", "xp": 30, "gold": 20, "risk": 0.25},
            {"id": "seal_graves", "label": "🔒 Запечатать могилы", "xp": 25, "gold": 10, "risk": 0.1},
            {"id": "loot_graves", "label": "💰 Ограбить могилы", "xp": 10, "gold": 40, "risk": 0.2, "rep_loss": 20},
        ],
    },
    "clan_war": {
        "name": "Участие в войне кланов",
        "description": "Два клана дерутся. На чьей стороне?",
        "actions": [
            {"id": "fight_alpha", "label": "⚔️ Сражаться за Альфа-клан", "xp": 25, "gold": 20, "risk": 0.2},
            {"id": "fight_beta", "label": "⚔️ Сражаться за Бета-клан", "xp": 25, "gold": 20, "risk": 0.2},
            {"id": "peacekeeper", "label": "🕊️ Попытаться примирить", "xp": 30, "gold": 10, "risk": 0.05},
        ],
    },
    "bandits_on_road": {
        "name": "Разбойники на дорогах",
        "description": "Бандиты перекрыли путь. Что делаешь?",
        "actions": [
            {"id": "fight_bandits", "label": "⚔️ Вступить в бой", "xp": 20, "gold": 25, "risk": 0.2},
            {"id": "sneak", "label": "🤫 Прокрасться мимо", "xp": 15, "gold": 0, "risk": 0.1},
            {"id": "pay_toll", "label": "💰 заплатить", "xp": 5, "gold": -20, "risk": 0.0},
        ],
    },
    "wandering_merchant": {
        "name": "Встреча со странником",
        "description": "Загадочный торговец. Общаешься?",
        "actions": [
            {"id": "buy_map", "label": "🗺️ Купить карту", "xp": 10, "gold": -15, "risk": 0.0},
            {"id": "listen_stories", "label": "📖 Слушать его истории", "xp": 15, "gold": 0, "risk": 0.0},
            {"id": "rob", "label": "🗡️ Ограбить", "xp": 10, "gold": 35, "risk": 0.3, "rep_loss": 25},
        ],
    },
    "meteorite": {
        "name": "Исследование метеорита",
        "description": "Огненный шар упал. Что будешь делать?",
        "actions": [
            {"id": "mine_crystals", "label": "💎 Добывать кристаллы", "xp": 30, "gold": 40, "risk": 0.1},
            {"id": "study_energy", "label": "🔬 Изучать энергию", "xp": 35, "gold": 0, "risk": 0.15},
            {"id": "sell_location", "label": "📍 Продать координаты", "xp": 5, "gold": 50, "risk": 0.0, "rep_loss": 5},
        ],
    },
    "lantern_festival": {
        "name": "Праздник огней",
        "description": "Тысячи фонарей в небе. Как проведёшь?",
        "actions": [
            {"id": "release_lantern", "label": "🏮 Выпустить фонарь", "xp": 10, "gold": -2, "risk": 0.0},
            {"id": "find_love", "label": "💕 Найти спутника", "xp": 15, "gold": 0, "risk": 0.0},
            {"id": "steal_lantern", "label": "🏮 Красть фонарь", "xp": 5, "gold": 10, "risk": 0.05, "rep_loss": 5},
        ],
    },
    "fog_storm": {
        "name": "Выживание в тумане",
        "description": "Густой туман. Видимость — ноль.",
        "actions": [
            {"id": "navigate", "label": "🧭 Пробираться наугад", "xp": 20, "gold": 10, "risk": 0.2},
            {"id": "wait", "label": "⏰ Ждать когда рассеется", "xp": 10, "gold": 0, "risk": 0.0},
            {"id": "explore", "label": "🔍 Исследовать туман", "xp": 25, "gold": 15, "risk": 0.25},
        ],
    },
    "ruin_anomaly": {
        "name": "Исследование аномалии",
        "description": "Из руин исходит свечение. Что делаешь?",
        "actions": [
            {"id": "enter_ruins", "label": "🏚️ Войти в руины", "xp": 25, "gold": 20, "risk": 0.2},
            {"id": "collect_energy", "label": "⚡ Собрать энергию", "xp": 20, "gold": 10, "risk": 0.1},
            {"id": "set_camp", "label": "⛺ Разбить лагерь рядом", "xp": 10, "gold": 0, "risk": 0.0},
        ],
    },
    "ship_in_harbour": {
        "name": "Встреча с моряками",
        "description": "Корабль в гавани. Экипаж ищетHelpers.",
        "actions": [
            {"id": "join_crew", "label": "⚓ Вступить в экипаж", "xp": 20, "gold": 25, "risk": 0.1},
            {"id": "trade_with_crew", "label": "🤝 Торговать с экипажем", "xp": 10, "gold": 20, "risk": 0.0},
            {"id": "steal_from_ship", "label": "🚢 Красть с корабля", "xp": 15, "gold": 35, "risk": 0.25, "rep_loss": 15},
        ],
    },
}


class EventService:

    def __init__(self, chronicle, player):
        self.chronicle = chronicle
        self.player = player

    async def get_active_events(self, region_id: str = None) -> list:
        async for db in get_db():
            if region_id:
                result = await db.execute(
                    text("SELECT * FROM world_event_records WHERE is_active = 1 AND region_id = :rid ORDER BY start_day DESC"),
                    {"rid": region_id},
                )
            else:
                result = await db.execute(
                    text("SELECT * FROM world_event_records WHERE is_active = 1 ORDER BY start_day DESC")
                )
            events = []
            for row in result.mappings().all():
                ev = dict(row)
                ev["participations"] = EVENT_PARTICIPATIONS.get(ev["event_type"])
                events.append(ev)
            return events

    async def get_event(self, record_id: str) -> dict | None:
        async for db in get_db():
            result = await db.execute(
                text("SELECT * FROM world_event_records WHERE id = :id"),
                {"id": record_id},
            )
            row = result.mappings().first()
            if row:
                ev = dict(row)
                ev["participations"] = EVENT_PARTICIPATIONS.get(ev["event_type"])
                return ev
            return None

    async def participate(self, record_id: str, user_id: int, action_id: str) -> dict:
        user = await self.player.get(user_id)
        if not user or not user["is_alive"]:
            return {"success": False, "message": "Ты не можешь участвовать."}

        ev = await self.get_event(record_id)
        if not ev or not ev["is_active"]:
            return {"success": False, "message": "Событие завершено."}

        participations = EVENT_PARTICIPATIONS.get(ev["event_type"], {})
        actions = participations.get("actions", [])
        action = next((a for a in actions if a["id"] == action_id), None)
        if not action:
            return {"success": False, "message": "Действие не найдено."}

        risk = action.get("risk", 0.0)
        hit = random.random() < risk

        if hit:
            damage = random.randint(10, 25)
            from sqlalchemy import update

            from database.models.user import UserModel
            async for db in get_db():
                if user["hp"] <= damage:
                    await db.execute(
                        update(UserModel)
                        .where(UserModel.user_id == user_id)
                        .values(hp=1, is_alive=False)
                    )
                    await db.commit()

                    await self.chronicle.publish(
                        EventType.DEATH,
                        f"💀 {user['name']} погиб, участвуя в событии: {participations['name']}",
                        importance=Importance.RARE,
                    )

                    return {
                        "success": False,
                        "killed": True,
                        "message": f"💀 Ты получил {damage} урона и погиб!",
                    }

                await db.execute(
                    update(UserModel)
                    .where(UserModel.user_id == user_id)
                    .values(hp=UserModel.hp - damage)
                )
                await db.commit()

            return {
                "success": True,
                "damaged": True,
                "damage": damage,
                "message": f"⚠️ Ты получил {damage} урона!",
                "xp": 0,
                "gold": 0,
            }

        xp = action.get("xp", 0)
        gold = action.get("gold", 0)
        rep_loss = action.get("rep_loss", 0)

        from sqlalchemy import update

        from database.models.user import UserModel
        async for db in get_db():
            new_gold = max(0, user["gold"] + gold)
            await db.execute(
                update(UserModel)
                .where(UserModel.user_id == user_id)
                .values(
                    xp=UserModel.xp + xp,
                    gold=new_gold,
                )
            )
            await db.commit()

        msg = f"✅ Участие: {action['label']}\n"
        if xp > 0:
            msg += f"XP: +{xp}\n"
        if gold != 0:
            msg += f"Gold: {'+' if gold > 0 else ''}{gold}\n"
        if rep_loss > 0:
            msg += f"⚠️ Репутация: -{rep_loss}\n"

        await self.chronicle.publish(
            EventType.WORLD_EVENT,
            f"🎭 {user['name']} участвует в: {participations['name']}",
            importance=Importance.TRIVIAL,
        )

        return {
            "success": True,
            "xp": xp,
            "gold": gold,
            "message": msg,
        }
