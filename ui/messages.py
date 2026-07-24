WELCOME = (
    "🌫 <b>Добро пожаловать в MIST</b>\n\n"
    "Ты просыпаешься в тумане.\n"
    "Не помнишь, как сюда попал.\n\n"
    "Туман помнит всё.\n\n"
    "📍 <b>{location}</b>\n"
    "❤️ HP: {hp}/{max_hp} | ⭐ Ур. {level}\n"
    "🪙 {gold} | 💎 {gems} | 🎫 {tokens}\n"
)

DEATH = (
    "<pre>💀\n🕯️👁🕯️\n💀</pre>\n"
    "💀 <b>Ты мёртв.</b>\n\n"
    "Туман накрыл тебя. Но он не отпускает.\n"
    "Ты чувствуешь — ты ещё нужен."
)

STATUS = (
    "👤 <b>{name}</b>\n\n"
    "❤️ HP: {hp}/{max_hp}\n"
    "⭐ Уровень: {level} (XP: {xp}/{xp_needed})\n"
    "⚔️ Атака: {attack} | 🛡️ Защита: {defense}\n"
    "🪙 Золото: {gold} | 💎 Камни: {gems} | 🎫 Токены: {tokens}\n"
    "📊 Репутация: {reputation} ({rep_level})\n"
    "🏆 PvP: {pvp_wins} побед / {pvp_losses} поражений\n"
    "📅 Дней в MIST: {days}"
)

NO_ITEMS = "🎒 <b>Инвентарь пуст</b>\n\nНайди что-нибудь в тумане."

HEAL_SUCCESS = "💚 <b>Исцеление</b>\n\nHP восстановлены: {hp}/{max_hp}"

HEAL_ALREADY = "💚 <b>Уже здоров</b>\n\nHP: {hp}/{max_hp}"

COMBAT_START = (
    "⚔️ <b>Бой начинается!</b>\n\n"
    "Противник: {enemy_name}\n"
    "HP противника: {enemy_hp}\n\n"
    "Твои HP: {hp}/{max_hp}"
)

COMBAT_VICTORY = (
    "🏆 <b>Победа!</b>\n\n"
    "Ты победил {enemy_name}!\n"
    "Получено: +{xp} XP, +{gold} 🪙"
)

COMBAT_DEFEAT = (
    "💀 <b>Поражение...</b>\n\n"
    "Ты был повержен {enemy_name}.\n"
    "Туман накрывает тебя..."
)

QUEST_ACCEPTED = "📜 <b>Квест принят:</b> {name}\n\n{description}"

QUEST_COMPLETED = (
    "✅ <b>Квест выполнен!</b>\n\n"
    "{name}\n"
    "Награда: +{xp} XP, +{gold} 🪙"
)

GUILD_CREATED = "🏰 <b>Гильдия «{name}» создана!</b>"

GUILD_JOINED = "🏰 <b>Ты вступил в «{name}»!</b>"

TRADE_OFFER = (
    "🤝 <b>Предложение трейда</b>\n\n"
    "От: {from_name}\n"
    "Предлагает: {offers}\n"
    "Хочет: {wants}"
)

ACHIEVEMENT_UNLOCKED = (
    "🔓 <b>Новое достижение!</b>\n\n"
    "{icon} {name}\n"
    "{description}\n"
    "Награда: +{xp} XP, +{gold} 🪙"
)

NPC_TALK = "🗣️ <b>{name}</b>\n\n{dialogue}"

SHOP_BUY = "🛒 <b>Куплено:</b> {name} x{qty} за {price} 🪙"

SHOP_SELL = "💰 <b>Продано:</b> {name} x{qty} за {price} 🪙"

CRAFT_SUCCESS = "⚒️ <b>Скрафчено:</b> {name} x{qty}"

DAILY_COMPLETE = "📅 <b>Ежедневный квест выполнен!</b>\n\n+{xp} XP, +{gold} 🪙"
