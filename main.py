import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

# =========================
# НАСТРОЙКИ
# =========================
API_TOKEN = "8350014461:AAEyVma4nqUQqtMc3vls8xyZ_AlJOoCezAY"  # <--- новый токен
ADMIN_ID = 1775076318
USERS_FILE = "users.txt"
STATUS_PHOTO = "status.jpg"  # <--- файл с фото для кнопки Статус

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()


# =========================
# РАБОТА С ПОЛЬЗОВАТЕЛЯМИ
# =========================
def save_user(user_id: int) -> bool:
    """Сохраняет пользователя, возвращает True если новый"""
    Path(USERS_FILE).touch(exist_ok=True)

    user_id = str(user_id)
    with open(USERS_FILE, "r+", encoding="utf-8") as f:
        users = f.read().splitlines()
        if user_id not in users:
            f.write(user_id + "\n")
            return True
    return False


def get_users() -> list[int]:
    Path(USERS_FILE).touch(exist_ok=True)

    users = []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.isdigit():
                users.append(int(line))
    return users


def remove_user(user_id: int):
    users = get_users()
    users = [u for u in users if u != user_id]

    with open(USERS_FILE, "w", encoding="utf-8") as f:
        for u in users:
            f.write(f"{u}\n")


# =========================
# КЛАВИАТУРА
# =========================
def get_main_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="🌐 МОЙ САЙТ"),
        types.KeyboardButton(text="📊 СТАТУС БАЙПАСА")
    )
    return builder.as_markup(resize_keyboard=True)


# =========================
# /start
# =========================
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    is_new = save_user(message.from_user.id)

    if is_new:
        username = f"@{message.from_user.username}" if message.from_user.username else "нет username"
        first_name = message.from_user.first_name or "Без имени"
        user_id = message.from_user.id

        try:
            await bot.send_message(
                ADMIN_ID,
                f"🆕 <b>Новый пользователь запустил бота</b>\n\n"
                f"👤 Имя: <b>{first_name}</b>\n"
                f"🔗 Username: <b>{username}</b>\n"
                f"🆔 ID: <code>{user_id}</code>"
            )
        except Exception as e:
            logger.warning(f"Не удалось отправить уведомление админу: {e}")

    await message.answer(
        "🦾 <b>HELIOS CORE</b> запущен.",
        reply_markup=get_main_kb()
    )


# =========================
# /id
# =========================
@dp.message(Command("id"))
async def cmd_id(message: types.Message):
    save_user(message.from_user.id)
    await message.answer(f"🆔 Ваш ID: <code>{message.from_user.id}</code>")


# =========================
# /users
# =========================
@dp.message(Command("users"))
async def cmd_users(message: types.Message):
    save_user(message.from_user.id)

    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ У вас нет прав.")

    users = get_users()
    await message.answer(f"👥 Всего пользователей: <b>{len(users)}</b>")


# =========================
# /send ТЕКСТ
# =========================
@dp.message(Command("send"))
async def cmd_send(message: types.Message):
    save_user(message.from_user.id)

    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ У вас нет прав.")

    args = message.text.replace("/send", "", 1).strip()
    if not args:
        return await message.answer("Использование:\n<code>/send Текст сообщения</code>")

    users = get_users()
    if not users:
        return await message.answer("⚠️ Список пользователей пуст.")

    sent = 0
    failed = 0
    blocked = 0

    await message.answer(f"📤 Начинаю рассылку по <b>{len(users)}</b> пользователям...")

    for user_id in users:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=f"📣 <b>ОБЪЯВЛЕНИЕ:</b>\n\n{args}"
            )
            sent += 1
            await asyncio.sleep(0.05)

        except TelegramForbiddenError:
            blocked += 1
            remove_user(user_id)

        except TelegramBadRequest as e:
            failed += 1
            logger.warning(f"Ошибка отправки {user_id}: {e}")

        except Exception as e:
            failed += 1
            logger.exception(f"Неизвестная ошибка при отправке {user_id}: {e}")

    await message.answer(
        f"✅ <b>Рассылка завершена</b>\n\n"
        f"📨 Отправлено: <b>{sent}</b>\n"
        f"🚫 Заблокировали бота: <b>{blocked}</b>\n"
        f"⚠️ Ошибок: <b>{failed}</b>"
    )


# =========================
# КНОПКИ
# =========================
@dp.message(lambda message: message.text == "📊 СТАТУС БАЙПАСА")
async def bypass_status(message: types.Message):
    save_user(message.from_user.id)

    status_text = (
        "📡 <b>STATUS</b>\n\n"
        "<code>"
        "gl-not safe\n"
        "tw-safe\n"
        "kr-safe\n"
        "vng-test"
        "</code>"
    )

    try:
        photo = types.FSInputFile(STATUS_PHOTO)
        await message.answer_photo(
            photo=photo,
            caption=status_text
        )
    except Exception as e:
        logger.error(f"Ошибка отправки фото статуса: {e}")
        await message.answer("❌ Не удалось отправить фото статуса.")


@dp.message(lambda message: message.text == "🌐 МОЙ САЙТ")
async def my_site(message: types.Message):
    save_user(message.from_user.id)
    await message.answer("Сайт: https://krytouperec.vercel.app/")


# =========================
# ВСЁ ОСТАЛЬНОЕ
# =========================
@dp.message()
async def fallback(message: types.Message):
    save_user(message.from_user.id)
    await message.answer("Используй кнопки меню 👇", reply_markup=get_main_kb())


# =========================
# ЗАПУСК
# =========================
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())