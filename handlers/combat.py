import json
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import game_engine as ge

router = Router()


@router.message(Command("attack"))
async def cmd_attack(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Кого атаковать? Используй /look чтобы увидеть существ.")
        return

    creature_id = parts[1]
    result = await ge.start_combat(message.from_user.id, creature_id)

    if not result["success"]:
        await message.answer(result["message"])
        return

    combat = await ge.resolve_combat(message.from_user.id, creature_id)
    text = ge.format_combat_result(combat, result["creature"]["name"])
    await message.answer(text, parse_mode="Markdown")

    # Обновляем прогресс квестов на убийство существ
    if combat.get("outcome") == "victory":
        user_quests = await ge.get_user_quests(message.from_user.id)
        for uq in user_quests:
            if uq["status"] != "active":
                continue
            objectives = json.loads(uq["objectives"]) if isinstance(uq["objectives"], str) else uq["objectives"]
            for obj in objectives:
                if obj.get("type") == "kill" and obj.get("creature") == creature_id:
                    await ge.update_quest_progress(
                        message.from_user.id, uq["quest_id"], obj["id"]
                    )


@router.message(Command("fight"))
async def cmd_fight(message: Message):
    user = await ge.get_or_create_user(message.from_user.id)
    creatures = await ge.get_creatures_at_location(user["current_location"])

    hostile = [c for c in creatures if c["disposition"] in ("hostile", "neutral") and c["is_alive"]]

    if not hostile:
        await message.answer("Здесь нет существ для боя.")
        return

    text = "⚔️ *Доступные противники:*\n\n"
    for c in hostile:
        text += f"• /attack_{c['creature_id']} — {c['name']} (HP: {c['hp']})\n"

    await message.answer(text, parse_mode="Markdown")


@router.message(F.text.startswith("/attack_"))
async def cmd_attack_short(message: Message):
    creature_id = message.text.replace("/attack_", "")
    result = await ge.start_combat(message.from_user.id, creature_id)

    if not result["success"]:
        await message.answer(result["message"])
        return

    combat = await ge.resolve_combat(message.from_user.id, creature_id)
    text = ge.format_combat_result(combat, result["creature"]["name"])
    await message.answer(text, parse_mode="Markdown")

    # Обновляем прогресс квестов на убийство существ
    if combat.get("outcome") == "victory":
        user_quests = await ge.get_user_quests(message.from_user.id)
        for uq in user_quests:
            if uq["status"] != "active":
                continue
            objectives = json.loads(uq["objectives"]) if isinstance(uq["objectives"], str) else uq["objectives"]
            for obj in objectives:
                if obj.get("type") == "kill" and obj.get("creature") == creature_id:
                    await ge.update_quest_progress(
                        message.from_user.id, uq["quest_id"], obj["id"]
                    )


@router.message(Command("heal"))
async def cmd_heal(message: Message):
    user = await ge.get_or_create_user(message.from_user.id)

    if user["hp"] >= user["max_hp"]:
        await message.answer("❤️ Твоё HP уже максимум.")
        return

    heal_amount = min(30, user["max_hp"] - user["hp"])
    await ge.update_user(message.from_user.id, hp=user["hp"] + heal_amount)
    await ge._log_action(message.from_user.id, "heal", {"amount": heal_amount})

    await message.answer(
        f"💚 Ты восстановил *{heal_amount}* HP.\n"
        f"❤️ HP: {user['hp'] + heal_amount}/{user['max_hp']}",
        parse_mode="Markdown"
    )


@router.message(Command("combat_history"))
async def cmd_combat_history(message: Message):
    history = await ge.get_combat_history(message.from_user.id, limit=10)

    if not history:
        await message.answer("⚔️ Ты ещё не сражался.")
        return

    text = "⚔️ *История боёв:*\n\n"
    icons = {"victory": "🏆", "defeat": "💀", "draw": "🤝"}

    for h in history:
        icon = icons.get(h["result"], "?")
        text += f"{icon} {h['creature_id']} — +{h['xp_gained']} XP\n"

    await message.answer(text, parse_mode="Markdown")
