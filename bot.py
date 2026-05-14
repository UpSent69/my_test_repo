import os
import subprocess
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# --- НАСТРОЙКИ ---
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise Exception("Токен не найден! Создай файл .env с BOT_TOKEN=....")

ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

# Инициализация
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Глобальная переменная для текущего репозитория
current_repo = None

def run_git_command(command, repo_path=".") -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip() or "✅ Успешно выполнено!"
        else:
            return f"❌ Ошибка:\n{result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "⏰ Ошибка: команда выполнялась слишком долго."
    except Exception as e:
        return f"⚠️ Неизвестная ошибка: {str(e)}"

async def admin_filter(message: types.Message):
    if message.from_user.id != ADMIN_ID and ADMIN_ID != 0:
        await message.answer("🚫 Доступ запрещен.")
        return False
    return True

@dp.message(Command("start"))
async def start_command(message: Message):
    if not await admin_filter(message): 
        return
    await message.answer(
        "👋 Привет! Я Git бот.\n\n"
        "Команды:\n"
        "/clone [url] - Клонировать репозиторий\n"
        "/status - Показать статус\n"
        "/commit [message] - Создать коммит\n"
        "/push - Отправить на GitHub\n"
        "/pull - Скачать обновления\n"
        "/log - Показать историю"
    )

@dp.message(Command("clone"))
async def clone_repo(message: Message):
    global current_repo
    if not await admin_filter(message): 
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажи ссылку. Пример: `/clone https://github.com/user/repo.git`")
        return

    url = args[1]
    repo_name = url.split('/')[-1].replace('.git', '')
    repo_path = os.path.join(os.getcwd(), repo_name)

    await message.answer(f"📥 Клонирую `{url}`...")
    
    output = run_git_command(f"git clone {url}", repo_path=".")
    
    if "Успешно" in output or "fatal" not in output.lower():
        current_repo = repo_name
        await message.answer(f"✅ Репозиторий склонирован в папку `{repo_name}`")
    else:
        await message.answer(f"❌ Ошибка:\n{output}")

@dp.message(Command("status"))
async def status_command(message: Message):
    if not await admin_filter(message): 
        return
    path = os.path.join(os.getcwd(), current_repo) if current_repo else "."
    output = run_git_command("git status", repo_path=path)
    await message.answer(f"📊 *Статус:*\n```\n{output[:3000]}\n```", parse_mode="Markdown")

@dp.message(Command("pull"))
async def pull_command(message: Message):
    if not await admin_filter(message): 
        return
    path = os.path.join(os.getcwd(), current_repo) if current_repo else "."
    await message.answer("🔄 Скачиваю обновления...")
    output = run_git_command("git pull", repo_path=path)
    await message.answer(f"📥 *Результат:*\n```\n{output[:3000]}\n```", parse_mode="Markdown")

@dp.message(Command("push"))
async def push_command(message: Message):
    if not await admin_filter(message): 
        return
    path = os.path.join(os.getcwd(), current_repo) if current_repo else "."
    await message.answer("🚀 Отправляю изменения...")
    output = run_git_command("git push", repo_path=path)
    await message.answer(f"📤 *Результат:*\n```\n{output[:3000]}\n```", parse_mode="Markdown")

@dp.message(Command("commit"))
async def commit_command(message: Message):
    if not await admin_filter(message): 
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажи сообщение. Пример: `/commit Мой коммит`")
        return
    
    commit_message = args[1]
    path = os.path.join(os.getcwd(), current_repo) if current_repo else "."
    
    run_git_command("git add .", repo_path=path)
    output = run_git_command(f'git commit -m "{commit_message}"', repo_path=path)
    
    await message.answer(f"💾 *Коммит:*\n```\n{output[:3000]}\n```", parse_mode="Markdown")

@dp.message(Command("log"))
async def log_command(message: Message):
    if not await admin_filter(message): 
        return
    path = os.path.join(os.getcwd(), current_repo) if current_repo else "."
    output = run_git_command("git log --oneline -10", repo_path=path)
    await message.answer(f"📜 *История:*\n```\n{output[:3000]}\n```", parse_mode="Markdown")

async def main():
    logging.basicConfig(level=logging.INFO)
    print("🚀 Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())