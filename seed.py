import json
import asyncio
import uuid
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')

from sqlalchemy import text
from database.base import init_db, get_db
from database.models import (
    ContinentModel, RegionModel, LocationModel, POIModel,
    CreatureModel, NPCModel,
    ItemTemplateModel,
    QuestModel, ShopItemModel, CraftingRecipeModel,
    AchievementModel, GroundItemModel, SecretModel,
    WorldStateModel,
)


CONTINENT_ID = "mistlands-001"
REGIONS = {
    "dark_forest": {"id": "region-dark-forest", "name": "Тёмный лес", "x": 0, "y": 0},
    "coast": {"id": "region-coast", "name": "Побережье", "x": 1, "y": 0},
    "mountains": {"id": "region-mountains", "name": "Горные земли", "x": 0, "y": 1},
    "civilization": {"id": "region-civilization", "name": "Островки цивилизации", "x": 1, "y": 1},
    "secret": {"id": "region-secret", "name": "Скрытые земли", "x": 0, "y": 2},
}

LOCATION_REGIONS = {
    "dark_forest": "dark_forest", "wolf_den": "dark_forest", "blood_meadow": "dark_forest",
    "abandoned_camp": "dark_forest", "witch_swamp": "dark_forest", "dark_harbour": "dark_forest",
    "thornwood": "dark_forest", "ancient_battlefield": "dark_forest",
    "riverbank": "coast", "fishing_village": "coast", "underwater_cave": "coast",
    "misty_bay": "coast", "shipwreck_beach": "coast", "crystal_lake": "coast",
    "rusty_docks": "coast", "ember_swamp": "coast", "whispering_shore": "coast",
    "ancient_ruins": "mountains", "crystal_cave": "mountains", "obsidian_tower": "mountains",
    "tower_summit": "mountains", "ash_fields": "mountains", "white_forest": "mountains",
    "bone_desert": "mountains", "iron_mine": "mountains", "starfall_valley": "mountains",
    "frost_hollow": "mountains", "storm_cliffs": "mountains",
    "market_square": "civilization", "temple_of_shadows": "civilization", "shadow_market": "civilization",
    "sunflower_fields": "civilization", "fog_village": "civilization", "rotten_market": "civilization",
    "library_of_echoes": "secret", "mirror_hall": "secret", "portal_nexus": "secret",
    "void_gate": "secret", "heart_of_mist": "secret", "clockwork_city": "secret", "dragon_peak": "secret",
    "forgotten_library": "secret", "spirit_grove": "secret", "shadow_chasm": "secret",
    "gilded_cathedral": "secret", "echo_caves": "secret",
}

POI_TEMPLATES = {
    "fishing_village": [
        {"poi_type": "shop", "name": "Рыбацкий склад", "description": "Здесь можно купить снаряжение."},
        {"poi_type": "quest_giver", "name": "Старый рыбак", "description": "Он знает многое."},
    ],
    "market_square": [
        {"poi_type": "shop", "name": "Торговые палатки", "description": "Товары со всего мира."},
        {"poi_type": "quest_giver", "name": "Торговец", "description": "Он шепчет о сделках."},
    ],
    "temple_of_shadows": [
        {"poi_type": "altar", "name": "Алтарь теней", "description": "Приноси жертвы."},
        {"poi_type": "quest_giver", "name": "Жрец", "description": "Он служит теням."},
    ],
    "library_of_echoes": [
        {"poi_type": "quest_giver", "name": "Библиотекарь", "description": "Хранитель знаний."},
    ],
    "obsidian_tower": [
        {"poi_type": "shop", "name": "Лавка мага", "description": "Магические товары."},
    ],
    "clockwork_city": [
        {"poi_type": "shop", "name": "Механическая лавка", "description": "Шестерёнки и штуки."},
        {"poi_type": "quest_giver", "name": "Инженер", "description": "Он строит невозможное."},
    ],
    "dragon_peak": [
        {"poi_type": "altar", "name": "Гнездо дракона", "description": "Здесь пахнет серой."},
    ],
}


def _gen_uuid():
    return str(uuid.uuid4())


async def seed():
    await init_db()
    async for db in get_db():

        result = await db.execute(text("SELECT COUNT(*) FROM continents"))
        cont_count = result.scalar()
        if cont_count == 0:
            db.add(ContinentModel(
                id=CONTINENT_ID,
                name="Mistlands",
                description="Земли, окутанные вечным туманом. Здесь время течёт иначе.",
                x=0, y=0,
            ))
            for reg in REGIONS.values():
                db.add(RegionModel(
                    id=reg["id"],
                    name=reg["name"],
                    continent_id=CONTINENT_ID,
                    x=reg["x"], y=reg["y"],
                ))
            await db.commit()
            print(f"   🌍 Континентов: 1, регионов: {len(REGIONS)}")

        result = await db.execute(text("SELECT COUNT(*) FROM locations"))
        loc_count = result.scalar()
        if loc_count == 0:
            locations = [
                {
                    "location_id": "dark_forest", "name": "Тёмный лес", "x": 0, "y": 0,
                    "description": "Деревья так плотно, что свет с трудом пробивается сквозь кроны. Корни деревьев шевелятся, словно живые. В воздухе — запах гнили и чего-то сладкого.\n\nЗдесь ты очнулся. Запомни это место.",
                    "discovered": True, "discovered_by": 1,
                    "connections": ["riverbank", "ancient_ruins", "wolf_den", "dark_harbour", "witch_swamp", "abandoned_camp"],
                    "is_secret": False, "required_karma": 0,
                    "danger_level": 70, "food_supply": 40, "tree_density": 90,
                    "magic_level": 60, "creature_count": 12, "population": 0, "wealth": 10,
                },
                {
                    "location_id": "riverbank", "name": "Берег реки", "x": 1, "y": 0,
                    "description": "Река течёт медленно, почти беззвучно. Вода чёрная, как ночь. На противоположном берегу — что-то блестит.\n\nРыбак говорит, что в этой реке водятся существа, которых лучше не видеть.",
                    "connections": ["dark_forest", "fishing_village", "underwater_cave", "dark_harbour", "abandoned_camp"],
                    "danger_level": 35, "food_supply": 65, "tree_density": 40,
                    "magic_level": 25, "creature_count": 6, "population": 3, "wealth": 25,
                },
                {
                    "location_id": "ancient_ruins", "name": "Древние руины", "x": 0, "y": 1,
                    "description": "Колонны, покрытые мхом, возвышаются над землёй. Между ними — каменные плиты с невиданными символами. Каждый символ слабо светится в темноте.\n\nЗдесь царит тишина. Но ты чувствуешь — за тобой наблюдают.",
                    "connections": ["dark_forest", "library_of_echoes", "obsidian_tower", "crystal_cave", "ash_fields", "portal_nexus"],
                    "danger_level": 45, "food_supply": 15, "tree_density": 20,
                    "magic_level": 70, "creature_count": 4, "population": 0, "wealth": 20,
                },
                {
                    "location_id": "wolf_den", "name": "Логово волков", "x": -1, "y": 1,
                    "description": "Пахнет кровью и мокрой шерстью. Кости разбросаны по полу. Глаза светятся в темноте — десятки пар.\n\nВожак наблюдает. Он решит — друг ты или пища.",
                    "connections": ["dark_forest", "blood_meadow"],
                    "danger_level": 85, "food_supply": 30, "tree_density": 60,
                    "magic_level": 5, "creature_count": 15, "population": 0, "wealth": 5,
                },
                {
                    "location_id": "fishing_village", "name": "Рыбацкая деревня", "x": 2, "y": 0,
                    "description": "Три хижины у воды. Старик с крючком сидит на пристани. Он не смотрит на тебя, но говорит: «Знаю, зачем ты пришёл. Все приходят за тем же.»\n\nЗдесь можно отдохнуть и купить снаряжение.",
                    "connections": ["riverbank", "market_square"],
                    "danger_level": 15, "food_supply": 80, "tree_density": 25,
                    "magic_level": 5, "creature_count": 2, "population": 12, "wealth": 40,
                },
                {
                    "location_id": "market_square", "name": "Торговая площадь", "x": 2, "y": 1,
                    "description": "Палатки с товарами, которых ты никогда не видел. Кристаллы, зелья, свёртки с непонятным содержимым.\n\nТорговец шепчет: «У меня есть то, что тебе нужно. Но сначала — докажи, что стоишь.»",
                    "connections": ["fishing_village", "temple_of_shadows", "shadow_market"],
                    "danger_level": 10, "food_supply": 70, "tree_density": 5,
                    "magic_level": 15, "creature_count": 0, "population": 25, "wealth": 80,
                },
                {
                    "location_id": "library_of_echoes", "name": "Библиотека эхов", "x": 1, "y": 2,
                    "description": "Стеллажи уходят ввысь, теряясь во тьме. Книги здесь — живые. Они шепчут, когда ты проходишь мимо. Некоторые — кричат.\n\nОдна книга открыта на странице: «Тот, кто читает — становится прочитанным.»",
                    "connections": ["ancient_ruins", "mirror_hall"],
                    "danger_level": 25, "food_supply": 5, "tree_density": 0,
                    "magic_level": 80, "creature_count": 2, "population": 3, "wealth": 35,
                },
                {
                    "location_id": "obsidian_tower", "name": "Обсидиановая башня", "x": 0, "y": 2,
                    "description": "Башня из чёрного стекла. Она не отражает свет — поглощает его. На каждом этаже — ловушки и загадки.\n\nВерхний этаж закрыт. Говорят, там живёт Хранитель.",
                    "connections": ["ancient_ruins", "tower_summit"], "required_karma": 5,
                    "danger_level": 75, "food_supply": 0, "tree_density": 0,
                    "magic_level": 65, "creature_count": 4, "population": 1, "wealth": 50,
                },
                {
                    "location_id": "blood_meadow", "name": "Кровавый луг", "x": -1, "y": 2,
                    "description": "Трава здесь красная. Не от заката — от чего-то другого. В центре луга — дерево, лишённое коры. На нём — следы когтей.\n\nВоздух тяжёлый. Ты слышишь сердцебиение. Не своё.",
                    "connections": ["wolf_den", "white_forest", "witch_swamp", "forgotten_graveyard"],
                    "danger_level": 80, "food_supply": 10, "tree_density": 15,
                    "magic_level": 75, "creature_count": 6, "population": 0, "wealth": 5,
                },
                {
                    "location_id": "white_forest", "name": "Белый лес", "x": -1, "y": 3,
                    "description": "Деревья белые, как кости. Листьев нет. Снег — зимой и летом. Здесь холодно. Не от температуры — от чего-то внутри.\n\nЭто место помнит что-то страшное. И не хочет, чтобы ты знал что.",
                    "connections": ["blood_meadow", "frozen_lake", "forgotten_graveyard", "ash_fields", "enchanted_grove"],
                    "danger_level": 65, "food_supply": 20, "tree_density": 70,
                    "magic_level": 55, "creature_count": 5, "population": 0, "wealth": 10,
                },
                {
                    "location_id": "underwater_cave", "name": "Подводная пещера", "x": 2, "y": -1,
                    "description": "Ты нырнул. Вода тёплая — слишком тёплая. На дне — руины, похожие на древние руины на поверхности.\n\nЧто-то движется в темноте. Оно большое.",
                    "connections": ["riverbank", "sunken_throne", "crystal_cave"],
                    "danger_level": 55, "food_supply": 35, "tree_density": 0,
                    "magic_level": 50, "creature_count": 3, "population": 0, "wealth": 15,
                },
                {
                    "location_id": "temple_of_shadows", "name": "Храм теней", "x": 3, "y": 1,
                    "description": "Колонны из чёрного мрамора. Между ними — статуи без лиц. В центре — алтарь, на котором лежит нож.\n\nГолос: «Принеси жертву. И получи то, что ищешь.»",
                    "connections": ["market_square", "void_gate", "shadow_market"],
                    "danger_level": 40, "food_supply": 5, "tree_density": 0,
                    "magic_level": 70, "creature_count": 3, "population": 5, "wealth": 60,
                },
                {
                    "location_id": "mirror_hall", "name": "Зеркальный зал", "x": 2, "y": 2,
                    "description": "Зеркала повсюду. Но отражения — не твои. Они двигаются, когда ты стоишь на месте. Улыбаются.\n\nОдно зеркало показывает что-то знакомое. Ты помнишь это место... или нет?",
                    "connections": ["library_of_echoes"], "is_secret": True, "required_karma": 10,
                    "danger_level": 50, "food_supply": 0, "tree_density": 0,
                    "magic_level": 90, "creature_count": 1, "population": 0, "wealth": 40,
                },
                {
                    "location_id": "tower_summit", "name": "Вершина башни", "x": 0, "y": 3,
                    "description": "Отсюда видно весь MIST. Туман стелется ниже. На вершине — камень с вырезанным символом: 👁\n\nХранитель ждал тебя. Давно.",
                    "connections": ["obsidian_tower"], "required_karma": 10,
                    "danger_level": 90, "food_supply": 0, "tree_density": 0,
                    "magic_level": 85, "creature_count": 1, "population": 0, "wealth": 70,
                },
                {
                    "location_id": "frozen_lake", "name": "Замёрзшее озеро", "x": -1, "y": 4,
                    "description": "Озеро покрыто льдом, но подо льдом — что-то двигается. На середине — трещина. Из неё — свет.\n\nЕсли прислушаться, можно услышать голоса. Мёртвых.",
                    "connections": ["white_forest", "heart_of_mist"],
                    "danger_level": 60, "food_supply": 15, "tree_density": 5,
                    "magic_level": 60, "creature_count": 2, "population": 0, "wealth": 10,
                },
                {
                    "location_id": "sunken_throne", "name": "Затонутый трон", "x": 3, "y": -1,
                    "description": "На дне озера — трон из кораллов. На нём — скелет в короне. В руке скелета — кольцо.\n\nКороль мёртвых. Но его власть — нет.",
                    "connections": ["underwater_cave"], "is_secret": True, "required_karma": 15,
                    "danger_level": 70, "food_supply": 20, "tree_density": 0,
                    "magic_level": 75, "creature_count": 1, "population": 0, "wealth": 80,
                },
                {
                    "location_id": "void_gate", "name": "Врата Пустоты", "x": 4, "y": 1,
                    "description": "Два столба из чёрного камня. Между ними — пустота. Абсолютная. Ты смотришь в неё — и она смотрит в тебя.\n\nЗа вратами — конец. Или начало.",
                    "connections": ["temple_of_shadows", "heart_of_mist", "portal_nexus"], "required_karma": 20,
                    "danger_level": 95, "food_supply": 0, "tree_density": 0,
                    "magic_level": 100, "creature_count": 2, "population": 0, "wealth": 30,
                },
                {
                    "location_id": "heart_of_mist", "name": "Сердце MIST", "x": 0, "y": 5,
                    "description": "Ты здесь. Ты всегда был здесь.\n\nТуман отступает. На мгновение ты видишь — тысячи лиц. Тех, кто был до тебя. Тех, кто будет после.\n\nMIST — это не место. MIST — это ты.",
                    "connections": ["frozen_lake", "void_gate", "portal_nexus"], "is_secret": True, "required_karma": 30,
                    "danger_level": 98, "food_supply": 0, "tree_density": 0,
                    "magic_level": 100, "creature_count": 0, "population": 0, "wealth": 100,
                },
                {
                    "location_id": "witch_swamp", "name": "Топи ведьмы", "x": -2, "y": 2,
                    "description": "Болото дышит. Пузыри лопаются на поверхности, выпуская зловонный газ. Среди мглы — силуэт хижины на куриных ножках.\n\nВедьма здесь. Она знает твоё имя.",
                    "connections": ["dark_forest", "blood_meadow", "forgotten_graveyard", "enchanted_grove"],
                    "danger_level": 55, "food_supply": 25, "tree_density": 30,
                    "magic_level": 65, "creature_count": 8, "population": 1, "wealth": 15,
                },
                {
                    "location_id": "forgotten_graveyard", "name": "Забытое кладбище", "x": -2, "y": 3,
                    "description": "Надгробия покосились. Имена стёрты. Земля здесь мягкая — слишком мягкая. Из-под камней торчат кости.\n\nСтраж не спит. Он ждёт.",
                    "connections": ["witch_swamp", "white_forest", "dark_harbour"],
                    "danger_level": 70, "food_supply": 5, "tree_density": 10,
                    "magic_level": 70, "creature_count": 7, "population": 0, "wealth": 10,
                },
                {
                    "location_id": "crystal_cave", "name": "Хрустальная пещера", "x": 1, "y": 1,
                    "description": "Стены пещеры покрыты кристаллами. Они светятся изнутри — синим, фиолетовым, белым. Свет мерцает, как живой.\n\nКристаллы звенят, когда ты проходишь мимо. Они поют.",
                    "connections": ["ancient_ruins", "underwater_cave", "ash_fields", "abandoned_mine"], "required_karma": 5,
                    "danger_level": 50, "food_supply": 10, "tree_density": 0,
                    "magic_level": 80, "creature_count": 4, "population": 2, "wealth": 45,
                },
                {
                    "location_id": "dark_harbour", "name": "Тёмная гавань", "x": 0, "y": -1,
                    "description": "Причал, поросший мхом. Корабль стоит на якоре — но экипажа нет. Только чёрные паруса колышутся на ветру.\n\nКонтрабандисты говорят, что отсюда уплывают в другие миры.",
                    "connections": ["dark_forest", "forgotten_graveyard", "riverbank"],
                    "danger_level": 45, "food_supply": 30, "tree_density": 5,
                    "magic_level": 35, "creature_count": 4, "population": 5, "wealth": 50,
                },
                {
                    "location_id": "ash_fields", "name": "Пепельные поля", "x": 0, "y": 4,
                    "description": "Земля серая, как пепел. Трава не растёт. Воздух тяжёлый, горячий. Из трещин в земле сочится пар.\n\nЗдесь когда-то был город. Теперь — только пепел и воспоминания.",
                    "connections": ["white_forest", "crystal_cave", "ancient_ruins", "abandoned_mine"], "required_karma": 5,
                    "danger_level": 60, "food_supply": 5, "tree_density": 0,
                    "magic_level": 45, "creature_count": 5, "population": 0, "wealth": 15,
                },
                {
                    "location_id": "shadow_market", "name": "Теневой рынок", "x": 3, "y": 2,
                    "description": "Палатки из чёрной ткани. Продавцы в масках. Товары, которые нельзя найти больше нигде.\n\nТорговец шепчет: «Золото не нужно. Принеси мне кое-что... интересное.»",
                    "connections": ["market_square", "temple_of_shadows"], "required_karma": 10,
                    "danger_level": 20, "food_supply": 10, "tree_density": 0,
                    "magic_level": 40, "creature_count": 0, "population": 15, "wealth": 90,
                },
                {
                    "location_id": "abandoned_mine", "name": "Заброшенная шахта", "x": 0, "y": 5,
                    "description": "Рельсы заржавели. Вагонетки стоят на месте. Из глубины — стук киркомолота. Но работников нет.\n\nШахта помнит тех, кто спустился и не вернулся.",
                    "connections": ["crystal_cave", "ash_fields"], "required_karma": 3,
                    "danger_level": 55, "food_supply": 5, "tree_density": 5,
                    "magic_level": 30, "creature_count": 6, "population": 0, "wealth": 25,
                },
                {
                    "location_id": "enchanted_grove", "name": "Зачарованная роща", "x": -2, "y": 4,
                    "description": "Деревья здесь светятся. Листья — из света. Корни переплетаются, образуя узоры.\n\nВ центре — дерево, внутри которого что-то пульсирует.",
                    "connections": ["white_forest", "witch_swamp"], "required_karma": 8,
                    "danger_level": 30, "food_supply": 40, "tree_density": 85,
                    "magic_level": 90, "creature_count": 3, "population": 2, "wealth": 20,
                },
                {
                    "location_id": "abandoned_camp", "name": "Покинутый лагерь", "x": 1, "y": -1,
                    "description": "Костёр ещё тлеет. Палатка порвана. На земле — следы. Много следов.\n\nКто-то был здесь недавно. И ушёл... быстро.",
                    "connections": ["dark_forest", "riverbank"],
                    "danger_level": 40, "food_supply": 35, "tree_density": 45,
                    "magic_level": 10, "creature_count": 3, "population": 0, "wealth": 15,
                },
                {
                    "location_id": "portal_nexus", "name": "Узел порталов", "x": 0, "y": 6,
                    "description": "Четыре арки из разного камня. В каждой — вихрь. Каждый портал ведёт в разное место.\n\nЗдесь время течёт иначе. Слишком иначе.",
                    "connections": ["ancient_ruins", "void_gate", "heart_of_mist"], "is_secret": True, "required_karma": 25,
                    "danger_level": 85, "food_supply": 0, "tree_density": 0,
                    "magic_level": 100, "creature_count": 2, "population": 0, "wealth": 50,
                },
                # ══════════════════════════════════════════════
                #  25 НОВЫХ ЛОКАЦИЙ
                # ══════════════════════════════════════════════
                {
                    "location_id": "misty_bay", "name": "Туманная бухта", "x": 2, "y": -1,
                    "description": "Бухта, скрытая вечным туманом. Вода здесь чёрная, как ночь. На берегу — обломки кораблей.",
                    "connections": ["dark_harbour", "riverbank", "shipwreck_beach"],
                    "danger_level": 40, "food_supply": 50, "tree_density": 10,
                    "magic_level": 30, "creature_count": 4, "population": 2, "wealth": 20,
                },
                {
                    "location_id": "shipwreck_beach", "name": "Пляж кораблекрушений", "x": 3, "y": -1,
                    "description": "Песок усыпан обломками кораблей. Среди досок — сундуки с сокровищами. И кости.",
                    "connections": ["misty_bay", "dark_harbour"],
                    "danger_level": 50, "food_supply": 30, "tree_density": 5,
                    "magic_level": 15, "creature_count": 6, "population": 0, "wealth": 40,
                },
                {
                    "location_id": "clockwork_city", "name": "Шестерёнчатый город", "x": -1, "y": 2,
                    "description": "Город из шестерёнок и пружин. Зубчатые колёса вращаются сами. Здесь пахнет маслом и медью.",
                    "connections": ["ancient_ruins", "portal_nexus", "dragon_peak"],
                    "is_secret": True, "required_karma": 15,
                    "danger_level": 30, "food_supply": 40, "tree_density": 0,
                    "magic_level": 80, "creature_count": 3, "population": 5, "wealth": 70,
                },
                {
                    "location_id": "dragon_peak", "name": "Драконья вершина", "x": -2, "y": 1,
                    "description": "Вершина горы, где гнездится дракон. Земля обожжёна. Воздух дрожит от жара.",
                    "connections": ["obsidian_tower", "clockwork_city"],
                    "is_secret": True, "required_karma": 20,
                    "danger_level": 95, "food_supply": 5, "tree_density": 0,
                    "magic_level": 90, "creature_count": 1, "population": 0, "wealth": 100,
                },
                {
                    "location_id": "forgotten_library", "name": "Забытая библиотека", "x": 1, "y": 1,
                    "description": "Библиотека, которую забыли даже эхи. Книги здесь пылятся веками. Но некоторые — шевелятся.",
                    "connections": ["library_of_echoes", "mirror_hall"],
                    "danger_level": 25, "food_supply": 10, "tree_density": 0,
                    "magic_level": 60, "creature_count": 2, "population": 1, "wealth": 50,
                },
                {
                    "location_id": "crystal_lake", "name": "Хрустальное озеро", "x": 0, "y": -1,
                    "description": "Озеро с кристально чистой водой. На дне — хрустали. Но кто-то следит за тобой.",
                    "connections": ["riverbank", "frozen_lake", "enchanted_grove"],
                    "danger_level": 35, "food_supply": 60, "tree_density": 30,
                    "magic_level": 40, "creature_count": 3, "population": 0, "wealth": 25,
                },
                {
                    "location_id": "bone_desert", "name": "Костяная пустыня", "x": -1, "y": -1,
                    "description": "Пустыня из костей. Черепа усеивают песок. Ветер воет среди рёбер гигантов.",
                    "connections": ["ash_fields", "blood_meadow"],
                    "danger_level": 70, "food_supply": 5, "tree_density": 0,
                    "magic_level": 20, "creature_count": 8, "population": 0, "wealth": 15,
                },
                {
                    "location_id": "spirit_grove", "name": "Роща духов", "x": 1, "y": 2,
                    "description": "Деревья здесь светятся голубым. Между ними — призрачные фигуры. Они танцуют.",
                    "connections": ["enchanted_grove", "white_forest"],
                    "danger_level": 45, "food_supply": 20, "tree_density": 80,
                    "magic_level": 75, "creature_count": 5, "population": 3, "wealth": 30,
                },
                {
                    "location_id": "iron_mine", "name": "Железная шахта", "x": -2, "y": 0,
                    "description": "Шахта, полная железной руды. Здесь работают шахтёры. И кое-что ещё.",
                    "connections": ["abandoned_mine", "ash_fields"],
                    "danger_level": 55, "food_supply": 15, "tree_density": 0,
                    "magic_level": 10, "creature_count": 7, "population": 4, "wealth": 45,
                },
                {
                    "location_id": "moonlight_clearing", "name": "Лунная поляна", "x": 2, "y": 1,
                    "description": "Поляна, освещённая лунным светом. Даже днём здесь мерцает луна.",
                    "connections": ["white_forest", "enchanted_grove", "forgotten_graveyard"],
                    "danger_level": 20, "food_supply": 45, "tree_density": 50,
                    "magic_level": 50, "creature_count": 2, "population": 1, "wealth": 20,
                },
                {
                    "location_id": "storm_cliffs", "name": "Штормовые утёсы", "x": 3, "y": 0,
                    "description": "Утёсы, омываемые штормами. Волны бьются о скалы. Здесь стоят маяки.",
                    "connections": ["dark_harbour", "misty_bay"],
                    "danger_level": 60, "food_supply": 20, "tree_density": 0,
                    "magic_level": 25, "creature_count": 4, "population": 1, "wealth": 15,
                },
                {
                    "location_id": "ancient_battlefield", "name": "Древнее поле битвы", "x": -1, "y": 0,
                    "description": "Здесь когда-то сражались армии. Кости до сих пор лежат в строю. Оружие ржавеет.",
                    "connections": ["blood_meadow", "bone_desert", "wolf_den"],
                    "danger_level": 65, "food_supply": 10, "tree_density": 10,
                    "magic_level": 35, "creature_count": 10, "population": 0, "wealth": 30,
                },
                {
                    "location_id": "fog_village", "name": "Туманная деревня", "x": 0, "y": 2,
                    "description": "Деревня, скрытая в тумане. Жители не видят солнца. Они ждут.",
                    "connections": ["witch_swamp", "forgotten_graveyard", "spirit_grove"],
                    "danger_level": 30, "food_supply": 35, "tree_density": 40,
                    "magic_level": 45, "creature_count": 3, "population": 8, "wealth": 20,
                },
                {
                    "location_id": "shadow_chasm", "name": "Теневая пропасть", "x": -2, "y": 2,
                    "description": "Пропасть, из которой льётся тьма. Никто не видел дна. Некоторые спускались.",
                    "connections": ["void_gate", "iron_mine"],
                    "is_secret": True, "required_karma": 20,
                    "danger_level": 80, "food_supply": 0, "tree_density": 0,
                    "magic_level": 85, "creature_count": 6, "population": 0, "wealth": 10,
                },
                {
                    "location_id": "sunflower_fields", "name": "Поля подсолнухов", "x": 1, "y": 0,
                    "description": "Поля, усеянные подсолнухами. Они поворачиваются за тобой. Всегда.",
                    "connections": ["fishing_village", "market_square", "moonlight_clearing"],
                    "danger_level": 10, "food_supply": 70, "tree_density": 20,
                    "magic_level": 15, "creature_count": 1, "population": 5, "wealth": 35,
                },
                {
                    "location_id": "rusty_docks", "name": "Ржавые дocks", "x": 2, "y": -2,
                    "description": "Дocks, покрытые ржавчиной. Корабли гниют. Рыба не берёт наживку.",
                    "connections": ["dark_harbour", "misty_bay"],
                    "danger_level": 45, "food_supply": 25, "tree_density": 0,
                    "magic_level": 10, "creature_count": 5, "population": 2, "wealth": 20,
                },
                {
                    "location_id": "thornwood", "name": "Шиповниковый лес", "x": -1, "y": 1,
                    "description": "Лес, где деревья — шипы. Они царапают. Они помнят каждого, кто вошёл.",
                    "connections": ["dark_forest", "witch_swamp", "blood_meadow"],
                    "danger_level": 55, "food_supply": 15, "tree_density": 95,
                    "magic_level": 30, "creature_count": 8, "population": 0, "wealth": 5,
                },
                {
                    "location_id": "echo_caves", "name": "Пещеры эхов", "x": 0, "y": 0,
                    "description": "Пещеры, где каждый звук повторяется бесконечно. Ты слышишь прошлое.",
                    "connections": ["ancient_ruins", "crystal_cave", "forgotten_library"],
                    "danger_level": 40, "food_supply": 10, "tree_density": 0,
                    "magic_level": 55, "creature_count": 4, "population": 0, "wealth": 15,
                },
                {
                    "location_id": "ember_swamp", "name": "Угольное болото", "x": 2, "y": 0,
                    "description": "Болото, где вода тёплая. Из грязи торчат угли. Здесь пахнет гарью.",
                    "connections": ["witch_swamp", "ash_fields", "riverbank"],
                    "danger_level": 50, "food_supply": 20, "tree_density": 30,
                    "magic_level": 25, "creature_count": 6, "population": 0, "wealth": 10,
                },
                {
                    "location_id": "starfall_valley", "name": "Долина падших звёзд", "x": -2, "y": -1,
                    "description": "Долина, где падают звёзды. Кратеры светятся. Здесь магия сильнее.",
                    "connections": ["bone_desert", "ancient_battlefield"],
                    "is_secret": True, "required_karma": 10,
                    "danger_level": 55, "food_supply": 15, "tree_density": 20,
                    "magic_level": 95, "creature_count": 3, "population": 0, "wealth": 60,
                },
                {
                    "location_id": "frost_hollow", "name": "Морозная лощина", "x": 0, "y": -2,
                    "description": "Лощина, где всегда зима. Деревья покрыты инеем. Воздух режет лёгкие.",
                    "connections": ["frozen_lake", "white_forest", "crystal_lake"],
                    "danger_level": 45, "food_supply": 25, "tree_density": 60,
                    "magic_level": 35, "creature_count": 5, "population": 0, "wealth": 10,
                },
                {
                    "location_id": "gilded_cathedral", "name": "Золочёный собор", "x": 1, "y": 3,
                    "description": "Собор, покрытый золотом. Он стоит пустой. Но двери открыты.",
                    "connections": ["temple_of_shadows", "forgotten_library"],
                    "is_secret": True, "required_karma": 25,
                    "danger_level": 35, "food_supply": 5, "tree_density": 0,
                    "magic_level": 70, "creature_count": 2, "population": 1, "wealth": 90,
                },
                {
                    "location_id": "whispering_shore", "name": "Шепчущий берег", "x": 3, "y": 1,
                    "description": "Берег, где волны шепчут. Они говорят имена. Имена тех, кто утонул.",
                    "connections": ["storm_cliffs", "shipwreck_beach", "misty_bay"],
                    "danger_level": 55, "food_supply": 15, "tree_density": 0,
                    "magic_level": 40, "creature_count": 4, "population": 0, "wealth": 20,
                },
                {
                    "location_id": "rotten_market", "name": "Тухлый рынок", "x": -2, "y": 1,
                    "description": "Рынок, где продают не товары, а тайны. Здесь пахнет гнилью и деньгами.",
                    "connections": ["shadow_market", "iron_mine", "rotten_market"],
                    "danger_level": 40, "food_supply": 10, "tree_density": 0,
                    "magic_level": 20, "creature_count": 3, "population": 6, "wealth": 55,
                },
            ]

            for loc in locations:
                region_key = LOCATION_REGIONS.get(loc["location_id"], "dark_forest")
                region_id = REGIONS[region_key]["id"]
                loc_id = _gen_uuid()
                db.add(LocationModel(
                    id=loc_id,
                    location_id=loc["location_id"],
                    name=loc["name"],
                    description=loc["description"],
                    region_id=region_id,
                    x=loc.get("x", 0),
                    y=loc.get("y", 0),
                    discovered=loc.get("discovered", False),
                    discovered_by=loc.get("discovered_by"),
                    connections=loc["connections"],
                    is_secret=loc.get("is_secret", False),
                    required_karma=loc.get("required_karma", 0),
                    danger_level=loc.get("danger_level", 30),
                    food_supply=loc.get("food_supply", 50),
                    tree_density=loc.get("tree_density", 50),
                    magic_level=loc.get("magic_level", 10),
                    creature_count=loc.get("creature_count", 5),
                    population=loc.get("population", 0),
                    wealth=loc.get("wealth", 30),
                ))
                pois = POI_TEMPLATES.get(loc["location_id"], [])
                for poi in pois:
                    db.add(POIModel(
                        id=_gen_uuid(),
                        location_id=loc_id,
                        poi_type=poi["poi_type"],
                        name=poi["name"],
                        description=poi.get("description", ""),
                    ))
            await db.commit()
            print(f"   📍 Локаций: {len(locations)}")

        # ══════════════════════════════════════════════
        #  СУЩЕСТВА
        # ══════════════════════════════════════════════

        creatures = [
            {
                "creature_id": "wolf_alpha",
                "name": "Альфа-волк",
                "description": "Огромный волк с глазами цвета угля. Он — вожак. Убей его — и стадо признает тебя.",
                "location": "wolf_den",
                "disposition": "hostile",
                "hp": 80, "max_hp": 80,
                "attack": 14, "defense": 5,
                "xp_reward": 40,
                "loot_table": [
                    {"item_id": "wolf_fang", "chance": 0.8, "qty": 2},
                    {"item_id": "alpha_pelt", "chance": 0.4, "qty": 1},
                    {"item_id": "bloodstone", "chance": 0.15, "qty": 1},
                ],
            },
            {
                "creature_id": "wolf_pack",
                "name": "Волк",
                "description": "Обычный волк. Но в MIST ничего не бывает обычным.",
                "location": "wolf_den",
                "disposition": "hostile",
                "hp": 40, "max_hp": 40,
                "attack": 8, "defense": 3,
                "xp_reward": 20,
                "loot_table": [
                    {"item_id": "wolf_fang", "chance": 0.6, "qty": 1},
                    {"item_id": "wolf_pelt", "chance": 0.5, "qty": 1},
                ],
            },
            {
                "creature_id": "shadow_stalker",
                "name": "Тень-охотник",
                "description": "Существо из тьмы. Оно не имеет формы, но имеет когти.",
                "location": "dark_forest",
                "disposition": "hostile",
                "hp": 60, "max_hp": 60,
                "attack": 12, "defense": 7,
                "xp_reward": 35,
                "loot_table": [
                    {"item_id": "shadow_essence", "chance": 0.7, "qty": 1},
                    {"item_id": "dark_shard", "chance": 0.3, "qty": 1},
                ],
            },
            {
                "creature_id": "river_serpent",
                "name": "Речной змей",
                "description": "Длинное чёрное тело извивается в воде. Глаза — два жёлтых огонька.",
                "location": "riverbank",
                "disposition": "hostile",
                "hp": 70, "max_hp": 70,
                "attack": 10, "defense": 4,
                "xp_reward": 30,
                "loot_table": [
                    {"item_id": "serpent_scale", "chance": 0.7, "qty": 2},
                    {"item_id": "river_pearl", "chance": 0.2, "qty": 1},
                ],
            },
            {
                "creature_id": "elder_fisherman",
                "name": "Старый рыбак",
                "description": "Старик с лицом, испещрённым морщинами. Он знает многое. Может и слишком многое.",
                "location": "fishing_village",
                "disposition": "friendly",
                "hp": 30, "max_hp": 30,
                "attack": 3, "defense": 2,
                "xp_reward": 10,
                "loot_table": [],
            },
            {
                "creature_id": "echo_wraith",
                "name": "Призрак эха",
                "description": "Остатки чьей-то памяти. Оно повторяет твои слова, но говорит то, что ты думаешь.",
                "location": "library_of_echoes",
                "disposition": "neutral",
                "hp": 45, "max_hp": 45,
                "attack": 9, "defense": 6,
                "xp_reward": 25,
                "loot_table": [
                    {"item_id": "echo_crystal", "chance": 0.5, "qty": 1},
                    {"item_id": "forgotten_page", "chance": 0.3, "qty": 1},
                ],
            },
            {
                "creature_id": "gargoyle",
                "name": "Гаргулья",
                "description": "Каменное создание, ожившее на стене башни. Оно защищает то, что внутри.",
                "location": "obsidian_tower",
                "disposition": "hostile",
                "hp": 90, "max_hp": 90,
                "attack": 16, "defense": 12,
                "xp_reward": 50,
                "loot_table": [
                    {"item_id": "gargoyle_eye", "chance": 0.4, "qty": 1},
                    {"item_id": "obsidian_shard", "chance": 0.6, "qty": 2},
                ],
            },
            {
                "creature_id": "blood_tree",
                "name": "Кровавое дерево",
                "description": "Дерево, лишённое коры. Из его ствола сочится красная жидкость. Оно чувствует боль.",
                "location": "blood_meadow",
                "disposition": "hostile",
                "hp": 120, "max_hp": 120,
                "attack": 20, "defense": 15,
                "xp_reward": 60,
                "loot_table": [
                    {"item_id": "blood_wood", "chance": 0.7, "qty": 1},
                    {"item_id": "living_bark", "chance": 0.3, "qty": 1},
                ],
            },
            {
                "creature_id": "frost_spirit",
                "name": "Дух мороза",
                "description": "Существо изо льда. Оно не двигается — оно замораживает.",
                "location": "white_forest",
                "disposition": "hostile",
                "hp": 55, "max_hp": 55,
                "attack": 11, "defense": 8,
                "xp_reward": 30,
                "loot_table": [
                    {"item_id": "frost_shard", "chance": 0.6, "qty": 1},
                    {"item_id": "frozen_tear", "chance": 0.25, "qty": 1},
                ],
            },
            {
                "creature_id": "mirror_copy",
                "name": "Отражение",
                "description": "Твоё собственное отражение. Но оно улыбается. Ты — нет.",
                "location": "mirror_hall",
                "disposition": "hostile",
                "hp": 100, "max_hp": 100,
                "attack": 15, "defense": 10,
                "xp_reward": 45,
                "loot_table": [
                    {"item_id": "mirror_fragment", "chance": 0.5, "qty": 1},
                    {"item_id": "stolen_memory", "chance": 0.3, "qty": 1},
                ],
            },
            {
                "creature_id": "the_keeper",
                "name": "Хранитель",
                "description": "Существо в мантии. Его лицо — пустота. Он стоит на вершине башни и ждёт.",
                "location": "tower_summit",
                "disposition": "neutral",
                "hp": 200, "max_hp": 200,
                "attack": 25, "defense": 18,
                "xp_reward": 100,
                "loot_table": [
                    {"item_id": "keeper_key", "chance": 0.5, "qty": 1},
                    {"item_id": "void_shard", "chance": 0.3, "qty": 1},
                    {"item_id": "legendary_essence", "chance": 0.1, "qty": 1},
                ],
            },
            {
                "creature_id": "dead_king",
                "name": "Король мёртвых",
                "description": "Скелет в короне. Его кольцо — ключ ко всем тайнам.",
                "location": "sunken_throne",
                "disposition": "hostile",
                "hp": 150, "max_hp": 150,
                "attack": 22, "defense": 14,
                "xp_reward": 80,
                "loot_table": [
                    {"item_id": "dead_king_ring", "chance": 0.4, "qty": 1},
                    {"item_id": "crown_shard", "chance": 0.6, "qty": 1},
                ],
            },
            {
                "creature_id": "void_walker",
                "name": "Странник пустоты",
                "description": "Существо из врата. Оно не от мира сего.",
                "location": "void_gate",
                "disposition": "hostile",
                "hp": 180, "max_hp": 180,
                "attack": 28, "defense": 20,
                "xp_reward": 120,
                "loot_table": [
                    {"item_id": "void_crystal", "chance": 0.4, "qty": 1},
                    {"item_id": "essence_of_nothing", "chance": 0.2, "qty": 1},
                ],
            },
            # ═══ НОВЫЕ СУЩЕСТВА ═══
            {
                "creature_id": "swamp_witch",
                "name": "Ведьма болот",
                "description": "Старуха с глазами цвета болотной жижи. Она торгует secrets за memories.",
                "location": "witch_swamp",
                "disposition": "neutral",
                "hp": 60, "max_hp": 60,
                "attack": 12, "defense": 8,
                "xp_reward": 30,
                "loot_table": [
                    {"item_id": "witch_brew", "chance": 0.6, "qty": 1},
                    {"item_id": "swamp_root", "chance": 0.5, "qty": 2},
                ],
            },
            {
                "creature_id": "bogey",
                "name": "Болотная тварь",
                "description": "Мерзкое слизкое создание. Оно тянет ноги в трясину.",
                "location": "witch_swamp",
                "disposition": "hostile",
                "hp": 55, "max_hp": 55,
                "attack": 10, "defense": 6,
                "xp_reward": 25,
                "loot_table": [
                    {"item_id": "swamp_slime", "chance": 0.7, "qty": 1},
                    {"item_id": "bogey_eye", "chance": 0.3, "qty": 1},
                ],
            },
            {
                "creature_id": "grave_sentinel",
                "name": "Страж кладбища",
                "description": "Скелет в ржавых доспехах. Он охраняет то, что давно мертво.",
                "location": "forgotten_graveyard",
                "disposition": "neutral",
                "hp": 70, "max_hp": 70,
                "attack": 14, "defense": 10,
                "xp_reward": 35,
                "loot_table": [
                    {"item_id": "rusted_armour", "chance": 0.4, "qty": 1},
                    {"item_id": "grave_dust", "chance": 0.6, "qty": 2},
                ],
            },
            {
                "creature_id": "crystal_golem",
                "name": "Кристальный голем",
                "description": "Гигант из кристаллов. Он двигается медленно, но бьёт страшно.",
                "location": "crystal_cave",
                "disposition": "hostile",
                "hp": 110, "max_hp": 110,
                "attack": 18, "defense": 14,
                "xp_reward": 55,
                "loot_table": [
                    {"item_id": "crystal_core", "chance": 0.4, "qty": 1},
                    {"item_id": "prism_shard", "chance": 0.6, "qty": 2},
                ],
            },
            {
                "creature_id": "harbour_ghost",
                "name": "Призрак гавани",
                "description": "Призрак капитана. Он ищет свой корабль. Но забыл, как управлять.",
                "location": "dark_harbour",
                "disposition": "hostile",
                "hp": 65, "max_hp": 65,
                "attack": 13, "defense": 9,
                "xp_reward": 35,
                "loot_table": [
                    {"item_id": "ghost_essence", "chance": 0.5, "qty": 1},
                    {"item_id": "torn_map", "chance": 0.3, "qty": 1},
                ],
            },
            {
                "creature_id": "ash_wraith",
                "name": "Пепельный призрак",
                "description": "Существо из пепла. Оно горячее. Оно голодное.",
                "location": "ash_fields",
                "disposition": "hostile",
                "hp": 80, "max_hp": 80,
                "attack": 16, "defense": 11,
                "xp_reward": 40,
                "loot_table": [
                    {"item_id": "ash_essence", "chance": 0.5, "qty": 1},
                    {"item_id": "burnt_relic", "chance": 0.25, "qty": 1},
                ],
            },
            {
                "creature_id": "skeleton_mage",
                "name": "Скелет-маг",
                "description": "Скелет в мантии. Его руки светятся. Он помнит заклинания.",
                "location": "forgotten_graveyard",
                "disposition": "hostile",
                "hp": 50, "max_hp": 50,
                "attack": 15, "defense": 5,
                "xp_reward": 30,
                "loot_table": [
                    {"item_id": "arcane_dust", "chance": 0.6, "qty": 1},
                    {"item_id": "forgotten_page", "chance": 0.2, "qty": 1},
                ],
            },
            {
                "creature_id": "kraken_tentacle",
                "name": "Щупальце кракена",
                "description": "Огромное щупальце из тьмы реки. Оно тянет на дно.",
                "location": "dark_harbour",
                "disposition": "hostile",
                "hp": 90, "max_hp": 90,
                "attack": 17, "defense": 12,
                "xp_reward": 45,
                "loot_table": [
                    {"item_id": "kraken_ink", "chance": 0.5, "qty": 1},
                    {"item_id": "tentacle_strip", "chance": 0.4, "qty": 2},
                ],
            },
            # ═══ НОВЫЕ СУЩЕСТВА v2 ═══
            {
                "creature_id": "mine_crawler",
                "name": "Шахтёр-ползун",
                "description": "Существо, мутировавшее от кристаллов. Оно ползёт по стенам шахты.",
                "location": "abandoned_mine",
                "disposition": "hostile",
                "hp": 85, "max_hp": 85,
                "attack": 15, "defense": 10,
                "xp_reward": 40,
                "loot_table": [
                    {"item_id": "raw_crystal", "chance": 0.6, "qty": 2},
                    {"item_id": "mine_pickaxe", "chance": 0.2, "qty": 1},
                ],
            },
            {
                "creature_id": "crystal_spider",
                "name": "Кристальный паук",
                "description": "Паук из кристалла. Его яд — светящаяся жидкость.",
                "location": "abandoned_mine",
                "disposition": "hostile",
                "hp": 60, "max_hp": 60,
                "attack": 13, "defense": 8,
                "xp_reward": 30,
                "loot_table": [
                    {"item_id": "crystal_thread", "chance": 0.5, "qty": 1},
                    {"item_id": "spider_venom", "chance": 0.3, "qty": 1},
                ],
            },
            {
                "creature_id": "grove_sprite",
                "name": "Дух рощи",
                "description": "Крошечное светящееся существо. Оно хранит древние знания.",
                "location": "enchanted_grove",
                "disposition": "neutral",
                "hp": 35, "max_hp": 35,
                "attack": 6, "defense": 12,
                "xp_reward": 20,
                "loot_table": [
                    {"item_id": "grove_essence", "chance": 0.6, "qty": 1},
                    {"item_id": "light_leaf", "chance": 0.4, "qty": 2},
                ],
            },
            {
                "creature_id": "ancient_warden",
                "name": "Древний страж",
                "description": "Статуя, ожившая из камня и мха. Она защищает рощу.",
                "location": "enchanted_grove",
                "disposition": "hostile",
                "hp": 130, "max_hp": 130,
                "attack": 20, "defense": 16,
                "xp_reward": 65,
                "loot_table": [
                    {"item_id": "warden_heart", "chance": 0.3, "qty": 1},
                    {"item_id": "mossy_stone", "chance": 0.6, "qty": 2},
                ],
            },
            {
                "creature_id": "camp_stalker",
                "name": "Лагерный вор",
                "description": "Существо, подражающее голосам. Оно заманивает в ловушку.",
                "location": "abandoned_camp",
                "disposition": "hostile",
                "hp": 50, "max_hp": 50,
                "attack": 11, "defense": 6,
                "xp_reward": 25,
                "loot_table": [
                    {"item_id": "torn_cloth", "chance": 0.5, "qty": 1},
                    {"item_id": "old_coin", "chance": 0.4, "qty": 2},
                ],
            },
            {
                "creature_id": "portal_phantom",
                "name": "Фантом портала",
                "description": "Существо из вихря порталов. Оно существует во всех мирах одновременно.",
                "location": "portal_nexus",
                "disposition": "hostile",
                "hp": 160, "max_hp": 160,
                "attack": 24, "defense": 18,
                "xp_reward": 90,
                "loot_table": [
                    {"item_id": "void_crystal", "chance": 0.3, "qty": 1},
                    {"item_id": "portal_shard", "chance": 0.4, "qty": 1},
                    {"item_id": "legendary_essence", "chance": 0.08, "qty": 1},
                ],
            },
        ]

        result = await db.execute(text("SELECT COUNT(*) FROM creatures"))
        cre_count = result.scalar()
        if cre_count == 0:
            for c in creatures:
                db.add(CreatureModel(
                    creature_id=c["creature_id"],
                    name=c["name"],
                    description=c["description"],
                    location=c["location"],
                    disposition=c["disposition"],
                    hp=c["hp"],
                    max_hp=c["max_hp"],
                    attack=c["attack"],
                    defense=c["defense"],
                    xp_reward=c["xp_reward"],
                    loot_table=json.dumps(c["loot_table"]),
                ))
            await db.commit()
            print(f"   🐾 Существ: {len(creatures)}")

        # ══════════════════════════════════════════════
        #  NPC
        # ══════════════════════════════════════════════

        npcs = [
            {
                "npc_id": "elder_fisherman",
                "name": "Старый рыбак",
                "description": "Старик с лицом, испещрённым морщинами. Он знает многое. Может и слишком многое.",
                "npc_type": "elder",
                "location_str": "fishing_village",
                "disposition": "friendly",
                "dialogue_tree": {
                    "idle": {"greeting": "«Приветствую, странник. Ты пришёл не за рыбой. Я знаю.»"},
                },
            },
            {
                "npc_id": "merchant_shadow",
                "name": "Торговец тенями",
                "description": "Человек в чёрном капюшоне. Его лицо скрыто. Он торгует всем — за правильную цену.",
                "npc_type": "merchant",
                "location_str": "shadow_market",
                "disposition": "neutral",
                "dialogue_tree": {
                    "idle": {"greeting": "«У меня есть то, что тебе нужно. Но сначала — покажи золото.»"},
                    "trading": {"greeting": "«Выбирай. Но не трогай лишнего.»"},
                },
            },
            {
                "npc_id": "guard_temple",
                "name": "Страж храма",
                "description": "Высокий воин в чёрных доспехах. Он не говорит. Он наблюдает.",
                "npc_type": "guard",
                "location_str": "temple_of_shadows",
                "disposition": "neutral",
                "dialogue_tree": {
                    "idle": {"greeting": "«Проходи. Но не нарушай покой мёртвых.»"},
                },
            },
            {
                "npc_id": "healer_grove",
                "name": "Целительница рощи",
                "description": "Женщина с зелёными глазами. Она шепчет деревьям, и они отвечают.",
                "npc_type": "healer",
                "location_str": "enchanted_grove",
                "disposition": "friendly",
                "dialogue_tree": {
                    "idle": {"greeting": "«Я помогу тебе. Но сначала — расскажи, что тебя привело в MIST.»"},
                },
            },
            {
                "npc_id": "bartender_dark",
                "name": "Кабатчик",
                "description": "Полный мужчина с бородой. Он наливает напитки, которые ты не заказывал.",
                "npc_type": "bartender",
                "location_str": "dark_harbour",
                "disposition": "neutral",
                "dialogue_tree": {
                    "idle": {"greeting": "«Что пьёшь? У меня есть кое-что... интересное.»"},
                },
            },
            {
                "npc_id": "shady_informant",
                "name": "Осведомитель",
                "description": "Человек без имени. Он знает всё. Но за каждую информацию — цена.",
                "npc_type": "shady",
                "location_str": "market_square",
                "disposition": "neutral",
                "dialogue_tree": {
                    "idle": {"greeting": "«Хочешь знать что-то? Заплати. Или уходи.»"},
                },
            },
            {
                "npc_id": "quest_scholar",
                "name": "Учёный",
                "description": "Старик с очками. Он ищет древние знания. И ему нужна помощь.",
                "npc_type": "quest_giver",
                "location_str": "library_of_echoes",
                "disposition": "friendly",
                "dialogue_tree": {
                    "idle": {"greeting": "«А, посетитель! Ты не читаешь книги. Ты — книга. Позволь мне прочитать тебя.»"},
                },
            },
            {
                "npc_id": "merchant_crystal",
                "name": "Кристальный торговец",
                "description": "Человек, чьё тело светится кристаллами. Он продаёт свет и тьму.",
                "npc_type": "merchant",
                "location_str": "crystal_cave",
                "disposition": "neutral",
                "dialogue_tree": {
                    "idle": {"greeting": "«Кристаллы звенят. Они говорят, что ты ищешь силу.»"},
                },
            },
        ]

        result = await db.execute(text("SELECT COUNT(*) FROM npcs"))
        npc_count = result.scalar()
        if npc_count == 0:
            for npc in npcs:
                db.add(NPCModel(
                    npc_id=npc["npc_id"],
                    name=npc["name"],
                    description=npc["description"],
                    npc_type=npc["npc_type"],
                    location_str=npc["location_str"],
                    disposition=npc["disposition"],
                    dialogue_tree=npc["dialogue_tree"],
                ))
            await db.commit()
            print(f"   NPC: {len(npcs)}")

        # ══════════════════════════════════════════════
        #  ПРЕДМЕТЫ
        # ══════════════════════════════════════════════

        items = [
            {"item_id": "wolf_fang", "name": "Клык волка", "description": "Острый, как бритва. Используется в ритуалах.", "rarity": "common", "is_usable": False},
            {"item_id": "wolf_pelt", "name": "Шкура волка", "description": "Тёплая. Но от неё пахнет страхом.", "rarity": "common", "is_usable": False},
            {"item_id": "alpha_pelt", "name": "Шкура альфы", "description": "Шкура вожака. Она помнит каждый бой.", "rarity": "rare", "is_usable": False},
            {"item_id": "bloodstone", "name": "Кровавый камень", "description": "Камень, пульсирующий красным. Он горячий.", "rarity": "rare", "is_usable": False},
            {"item_id": "shadow_essence", "name": "Суть тени", "description": "Жидкость, которая не отражает свет.", "rarity": "rare", "is_usable": True, "use_effect": {"heal": 30}},
            {"item_id": "dark_shard", "name": "Осколок тьмы", "description": "Чёрный осколок. Он поглощает звук.", "rarity": "rare", "is_usable": False},
            {"item_id": "serpent_scale", "name": "Чешуя змея", "description": "Чешуя, как броня. Но она гибкая.", "rarity": "common", "is_usable": False},
            {"item_id": "river_pearl", "name": "Речная жемчужина", "description": "Жемчужина из чёрной воды. Она светится в темноте.", "rarity": "rare", "is_usable": True, "use_effect": {"light": True}},
            {"item_id": "echo_crystal", "name": "Кристалл эха", "description": "Внутри — чей-то голос. Он повторяет твои мысли.", "rarity": "rare", "is_usable": True, "use_effect": {"reveal_secret": True}},
            {"item_id": "forgotten_page", "name": "Забытая страница", "description": "Страница из книги, которой не существует.", "rarity": "rare", "is_usable": False},
            {"item_id": "gargoyle_eye", "name": "Глаз гаргульи", "description": "Каменный глаз. Он видит сквозь стены.", "rarity": "epic", "is_usable": True, "use_effect": {"vision": True}},
            {"item_id": "obsidian_shard", "name": "Осколок обсидиана", "description": "Чёрное стекло. Острым, как скальпель.", "rarity": "common", "is_usable": False},
            {"item_id": "blood_wood", "name": "Кровавое дерево", "description": "Древесина, которая помнит боль.", "rarity": "rare", "is_usable": False},
            {"item_id": "living_bark", "name": "Живая кора", "description": "Кора, которая дышит. Она растёт.", "rarity": "rare", "is_usable": False},
            {"item_id": "frost_shard", "name": "Осколок мороза", "description": "Лёд, который не тает. Он замораживает всё.", "rarity": "common", "is_usable": True, "use_effect": {"damage": 15}},
            {"item_id": "frozen_tear", "name": "Замёрзшая слеза", "description": "Слеза кого-то, кто давно мёртв.", "rarity": "rare", "is_usable": True, "use_effect": {"heal": 50}},
            {"item_id": "mirror_fragment", "name": "Осколок зеркала", "description": "Осколок, который отражает не тебя, а то, кем ты мог бы быть.", "rarity": "epic", "is_usable": False},
            {"item_id": "stolen_memory", "name": "Украденная память", "description": "Чьи-то воспоминания. Ты видишь чужую жизнь.", "rarity": "epic", "is_usable": True, "use_effect": {"xp": 50}},
            {"item_id": "keeper_key", "name": "Ключ хранителя", "description": "Ключ, который открывает всё. И закрывает тоже.", "rarity": "legendary", "is_usable": False},
            {"item_id": "void_shard", "name": "Осколок пустоты", "description": "Ничто, оформленное в материю.", "rarity": "legendary", "is_usable": False},
            {"item_id": "legendary_essence", "name": "Легендарная суть", "description": "Квинтэссенция MIST. Её мало кто видел.", "rarity": "legendary", "is_usable": True, "use_effect": {"level_up": True}},
            {"item_id": "dead_king_ring", "name": "Кольцо мёртвого короля", "description": "Кольцо, которое даёт власть над мёртвыми. Временно.", "rarity": "legendary", "is_usable": True, "use_effect": {"resurrect": True}},
            {"item_id": "crown_shard", "name": "Осколок короны", "description": "Часть короны, которая правила миром.", "rarity": "epic", "is_usable": False},
            {"item_id": "void_crystal", "name": "Кристалл пустоты", "description": "Кристалл, внутри — вакуум. Он поглощает всё.", "rarity": "legendary", "is_usable": False},
            {"item_id": "essence_of_nothing", "name": "Суть ничто", "description": "Это... ничего. Но это что-то.", "rarity": "legendary", "is_usable": False},
            {"item_id": "healing_herb", "name": "Целебная трава", "description": "Растёт у реки. Восстанавливает 20 HP.", "rarity": "common", "is_usable": True, "use_effect": {"heal": 20}},
            {"item_id": "mysterious_map", "name": "Загадочная карта", "description": "Карта, которая меняется. Каждый раз — новая.", "rarity": "rare", "is_usable": False},
            {"item_id": "old_coin", "name": "Старая монета", "description": "Монета с профилем того, кого никто не помнит.", "rarity": "common", "is_usable": False},
            # ═══ НОВЫЕ ПРЕДМЕТЫ ═══
            {"item_id": "witch_brew", "name": "Зелье ведьмы", "description": "Пузырящаяся жидкость зелёного цвета. Пахнет... интересно.", "rarity": "rare", "is_usable": True, "use_effect": {"heal": 40, "xp": 15}},
            {"item_id": "swamp_root", "name": "Болотный корень", "description": "Корень, который дышит. Его можно жевать.", "rarity": "common", "is_usable": True, "use_effect": {"heal": 15}},
            {"item_id": "swamp_slime", "name": "Болотная слизь", "description": "Липкая масса. Она двигается.", "rarity": "common", "is_usable": False},
            {"item_id": "bogey_eye", "name": "Глаз болотной твари", "description": "Красный, влажный. Он ещё моргает.", "rarity": "rare", "is_usable": False},
            {"item_id": "rusted_armour", "name": "Ржавые доспехи", "description": "Доспехи стража. Ещё держатся.", "rarity": "rare", "is_usable": False},
            {"item_id": "grave_dust", "name": "Прах могил", "description": "Пепел, который не тает на ветру.", "rarity": "common", "is_usable": False},
            {"item_id": "crystal_core", "name": "Кристальное ядро", "description": "Ядро голема. Пульсирует энергией.", "rarity": "epic", "is_usable": True, "use_effect": {"xp": 40, "level_up": True}},
            {"item_id": "prism_shard", "name": "Осколок призмы", "description": "Кристалл, разделяющий свет на цвета.", "rarity": "rare", "is_usable": False},
            {"item_id": "ghost_essence", "name": "Суть призрака", "description": "Полупрозрачная жидкость. Она холодная.", "rarity": "rare", "is_usable": True, "use_effect": {"heal": 35}},
            {"item_id": "torn_map", "name": "Рваная карта", "description": "Часть карты. Показывает путь... куда-то.", "rarity": "rare", "is_usable": False},
            {"item_id": "ash_essence", "name": "Пепельная суть", "description": "Горячий пепел. Он горит изнутри.", "rarity": "rare", "is_usable": True, "use_effect": {"damage": 20}},
            {"item_id": "burnt_relic", "name": "Оплавленный реликт", "description": "Артефакт, оплавленный жаром. Ещё теплый.", "rarity": "epic", "is_usable": False},
            {"item_id": "arcane_dust", "name": "Магическая пыль", "description": "Пыль, которая светится. Искры магии.", "rarity": "common", "is_usable": False},
            {"item_id": "kraken_ink", "name": "Чернила кракена", "description": "Чернила кракена. Ими можно писать... или отравлять.", "rarity": "rare", "is_usable": True, "use_effect": {"heal": 25}},
            {"item_id": "tentacle_strip", "name": "Полоска щупальца", "description": "Жёсткая, как кожаный ремень. Но живая.", "rarity": "common", "is_usable": False},
            {"item_id": "enchanted_compass", "name": "Заколдованный компас", "description": "Стрелка указывает не на север, а на то, что ты ищешь.", "rarity": "epic", "is_usable": False},
            {"item_id": "soul_bottle", "name": "Бутылка с душой", "description": "Внутри — чей-то крик. Закрой горлышко.", "rarity": "legendary", "is_usable": True, "use_effect": {"heal": 80}},
            {"item_id": "gold_coin", "name": "Золотая монета", "description": "Валюта теневого рынка. Блестит даже в темноте.", "rarity": "common", "is_usable": False},
            # ═══ НОВЫЕ ПРЕДМЕТЫ v2 ═══
            {"item_id": "raw_crystal", "name": "Необработанный кристалл", "description": "Грубый кристалл из шахты. Нужна огранка.", "rarity": "common", "is_usable": False},
            {"item_id": "mine_pickaxe", "name": "Шахтёрская кирка", "description": "Ржавая, но крепкая. Открывает новые проходы.", "rarity": "rare", "is_usable": True, "use_effect": {"xp": 20, "gold": 15}},
            {"item_id": "crystal_thread", "name": "Кристальная нить", "description": "Прочнее стали. Светится в темноте.", "rarity": "rare", "is_usable": False},
            {"item_id": "spider_venom", "name": "Яд паука", "description": "Светящаяся жидкость. Её можно намазать на оружие.", "rarity": "rare", "is_usable": True, "use_effect": {"damage": 25}},
            {"item_id": "grove_essence", "name": "Суть рощи", "description": "Жидкий свет. Восстанавливает и очищает.", "rarity": "epic", "is_usable": True, "use_effect": {"heal": 60, "xp": 25}},
            {"item_id": "light_leaf", "name": "Светящийся лист", "description": "Лист из зачарованной рощи. Он никогда не вянет.", "rarity": "common", "is_usable": True, "use_effect": {"heal": 20}},
            {"item_id": "warden_heart", "name": "Сердце стража", "description": "Каменное сердце, пульсирующее зелёным. Оно помнит века.", "rarity": "epic", "is_usable": False},
            {"item_id": "mossy_stone", "name": "Мшистый камень", "description": "Камень, покрытый древним мхом. Он тёплый.", "rarity": "common", "is_usable": False},
            {"item_id": "torn_cloth", "name": "Рваная ткань", "description": "Кусок ткани из лагеря. На нём — следы когтей.", "rarity": "common", "is_usable": False},
            {"item_id": "portal_shard", "name": "Осколок портала", "description": "Фрагмент пространственного разлома. Он искрится.", "rarity": "legendary", "is_usable": False},
            {"item_id": "crystal_blade", "name": "Кристальный клинок", "description": "Клинок из кристалла. Он режет сам.", "rarity": "epic", "is_usable": True, "use_effect": {"damage": 35}},
            {"item_id": "grove_amulet", "name": "Амулет рощи", "description": "Амулет из светящегося дерева. Защищает от тьмы.", "rarity": "epic", "is_usable": True, "use_effect": {"heal": 70}},
        ]

        result = await db.execute(text("SELECT COUNT(*) FROM item_templates"))
        item_count = result.scalar()
        if item_count == 0:
            for item in items:
                use_effect = item.get("use_effect", {})
                db.add(ItemTemplateModel(
                    item_id=item["item_id"],
                    name=item["name"],
                    description=item["description"],
                    rarity=item["rarity"],
                    is_usable=item.get("is_usable", False),
                    use_effect=json.dumps(use_effect),
                ))
            await db.commit()
            print(f"   🏺 Предметов: {len(items)}")

        # ══════════════════════════════════════════════
        #  КВЕСТЫ
        # ══════════════════════════════════════════════

        quests = [
            # Цепочка 1: Волки
            {
                "quest_id": "q_start1",
                "name": "Пробуждение",
                "description": "Ты очнулся в тумане. Осмотрись и выживи.",
                "giver": "unknown",
                "location": "dark_forest",
                "objectives": [{"id": "visit_any", "type": "visit", "location": "riverbank", "target": 1, "description": "Доберись до берега реки"}],
                "rewards": {"xp": 15, "memories": 2, "gold": 5},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_wolf1",
                "name": "Волчий клык",
                "description": "Старый рыбак просит принести клык волка. Для ритуала.",
                "giver": "elder_fisherman",
                "location": "fishing_village",
                "objectives": [{"id": "kill_wolf", "type": "kill", "creature": "wolf_pack", "target": 3, "description": "Убить 3 волков"}],
                "rewards": {"xp": 30, "memories": 2, "karma": 2, "gold": 10, "items": [{"id": "healing_herb", "qty": 3}]},
                "is_active": True, "is_repeating": True,
            },
            {
                "quest_id": "q_wolf2",
                "name": "Вожак стаи",
                "description": "Альфа-волк угрожает деревне. Убей его.",
                "giver": "elder_fisherman",
                "location": "fishing_village",
                "objectives": [{"id": "kill_alpha", "type": "kill", "creature": "wolf_alpha", "target": 1, "description": "Убить альфа-волка"}],
                "rewards": {"xp": 60, "memories": 5, "karma": 5, "gold": 25, "items": [{"id": "alpha_pelt", "qty": 1}]},
                "is_active": True, "is_repeating": False,
            },
            # Цепочка 2: Древние руины
            {
                "quest_id": "q_ruins1",
                "name": "Символы прошлого",
                "description": "Исследуй древние руины. Прочитай символы.",
                "giver": "unknown",
                "location": "ancient_ruins",
                "objectives": [{"id": "visit_ruins", "type": "visit", "location": "ancient_ruins", "target": 1, "description": "Посетить древние руины"}],
                "rewards": {"xp": 20, "memories": 3, "gold": 5},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_ruins2",
                "name": "Голос книг",
                "description": "В библиотеке есть книга, которая говорит. Найди её.",
                "giver": "unknown",
                "location": "library_of_echoes",
                "objectives": [{"id": "visit_library", "type": "visit", "location": "library_of_echoes", "target": 1, "description": "Посетить библиотеку эхов"}],
                "rewards": {"xp": 30, "memories": 4, "gold": 8, "items": [{"id": "echo_crystal", "qty": 1}]},
                "is_active": True, "is_repeating": False,
            },
            # Цепочка 3: Башня
            {
                "quest_id": "q_tower1",
                "name": "Чёрная башня",
                "description": "Обсидиановая башня хранит секрет. Найди его.",
                "giver": "unknown",
                "location": "obsidian_tower",
                "objectives": [
                    {"id": "visit_tower", "type": "visit", "location": "obsidian_tower", "target": 1, "description": "Посетить башню"},
                    {"id": "kill_gargoyle", "type": "kill", "creature": "gargoyle", "target": 1, "description": "Победить гаргулью"}
                ],
                "rewards": {"xp": 70, "memories": 6, "karma": 3, "gold": 30},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_tower2",
                "name": "Вершина мира",
                "description": "Поднимись на вершину башни. Встреть Хранителя.",
                "giver": "unknown",
                "location": "tower_summit",
                "objectives": [{"id": "visit_summit", "type": "visit", "location": "tower_summit", "target": 1, "description": "Подняться на вершину"}],
                "rewards": {"xp": 100, "memories": 10, "karma": 10, "gold": 50, "items": [{"id": "keeper_key", "qty": 1}]},
                "is_active": True, "is_repeating": False,
            },
            # Цепочка 4: Теневой храм
            {
                "quest_id": "q_temple1",
                "name": "Жертва",
                "description": "В храме просят жертву. Принеси шкуру волка.",
                "giver": "unknown",
                "location": "temple_of_shadows",
                "objectives": [{"id": "visit_temple", "type": "visit", "location": "temple_of_shadows", "target": 1, "description": "Посетить храм теней"}],
                "rewards": {"xp": 40, "memories": 5, "karma": -3, "gold": 15},
                "is_active": True, "is_repeating": False,
            },
            # Цепочка 5: Белый лес
            {
                "quest_id": "q_white1",
                "name": "Холод внутри",
                "description": "Белый лес помнит что-то страшное. Узнай что.",
                "giver": "unknown",
                "location": "white_forest",
                "objectives": [{"id": "visit_white", "type": "visit", "location": "white_forest", "target": 1, "description": "Посетить белый лес"}],
                "rewards": {"xp": 30, "memories": 4, "gold": 10},
                "is_active": True, "is_repeating": False,
            },
            # Цепочка 6: Финал
            {
                "quest_id": "q_heart1",
                "name": "Сердце MIST",
                "description": "Найди путь к сердцу MIST. Пойми, что ты здесь делаешь.",
                "giver": "unknown",
                "location": "heart_of_mist",
                "objectives": [{"id": "visit_heart", "type": "visit", "location": "heart_of_mist", "target": 1, "description": "Добраться до сердца MIST"}],
                "rewards": {"xp": 200, "memories": 20, "karma": 15, "gold": 100, "items": [{"id": "legendary_essence", "qty": 1}]},
                "is_active": True, "is_repeating": False,
            },
            # Повторяющийся: Охота на теней
            {
                "quest_id": "q_hunt_shadows",
                "name": "Охотник теней",
                "description": "Тени нападают на деревню. Уничтожь их.",
                "giver": "elder_fisherman",
                "location": "fishing_village",
                "objectives": [{"id": "kill_shadow", "type": "kill", "creature": "shadow_stalker", "target": 2, "description": "Убить 2 теней-охотников"}],
                "rewards": {"xp": 40, "memories": 3, "karma": 2, "gold": 15},
                "is_active": True, "is_repeating": True,
            },
            # ═══ НОВЫЕ КВЕСТЫ ═══
            # Цепочка: Топи ведьмы
            {
                "quest_id": "q_witch1",
                "name": "Зелье для ведьмы",
                "description": "Ведуна просит принести болотный корень для зелья.",
                "giver": "swamp_witch",
                "location": "witch_swamp",
                "objectives": [
                    {"id": "collect_swamp_root", "type": "collect", "item": "swamp_root", "target": 3, "description": "Собрать 3 болотных корня"}
                ],
                "rewards": {"xp": 35, "memories": 4, "karma": 3, "gold": 12, "items": [{"id": "witch_brew", "qty": 2}]},
                "is_active": True, "is_repeating": True,
            },
            {
                "quest_id": "q_witch2",
                "name": "Тайна болот",
                "description": "Ведьма хочет знать, кто крадёт её зелья.",
                "giver": "swamp_witch",
                "location": "witch_swamp",
                "objectives": [
                    {"id": "kill_bogey", "type": "kill", "creature": "bogey", "target": 3, "description": "Убить 3 болотных тварей"}
                ],
                "rewards": {"xp": 50, "memories": 6, "karma": 4, "gold": 20, "items": [{"id": "enchanted_compass", "qty": 1}]},
                "is_active": True, "is_repeating": False,
            },
            # Цепочка: Кладбище
            {
                "quest_id": "q_grave1",
                "name": "Дозор мёртвых",
                "description": "Страж кладбища просит очистить могилы от нежити.",
                "giver": "grave_sentinel",
                "location": "forgotten_graveyard",
                "objectives": [
                    {"id": "kill_skeleton", "type": "kill", "creature": "skeleton_mage", "target": 3, "description": "Убить 3 скелетов-магов"}
                ],
                "rewards": {"xp": 45, "memories": 5, "karma": 5, "gold": 15, "items": [{"id": "grave_dust", "qty": 3}]},
                "is_active": True, "is_repeating": True,
            },
            {
                "quest_id": "q_grave2",
                "name": "Забытое имя",
                "description": "Страж ищет своё имя. Оно где-то здесь.",
                "giver": "grave_sentinel",
                "location": "forgotten_graveyard",
                "objectives": [
                    {"id": "visit_grave", "type": "visit", "location": "forgotten_graveyard", "target": 1, "description": "Осмотреть кладбище"}
                ],
                "rewards": {"xp": 30, "memories": 8, "karma": 3, "gold": 10},
                "is_active": True, "is_repeating": False,
            },
            # Цепочка: Кристальная пещера
            {
                "quest_id": "q_crystal1",
                "name": "Голос кристаллов",
                "description": "Кристаллы поют. Но один из них — кричит.",
                "giver": "unknown",
                "location": "crystal_cave",
                "objectives": [
                    {"id": "kill_golem", "type": "kill", "creature": "crystal_golem", "target": 1, "description": "Победить кристального голема"}
                ],
                "rewards": {"xp": 60, "memories": 7, "karma": 4, "gold": 25, "items": [{"id": "crystal_core", "qty": 1}]},
                "is_active": True, "is_repeating": False,
            },
            # Цепочка: Тёмная гавань
            {
                "quest_id": "q_harbour1",
                "name": "Потерянный корабль",
                "description": "Призрак капитана хочет вернуться на корабль. Но ему нужна карта.",
                "giver": "harbour_ghost",
                "location": "dark_harbour",
                "objectives": [
                    {"id": "collect_map", "type": "collect", "item": "torn_map", "target": 1, "description": "Найти рваную карту"}
                ],
                "rewards": {"xp": 45, "memories": 6, "karma": 4, "gold": 20, "items": [{"id": "gold_coin", "qty": 5}]},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_harbour2",
                "name": "Чёрные паруса",
                "description": "Кракен разорвал паруса. Нужны новые щупальца.",
                "giver": "unknown",
                "location": "dark_harbour",
                "objectives": [
                    {"id": "kill_kraken", "type": "kill", "creature": "kraken_tentacle", "target": 2, "description": "Убить 2 щупальца кракена"}
                ],
                "rewards": {"xp": 55, "memories": 5, "karma": 3, "gold": 20, "items": [{"id": "kraken_ink", "qty": 2}]},
                "is_active": True, "is_repeating": True,
            },
            # Цепочка: Пепельные поля
            {
                "quest_id": "q_ash1",
                "name": "Пепел городов",
                "description": "Среди пепла — оплавленные реликвии. Собери их.",
                "giver": "unknown",
                "location": "ash_fields",
                "objectives": [
                    {"id": "kill_ash_wraith", "type": "kill", "creature": "ash_wraith", "target": 2, "description": "Убить 2 пепельных призраков"},
                    {"id": "collect_relic", "type": "collect", "item": "burnt_relic", "target": 1, "description": "Найти оплавленный реликт"}
                ],
                "rewards": {"xp": 65, "memories": 8, "karma": 5, "gold": 35, "items": [{"id": "soul_bottle", "qty": 1}]},
                "is_active": True, "is_repeating": False,
            },
            # Цепочка: Теневой рынок
            {
                "quest_id": "q_market1",
                "name": "Теневой клиент",
                "description": "Торговец хочет редкий товар. Принеси ему кристалл эха.",
                "giver": "unknown",
                "location": "shadow_market",
                "objectives": [
                    {"id": "collect_echo", "type": "collect", "item": "echo_crystal", "target": 1, "description": "Принести кристалл эха"}
                ],
                "rewards": {"xp": 50, "memories": 5, "karma": 2, "gold": 25, "items": [{"id": "gold_coin", "qty": 8}]},
                "is_active": True, "is_repeating": True,
            },
            # ═══ НОВЫЕ КВЕСТЫ v2 ═══
            {
                "quest_id": "q_mine1",
                "name": "Шахтёрские тайны",
                "description": "Шахта полна кристаллов. Но и опасностей тоже.",
                "giver": "unknown",
                "location": "abandoned_mine",
                "objectives": [
                    {"id": "kill_crawler", "type": "kill", "creature": "mine_crawler", "target": 2, "description": "Убить 2 шахтёров-ползунов"},
                    {"id": "collect_crystal", "type": "collect", "item": "raw_crystal", "target": 3, "description": "Собрать 3 необработанных кристалла"}
                ],
                "rewards": {"xp": 55, "memories": 6, "karma": 3, "gold": 20, "items": [{"id": "mine_pickaxe", "qty": 1}]},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_mine2",
                "name": "Глубже",
                "description": "Пауки заполонили шахту. Уничтожь их.",
                "giver": "unknown",
                "location": "abandoned_mine",
                "objectives": [
                    {"id": "kill_spider", "type": "kill", "creature": "crystal_spider", "target": 3, "description": "Убить 3 кристальных пауков"}
                ],
                "rewards": {"xp": 45, "memories": 4, "karma": 2, "gold": 15, "items": [{"id": "crystal_thread", "qty": 2}]},
                "is_active": True, "is_repeating": True,
            },
            {
                "quest_id": "q_grove1",
                "name": "Голос рощи",
                "description": "Духи рощи просят защиты. Страж стал враждебным.",
                "giver": "grove_sprite",
                "location": "enchanted_grove",
                "objectives": [
                    {"id": "kill_warden", "type": "kill", "creature": "ancient_warden", "target": 1, "description": "Победить древнего стража"}
                ],
                "rewards": {"xp": 70, "memories": 8, "karma": 6, "gold": 30, "items": [{"id": "warden_heart", "qty": 1}]},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_grove2",
                "name": "Свет рощи",
                "description": "Собери светящиеся листья для амулета.",
                "giver": "grove_sprite",
                "location": "enchanted_grove",
                "objectives": [
                    {"id": "collect_leaf", "type": "collect", "item": "light_leaf", "target": 5, "description": "Собрать 5 светящихся листьев"}
                ],
                "rewards": {"xp": 40, "memories": 5, "karma": 4, "gold": 15, "items": [{"id": "grove_amulet", "qty": 1}]},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_camp1",
                "name": "Что случилось в лагере",
                "description": "Лагерь покинут. Но кто-то был здесь недавно.",
                "giver": "unknown",
                "location": "abandoned_camp",
                "objectives": [
                    {"id": "kill_stalker", "type": "kill", "creature": "camp_stalker", "target": 2, "description": "Убить 2 лагерных воров"}
                ],
                "rewards": {"xp": 35, "memories": 4, "karma": 2, "gold": 12},
                "is_active": True, "is_repeating": True,
            },
            {
                "quest_id": "q_camp2",
                "name": "Следы",
                "description": "Найди зацепки. Кто был в лагере?",
                "giver": "unknown",
                "location": "abandoned_camp",
                "objectives": [
                    {"id": "visit_camp", "type": "visit", "location": "abandoned_camp", "target": 1, "description": "Осмотреть лагерь"}
                ],
                "rewards": {"xp": 20, "memories": 5, "gold": 8, "items": [{"id": "mysterious_map", "qty": 1}]},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_portal1",
                "name": "Узел миров",
                "description": "Порталы ведут в другие миры. Но фантомы не пускают.",
                "giver": "unknown",
                "location": "portal_nexus",
                "objectives": [
                    {"id": "kill_phantom", "type": "kill", "creature": "portal_phantom", "target": 1, "description": "Победить фантома портала"}
                ],
                "rewards": {"xp": 100, "memories": 12, "karma": 8, "gold": 50, "items": [{"id": "portal_shard", "qty": 1}]},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_craft1",
                "name": "Мастер крафта",
                "description": "Научись создавать предметы. Скрафти что-нибудь.",
                "giver": "unknown",
                "location": "crystal_cave",
                "objectives": [
                    {"id": "craft_any", "type": "craft", "recipe": "any", "target": 1, "description": "Скрафти любой предмет"}
                ],
                "rewards": {"xp": 30, "memories": 3, "gold": 10},
                "is_active": True, "is_repeating": False,
            },
            # ══════════════════════════════════════════════
            #  20+ НОВЫХ КВЕСТОВ
            # ══════════════════════════════════════════════
            {
                "quest_id": "q_bay1", "name": "Туманная бухта",
                "description": "Бухта скрыта туманом. Найди источник тумана.",
                "giver": "elder_fisherman", "location": "misty_bay",
                "objectives": [{"id": "visit_bay", "type": "visit", "location": "misty_bay", "target": 1, "description": "Доберись до Туманной бухты"}],
                "rewards": {"xp": 25, "memories": 3, "gold": 15},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_wreck1", "name": "Кораблекрушение",
                "description": "На пляже — обломки корабля. Найди капитанский сундук.",
                "giver": "bartender_dark", "location": "shipwreck_beach",
                "objectives": [
                    {"id": "visit_wreck", "type": "visit", "location": "shipwreck_beach", "target": 1, "description": "Обыщи пляж"},
                    {"id": "kill_crawlers", "type": "kill", "creature": "camp_stalker", "target": 3, "description": "Прогони воров"},
                ],
                "rewards": {"xp": 35, "memories": 4, "gold": 25},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_clock1", "name": "Шестерёнки",
                "description": "Шестерёнчатый город движется без людей. Кто его создал?",
                "giver": "quest_scholar", "location": "clockwork_city",
                "objectives": [{"id": "visit_clock", "type": "visit", "location": "clockwork_city", "target": 1, "description": "Найди Шестерёнчатый город"}],
                "rewards": {"xp": 40, "memories": 5, "gold": 20},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_dragon1", "name": "Драконья вершина",
                "description": "На вершине горы — дракон. Или то, что от него осталось.",
                "giver": "quest_scholar", "location": "dragon_peak",
                "objectives": [
                    {"id": "visit_peak", "type": "visit", "location": "dragon_peak", "target": 1, "description": "Поднимись на Драконью вершину"},
                ],
                "rewards": {"xp": 80, "memories": 10, "gold": 50},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_lib1", "name": "Забытые знания",
                "description": "Библиотека, которую забыли даже эхи. Там есть ответы.",
                "giver": "quest_scholar", "location": "forgotten_library",
                "objectives": [{"id": "visit_lib", "type": "visit", "location": "forgotten_library", "target": 1, "description": "Найди Забытую библиотеку"}],
                "rewards": {"xp": 30, "memories": 5, "gold": 15},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_lake1", "name": "Хрустальное озеро",
                "description": "Озеро с кристально чистой водой. На дне — хрустали.",
                "giver": "healer_grove", "location": "crystal_lake",
                "objectives": [{"id": "visit_lake", "type": "visit", "location": "crystal_lake", "target": 1, "description": "Доберись до Хрустального озера"}],
                "rewards": {"xp": 20, "memories": 2, "gold": 10},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_bone1", "name": "Кости великанов",
                "description": "В пустыне — кости кого-то огромного. Что здесь умерло?",
                "giver": "shady_informant", "location": "bone_desert",
                "objectives": [
                    {"id": "visit_bone", "type": "visit", "location": "bone_desert", "target": 1, "description": "Исследуй Костяную пустыню"},
                    {"id": "kill_skeletons", "type": "kill", "creature": "skeleton_mage", "target": 5, "description": "Очисти пустыню от нежити"},
                ],
                "rewards": {"xp": 45, "memories": 5, "gold": 20},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_spirit1", "name": "Танцующие духи",
                "description": "В роще танцуют призраки. Они ищут покоя.",
                "giver": "healer_grove", "location": "spirit_grove",
                "objectives": [{"id": "visit_spirit", "type": "visit", "location": "spirit_grove", "target": 1, "description": "Войди в Рощу духов"}],
                "rewards": {"xp": 30, "memories": 4, "gold": 10},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_iron1", "name": "Железная жила",
                "description": "Шахтёры нашли железо. Но среди руды — кое-что странное.",
                "giver": "shady_informant", "location": "iron_mine",
                "objectives": [
                    {"id": "visit_iron", "type": "visit", "location": "iron_mine", "target": 1, "description": "Спустись в Железную шахту"},
                    {"id": "collect_ore", "type": "collect", "item": "raw_crystal", "target": 5, "description": "Собери железную руду"},
                ],
                "rewards": {"xp": 35, "memories": 3, "gold": 30},
                "is_active": True, "is_repeating": True,
            },
            {
                "quest_id": "q_moon1", "name": "Лунный свет",
                "description": "На поляне светит луна. Даже днём.",
                "giver": "healer_grove", "location": "moonlight_clearing",
                "objectives": [{"id": "visit_moon", "type": "visit", "location": "moonlight_clearing", "target": 1, "description": "Найди Лунную поляну"}],
                "rewards": {"xp": 20, "memories": 3, "gold": 10},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_storm1", "name": "Штормовые скалы",
                "description": "На утёсах — маяк. Он не горит. Почини его.",
                "giver": "bartender_dark", "location": "storm_cliffs",
                "objectives": [
                    {"id": "visit_storm", "type": "visit", "location": "storm_cliffs", "target": 1, "description": "Доберись до Штормовых утёсов"},
                ],
                "rewards": {"xp": 25, "memories": 2, "gold": 15},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_battle1", "name": "Поле битвы",
                "description": "Здесь сражались армии. Их кости до сих пор стоят в строю.",
                "giver": "shady_informant", "location": "ancient_battlefield",
                "objectives": [
                    {"id": "visit_battle", "type": "visit", "location": "ancient_battlefield", "target": 1, "description": "Обыщи Древнее поле битвы"},
                    {"id": "kill_dead", "type": "kill", "creature": "skeleton_mage", "target": 3, "description": "Успокой мёртвых воинов"},
                ],
                "rewards": {"xp": 40, "memories": 4, "gold": 20},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_fog1", "name": "Туманная деревня",
                "description": "Деревня в тумане. Жители ждут. Чего?",
                "giver": "elder_fisherman", "location": "fog_village",
                "objectives": [{"id": "visit_fog", "type": "visit", "location": "fog_village", "target": 1, "description": "Найди Туманную деревню"}],
                "rewards": {"xp": 25, "memories": 3, "gold": 10},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_shadow1", "name": "Теневая пропасть",
                "description": "Пропасть, из которой льётся тьма. Никто не видел дна.",
                "giver": "quest_scholar", "location": "shadow_chasm",
                "objectives": [{"id": "visit_shadow", "type": "visit", "location": "shadow_chasm", "target": 1, "description": "Найди Теневую пропасть"}],
                "rewards": {"xp": 50, "memories": 7, "gold": 25},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_flower1", "name": "Подсолнухи",
                "description": "Поля подсолнухов поворачиваются за тобой. Всегда.",
                "giver": "healer_grove", "location": "sunflower_fields",
                "objectives": [{"id": "visit_flower", "type": "visit", "location": "sunflower_fields", "target": 1, "description": "Побывай на Полях подсолнухов"}],
                "rewards": {"xp": 15, "memories": 2, "gold": 5},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_rusty1", "name": "Ржавые дocks",
                "description": "Дocks гниют. Корабли не приходят. Что случилось?",
                "giver": "bartender_dark", "location": "rusty_docks",
                "objectives": [{"id": "visit_rusty", "type": "visit", "location": "rusty_docks", "target": 1, "description": "Обыщи Ржавые дocks"}],
                "rewards": {"xp": 20, "memories": 2, "gold": 10},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_thorn1", "name": "Шипы",
                "description": "Лес из шипов. Он царапает. Он помнит.",
                "giver": "swamp_witch", "location": "thornwood",
                "objectives": [
                    {"id": "visit_thorn", "type": "visit", "location": "thornwood", "target": 1, "description": "Пройди через Шиповниковый лес"},
                    {"id": "kill_thorns", "type": "kill", "creature": "blood_tree", "target": 2, "description": "Убей Шиповник-деревья"},
                ],
                "rewards": {"xp": 35, "memories": 4, "gold": 15},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_echo1", "name": "Эхо прошлого",
                "description": "В пещерах — каждый звук повторяется. Ты слышишь прошлое.",
                "giver": "quest_scholar", "location": "echo_caves",
                "objectives": [{"id": "visit_echo", "type": "visit", "location": "echo_caves", "target": 1, "description": "Войди в Пещеры эхов"}],
                "rewards": {"xp": 30, "memories": 4, "gold": 15},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_ember1", "name": "Тлеющие болота",
                "description": "Болото тёплое. Из грязи торчат угли. Здесь пахнет гарью.",
                "giver": "swamp_witch", "location": "ember_swamp",
                "objectives": [{"id": "visit_ember", "type": "visit", "location": "ember_swamp", "target": 1, "description": "Исследуй Угольное болото"}],
                "rewards": {"xp": 25, "memories": 3, "gold": 10},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_star1", "name": "Падшие звёзды",
                "description": "В долине падают звёзды. Кратеры светятся. Здесь магия сильнее.",
                "giver": "quest_scholar", "location": "starfall_valley",
                "objectives": [{"id": "visit_star", "type": "visit", "location": "starfall_valley", "target": 1, "description": "Найди Долину падших звёзд"}],
                "rewards": {"xp": 45, "memories": 6, "gold": 30},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_frost1", "name": "Морозная лощина",
                "description": "Здесь всегда зима. Деревья покрыты инеем.",
                "giver": "healer_grove", "location": "frost_hollow",
                "objectives": [{"id": "visit_frost", "type": "visit", "location": "frost_hollow", "target": 1, "description": "Доберись до Морозной лощины"}],
                "rewards": {"xp": 25, "memories": 3, "gold": 10},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_cathedral1", "name": "Золочёный собор",
                "description": "Собор, покрытый золотом. Он стоит пустой. Но двери открыты.",
                "giver": "quest_scholar", "location": "gilded_cathedral",
                "objectives": [{"id": "visit_cathedral", "type": "visit", "location": "gilded_cathedral", "target": 1, "description": "Найди Золочёный собор"}],
                "rewards": {"xp": 55, "memories": 8, "gold": 40},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_whisper1", "name": "Шёпот волн",
                "description": "На берегу волны шепчут. Они говорят имена.",
                "giver": "bartender_dark", "location": "whispering_shore",
                "objectives": [{"id": "visit_whisper", "type": "visit", "location": "whispering_shore", "target": 1, "description": "Послушай Шепчущий берег"}],
                "rewards": {"xp": 25, "memories": 3, "gold": 10},
                "is_active": True, "is_repeating": False,
            },
            {
                "quest_id": "q_rotten1", "name": "Тухлый рынок",
                "description": "Рынок, где продают тайны. Здесь пахнет гнилью и деньгами.",
                "giver": "shady_informant", "location": "rotten_market",
                "objectives": [{"id": "visit_rotten", "type": "visit", "location": "rotten_market", "target": 1, "description": "Обыщи Тухлый рынок"}],
                "rewards": {"xp": 20, "memories": 2, "gold": 20},
                "is_active": True, "is_repeating": False,
            },
        ]

        result = await db.execute(text("SELECT COUNT(*) FROM quests"))
        q_count = result.scalar()
        if q_count == 0:
            for q in quests:
                db.add(QuestModel(
                    quest_id=q["quest_id"],
                    name=q["name"],
                    description=q["description"],
                    giver=q["giver"],
                    location=q["location"],
                    objectives=json.dumps(q["objectives"]),
                    rewards=json.dumps(q["rewards"]),
                    is_active=q["is_active"],
                    is_repeating=q["is_repeating"],
                ))
            await db.commit()
            print(f"   📜 Квестов: {len(quests)}")

        # ══════════════════════════════════════════════
        #  СЕКРЕТЫ
        # ══════════════════════════════════════════════

        secrets = [
            {
                "secret_id": "secret_first_blood",
                "secret_type": "achievement",
                "name": "Первая кровь",
                "description": "Ты убил своё первое существо. Мир запомнил это.",
                "trigger_condition": {"type": "action_count", "action": "combat_victory", "value": 1},
                "reward": {"memories": 3, "karma": 1},
            },
            {
                "secret_id": "secret_explorer",
                "secret_type": "achievement",
                "name": "Первопроходец",
                "description": "Ты открыл 5 локаций. Ты — исследователь.",
                "trigger_condition": {"type": "action_count", "action": "location_discover", "value": 5},
                "reward": {"memories": 10, "karma": 5},
            },
            {
                "secret_id": "secret_whisperer",
                "secret_type": "achievement",
                "name": "Тихоня",
                "description": "Ты слушал шёпот тумана 10 раз. Он начал тебе доверять.",
                "trigger_condition": {"type": "action_count", "action": "whisper", "value": 10},
                "reward": {"memories": 8, "karma": 3},
            },
            {
                "secret_id": "secret_wolf_friend",
                "secret_type": "achievement",
                "name": "Друг волков",
                "description": "Ты покормил волка. Он запомнил тебя.",
                "trigger_condition": {"type": "visit_location", "location": "wolf_den"},
                "reward": {"memories": 5, "karma": 5},
            },
            # ══════════════════════════════════════════════
            #  10+ НОВЫХ СЕКРЕТОВ
            # ══════════════════════════════════════════════
            {
                "secret_id": "secret_dragon_slayer", "secret_type": "achievement",
                "name": "Убийца драконов",
                "description": "Ты убил дракона. Мир запомнил это навсегда.",
                "trigger_condition": {"type": "action_count", "action": "combat_victory", "value": 50},
                "reward": {"memories": 20, "karma": 10},
            },
            {
                "secret_id": "secret_deep_diver", "secret_type": "achievement",
                "name": "Глубоководный",
                "description": "Ты спустился в Подводную пещеру. Ты не боишься глубины.",
                "trigger_condition": {"type": "visit_location", "location": "underwater_cave"},
                "reward": {"memories": 8, "karma": 3},
            },
            {
                "secret_id": "secret_void_walker", "secret_type": "achievement",
                "name": "Странник пустоты",
                "description": "Ты прошёл через Врата пустоты. Ты видел то, что не должно быть видно.",
                "trigger_condition": {"type": "visit_location", "location": "void_gate"},
                "reward": {"memories": 15, "karma": -5},
            },
            {
                "secret_id": "secret_heart_found", "secret_type": "achievement",
                "name": "Сердце MIST",
                "description": "Ты нашёл Сердце MIST. Оно бьётся. Для тебя.",
                "trigger_condition": {"type": "visit_location", "location": "heart_of_mist"},
                "reward": {"memories": 25, "karma": 10},
            },
            {
                "secret_id": "secret_master_crafter", "secret_type": "achievement",
                "name": "Мастер крафта",
                "description": "Ты создал 10 предметов. Руки помнят каждый.",
                "trigger_condition": {"type": "action_count", "action": "craft_completed", "value": 10},
                "reward": {"memories": 12, "karma": 5},
            },
            {
                "secret_id": "secret_guild_leader", "secret_type": "achievement",
                "name": "Лидер гильдии",
                "description": "Ты основал гильдию. Люди идут за тобой.",
                "trigger_condition": {"type": "action_count", "action": "guild_created", "value": 1},
                "reward": {"memories": 10, "karma": 5},
            },
            {
                "secret_id": "secret_pvp_champion", "secret_type": "achievement",
                "name": "Чемпион PvP",
                "description": "Ты победил 10 игроков на арене. Тебя боятся.",
                "trigger_condition": {"type": "action_count", "action": "pvp_win", "value": 10},
                "reward": {"memories": 15, "karma": 0},
            },
            {
                "secret_id": "secret_home_owner", "secret_type": "achievement",
                "name": "Домосед",
                "description": "Ты построил дом. У тебя есть крыша над головой.",
                "trigger_condition": {"type": "action_count", "action": "home_built", "value": 1},
                "reward": {"memories": 8, "karma": 3},
            },
            {
                "secret_id": "secret_night_walker", "secret_type": "achievement",
                "name": "Ночной странник",
                "description": "Ты путешествовал ночью 20 раз. Ты привык к темноте.",
                "trigger_condition": {"type": "action_count", "action": "movement_night", "value": 20},
                "reward": {"memories": 10, "karma": 2},
            },
            {
                "secret_id": "secret_secret_finder", "secret_type": "achievement",
                "name": "Охотник за тайнами",
                "description": "Ты нашёл 5 секретов. Ты знаешь то, что не должен знать.",
                "trigger_condition": {"type": "action_count", "action": "secret_found", "value": 5},
                "reward": {"memories": 20, "karma": 8},
            },
            {
                "secret_id": "secret_whisper_master", "secret_type": "achievement",
                "name": "Повелитель шёпотов",
                "description": "Ты слушал шёпот 50 раз. Туман доверяет тебе.",
                "trigger_condition": {"type": "action_count", "action": "whisper", "value": 50},
                "reward": {"memories": 25, "karma": 10},
            },
        ]

        result = await db.execute(text("SELECT COUNT(*) FROM secrets"))
        s_count = result.scalar()
        if s_count == 0:
            for s in secrets:
                db.add(SecretModel(
                    secret_id=s["secret_id"],
                    secret_type=s["secret_type"],
                    name=s["name"],
                    description=s["description"],
                    trigger_condition=json.dumps(s["trigger_condition"]),
                    reward=json.dumps(s["reward"]),
                ))
            await db.commit()
            print(f"   🔮 Секретов: {len(secrets)}")

        # ══════════════════════════════════════════════
        #  ПРЕДМЕТЫ НА ЗЕМЛЕ
        # ══════════════════════════════════════════════

        ground = [
            ("dark_forest", "healing_herb", 2),
            ("dark_forest", "wolf_fang", 1),
            ("riverbank", "healing_herb", 1),
            ("riverbank", "old_coin", 1),
            ("ancient_ruins", "old_coin", 2),
            ("ancient_ruins", "mysterious_map", 1),
            ("wolf_den", "wolf_pelt", 1),
            ("fishing_village", "healing_herb", 3),
            ("blood_meadow", "blood_wood", 1),
            ("white_forest", "frost_shard", 1),
            ("library_of_echoes", "forgotten_page", 1),
            ("obsidian_tower", "obsidian_shard", 1),
            # ═══ НОВЫЕ ПРЕДМЕТЫ НА ЗЕМЛЕ ═══
            ("witch_swamp", "swamp_root", 2),
            ("witch_swamp", "swamp_slime", 1),
            ("forgotten_graveyard", "grave_dust", 2),
            ("forgotten_graveyard", "arcane_dust", 1),
            ("crystal_cave", "prism_shard", 2),
            ("crystal_cave", "healing_herb", 1),
            ("dark_harbour", "tentacle_strip", 2),
            ("dark_harbour", "old_coin", 1),
            ("ash_fields", "ash_essence", 1),
            ("ash_fields", "grave_dust", 1),
            ("shadow_market", "gold_coin", 3),
            ("shadow_market", "old_coin", 2),
            # ═══ НОВЫЕ ПРЕДМЕТЫ НА ЗЕМЛЕ v2 ═══
            ("abandoned_mine", "raw_crystal", 3),
            ("abandoned_mine", "obsidian_shard", 1),
            ("enchanted_grove", "light_leaf", 2),
            ("enchanted_grove", "grove_essence", 1),
            ("abandoned_camp", "old_coin", 2),
            ("abandoned_camp", "healing_herb", 1),
            ("portal_nexus", "portal_shard", 1),
            ("portal_nexus", "void_crystal", 1),
        ]

        result = await db.execute(text("SELECT COUNT(*) FROM ground_items"))
        gi_count = result.scalar()
        if gi_count == 0:
            for loc_id, item_id, qty in ground:
                db.add(GroundItemModel(
                    location_id=loc_id,
                    item_id=item_id,
                    quantity=qty,
                ))
            await db.commit()
            print(f"   📦 Предметов на земле: {len(ground)}")

        # ══════════════════════════════════════════════
        #  ПРЕДМЕТЫ МАГАЗИНОВ
        # ══════════════════════════════════════════════

        shop_items = [
            # ═══ РЫБАЦКАЯ ДЕРЕВНЯ — базовые зелья ═══
            ("fishing_village", "healing_herb", 5, -1, 1, 0),
            ("fishing_village", "swamp_root", 8, -1, 1, 0),
            ("fishing_village", "wolf_fang", 10, -1, 1, 0),
            # ═══ ТОРГОВАЯ ПЛОЩАДЬ — оружие и броня ═══
            ("market_square", "obsidian_shard", 15, -1, 2, 0),
            ("market_square", "serpent_scale", 12, -1, 2, 0),
            ("market_square", "frost_shard", 18, -1, 3, 0),
            ("market_square", "shadow_essence", 25, 5, 3, 0),
            # ═══ ТЕНЕВОЙ РЫНОК — редкое ═══
            ("shadow_market", "echo_crystal", 40, 3, 5, 5),
            ("shadow_market", "gargoyle_eye", 60, 2, 7, 10),
            ("shadow_market", "mirror_fragment", 55, 2, 6, 8),
            ("shadow_market", "frozen_tear", 35, -1, 4, 3),
            ("shadow_market", "soul_bottle", 100, 1, 10, 15),
            # ═══ ХРАМ ТЕНЕЙ — тёмные предметы ═══
            ("temple_of_shadows", "dark_shard", 20, -1, 3, -5),
            ("temple_of_shadows", "bloodstone", 30, 5, 5, -3),
            ("temple_of_shadows", "arcane_dust", 8, -1, 1, 0),
            # ═══ ШАХТА — кристаллы ═══
            ("abandoned_mine", "raw_crystal", 10, -1, 2, 0),
            ("abandoned_mine", "crystal_thread", 22, 3, 4, 0),
            ("abandoned_mine", "spider_venom", 18, 4, 3, 0),
            # ═══ РЫБАЦКАЯ ДЕРЕВНЯ — обновление ═══
            ("fishing_village", "light_leaf", 12, -1, 2, 0),
        ]

        result = await db.execute(text("SELECT COUNT(*) FROM shop_items"))
        sh_count = result.scalar()
        if sh_count == 0:
            for shop_id, item_id, price, stock, req_level, req_karma in shop_items:
                db.add(ShopItemModel(
                    shop_id=shop_id,
                    item_id=item_id,
                    price=price,
                    stock=stock,
                    required_level=req_level,
                    required_karma=req_karma,
                ))
            await db.commit()
            print(f"   🛒 Предметов магазинов: {len(shop_items)}")

        # ══════════════════════════════════════════════
        #  РЕЦЕПТЫ КРАФТА
        # ══════════════════════════════════════════════

        crafting_recipes = [
            {
                "recipe_id": "craft_crystal_blade",
                "name": "Кристальный клинок",
                "description": "Слей кристаллы в острый клинок.",
                "result_item": "crystal_blade",
                "result_qty": 1,
                "ingredients": [
                    {"item_id": "raw_crystal", "qty": 3},
                    {"item_id": "crystal_thread", "qty": 2},
                ],
                "required_location": "crystal_cave",
                "required_level": 3,
                "xp_reward": 30,
            },
            {
                "recipe_id": "craft_grove_amulet",
                "name": "Амулет рощи",
                "description": "Сплети листья и суть рощи в амулет.",
                "result_item": "grove_amulet",
                "result_qty": 1,
                "ingredients": [
                    {"item_id": "light_leaf", "qty": 4},
                    {"item_id": "grove_essence", "qty": 1},
                ],
                "required_location": "enchanted_grove",
                "required_level": 5,
                "xp_reward": 40,
            },
            {
                "recipe_id": "craft_witch_brew",
                "name": "Зелье ведьмы",
                "description": "Свари зелье из болотных ингредиентов.",
                "result_item": "witch_brew",
                "result_qty": 2,
                "ingredients": [
                    {"item_id": "swamp_root", "qty": 3},
                    {"item_id": "grave_dust", "qty": 1},
                ],
                "required_location": "witch_swamp",
                "required_level": 2,
                "xp_reward": 20,
            },
            {
                "recipe_id": "craft_enchanted_compass",
                "name": "Заколдованный компас",
                "description": "Направь эхо на старую стрелку.",
                "result_item": "enchanted_compass",
                "result_qty": 1,
                "ingredients": [
                    {"item_id": "echo_crystal", "qty": 1},
                    {"item_id": "old_coin", "qty": 2},
                ],
                "required_location": "library_of_echoes",
                "required_level": 4,
                "xp_reward": 35,
            },
            {
                "recipe_id": "craft_soul_bottle",
                "name": "Бутылка с душой",
                "description": "Запри суть призрака в бутылку.",
                "result_item": "soul_bottle",
                "result_qty": 1,
                "ingredients": [
                    {"item_id": "ghost_essence", "qty": 2},
                    {"item_id": "dark_shard", "qty": 1},
                ],
                "required_location": "dark_harbour",
                "required_level": 8,
                "xp_reward": 50,
            },
            {
                "recipe_id": "craft_obsidian_armour",
                "name": "Доспех из обсидиана",
                "description": "Склей осколки обсидиана в броню.",
                "result_item": "rusted_armour",
                "result_qty": 1,
                "ingredients": [
                    {"item_id": "obsidian_shard", "qty": 4},
                    {"item_id": "tentacle_strip", "qty": 2},
                ],
                "required_location": "obsidian_tower",
                "required_level": 5,
                "xp_reward": 35,
            },
        ]

        result = await db.execute(text("SELECT COUNT(*) FROM crafting_recipes"))
        cr_count = result.scalar()
        if cr_count == 0:
            for recipe in crafting_recipes:
                db.add(CraftingRecipeModel(
                    recipe_id=recipe["recipe_id"],
                    name=recipe["name"],
                    description=recipe["description"],
                    result_item=recipe["result_item"],
                    result_qty=recipe["result_qty"],
                    ingredients=json.dumps(recipe["ingredients"]),
                    required_location=recipe["required_location"],
                    required_level=recipe["required_level"],
                    xp_reward=recipe["xp_reward"],
                ))
            await db.commit()
            print(f"   ⚒️ Рецептов крафта: {len(crafting_recipes)}")

        # ══════════════════════════════════════════════
        #  ДОСТИЖЕНИЯ
        # ══════════════════════════════════════════════

        achievements = [
            {"achievement_id": "first_blood", "name": "Первая кровь", "description": "Убей первое существо", "icon": "🩸", "category": "combat", "requirement": {"type": "kill_count", "target": 1}, "reward_xp": 25, "reward_gold": 0},
            {"achievement_id": "monster_hunter", "name": "Охотник", "description": "Убей 10 существ", "icon": "⚔️", "category": "combat", "requirement": {"type": "kill_count", "target": 10}, "reward_xp": 100, "reward_gold": 50},
            {"achievement_id": "slayer", "name": "Бог убийств", "description": "Убей 50 существ", "icon": "💀", "category": "combat", "requirement": {"type": "kill_count", "target": 50}, "reward_xp": 500, "reward_gold": 200},
            {"achievement_id": "explorer_5", "name": "Исследователь", "description": "Открой 5 локаций", "icon": "🗺️", "category": "explore", "requirement": {"type": "locations_discovered", "target": 5}, "reward_xp": 50, "reward_gold": 0},
            {"achievement_id": "explorer_15", "name": "Странник", "description": "Открой 15 локаций", "icon": "🌍", "category": "explore", "requirement": {"type": "locations_discovered", "target": 15}, "reward_xp": 200, "reward_gold": 100},
            {"achievement_id": "explorer_all", "name": "Повелитель тумана", "description": "Открой все локации", "icon": "👁️", "category": "explore", "requirement": {"type": "locations_discovered", "target": 28}, "reward_xp": 1000, "reward_gold": 500, "is_secret": True},
            {"achievement_id": "quest_5", "name": "Исполнитель", "description": "Выполни 5 квестов", "icon": "📜", "category": "quests", "requirement": {"type": "quests_completed", "target": 5}, "reward_xp": 75, "reward_gold": 0},
            {"achievement_id": "quest_all", "name": "Хранитель слов", "description": "Выполни все квесты", "icon": "📖", "category": "quests", "requirement": {"type": "quests_completed", "target": 28}, "reward_xp": 2000, "reward_gold": 1000, "is_secret": True},
            {"achievement_id": "level_5", "name": "Новичок", "description": "Достигни 5 уровня", "icon": "⭐", "category": "progress", "requirement": {"type": "level", "target": 5}, "reward_xp": 50, "reward_gold": 0},
            {"achievement_id": "level_10", "name": "Воин", "description": "Достигни 10 уровня", "icon": "🌟", "category": "progress", "requirement": {"type": "level", "target": 10}, "reward_xp": 200, "reward_gold": 100},
            {"achievement_id": "level_20", "name": "Легенда", "description": "Достигни 20 уровня", "icon": "💫", "category": "progress", "requirement": {"type": "level", "target": 20}, "reward_xp": 500, "reward_gold": 300},
            {"achievement_id": "gold_500", "name": "Скупщик", "description": "Накопи 500 золота", "icon": "🪙", "category": "wealth", "requirement": {"type": "gold", "target": 500}, "reward_xp": 50, "reward_gold": 0},
            {"achievement_id": "gold_5000", "name": "Торговец", "description": "Накопи 5000 золота", "icon": "💰", "category": "wealth", "requirement": {"type": "gold", "target": 5000}, "reward_xp": 300, "reward_gold": 500},
            {"achievement_id": "craft_3", "name": "Ремесленник", "description": "Скрафти 3 предмета", "icon": "⚒️", "category": "craft", "requirement": {"type": "craft_count", "target": 3}, "reward_xp": 50, "reward_gold": 0},
            {"achievement_id": "boss_killer", "name": "Убийца боссов", "description": "Убей босса", "icon": "👑", "category": "combat", "requirement": {"type": "boss_kills", "target": 1}, "reward_xp": 200, "reward_gold": 100},
            {"achievement_id": "pvp_5", "name": "Гладиатор", "description": "Выиграй 5 PvP боёв", "icon": "🏟️", "category": "pvp", "requirement": {"type": "pvp_wins", "target": 5}, "reward_xp": 100, "reward_gold": 50},
            {"achievement_id": "first_day", "name": "Первый день", "description": "Проведи 1 день в MIST", "icon": "🌅", "category": "progress", "requirement": {"type": "days_in_mist", "target": 1}, "reward_xp": 10, "reward_gold": 0},
            {"achievement_id": "week_survivor", "name": "Выживший", "description": "Проведи 7 дней в MIST", "icon": "🗓️", "category": "progress", "requirement": {"type": "days_in_mist", "target": 7}, "reward_xp": 150, "reward_gold": 75},
            {"achievement_id": "equipped", "name": "Экипирован", "description": "Экипируй предмет", "icon": "🎒", "category": "general", "requirement": {"type": "equipped", "target": 1}, "reward_xp": 10, "reward_gold": 0},
            {"achievement_id": "social_butterfly", "name": "Душа компании", "description": "Вступи в гильдию", "icon": "🏰", "category": "social", "requirement": {"type": "guild_member", "target": 1}, "reward_xp": 25, "reward_gold": 0},
        ]

        result = await db.execute(text("SELECT COUNT(*) FROM achievements"))
        ach_count = result.scalar()
        if ach_count == 0:
            for ach in achievements:
                db.add(AchievementModel(
                    achievement_id=ach["achievement_id"],
                    name=ach["name"],
                    description=ach["description"],
                    icon=ach["icon"],
                    category=ach["category"],
                    requirement=json.dumps(ach["requirement"]),
                    reward_xp=ach["reward_xp"],
                    reward_gold=ach["reward_gold"],
                    is_secret=ach.get("is_secret", False),
                ))
            await db.commit()
            print(f"   🏆 Достижений: {len(achievements)}")

        # ══════════════════════════════════════════════
        #  СОСТОЯНИЕ МИРА (World State)
        # ══════════════════════════════════════════════

        result = await db.execute(text("SELECT COUNT(*) FROM world_state"))
        ws_count = result.scalar()
        if ws_count == 0:
            db.add(WorldStateModel(
                game_day=1,
                game_hour=8,
                game_minute=0,
                season="spring",
                world_pressure=10,
                prosperity=50,
                chaos=10,
                magic_level=20,
                danger_level=30,
                events_count=0,
            ))
            await db.commit()
            print("   🌍 Состояние мира: День 1, 08:00, Весна")

        print("\n✅ Контент MIST загружен!")
        print(f"   🌍 Мир: Mistlands")
        print(f"   📍 Регионов: {len(REGIONS)}")
        loc_count_result = await db.execute(text("SELECT COUNT(*) FROM locations"))
        loc_total = loc_count_result.scalar() or 0
        print(f"   📍 Локаций: {loc_total}")
        print(f"   🐾 Существ: {len(creatures)}")
        print(f"   NPC: {len(npcs)}")
        print(f"   🏺 Предметов: {len(items)}")
        print(f"   📜 Квестов: {len(quests)}")
        print(f"   🔮 Секретов: {len(secrets)}")
        print(f"   📦 Предметов на земле: {len(ground)}")
        print(f"   🛒 Предметов магазинов: {len(shop_items)}")
        print(f"   ⚒️ Рецептов крафта: {len(crafting_recipes)}")
        print(f"   🏆 Достижений: {len(achievements)}")


if __name__ == "__main__":
    asyncio.run(seed())
