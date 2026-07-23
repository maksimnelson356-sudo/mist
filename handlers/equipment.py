from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
import game_engine as ge

router = Router()

@router.callback_query(F.data == "equipment_menu")
async def cb_equipment_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    equipment = ge.get_equipment(user_id)
    inventory = ge.get_inventory(user_id)

    lines = ["<b>🛡️ Снаряжение</b>\n"]
    buttons = []

    for slot_id, slot_name in ge.EQUIPMENT_SLOTS.items():
        item = equipment.get(slot_id)
        if item:
            lines.append(f"{slot_name}: {item['name']}")
            stats = ge.EQUIPMENT_STATS.get(item.get('item_id', ''), {})
            stat_parts = []
            if stats.get("attack"):
                stat_parts.append(f"Атака: +{stats['attack']}")
            if stats.get("defense"):
                stat_parts.append(f"Защита: +{stats['defense']}")
            if stats.get("max_hp"):
                stat_parts.append(f"HP: +{stats['max_hp']}")
            if stat_parts:
                lines.append(f"   {', '.join(stat_parts)}")
            buttons.append([
                InlineKeyboardButton(text=f"❌ Снять {slot_name}", callback_data=f"unequip:{slot_id}")
            ])
        else:
            lines.append(f"{slot_name}: Пусто")

    equipable_items = []
    for inv_item in inventory:
        item_id = inv_item["item_id"]
        stats = ge.EQUIPMENT_STATS.get(item_id, {})
        if stats.get("slot"):
            equipable_items.append((inv_item, stats))

    if equipable_items:
        lines.append("\n📦 <b>Доступные предметы:</b>")
        for inv_item, stats in equipable_items:
            slot = stats["slot"]
            slot_name = ge.EQUIPMENT_SLOTS.get(slot, slot)
            stat_parts = []
            if stats.get("attack"):
                stat_parts.append(f"Ат: +{stats['attack']}")
            if stats.get("defense"):
                stat_parts.append(f"Защ: +{stats['defense']}")
            if stats.get("max_hp"):
                stat_parts.append(f"HP: +{stats['max_hp']}")
            stat_text = f" ({', '.join(stat_parts)})" if stat_parts else ""
            qty_text = f" x{inv_item['quantity']}" if inv_item.get("quantity", 1) > 1 else ""
            btn_text = f"{slot_name} {inv_item['name']}{stat_text}{qty_text}"
            buttons.append([
                InlineKeyboardButton(text=btn_text, callback_data=f"equip:{inv_item['item_id']}")
            ])

    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
    ])

    text = "\n".join(lines)
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("equip:"))
async def cb_equip(callback: CallbackQuery):
    user_id = callback.from_user.id
    item_id = callback.data.split(":", 1)[1]

    result = ge.equip_item(user_id, item_id)

    if result["success"]:
        await callback.answer(result["message"], show_alert=True)
    else:
        await callback.answer(result["message"], show_alert=True)
        return

    await cb_equipment_menu(callback)

@router.callback_query(F.data.startswith("unequip:"))
async def cb_unequip(callback: CallbackQuery):
    user_id = callback.from_user.id
    slot = callback.data.split(":", 1)[1]

    result = ge.unequip_item(user_id, slot)

    if result["success"]:
        await callback.answer(result["message"], show_alert=True)
    else:
        await callback.answer(result["message"], show_alert=True)
        return

    await cb_equipment_menu(callback)