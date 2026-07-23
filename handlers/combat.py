from aiogram import Router, F
from aiogram.types import CallbackQuery
import game_engine as ge

router = Router()


# Боевые колбэки уже обработаны в game.py (cb_fight_menu, cb_attack)
# Этот хендлер добавляет логирование квестов при убийстве существ

@router.callback_query(F.data.startswith("attack:"))
async def cb_attack_quest_progress(callback: CallbackQuery):
    creature_id = callback.data.split(":")[1]

    user_quests = await ge.get_user_quests(callback.from_user.id)
    for uq in user_quests:
        if uq["status"] != "active":
            continue
        import json
        objectives = json.loads(uq["objectives"]) if isinstance(uq["objectives"], str) else uq["objectives"]
        for obj in objectives:
            if obj.get("type") == "kill" and obj.get("creature") == creature_id:
                await ge.update_quest_progress(
                    callback.from_user.id, uq["quest_id"], obj["id"]
                )
