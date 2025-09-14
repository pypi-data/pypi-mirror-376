# Forgram

Простая и удобная библиотека для создания Telegram ботов на Python.

## Установка

```bash
pip install forgram
```

## Пример использования

```python
import asyncio
from forgram import Bot

bot = Bot("YOUR_BOT_TOKEN")

@bot.message_handler(commands=['start'])
async def start_handler(message):
    await message.reply("Привет! Это бот на Forgram")

@bot.message_handler()
async def echo_handler(message):
    if message.text:
        await message.reply(f"Вы написали: {message.text}")

async def main():
    await bot.polling()

asyncio.run(main())
```

## Основные возможности

- Простой и понятный API
- Поддержка асинхронности
- Встроенная система состояний
- Middleware для обработки запросов
- Различные типы хранилищ данных
- Поддержка webhook
- Система аналитики

## Документация

Полная документация находится в папке `docs/`

## Лицензия

MIT License

## Автор

Forgram Team
