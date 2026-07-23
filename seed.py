import json
import asyncio
import sys
sys.path.insert(0, '.')

from database.db import init_db, get_db


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
            "connections": json.dumps(["riverbank", "ancient_ruins", "wolf_den"]),
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
            "connections": json.dumps(["dark_forest", "fishing_village", "underwater_cave"]),
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
            "connections": json.dumps(["dark_forest", "library_of_echoes", "obsidian_tower"]),
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
            "connections": json.dumps(["fishing_village", "temple_of_shadows"]),
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
            "connections": json.dumps(["wolf_den", "white_forest"]),
            "is_secret": 0,
            "required_karma": 0,
        },
        {
            "location_id": "white_forest",
            "name": "Белый лес",
            "description": (
                "Деревья белые, как кости. Листьев нет. Снег —尽管是 лето. "
                "Здесь холодно. Не от температуры — от чего-то внутри.\n\n"
                "Это место помнит что-то страшное. И не хочет, чтобы ты знал что."
            ),
            "connections": json.dumps(["blood_meadow", "frozen_lake"]),
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
            "connections": json.dumps(["riverbank", "sunken_throne"]),
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
            "connections": json.dumps(["market_square", "void_gate"]),
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
                "Туман отступает. На мгновение ты видишь —千亿个 лиц. "
                "Тех, кто был до тебя. Тех, кто будет после.\n\n"
                "MIST — это не место. MIST — это ты."
            ),
            "connections": json.dumps(["frozen_lake", "void_gate"]),
            "is_secret": 1,
            "required_karma": 30,
        },
    ]

    for loc in locations:
        await db.execute(
            """INSERT OR REPLACE INTO locations (location_id, name, description, discovered, connections, is_secret, required_karma)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (loc["location_id"], loc["name"], loc["description"], loc["discovered"],
             loc["connections"], loc["is_secret"], loc["required_karma"])
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
            "quest_id": "q_wolf1",
            "name": "Волчий клык",
            "description": "Старый рыбак просит принести клык волка. Для ритуала.",
            "giver": "elder_fisherman",
            "location": "fishing_village",
            "objectives": json.dumps([{"id": "kill_wolf", "type": "kill", "creature": "wolf_pack", "target": 3, "description": "Убить 3 волков"}]),
            "rewards": json.dumps({"xp": 30, "memories": 2, "karma": 2, "items": [{"id": "healing_herb", "qty": 3}]}),
            "is_active": 1, "is_repeating": 1,
        },
        {
            "quest_id": "q_wolf2",
            "name": "Вожак стаи",
            "description": "Альфа-волк угрожает деревне. Убей его.",
            "giver": "elder_fisherman",
            "location": "fishing_village",
            "objectives": json.dumps([{"id": "kill_alpha", "type": "kill", "creature": "wolf_alpha", "target": 1, "description": "Убить альфа-волка"}]),
            "rewards": json.dumps({"xp": 60, "memories": 5, "karma": 5, "items": [{"id": "alpha_pelt", "qty": 1}]}),
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
            "rewards": json.dumps({"xp": 20, "memories": 3}),
            "is_active": 1, "is_repeating": 0,
        },
        {
            "quest_id": "q_ruins2",
            "name": "Голос книг",
            "description": "В библиотеке есть книга, которая говорит. Найди её.",
            "giver": "unknown",
            "location": "library_of_echoes",
            "objectives": json.dumps([{"id": "visit_library", "type": "visit", "location": "library_of_echoes", "target": 1, "description": "Посетить библиотеку эхов"}]),
            "rewards": json.dumps({"xp": 30, "memories": 4, "items": [{"id": "echo_crystal", "qty": 1}]}),
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
            "rewards": json.dumps({"xp": 70, "memories": 6, "karma": 3}),
            "is_active": 1, "is_repeating": 0,
        },
        {
            "quest_id": "q_tower2",
            "name": "Вершина мира",
            "description": "Поднимись на вершину башни. Встреть Хранителя.",
            "giver": "unknown",
            "location": "tower_summit",
            "objectives": json.dumps([{"id": "visit_summit", "type": "visit", "location": "tower_summit", "target": 1, "description": "Подняться на вершину"}]),
            "rewards": json.dumps({"xp": 100, "memories": 10, "karma": 10, "items": [{"id": "keeper_key", "qty": 1}]}),
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
            "rewards": json.dumps({"xp": 40, "memories": 5, "karma": -3}),
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
            "rewards": json.dumps({"xp": 30, "memories": 4}),
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
            "rewards": json.dumps({"xp": 200, "memories": 20, "karma": 15, "items": [{"id": "legendary_essence", "qty": 1}]}),
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
            "rewards": json.dumps({"xp": 40, "memories": 3, "karma": 2}),
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

    await db.commit()
    print("✅ Контент MIST загружен!")
    print(f"   📍 Локаций: {len(locations)}")
    print(f"   🐾 Существ: {len(creatures)}")
    print(f"   🏺 Предметов: {len(items)}")
    print(f"   📜 Квестов: {len(quests)}")
    print(f"   🔮 Секретов: {len(secrets)}")


if __name__ == "__main__":
    asyncio.run(seed())
