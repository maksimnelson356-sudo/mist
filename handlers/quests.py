import json
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import game_engine as ge

router = Router()


@router.message(Command("quests"))
async def cmd_quests(message: Message):
    quests = await ge.get_user_quests(message.from_user.id)

    if not quests:
        await message.answer("📜 У тебя нет активных квестов.\n\nИспользуй /quest_list чтобы увидеть доступные.")
        return

    text = "📜 *Твои квесты:*\n\n"
    for q in quests:
        status_icon = "⏳" if q["status"] == "active" else "✅"
        progress = json.loads(q["progress"]) if isinstance(q["progress"], str) else q["progress"]

        text += f"{status_icon} *{q['name']}*\n"
        text += f"_{q['description']}_\n"

        objectives = json.loads(q["objectives"]) if isinstance(q["objectives"], str) else q["objectives"]
        for obj in objectives:
            p = progress.get(obj["id"], {"current": 0, "target": obj["target"]})
            bar = "█" * (p["current"] // max(1, p["target"]) * 10) + "░" * (10 - p["current"] // max(1, p["target"]) * 10)
            text += f"  {obj['description']}: {p['current']}/{p['target']} {bar}\n"

        text += "\n"

    await message.answer(text, parse_mode="Markdown")


@router.message(Command("quest_list"))
async def cmd_quest_list(message: Message):
    user = await ge.get_or_create_user(message.from_user.id)
    quests = await ge.get_available_quests(message.from_user.id, user["current_location"])

    if not quests:
        await message.answer("📜 Нет доступных квестов в этой области.")
        return

    text = "📜 *Доступные квесты:*\n\n"
    for q in quests:
        rewards = json.loads(q["rewards"]) if isinstance(q["rewards"], str) else q["rewards"]
        reward_text = []
        if "xp" in rewards:
            reward_text.append(f"+{rewards['xp']} XP")
        if "memories" in rewards:
            reward_text.append(f"+{rewards['memories']} воспоминаний")
        if "karma" in rewards:
            reward_text.append(f"+{rewards['karma']} карма")

        text += f"📜 *{q['name']}*\n"
        text += f"_{q['description']}_\n"
        text += f"Награда: {', '.join(reward_text)}\n"
        text += f"/accept_{q['quest_id']} — принять\n\n"

    await message.answer(text, parse_mode="Markdown")


@router.message(Command("accept"))
async def cmd_accept(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Какой квест принять? Используй /quest_list")
        return

    quest_id = parts[1]
    result = await ge.accept_quest(message.from_user.id, quest_id)
    await message.answer(result["message"], parse_mode="Markdown")


@router.message(F.text.startswith("/accept_"))
async def cmd_accept_short(message: Message):
    quest_id = message.text.replace("/accept_", "")
    result = await ge.accept_quest(message.from_user.id, quest_id)
    await message.answer(result["message"], parse_mode="Markdown")


@router.message(Command("quest_complete"))
async def cmd_quest_complete(message: Message):
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Формат: /quest_complete [quest_id] [objective_id]")
        return

    quest_id = parts[1]
    objective_id = parts[2]

    result = await ge.update_quest_progress(message.from_user.id, quest_id, objective_id)

    if result["success"]:
        if result["completed"]:
            rewards = result["rewards"]
            reward_text = []
            if "xp" in rewards:
                reward_text.append(f"+{rewards['xp']} XP")
            if "memories" in rewards:
                reward_text.append(f"+{rewards['memories']} воспоминаний")
            if "karma" in rewards:
                reward_text.append(f"+{rewards['karma']} карма")

            text = f"{result['message']}\n\n🎁 Награда: {', '.join(reward_text)}"
        else:
            text = "📝 Прогресс обновлён."
    else:
        text = "❌ Не удалось обновить прогресс."

    await message.answer(text, parse_mode="Markdown")
