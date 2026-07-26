from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from services.container import services
from services.artifact_service import ARTIFACT_DEFS

router = Router()

RARITY_ICONS = {
    "legendary": "🟡",
    "epic": "🟣",
    "rare": "🔵",
    "uncommon": "🟢",
    "common": "⚪",
}

RARITY_NAMES = {
    "legendary": "Легендарный",
    "epic": "Эпический",
    "rare": "Редкий",
    "uncommon": "Необычный",
    "common": "Обычный",
}


@router.callback_query(F.data == "artifact_menu")
async def cb_artifact_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    artifacts = await services.artifact.get_by_owner(user_id)
    stats = await services.artifact.get_artifact_stats()

    text = (
        f"🏺 <b>Артефакты</b>\n\n"
        f"Найдено: {stats['found']} / {stats['total']}\n\n"
    )

    if not artifacts:
        text += (
            "У тебя нет артефактов.\n\n"
            "Артефакты скрыты в тумане. Они ждут тех, кто осмелится искать.\n"
            "Каждый артефакт — живая вещь. Он растёт с тобой."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")],
        ])
    else:
        buttons = []
        for a in artifacts:
            icon = RARITY_ICONS.get(a["rarity"], "⚪")
            uses = a.get("times_used", 0)
            text += f"{icon} <b>{a['name']}</b> — использований: {uses}\n"

            buttons.append([InlineKeyboardButton(
                text=f"{icon} {a['name']}",
                callback_data=f"artifact_view:{a['artifact_id']}"
            )])

        buttons.append([InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("artifact_view:"))
async def cb_artifact_view(callback: CallbackQuery):
    artifact_id = callback.data.split(":")[1]
    artifact = await services.artifact.get(artifact_id)

    if not artifact:
        await callback.answer("Артефакт не найден.", show_alert=True)
        return

    rarity_icon = RARITY_ICONS.get(artifact["rarity"], "⚪")
    rarity_name = RARITY_NAMES.get(artifact["rarity"], artifact["rarity"])

    text = (
        f"{rarity_icon} <b>{artifact['name']}</b>\n"
        f"<i>{rarity_name} • {artifact['artifact_type']}</i>\n\n"
        f"{artifact['description']}\n\n"
    )

    stats = artifact.get("stats", {})
    if stats:
        stat_parts = []
        for k, v in stats.items():
            if isinstance(v, bool):
                if v:
                    stat_parts.append(k.replace("_", " "))
            elif isinstance(v, float):
                stat_parts.append(f"+{int(v*100)}% {k.replace('_', ' ')}")
            else:
                stat_parts.append(f"+{v} {k.replace('_', ' ')}")
        text += f"📊 <b>Характеристики:</b> {', '.join(stat_parts)}\n\n"

    if artifact.get("blessing"):
        text += f"✨ <b>Благословение:</b> {artifact['blessing']}\n"
    if artifact.get("curse"):
        text += f"💀 <b>Проклятие:</b> {artifact['curse']}\n"

    uses = artifact.get("times_used", 0)
    kills = artifact.get("kills_with", 0)
    saves = artifact.get("saves_with", 0)
    text += f"\n📈 Использований: {uses} | Убийств: {kills} | Спасений: {saves}\n"

    buttons = [
        [InlineKeyboardButton(text="🔮 Использовать", callback_data=f"artifact_use:{artifact_id}")],
        [InlineKeyboardButton(text="📖 Лора", callback_data=f"artifact_lore:{artifact_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="artifact_menu")],
    ]

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("artifact_use:"))
async def cb_artifact_use(callback: CallbackQuery):
    artifact_id = callback.data.split(":")[1]
    user_id = callback.from_user.id

    result = await services.artifact.use_artifact(artifact_id, user_id, action="use")

    if result["success"]:
        text = (
            f"🔮 Артефакт пропитался твоей энергией.\n"
            f"Использований: {result['times_used']}\n\n"
            f"📖 <i>{result['new_lore'][-200:]}</i>"
        )
    else:
        text = f"❌ {result['message']}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔮 Ещё", callback_data=f"artifact_use:{artifact_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"artifact_view:{artifact_id}")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("artifact_lore:"))
async def cb_artifact_lore(callback: CallbackQuery):
    artifact_id = callback.data.split(":")[1]
    artifact = await services.artifact.get(artifact_id)

    if not artifact:
        await callback.answer("Артефакт не найден.", show_alert=True)
        return

    text = (
        f"📖 <b>Лора: {artifact['name']}</b>\n\n"
        f"<i>{artifact.get('lore', 'История утеряна...')}</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"artifact_view:{artifact_id}")],
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
