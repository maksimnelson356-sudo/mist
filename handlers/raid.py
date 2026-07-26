from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from services.container import services
from services.world_boss_service import WORLD_BOSS_DEFS

router = Router()


@router.callback_query(F.data == "raid_menu")
async def cb_raid_menu(callback: CallbackQuery):
    active_raids = await services.raid.get_active_raids()

    text = "🐉 <b>Рейды</b>\n\n"

    if not active_raids:
        text += (
            "Нет активных рейдов.\n\n"
            "Рейды — групповые бои с боссами.\n"
            "Нужно 2-5 игроков, чтобы победить."
        )
        buttons = [
            [InlineKeyboardButton(text="📢 Создать рейд", callback_data="raid_create")],
        ]
    else:
        text += "<b>Активные рейды:</b>\n"
        buttons = []
        for r in active_raids:
            hp_pct = int(r["hp"] / r["max_hp"] * 100)
            text += f"🐉 {r['name']} — {hp_pct}% | 👥 {r['participants']}\n"
            buttons.append([InlineKeyboardButton(
                text=f"⚔️ {r['name']} ({r['participants']} игроков)",
                callback_data=f"raid_join:{r['boss_id']}"
            )])
        buttons.append([InlineKeyboardButton(text="📢 Создать рейд", callback_data="raid_create")])

    buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data == "raid_create")
async def cb_raid_create(callback: CallbackQuery):
    text = "📢 <b>Создать рейд</b>\n\nВыбери босса:\n\n"
    buttons = []
    for bd in WORLD_BOSS_DEFS:
        text += f"🐉 {bd['name']} — HP: {bd['hp']}, Атака: {bd['attack']}\n"
        buttons.append([InlineKeyboardButton(
            text=f"🐉 {bd['name']}",
            callback_data=f"raid_create:{bd['boss_id']}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="raid_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data.startswith("raid_create:"))
async def cb_raid_create_confirm(callback: CallbackQuery):
    boss_id = callback.data.split(":")[1]
    result = await services.raid.create_raid(boss_id, callback.from_user.id)

    if result["success"]:
        text = f"✅ {result['message']}"
    else:
        text = f"❌ {result['message']}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐉 Рейды", callback_data="raid_menu")],
        [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data.startswith("raid_join:"))
async def cb_raid_join(callback: CallbackQuery):
    boss_id = callback.data.split(":")[1]
    result = await services.raid.join_raid(boss_id, callback.from_user.id)

    if result["success"]:
        text = f"✅ {result['message']}"
    else:
        text = f"❌ {result['message']}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⚔️ Атаковать", callback_data=f"raid_attack:{boss_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="raid_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
@router.callback_query(F.data.startswith("raid_attack:"))
async def cb_raid_attack(callback: CallbackQuery):
    boss_id = callback.data.split(":")[1]
    result = await services.raid.raid_attack(boss_id, callback.from_user.id)

    if not result["success"]:
        await callback.answer(result["message"], show_alert=True)
        return

    if result["killed"]:
        text = (
            f"🏆 <b>РЕЙД ПОБЕДИЛ!</b>\n\n"
            f"⚔️ Твой урон: {result['damage']}\n"
            f"XP: +{result['xp_reward']}\n"
            f"Gold: +{result['gold_reward']}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
        ])
    else:
        hp_pct = int(result["hp_left"] / (result["hp_left"] + result["damage"]) * 100)
        text = (
            f"⚔️ <b>Рейд атакует!</b>\n\n"
            f"Твой урон: {result['damage']}\n"
            f"❤️ Босс: {result['hp_left']} ({hp_pct}%)\n"
            f"📊 Фаза: {result['phase']}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚔️ Ещё удар", callback_data=f"raid_attack:{boss_id}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="raid_menu")],
        ])

    await callback.message.edit_text(text, reply_markup=kb)
