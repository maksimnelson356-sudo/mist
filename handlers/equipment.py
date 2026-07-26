from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from services.container import services
from services.equipment_service import EquipmentService

router = Router()

@router.callback_query(F.data == "equipment_menu")
async def cb_equipment_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    equipment = await services.equipment.get_equipment(user_id)
    inventory = await services.inventory.get(user_id)

    lines = ["<b>🛡️ Снаряжение</b>\n"]
    buttons = []

    for slot_id, slot_name in EquipmentService.EQUIPMENT_SLOTS.items():
        item = equipment.get(slot_id)
        if item:
            lines.append(f"{slot_name}: {item['name']}")
            stats = EquipmentService.EQUIPMENT_STATS.get(item.get('item_id', ''), {})
            stat_parts = []
            if stats.get("attack"):
                stat_parts.append(f"Атака: +{stats['attack']}")
            if stats.get("defense"):
                stat_parts.append(f"Защита: +{stats['defense']}")
            if stats.get("max_hp"):
                stat_parts.append(f"HP: +{stats['max_hp']}")
            if stat_parts:
                lines.append(f"   {', '.join(stat_parts)}")

            inv_candidates = [i for i in inventory if EquipmentService.EQUIPMENT_STATS.get(i["item_id"], {}).get("slot") == slot_id]
            if inv_candidates:
                buttons.append([
                    InlineKeyboardButton(text=f"⚖️ Сравнить {slot_name}", callback_data=f"compare:{slot_id}")
                ])

            buttons.append([
                InlineKeyboardButton(text=f"❌ Снять {slot_name}", callback_data=f"unequip:{slot_id}")
            ])
        else:
            lines.append(f"{slot_name}: Пусто")

    equipable_items = []
    for inv_item in inventory:
        item_id = inv_item["item_id"]
        stats = EquipmentService.EQUIPMENT_STATS.get(item_id, {})
        if stats.get("slot"):
            equipable_items.append((inv_item, stats))

    if equipable_items:
        lines.append("\n📦 <b>Доступные предметы:</b>")
        for inv_item, stats in equipable_items:
            slot = stats["slot"]
            slot_name = EquipmentService.EQUIPMENT_SLOTS.get(slot, slot)
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
@router.callback_query(F.data.startswith("equip:"))
async def cb_equip(callback: CallbackQuery):
    user_id = callback.from_user.id
    item_id = callback.data.split(":", 1)[1]

    result = await services.equipment.equip(user_id, item_id)

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

    result = await services.equipment.unequip(user_id, slot)

    if result["success"]:
        await callback.answer(result["message"], show_alert=True)
    else:
        await callback.answer(result["message"], show_alert=True)
        return

    await cb_equipment_menu(callback)

@router.callback_query(F.data.startswith("compare:"))
async def cb_compare(callback: CallbackQuery):
    user_id = callback.from_user.id
    slot = callback.data.split(":", 1)[1]
    equipment = await services.equipment.get_equipment(user_id)
    inventory = await services.inventory.get(user_id)

    current_item = equipment.get(slot)
    current_stats = {}
    if current_item:
        current_stats = EquipmentService.EQUIPMENT_STATS.get(current_item.get("item_id", ""), {})

    candidates = [
        i for i in inventory
        if EquipmentService.EQUIPMENT_STATS.get(i["item_id"], {}).get("slot") == slot
    ]

    slot_name = EquipmentService.EQUIPMENT_SLOTS.get(slot, slot)
    lines = [f"<b>⚖️ Сравнение: {slot_name}</b>\n"]

    def fmt(stats):
        parts = []
        for key, label in [("attack", "Ат"), ("defense", "Защ"), ("max_hp", "HP")]:
            val = stats.get(key)
            if val:
                parts.append(f"{label}: +{val}")
        return ", ".join(parts) if parts else "нет статов"

    if current_item:
        lines.append(f"<b>Текущее:</b> {current_item['name']}")
        lines.append(f"  {fmt(current_stats)}\n")
    else:
        lines.append("<b>Текущее:</b> Пусто\n")

    buttons = []
    for inv_item in candidates:
        inv_stats = EquipmentService.EQUIPMENT_STATS.get(inv_item["item_id"], {})
        diff_parts = []
        for key, label in [("attack", "Ат"), ("defense", "Защ"), ("max_hp", "HP")]:
            old = current_stats.get(key, 0)
            new = inv_stats.get(key, 0)
            delta = new - old
            if delta != 0:
                sign = "+" if delta > 0 else ""
                diff_parts.append(f"{label}: {sign}{delta}")
        diff_text = f" ({', '.join(diff_parts)})" if diff_parts else ""
        btn_text = f"{inv_item['name']}{diff_text}"
        buttons.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"equip:{inv_item['item_id']}")
        ])

    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="equipment_menu")
    ])

    text = "\n".join(lines)
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
