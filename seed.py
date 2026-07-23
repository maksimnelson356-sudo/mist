import json
import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')

from database.db import init_db, get_db
from game_engine import seed_shop


async def seed():
    await init_db()
    db = await get_db()

    # ══════════════════════════════════════════════
    #  ЛОКАЦИИ — Карта мира MIST
    # ══════════════════════════════════════════════

    locations = [
        {
            "location_id": "dark_forest",
            "name": "Тёмный лес",
            "description": (
                "Деревья так плотно, что свет с трудом пробивается сквозь кроны. "
                "Корни деревьев шевелятся, словно живые. В воздухе — запах гнили и чего-то сладкого.\n\n"
                "Здесь ты очнулся. Запомни это место."
            ),
            "discovered": 1,
            "connections": json.dumps(["riverbank", "ancient_ruins", "wolf_den", "dark_harbour", "witch_swamp"]),
            "is_secret": 0,
            "required_karma": 0,
        },
        {
            "location_id": "riverbank",
            "name": "Берег реки",
            "description": (
                "Река течёт медленно, почти беззвучно. Вода чёрная, как ночь. "
                "На противоположном берегу — что-то блестит.\n\n"
                "Рыбак говорит, что в этой реке водятся существа, которых лучше не видеть."
            ),
            "connections": json.dumps(["dark_forest", "fishing_village", "underwater_cave", "dark_harbour"]),
            "is_secret": 0,
            "required_karma": 0,
        },
        {
            "location_id": "ancient_ruins",
            "name": "Древние руины",
            "description": (
                "Колонны, покрытые мхом, возвышаются над землёй. Между ними — каменные плиты "
                "с невиданными символами. Каждый символ слабо светится в темноте.\n\n"
                "Здесь царит тишина. Но ты чувствуешь — за тобой наблюдают."
            ),
            "connections": json.dumps(["dark_forest", "library_of_echoes", "obsidian_tower", "crystal_cave", "ash_fields"]),
            "is_secret": 0,
            "required_karma": 0,
        },
        {
            "location_id": "wolf_den",
            "name": "Логово волков",
            "description": (
                "Пахнет кровью и мокрой шерстью. Кости разбросаны по полу. "
                "Глаза светятся в темноте — десятки пар.\n\n"
                "Вожак наблюдает. Он решит — друг ты или пища."
            ),
            "connections": json.dumps(["dark_forest", "blood_meadow"]),
            "is_secret": 0,
            "required_karma": 0,
        },
        {
            "location_id": "fishing_village",
            "name": "Рыбацкая деревня",
            "description": (
                "Три хижины у воды. Старик с крючком сидит на пристани. "
                "Он не смотрит на тебя, но говорит: «Знаю, зачем ты пришёл. Все приходят за тем же.»\n\n"
                "Здесь можно отдохнуть и купить снаряжение."
            ),
            "connections": json.dumps(["riverbank", "market_square"]),
            "is_secret": 0,
            "required_karma": 0,
        },
        {
            "location_id": "market_square",
            "name": "Торговая площадь",
            "description": (
                "Палатки с товарами, которых ты никогда не видел. "
                "Кристаллы, зелья, свёртки с непонятным содержимым.\n\n"
                "Торговец шепчет: «У меня есть то, что тебе нужно. Но сначала — докажи, что стоишь.»"
            ),
            "connections": json.dumps(["fishing_village", "temple_of_shadows", "shadow_market"]),
            "is_secret": 0,
            "required_karma": 0,
        },
        {
            "location_id": "library_of_echoes",
            "name": "Библиотека эхов",
            "description": (
                "Стеллажи уходят ввысь, теряясь во тьме. Книги здесь — живые. "
                "Они шепчут, когда ты проходишь мимо. Некоторые — кричат.\n\n"
                "Одна книга открыта на странице: «Тот, кто читает — становится прочитанным.»"
            ),
            "connections": json.dumps(["ancient_ruins", "mirror_hall"]),
            "is_secret": 0,
            "required_karma": 0,
        },
        {
            "location_id": "obsidian_tower",
            "name": "Обсидиановая башня",
            "description": (
                "Башня из чёрного стекла. Она не отражает свет — поглощает его. "
                "На каждом этаже — ловушки и загадки.\n\n"
                "Верхний этаж закрыт. Говорят, там живёт Хранитель."
            ),
            "connections": json.dumps(["ancient_ruins", "tower_summit"]),
            "is_secret": 0,
            "required_karma": 5,
        },
        {
            "location_id": "blood_meadow",
            "name": "Кровавый луг",
            "description": (
                "Трава здесь красная. Не от заката — от чего-то другого. "
                "В центре луга — дерево, лишённое коры. На нём — следы когтей.\n\n"
                "Воздух тяжёлый. Ты слышишь сердцебиение. Не своё."
            ),
            "connections": json.dumps(["wolf_den", "white_forest", "witch_swamp", "forgotten_graveyard"]),
            "is_secret": 0,
            "required_karma": 0,
        },
        {
            "location_id": "white_forest",
            "name": "Белый лес",
            "description": (
                "Деревья белые, как кости. Листьев нет. Снег — зимой и летом. "
                "Здесь холодно. Не от температуры — от чего-то внутри.\n\n"
                "Это место помнит что-то страшное. И не хочет, чтобы ты знал что."
            ),
            "connections": json.dumps(["blood_meadow", "frozen_lake", "forgotten_graveyard", "ash_fields"]),
            "is_secret": 0,
            "required_karma": 0,
        },
        {
            "location_id": "underwater_cave",
            "name": "Подводная пещера",
            "description": (
                "Ты нырнул. Вода тёплая — слишком тёплая. "
                "На дне — руины, похожие на древние руины на поверхности.\n\n"
                "Что-то движется в темноте. Оно большое."
            ),
            "connections": json.dumps(["riverbank", "sunken_throne", "crystal_cave"]),
            "is_secret": 0,
            "required_karma": 0,
        },
        {
            "location_id": "temple_of_shadows",
            "name": "Храм теней",
            "description": (
                "Колонны из чёрного мрамора. Между ними — статуи без лиц. "
                "В центре — алтарь, на котором лежит нож.\n\n"
                "Голос: «Принеси жертву. И получи то, что ищешь.»"
            ),
            "connections": json.dumps(["market_square", "void_gate", "shadow_market"]),
            "is_secret": 0,
            "required_karma": 0,
        },
        {
            "location_id": "mirror_hall",
            "name": "Зеркальный зал",
            "description": (
                "Зеркала повсюду. Но отражения — не твои. "
                "Они двигаются, когда ты стоишь на месте. Улыбаются.\n\n"
                "Одно зеркало показывает что-то знакомое. Ты помнишь это место... или нет?"
            ),
            "connections": json.dumps(["library_of_echoes"]),
            "is_secret": 1,
            "required_karma": 10,
        },
        {
            "location_id": "tower_summit",
            "name": "Вершина башни",
            "description": (
                "Отсюда видно весь MIST. Туман стелется ниже. "
                "На вершине — камень с вырезанным символом: 👁\n\n"
                "Хранитель ждал тебя. Давно."
            ),
            "connections": json.dumps(["obsidian_tower"]),
            "is_secret": 0,
            "required_karma": 10,
        },
        {
            "location_id": "frozen_lake",
            "name": "Замёрзшее озеро",
            "description": (
                "Озеро покрыто льдом, но подо льдом — что-то двигается. "
                "На середине — трещина. Из неё — свет.\n\n"
                "Если прислушаться, можно услышать голоса. Мёртвых."
            ),
            "connections": json.dumps(["white_forest", "heart_of_mist"]),
            "is_secret": 0,
            "required_karma": 0,
        },
        {
            "location_id": "sunken_throne",
            "name": "Затонутый трон",
            "description": (
                "На дне озера — трон из кораллов. На нём — скелет в короне. "
                "В руке скелета — кольцо.\n\n"
                "Король мёртвых. Но его власть — нет."
            ),
            "connections": json.dumps(["underwater_cave"]),
            "is_secret": 1,
            "required_karma": 15,
        },
        {
            "location_id": "void_gate",
            "name": "Врата Пустоты",
            "description": (
                "Два столба из чёрного камня. Между ними — пустота. "
                "Абсолютная. Ты смотришь в неё — и она смотрит в тебя.\n\n"
                "За вратами — конец. Или начало."
            ),
            "connections": json.dumps(["temple_of_shadows", "heart_of_mist"]),
            "is_secret": 0,
            "required_karma": 20,
        },
        {
            "location_id": "heart_of_mist",
            "name": "Сердце MIST",
            "description": (
                "Ты здесь. Ты всегда был здесь.\n\n"
                "Туман отступает. На мгновение ты видишь — тысячи лиц. "
                "Тех, кто был до тебя. Тех, кто будет после.\n\n"
                "MIST — это не место. MIST — это ты."
            ),
            "connections": json.dumps(["frozen_lake", "void_gate"]),
            "is_secret": 1,
            "required_karma": 30,
        },
        # ═══ НОВЫЕ ЛОКАЦИИ ═══
        {
            "location_id": "witch_swamp",
            "name": "Топи ведьмы",
            "description": (
                "Болото дышит. Пузыри лопаются на поверхности, выпуская зловонный газ. "
                "Среди мглы — силуэт хижины на куриных ножках.\n\n"
                "Ведьма здесь. Она знает твоё имя."
            ),
            "connections": json.dumps(["dark_forest", "blood_meadow", "forgotten_graveyard"]),
            "is_secret": 0,
            "required_karma": 0,
        },
        {
            "location_id": "forgotten_graveyard",
            "name": "Забытое кладбище",
            "description": (
                "Надгробия покосились. Имена стёрты. "
                "Земля здесь мягкая — слишком мягкая. "
                "Из-под камней торчат кости.\n\n"
                "Страж не спит. Он ждёт."
            ),
            "connections": json.dumps(["witch_swamp", "white_forest", "dark_harbour"]),
            "is_secret": 0,
            "required_karma": 0,
        },
        {
            "location_id": "crystal_cave",
            "name": "Хрустальная пещера",
            "description": (
                "Стены пещеры покрыты кристаллами. Они светятся изнутри — "
                "синим, фиолетовым, белым. Свет мерцает, как живой.\n\n"
                "Кристаллы звенят, когда ты проходишь мимо. Они поют."
            ),
            "connections": json.dumps(["ancient_ruins", "underwater_cave", "ash_fields"]),
            "is_secret": 0,
            "required_karma": 5,
        },
        {
            "location_id": "dark_harbour",
            "name": "Тёмная гавань",
            "description": (
                "Причал, поросший мхом. Корабль стоит на якоре — "
                "но экипажа нет. Только чёрные паруса колышутся на ветру.\n\n"
                "Контрабандисты говорят, что отсюда уплывают в другие миры."
            ),
            "connections": json.dumps(["dark_forest", "forgotten_graveyard", "riverbank"]),
            "is_secret": 0,
            "required_karma": 0,
        },
        {
            "location_id": "ash_fields",
            "name": "Пепельные поля",
            "description": (
                "Земля серая, как пепел. Трава не растёт. "
                "Воздух тяжёлый, горячий. Из трещин в земле сочится пар.\n\n"
                "Здесь когда-то был город. Теперь — только пепел и воспоминания."
            ),
            "connections": json.dumps(["white_forest", "crystal_cave", "ancient_ruins"]),
            "is_secret": 0,
            "required_karma": 5,
        },
        {
            "location_id": "shadow_market",
            "name": "Теневой рынок",
            "description": (
                "Палатки из чёрной ткани. Продавцы в масках. "
                "Товары, которые нельзя найти больше нигде.\n\n"
                "Торговец шепчет: «Золото не нужно. Принеси мне кое-что... интересное.»"
            ),
            "connections": json.dumps(["market_square", "temple_of_shadows"]),
            "is_secret": 0,
            "required_karma": 10,
        },
    ]

    for loc in locations:
        await db.execute(
            """INSERT OR REPLACE INTO locations (location_id, name, description, discovered, connections, is_secret, required_karma)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (loc["location_id"], loc["name"], loc["description"], loc.get("discovered", 0),
             loc["connections"], loc.get("is_secret", 0), loc.get("required_karma", 0))
        )

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
            "loot_table": json.dumps([
                {"item_id": "wolf_fang", "chance": 0.8, "qty": 2},
                {"item_id": "alpha_pelt", "chance": 0.4, "qty": 1},
                {"item_id": "bloodstone", "chance": 0.15, "qty": 1},
            ]),
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
            "loot_table": json.dumps([
                {"item_id": "wolf_fang", "chance": 0.6, "qty": 1},
                {"item_id": "wolf_pelt", "chance": 0.5, "qty": 1},
            ]),
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
            "loot_table": json.dumps([
                {"item_id": "shadow_essence", "chance": 0.7, "qty": 1},
                {"item_id": "dark_shard", "chance": 0.3, "qty": 1},
            ]),
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
            "loot_table": json.dumps([
                {"item_id": "serpent_scale", "chance": 0.7, "qty": 2},
                {"item_id": "river_pearl", "chance": 0.2, "qty": 1},
            ]),
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
            "loot_table": json.dumps([]),
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
            "loot_table": json.dumps([
                {"item_id": "echo_crystal", "chance": 0.5, "qty": 1},
                {"item_id": "forgotten_page", "chance": 0.3, "qty": 1},
            ]),
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
            "loot_table": json.dumps([
                {"item_id": "gargoyle_eye", "chance": 0.4, "qty": 1},
                {"item_id": "obsidian_shard", "chance": 0.6, "qty": 2},
            ]),
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
            "loot_table": json.dumps([
                {"item_id": "blood_wood", "chance": 0.7, "qty": 1},
                {"item_id": "living_bark", "chance": 0.3, "qty": 1},
            ]),
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
            "loot_table": json.dumps([
                {"item_id": "frost_shard", "chance": 0.6, "qty": 1},
                {"item_id": "frozen_tear", "chance": 0.25, "qty": 1},
            ]),
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
            "loot_table": json.dumps([
                {"item_id": "mirror_fragment", "chance": 0.5, "qty": 1},
                {"item_id": "stolen_memory", "chance": 0.3, "qty": 1},
            ]),
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
            "loot_table": json.dumps([
                {"item_id": "keeper_key", "chance": 0.5, "qty": 1},
                {"item_id": "void_shard", "chance": 0.3, "qty": 1},
                {"item_id": "legendary_essence", "chance": 0.1, "qty": 1},
            ]),
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
            "loot_table": json.dumps([
                {"item_id": "dead_king_ring", "chance": 0.4, "qty": 1},
                {"item_id": "crown_shard", "chance": 0.6, "qty": 1},
            ]),
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
            "loot_table": json.dumps([
                {"item_id": "void_crystal", "chance": 0.4, "qty": 1},
                {"item_id": "essence_of_nothing", "chance": 0.2, "qty": 1},
            ]),
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
            "loot_table": json.dumps([
                {"item_id": "witch_brew", "chance": 0.6, "qty": 1},
                {"item_id": "swamp_root", "chance": 0.5, "qty": 2},
            ]),
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
            "loot_table": json.dumps([
                {"item_id": "swamp_slime", "chance": 0.7, "qty": 1},
                {"item_id": "bogey_eye", "chance": 0.3, "qty": 1},
            ]),
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
            "loot_table": json.dumps([
                {"item_id": "rusted_armour", "chance": 0.4, "qty": 1},
                {"item_id": "grave_dust", "chance": 0.6, "qty": 2},
            ]),
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
            "loot_table": json.dumps([
                {"item_id": "crystal_core", "chance": 0.4, "qty": 1},
                {"item_id": "prism_shard", "chance": 0.6, "qty": 2},
            ]),
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
            "loot_table": json.dumps([
                {"item_id": "ghost_essence", "chance": 0.5, "qty": 1},
                {"item_id": "torn_map", "chance": 0.3, "qty": 1},
            ]),
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
            "loot_table": json.dumps([
                {"item_id": "ash_essence", "chance": 0.5, "qty": 1},
                {"item_id": "burnt_relic", "chance": 0.25, "qty": 1},
            ]),
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
            "loot_table": json.dumps([
                {"item_id": "arcane_dust", "chance": 0.6, "qty": 1},
                {"item_id": "forgotten_page", "chance": 0.2, "qty": 1},
            ]),
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
            "loot_table": json.dumps([
                {"item_id": "kraken_ink", "chance": 0.5, "qty": 1},
                {"item_id": "tentacle_strip", "chance": 0.4, "qty": 2},
            ]),
        },
    ]

    for c in creatures:
        await db.execute(
            """INSERT OR REPLACE INTO creatures
               (creature_id, name, description, location, disposition, hp, max_hp, attack, defense, xp_reward, loot_table)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (c["creature_id"], c["name"], c["description"], c["location"], c["disposition"],
             c["hp"], c["max_hp"], c["attack"], c["defense"], c["xp_reward"], c["loot_table"])
        )

    # ══════════════════════════════════════════════
    #  ПРЕДМЕТЫ
    # ══════════════════════════════════════════════

    items = [
        {"item_id": "wolf_fang", "name": "Клык волка", "description": "Острый, как бритва. Используется в ритуалах.", "rarity": "common", "is_usable": 0},
        {"item_id": "wolf_pelt", "name": "Шкура волка", "description": "Тёплая. Но от неё пахнет страхом.", "rarity": "common", "is_usable": 0},
        {"item_id": "alpha_pelt", "name": "Шкура альфы", "description": "Шкура вожака. Она помнит каждый бой.", "rarity": "rare", "is_usable": 0},
        {"item_id": "bloodstone", "name": "Кровавый камень", "description": "Камень, пульсирующий красным. Он горячий.", "rarity": "rare", "is_usable": 0},
        {"item_id": "shadow_essence", "name": "Суть тени", "description": "Жидкость, которая не отражает свет.", "rarity": "rare", "is_usable": 1, "use_effect": json.dumps({"heal": 30})},
        {"item_id": "dark_shard", "name": "Осколок тьмы", "description": "Чёрный осколок. Он поглощает звук.", "rarity": "rare", "is_usable": 0},
        {"item_id": "serpent_scale", "name": "Чешуя змея", "description": "Чешуя, как броня. Но она гибкая.", "rarity": "common", "is_usable": 0},
        {"item_id": "river_pearl", "name": "Речная жемчужина", "description": "Жемчужина из чёрной воды. Она светится в темноте.", "rarity": "rare", "is_usable": 1, "use_effect": json.dumps({"light": True})},
        {"item_id": "echo_crystal", "name": "Кристалл эха", "description": "Внутри — чей-то голос. Он повторяет твои мысли.", "rarity": "rare", "is_usable": 1, "use_effect": json.dumps({"reveal_secret": True})},
        {"item_id": "forgotten_page", "name": "Забытая страница", "description": "Страница из книги, которой не существует.", "rarity": "rare", "is_usable": 0},
        {"item_id": "gargoyle_eye", "name": "Глаз гаргульи", "description": "Каменный глаз. Он видит сквозь стены.", "rarity": "epic", "is_usable": 1, "use_effect": json.dumps({"vision": True})},
        {"item_id": "obsidian_shard", "name": "Осколок обсидиана", "description": "Чёрное стекло. Острым, как скальпель.", "rarity": "common", "is_usable": 0},
        {"item_id": "blood_wood", "name": "Кровавое дерево", "description": "Древесина, которая помнит боль.", "rarity": "rare", "is_usable": 0},
        {"item_id": "living_bark", "name": "Живая кора", "description": "Кора, которая дышит. Она растёт.", "rarity": "rare", "is_usable": 0},
        {"item_id": "frost_shard", "name": "Осколок мороза", "description": "Лёд, который не тает. Он замораживает всё.", "rarity": "common", "is_usable": 1, "use_effect": json.dumps({"damage": 15})},
        {"item_id": "frozen_tear", "name": "Замёрзшая слеза", "description": "Слеза кого-то, кто давно мёртв.", "rarity": "rare", "is_usable": 1, "use_effect": json.dumps({"heal": 50})},
        {"item_id": "mirror_fragment", "name": "Осколок зеркала", "description": "Осколок, который отражает не тебя, а то, кем ты мог бы быть.", "rarity": "epic", "is_usable": 0},
        {"item_id": "stolen_memory", "name": "Украденная память", "description": "Чьи-то воспоминания. Ты видишь чужую жизнь.", "rarity": "epic", "is_usable": 1, "use_effect": json.dumps({"xp": 50})},
        {"item_id": "keeper_key", "name": "Ключ хранителя", "description": "Ключ, который открывает всё. И закрывает тоже.", "rarity": "legendary", "is_usable": 0},
        {"item_id": "void_shard", "name": "Осколок пустоты", "description": "Ничто, оформленное в материю.", "rarity": "legendary", "is_usable": 0},
        {"item_id": "legendary_essence", "name": "Легендарная суть", "description": "Квинтэссенция MIST. Её мало кто видел.", "rarity": "legendary", "is_usable": 1, "use_effect": json.dumps({"level_up": True})},
        {"item_id": "dead_king_ring", "name": "Кольцо мёртвого короля", "description": "Кольцо, которое даёт власть над мёртвыми. Временно.", "rarity": "legendary", "is_usable": 1, "use_effect": json.dumps({"resurrect": True})},
        {"item_id": "crown_shard", "name": "Осколок короны", "description": "Часть короны, которая правила миром.", "rarity": "epic", "is_usable": 0},
        {"item_id": "void_crystal", "name": "Кристалл пустоты", "description": "Кристалл, внутри — вакуум. Он поглощает всё.", "rarity": "legendary", "is_usable": 0},
        {"item_id": "essence_of_nothing", "name": "Суть ничто", "description": "Это... ничего. Но это что-то.", "rarity": "legendary", "is_usable": 0},
        {"item_id": "healing_herb", "name": "Целебная трава", "description": "Растёт у реки. Восстанавливает 20 HP.", "rarity": "common", "is_usable": 1, "use_effect": json.dumps({"heal": 20})},
        {"item_id": "mysterious_map", "name": "Загадочная карта", "description": "Карта, которая меняется. Каждый раз — новая.", "rarity": "rare", "is_usable": 0},
        {"item_id": "old_coin", "name": "Старая монета", "description": "Монета с профилем того, кого никто не помнит.", "rarity": "common", "is_usable": 0},
        # ═══ НОВЫЕ ПРЕДМЕТЫ ═══
        {"item_id": "witch_brew", "name": "Зелье ведьмы", "description": "Пузырящаяся жидкость зелёного цвета. Пахнет... интересно.", "rarity": "rare", "is_usable": 1, "use_effect": json.dumps({"heal": 40, "xp": 15})},
        {"item_id": "swamp_root", "name": "Болотный корень", "description": "Корень, который дышит. Его можно жевать.", "rarity": "common", "is_usable": 1, "use_effect": json.dumps({"heal": 15})},
        {"item_id": "swamp_slime", "name": "Болотная слизь", "description": "Липкая масса. Она двигается.", "rarity": "common", "is_usable": 0},
        {"item_id": "bogey_eye", "name": "Глаз болотной твари", "description": "Красный, влажный. Он ещё моргает.", "rarity": "rare", "is_usable": 0},
        {"item_id": "rusted_armour", "name": "Ржавые доспехи", "description": "Доспехи стража. Ещё держатся.", "rarity": "rare", "is_usable": 0},
        {"item_id": "grave_dust", "name": "Прах могил", "description": "Пепел, который не тает на ветру.", "rarity": "common", "is_usable": 0},
        {"item_id": "crystal_core", "name": "Кристальное ядро", "description": "Ядро голема. Пульсирует энергией.", "rarity": "epic", "is_usable": 1, "use_effect": json.dumps({"xp": 40, "level_up": True})},
        {"item_id": "prism_shard", "name": "Осколок призмы", "description": "Кристалл, разделяющий свет на цвета.", "rarity": "rare", "is_usable": 0},
        {"item_id": "ghost_essence", "name": "Суть призрака", "description": "Полупрозрачная жидкость. Она холодная.", "rarity": "rare", "is_usable": 1, "use_effect": json.dumps({"heal": 35})},
        {"item_id": "torn_map", "name": "Рваная карта", "description": "Часть карты. Показывает путь... куда-то.", "rarity": "rare", "is_usable": 0},
        {"item_id": "ash_essence", "name": "Пепельная суть", "description": "Горячий пепел. Он горит изнутри.", "rarity": "rare", "is_usable": 1, "use_effect": json.dumps({"damage": 20})},
        {"item_id": "burnt_relic", "name": "Оплавленный реликт", "description": "Артефакт, оплавленный жаром. Ещё теплый.", "rarity": "epic", "is_usable": 0},
        {"item_id": "arcane_dust", "name": "Магическая пыль", "description": "Пыль, которая светится. Искры магии.", "rarity": "common", "is_usable": 0},
        {"item_id": "kraken_ink", "description": "Чернила кракена. Ими можно писать... или отравлять.", "name": "Чернила кракена", "rarity": "rare", "is_usable": 1, "use_effect": json.dumps({"heal": 25})},
        {"item_id": "tentacle_strip", "name": "Полоска щупальца", "description": "Жёсткая, как кожаный ремень. Но живая.", "rarity": "common", "is_usable": 0},
        {"item_id": "enchanted_compass", "name": "Заколдованный компас", "description": "Стрелка указывает не на север, а на то, что ты ищешь.", "rarity": "epic", "is_usable": 0},
        {"item_id": "soul_bottle", "name": "Бутылка с душой", "description": "Внутри — чей-то крик. Закрой горлышко.", "rarity": "legendary", "is_usable": 1, "use_effect": json.dumps({"heal": 80})},
        {"item_id": "gold_coin", "name": "Золотая монета", "description": "Валюта теневого рынка. Блестит даже в темноте.", "rarity": "common", "is_usable": 0},
    ]

    for item in items:
        use_effect = item.get("use_effect", "{}")
        if isinstance(use_effect, dict):
            use_effect = json.dumps(use_effect)
        await db.execute(
            """INSERT OR REPLACE INTO item_templates (item_id, name, description, rarity, is_usable, use_effect)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (item["item_id"], item["name"], item["description"], item["rarity"], item.get("is_usable", 0), use_effect)
        )

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
            "objectives": json.dumps([{"id": "visit_any", "type": "visit", "location": "riverbank", "target": 1, "description": "Доберись до берега реки"}]),
            "rewards": json.dumps({"xp": 15, "memories": 2, "gold": 5}),
            "is_active": 1, "is_repeating": 0,
        },
        {
            "quest_id": "q_wolf1",
            "name": "Волчий клык",
            "description": "Старый рыбак просит принести клык волка. Для ритуала.",
            "giver": "elder_fisherman",
            "location": "fishing_village",
            "objectives": json.dumps([{"id": "kill_wolf", "type": "kill", "creature": "wolf_pack", "target": 3, "description": "Убить 3 волков"}]),
            "rewards": json.dumps({"xp": 30, "memories": 2, "karma": 2, "gold": 10, "items": [{"id": "healing_herb", "qty": 3}]}),
            "is_active": 1, "is_repeating": 1,
        },
        {
            "quest_id": "q_wolf2",
            "name": "Вожак стаи",
            "description": "Альфа-волк угрожает деревне. Убей его.",
            "giver": "elder_fisherman",
            "location": "fishing_village",
            "objectives": json.dumps([{"id": "kill_alpha", "type": "kill", "creature": "wolf_alpha", "target": 1, "description": "Убить альфа-волка"}]),
            "rewards": json.dumps({"xp": 60, "memories": 5, "karma": 5, "gold": 25, "items": [{"id": "alpha_pelt", "qty": 1}]}),
            "is_active": 1, "is_repeating": 0,
        },
        # Цепочка 2: Древние руины
        {
            "quest_id": "q_ruins1",
            "name": "Символы прошлого",
            "description": "Исследуй древние руины. Прочитай символы.",
            "giver": "unknown",
            "location": "ancient_ruins",
            "objectives": json.dumps([{"id": "visit_ruins", "type": "visit", "location": "ancient_ruins", "target": 1, "description": "Посетить древние руины"}]),
            "rewards": json.dumps({"xp": 20, "memories": 3, "gold": 5}),
            "is_active": 1, "is_repeating": 0,
        },
        {
            "quest_id": "q_ruins2",
            "name": "Голос книг",
            "description": "В библиотеке есть книга, которая говорит. Найди её.",
            "giver": "unknown",
            "location": "library_of_echoes",
            "objectives": json.dumps([{"id": "visit_library", "type": "visit", "location": "library_of_echoes", "target": 1, "description": "Посетить библиотеку эхов"}]),
            "rewards": json.dumps({"xp": 30, "memories": 4, "gold": 8, "items": [{"id": "echo_crystal", "qty": 1}]}),
            "is_active": 1, "is_repeating": 0,
        },
        # Цепочка 3: Башня
        {
            "quest_id": "q_tower1",
            "name": "Чёрная башня",
            "description": "Обсидиановая башня хранит секрет. Найди его.",
            "giver": "unknown",
            "location": "obsidian_tower",
            "objectives": json.dumps([
                {"id": "visit_tower", "type": "visit", "location": "obsidian_tower", "target": 1, "description": "Посетить башню"},
                {"id": "kill_gargoyle", "type": "kill", "creature": "gargoyle", "target": 1, "description": "Победить гаргулью"}
            ]),
            "rewards": json.dumps({"xp": 70, "memories": 6, "karma": 3, "gold": 30}),
            "is_active": 1, "is_repeating": 0,
        },
        {
            "quest_id": "q_tower2",
            "name": "Вершина мира",
            "description": "Поднимись на вершину башни. Встреть Хранителя.",
            "giver": "unknown",
            "location": "tower_summit",
            "objectives": json.dumps([{"id": "visit_summit", "type": "visit", "location": "tower_summit", "target": 1, "description": "Подняться на вершину"}]),
            "rewards": json.dumps({"xp": 100, "memories": 10, "karma": 10, "gold": 50, "items": [{"id": "keeper_key", "qty": 1}]}),
            "is_active": 1, "is_repeating": 0,
        },
        # Цепочка 4: Теневой храм
        {
            "quest_id": "q_temple1",
            "name": "Жертва",
            "description": "В храме просят жертву. Принеси шкуру волка.",
            "giver": "unknown",
            "location": "temple_of_shadows",
            "objectives": json.dumps([{"id": "visit_temple", "type": "visit", "location": "temple_of_shadows", "target": 1, "description": "Посетить храм теней"}]),
            "rewards": json.dumps({"xp": 40, "memories": 5, "karma": -3, "gold": 15}),
            "is_active": 1, "is_repeating": 0,
        },
        # Цепочка 5: Белый лес
        {
            "quest_id": "q_white1",
            "name": "Холод внутри",
            "description": "Белый лес помнит что-то страшное. Узнай что.",
            "giver": "unknown",
            "location": "white_forest",
            "objectives": json.dumps([{"id": "visit_white", "type": "visit", "location": "white_forest", "target": 1, "description": "Посетить белый лес"}]),
            "rewards": json.dumps({"xp": 30, "memories": 4, "gold": 10}),
            "is_active": 1, "is_repeating": 0,
        },
        # Цепочка 6: Финал
        {
            "quest_id": "q_heart1",
            "name": "Сердце MIST",
            "description": "Найди путь к сердцу MIST. Пойми, что ты здесь делаешь.",
            "giver": "unknown",
            "location": "heart_of_mist",
            "objectives": json.dumps([{"id": "visit_heart", "type": "visit", "location": "heart_of_mist", "target": 1, "description": "Добраться до сердца MIST"}]),
            "rewards": json.dumps({"xp": 200, "memories": 20, "karma": 15, "gold": 100, "items": [{"id": "legendary_essence", "qty": 1}]}),
            "is_active": 1, "is_repeating": 0,
        },
        # Повторяющийся: Охота на теней
        {
            "quest_id": "q_hunt_shadows",
            "name": "Охотник теней",
            "description": "Тени нападают на деревню. Уничтожь их.",
            "giver": "elder_fisherman",
            "location": "fishing_village",
            "objectives": json.dumps([{"id": "kill_shadow", "type": "kill", "creature": "shadow_stalker", "target": 2, "description": "Убить 2 теней-охотников"}]),
            "rewards": json.dumps({"xp": 40, "memories": 3, "karma": 2, "gold": 15}),
            "is_active": 1, "is_repeating": 1,
        },
        # ═══ НОВЫЕ КВЕСТЫ ═══
        # Цепочка: Топи ведьмы
        {
            "quest_id": "q_witch1",
            "name": "Зелье для ведьмы",
            "description": "Ведуна просит принести болотный корень для зелья.",
            "giver": "swamp_witch",
            "location": "witch_swamp",
            "objectives": json.dumps([
                {"id": "collect_swamp_root", "type": "collect", "item": "swamp_root", "target": 3, "description": "Собрать 3 болотных корня"}
            ]),
            "rewards": json.dumps({"xp": 35, "memories": 4, "karma": 3, "gold": 12, "items": [{"id": "witch_brew", "qty": 2}]}),
            "is_active": 1, "is_repeating": 1,
        },
        {
            "quest_id": "q_witch2",
            "name": "Тайна болот",
            "description": "Ведьма хочет знать, кто крадёт её зелья.",
            "giver": "swamp_witch",
            "location": "witch_swamp",
            "objectives": json.dumps([
                {"id": "kill_bogey", "type": "kill", "creature": "bogey", "target": 3, "description": "Убить 3 болотных тварей"}
            ]),
            "rewards": json.dumps({"xp": 50, "memories": 6, "karma": 4, "gold": 20, "items": [{"id": "enchanted_compass", "qty": 1}]}),
            "is_active": 1, "is_repeating": 0,
        },
        # Цепочка: Кладбище
        {
            "quest_id": "q_grave1",
            "name": "Дозор мёртвых",
            "description": "Страж кладбища просит очистить могилы от нежити.",
            "giver": "grave_sentinel",
            "location": "forgotten_graveyard",
            "objectives": json.dumps([
                {"id": "kill_skeleton", "type": "kill", "creature": "skeleton_mage", "target": 3, "description": "Убить 3 скелетов-магов"}
            ]),
            "rewards": json.dumps({"xp": 45, "memories": 5, "karma": 5, "gold": 15, "items": [{"id": "grave_dust", "qty": 3}]}),
            "is_active": 1, "is_repeating": 1,
        },
        {
            "quest_id": "q_grave2",
            "name": "Забытое имя",
            "description": "Страж ищет своё имя. Оно где-то здесь.",
            "giver": "grave_sentinel",
            "location": "forgotten_graveyard",
            "objectives": json.dumps([
                {"id": "visit_grave", "type": "visit", "location": "forgotten_graveyard", "target": 1, "description": "Осмотреть кладбище"}
            ]),
            "rewards": json.dumps({"xp": 30, "memories": 8, "karma": 3, "gold": 10}),
            "is_active": 1, "is_repeating": 0,
        },
        # Цепочка: Кристальная пещера
        {
            "quest_id": "q_crystal1",
            "name": "Голос кристаллов",
            "description": "Кристаллы поют. Но один из них — кричит.",
            "giver": "unknown",
            "location": "crystal_cave",
            "objectives": json.dumps([
                {"id": "kill_golem", "type": "kill", "creature": "crystal_golem", "target": 1, "description": "Победить кристального голема"}
            ]),
            "rewards": json.dumps({"xp": 60, "memories": 7, "karma": 4, "gold": 25, "items": [{"id": "crystal_core", "qty": 1}]}),
            "is_active": 1, "is_repeating": 0,
        },
        # Цепочка: Тёмная гавань
        {
            "quest_id": "q_harbour1",
            "name": "Потерянный корабль",
            "description": "Призрак капитана хочет вернуться на корабль. Но ему нужна карта.",
            "giver": "harbour_ghost",
            "location": "dark_harbour",
            "objectives": json.dumps([
                {"id": "collect_map", "type": "collect", "item": "torn_map", "target": 1, "description": "Найти рваную карту"}
            ]),
            "rewards": json.dumps({"xp": 45, "memories": 6, "karma": 4, "gold": 20, "items": [{"id": "gold_coin", "qty": 5}]}),
            "is_active": 1, "is_repeating": 0,
        },
        {
            "quest_id": "q_harbour2",
            "name": "Чёрные паруса",
            "description": "Кракен разорвал паруса. Нужны новые щупальца.",
            "giver": "unknown",
            "location": "dark_harbour",
            "objectives": json.dumps([
                {"id": "kill_kraken", "type": "kill", "creature": "kraken_tentacle", "target": 2, "description": "Убить 2 щупальца кракена"}
            ]),
            "rewards": json.dumps({"xp": 55, "memories": 5, "karma": 3, "gold": 20, "items": [{"id": "kraken_ink", "qty": 2}]}),
            "is_active": 1, "is_repeating": 1,
        },
        # Цепочка: Пепельные поля
        {
            "quest_id": "q_ash1",
            "name": "Пепел городов",
            "description": "Среди пепла — оплавленные реликвии. Собери их.",
            "giver": "unknown",
            "location": "ash_fields",
            "objectives": json.dumps([
                {"id": "kill_ash_wraith", "type": "kill", "creature": "ash_wraith", "target": 2, "description": "Убить 2 пепельных призраков"},
                {"id": "collect_relic", "type": "collect", "item": "burnt_relic", "target": 1, "description": "Найти оплавленный реликт"}
            ]),
            "rewards": json.dumps({"xp": 65, "memories": 8, "karma": 5, "gold": 35, "items": [{"id": "soul_bottle", "qty": 1}]}),
            "is_active": 1, "is_repeating": 0,
        },
        # Цепочка: Теневой рынок
        {
            "quest_id": "q_market1",
            "name": "Теневой клиент",
            "description": "Торговец хочет редкий товар. Принеси ему кристалл эха.",
            "giver": "unknown",
            "location": "shadow_market",
            "objectives": json.dumps([
                {"id": "collect_echo", "type": "collect", "item": "echo_crystal", "target": 1, "description": "Принести кристалл эха"}
            ]),
            "rewards": json.dumps({"xp": 50, "memories": 5, "karma": 2, "gold": 25, "items": [{"id": "gold_coin", "qty": 8}]}),
            "is_active": 1, "is_repeating": 1,
        },
    ]

    for q in quests:
        await db.execute(
            """INSERT OR REPLACE INTO quests (quest_id, name, description, giver, location, objectives, rewards, is_active, is_repeating)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (q["quest_id"], q["name"], q["description"], q["giver"], q["location"],
             q["objectives"], q["rewards"], q["is_active"], q["is_repeating"])
        )

    # ══════════════════════════════════════════════
    #  СЕКРЕТЫ
    # ══════════════════════════════════════════════

    secrets = [
        {
            "secret_id": "secret_first_blood",
            "secret_type": "achievement",
            "name": "Первая кровь",
            "description": "Ты убил своё первое существо. Мир запомнил это.",
            "trigger_condition": json.dumps({"type": "action_count", "action": "combat_victory", "value": 1}),
            "reward": json.dumps({"memories": 3, "karma": 1}),
        },
        {
            "secret_id": "secret_explorer",
            "secret_type": "achievement",
            "name": "Первопроходец",
            "description": "Ты открыл 5 локаций. Ты — исследователь.",
            "trigger_condition": json.dumps({"type": "action_count", "action": "location_discover", "value": 5}),
            "reward": json.dumps({"memories": 10, "karma": 5}),
        },
        {
            "secret_id": "secret_whisperer",
            "secret_type": "achievement",
            "name": "Тихоня",
            "description": "Ты слушал шёпот тумана 10 раз. Он начал тебе доверять.",
            "trigger_condition": json.dumps({"type": "action_count", "action": "whisper", "value": 10}),
            "reward": json.dumps({"memories": 8, "karma": 3}),
        },
        {
            "secret_id": "secret_wolf_friend",
            "secret_type": "achievement",
            "name": "Друг волков",
            "description": "Ты покормил волка. Он запомнил тебя.",
            "trigger_condition": json.dumps({"type": "visit_location", "location": "wolf_den"}),
            "reward": json.dumps({"memories": 5, "karma": 5}),
        },
    ]

    for s in secrets:
        await db.execute(
            """INSERT OR REPLACE INTO secrets (secret_id, secret_type, name, description, trigger_condition, reward)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (s["secret_id"], s["secret_type"], s["name"], s["description"],
             s["trigger_condition"], s["reward"])
        )

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
    ]

    for loc_id, item_id, qty in ground:
        await db.execute(
            "INSERT INTO ground_items (location_id, item_id, quantity) VALUES (?, ?, ?)",
            (loc_id, item_id, qty)
        )

    await db.commit()

    await seed_shop()
    print("✅ Контент MIST загружен!")
    print(f"   📍 Локаций: {len(locations)}")
    print(f"   🐾 Существ: {len(creatures)}")
    print(f"   🏺 Предметов: {len(items)}")
    print(f"   📜 Квестов: {len(quests)}")
    print(f"   🔮 Секретов: {len(secrets)}")
    print(f"   📦 Предметов на земле: {len(ground)}")


if __name__ == "__main__":
    asyncio.run(seed())
