import logging

logger = logging.getLogger("MIST.dialogue")

DIALOGUES = {
    "elder": {
        "greeting": {
            "text": "Здравствуй, путник. Ты пришёл не вовремя... или вовремя. Туман не различает.",
            "options": [
                {"text": "Расскажи о тумане", "next": "about_mist", "req_rep": 0},
                {"text": "Что здесь случилось?", "next": "what_happened"},
                {"text": "Ухожу.", "next": None},
            ],
        },
        "about_mist": {
            "text": "Туман — это дыхание старого мира. Он пожирает то, что забывают. Чем больше людей покидает место, тем гуще туман.",
            "options": [
                {"text": "Можно ли его остановить?", "next": "stop_mist", "req_rep": 30},
                {"text": "Спасибо за историю.", "next": None},
            ],
        },
        "stop_mist": {
            "text": "Говорят, в Сердце MIST есть алтарь. Если принести ему жертву, туман отступит. Но кто решится?",
            "options": [
                {"text": "Я решусь.", "next": "brave_choice", "req_rep": 50},
                {"text": "Это слишком опасно.", "next": None},
            ],
        },
        "brave_choice": {
            "text": "Ты смел... или безумен. Алтарь в Сердце MIST. Но сначала — докажи, что ты достоин. Принеси мне Кристалл Тумана.",
            "options": [
                {"text": "Я найду его.", "next": None, "give_quest": "crystal_of_mist"},
            ],
        },
        "what_happened": {
            "text": "Здесь стояло село. Потом пришёл пожар. Потом — туман. Теперь только ветер и воспоминания.",
            "options": [
                {"text": "Кто виноват?", "next": "who_to_blame"},
                {"text": "Жалею.", "next": None},
            ],
        },
        "who_to_blame": {
            "text": "Никто и все. Туман не выбирает. Он просто есть.",
            "options": [
                {"text": "Понимаю.", "next": None},
            ],
        },
    },
    "bartender": {
        "greeting": {
            "text": "А, новое лицо. Или ты уже был здесь? Тут сложно отличить.",
            "options": [
                {"text": "Что слышно?", "next": "rumors"},
                {"text": "Налей что-нибудь.", "next": "drink"},
                {"text": "Просто прохожу.", "next": None},
            ],
        },
        "rumors": {
            "text": "Говорят, в Тёмном лесе видели свет. Не огонь — что-то другое. Ещё говорят, что Кракен вернулся.",
            "options": [
                {"text": "Расскажи про свет.", "next": "light_rumor"},
                {"text": "Расскажи про Кракена.", "next": "kraken_rumor"},
                {"text": "Хватит слухов.", "next": None},
            ],
        },
        "light_rumor": {
            "text": "Свет появляется по ночам. Говорят, это душа старого мага. Он ищет свой посох.",
            "options": [
                {"text": "Могу найти посох.", "next": None, "give_quest": "find_staff"},
                {"text": "Звучит опасно.", "next": None},
            ],
        },
        "kraken_rumor": {
            "text": "Кракен поднял волну. Рыбаки боятся выходить. Если убьёшь его — станешь легендой.",
            "options": [
                {"text": "Я попробую.", "next": None, "give_quest": "hunt_kraken"},
                {"text": "Я безумец, но не настолько.", "next": None},
            ],
        },
        "drink": {
            "text": "Держи. Это специальное зелье. +5 HP на 10 минут. Стоит 20 золотых.",
            "options": [
                {"text": "Беру (20 🪙)", "next": "drink_bought", "cost_gold": 20},
                {"text": "Дорого.", "next": None},
            ],
        },
        "drink_bought": {
            "text": "Приятного аппетита. И не забудь — в тумане всё забывается. Даже вкус.",
            "options": [
                {"text": "Спасибо.", "next": None},
            ],
        },
    },
    "merchant": {
        "greeting": {
            "text": "Добро пожаловать! У меня есть то, что тебе нужно. И то, что тебе не нужно.",
            "options": [
                {"text": "Что продаёшь?", "next": "wares"},
                {"text": "Что покупашь?", "next": "buying"},
                {"text": "Ничего не нужно.", "next": None},
            ],
        },
        "wares": {
            "text": "Зелья, свитки, редкие камни. Но у меня есть и кое-что особенное... Если у тебя хватит золота.",
            "options": [
                {"text": "Покажи особенное.", "next": "special", "req_gold": 100},
                {"text": "Обычные товары.", "next": None},
            ],
        },
        "special": {
            "text": "Этот камень светится. Говорят, он падал с неба. Стоит 100 золотых. Но он может спасти тебе жизнь.",
            "options": [
                {"text": "Беру (100 🪙)", "next": "special_bought", "cost_gold": 100},
                {"text": "Слишком дорого.", "next": None},
            ],
        },
        "special_bought": {
            "text": "Мудрый выбор. Или безумный. Время покажет.",
            "options": [
                {"text": "До встречи.", "next": None},
            ],
        },
        "buying": {
            "text": "Покупаю всё, что блестит. Зубы волков, перья воронов, старые монеты. Принеси — заплачу.",
            "options": [
                {"text": "Хорошо, поищу.", "next": None},
            ],
        },
    },
    "shady": {
        "greeting": {
            "text": "...Ты не из местных. И я тоже. Может, нам не о чём говорить.",
            "options": [
                {"text": "У меня есть информация.", "next": "info_trade", "req_rep": 20},
                {"text": "Что скрываешь?", "next": "what_hidden"},
                {"text": "Ухожу.", "next": None},
            ],
        },
        "what_hidden": {
            "text": "Всё. Ничего. Ты не должен знать. Но... если принесёшь мне Кристалл Тумана, я расскажу кое-что важное.",
            "options": [
                {"text": "Хорошо.", "next": None},
            ],
        },
        "info_trade": {
            "text": "Информация — товар дорогой. Но если ты знаешь что-то о Теневом короле... Я могу заплатить.",
            "options": [
                {"text": "Что ты знаешь о Теневом короле?", "next": "shadow_king", "req_rep": 50},
                {"text": "Ничего особенного.", "next": None},
            ],
        },
        "shadow_king": {
            "text": "Он правит Теневым рынком. Его тень — повсюду. Но у него есть слабость. Серебро. Чистое серебро.",
            "options": [
                {"text": "Спасибо за информацию.", "next": None},
            ],
        },
    },
}

DIALOGUE_QUESTS = {
    "crystal_of_mist": {
        "name": "Кристалл Тумана",
        "description": "Найди Кристалл Тумана для старейшины.",
        "location": "heart_of_mist",
    },
    "find_staff": {
        "name": "Посох мага",
        "description": "Найди посох старого мага в Тёмном лесу.",
        "location": "dark_forest",
    },
    "hunt_kraken": {
        "name": "Охота на Кракена",
        "description": "Победи Кракена в Тёмной гавани.",
        "location": "dark_harbour",
    },
}


class DialogueService:

    def __init__(self, chronicle, player):
        self.chronicle = chronicle
        self.player = player

    async def get_dialogue(self, npc_id: str, npc_type: str, user_id: int = None) -> dict:
        dialogue_tree = DIALOGUES.get(npc_type)
        if not dialogue_tree:
            return {"text": "NPC молчит.", "options": []}

        greeting = dialogue_tree.get("greeting", {})
        text = greeting.get("text", "...")
        options = greeting.get("options", [])

        if user_id:
            user = await self.player.get(user_id)
            reputation = user.get("reputation", 0) if user else 0
            gold = user.get("gold", 0) if user else 0
            player_class = user.get("player_class", "warrior") if user else "warrior"

            class_greetings = {
                "warrior": "\n\nЯ вижу на тебе следы戰争. Ты воин?",
                "mage": "\n\nТы пахнешь магией. Осторожнее здесь.",
                "scout": "\n\nТы двигаешься тихо. Разведчик?",
                "craftsman": "\n\nУ тебя руки мастера. Ты чинишь?",
            }
            if player_class in class_greetings:
                text += class_greetings[player_class]

            filtered_options = []
            for opt in options:
                req_rep = opt.get("req_rep", -999)
                req_gold = opt.get("req_gold", 0)
                if reputation >= req_rep and gold >= req_gold:
                    filtered_options.append(opt)
            options = filtered_options

        return {"text": text, "options": options, "npc_type": npc_type}

    async def continue_dialogue(self, npc_type: str, choice_id: str, user_id: int) -> dict:
        dialogue_tree = DIALOGUES.get(npc_type, {})
        node = dialogue_tree.get(choice_id)

        if not node:
            return {"text": "Диалог завершён.", "options": [], "finished": True}

        text = node.get("text", "...")
        options = node.get("options", [])

        result = {"text": text, "options": options, "finished": False}

        cost_gold = node.get("cost_gold", 0)
        if cost_gold > 0:
            user = await self.player.get(user_id)
            if user and user["gold"] >= cost_gold:
                from sqlalchemy import update

                from database.base import get_db
                from database.models.user import UserModel
                async for db in get_db():
                    await db.execute(
                        update(UserModel)
                        .where(UserModel.user_id == user_id)
                        .values(gold=user["gold"] - cost_gold)
                    )
                    await db.commit()
                result["gold_spent"] = cost_gold
            else:
                result["text"] = "У тебя недостаточно золота."
                result["options"] = []
                result["finished"] = True
                return result

        give_quest = node.get("give_quest")
        if give_quest:
            quest_def = DIALOGUE_QUESTS.get(give_quest)
            if quest_def:
                result["quest"] = quest_def
                result["text"] += f"\n\n📜 Новый квест: {quest_def['name']}"

        if user_id:
            user = await self.player.get(user_id)
            reputation = user.get("reputation", 0) if user else 0
            user_gold = user.get("gold", 0) if user else 0
            filtered_options = []
            for opt in options:
                req_rep = opt.get("req_rep", -999)
                req_gold = opt.get("req_gold", 0)
                if reputation >= req_rep and user_gold >= req_gold:
                    filtered_options.append(opt)
            result["options"] = filtered_options

        return result
