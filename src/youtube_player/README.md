# YouTube Player Module

Модуль для управления YouTube плеером - загрузка видео, управление очередью и воспроизведение аудио.

## Функциональность

- **URL Parser**: Извлечение YouTube ссылок из текста комментариев
- **Queue Manager**: Управление очередью с сохранением в JSON файл
- **YouTube Downloader**: Загрузка видео из YouTube (макс 10 минут, макс 10 файлов в кеше)
- **Audio Player**: Воспроизведение MP3 с управлением громкостью
- **Player UI**: Текстовый интерфейс для управления плеером

## Требования

```bash
pip install yt-dlp pygame
```

## Использование

```python
import asyncio
from src.youtube_player import YouTubePlayer, PlayerUI

async def main():
    # Создать плеер
    player = YouTubePlayer()

    # Добавить трек из комментария доната
    await player.add_from_comment("Классная музыка! https://youtu.be/...")

    # Запустить плеер
    await player.start()

    # Запустить UI интерфейс
    ui = PlayerUI(player)
    ui.start()

    # Держать работающим
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await player.stop()
        ui.stop()

asyncio.run(main())
```

## Ограничения

- Максимальная длина видео: **10 минут**
- Максимум файлов в кеше: **10 видео**
- Формат: **MP3 (192kbps)**

## Структура модуля

```
youtube_player/
├── __init__.py              # Экспорт классов
├── url_parser.py            # Парсинг URL из текста
├── queue_manager.py         # Управление очередью (JSON)
├── youtube_downloader.py    # Загрузка видео (yt-dlp)
├── player.py                # Аудиоплеер (pygame)
├── youtube_player.py        # Главный класс
├── ui.py                    # Текстовый интерфейс
├── test.py                  # Тесты
└── README.md                # Этот файл
```

## Команды интерфейса

| Команда | Описание |
|---------|---------|
| `p` | Пауза / Включить |
| `n` | Следующий трек |
| `v+` | Громче (+10%) |
| `v-` | Тише (-10%) |
| `q` | Показать очередь |
| `c` | Текущий трек |
| `s` | Выход |
| `?` | Помощь |

## JSON очередь

Очередь сохраняется в файл (по умолчанию `youtube_queue.json`):

```json
[
  {
    "url": "https://www.youtube.com/watch?v=...",
    "title": "Song Name",
    "duration_sec": 240,
    "added_at": "2026-01-17T12:34:56.789123",
    "file_path": "./youtube_cache/video_id.mp3",
    "downloaded": true
  }
]
```

## Кеш

Видео кешируются в директории `./youtube_cache/` с названием `{video_id}.mp3`.

При добавлении нового видео:
1. Проверяется длина (max 10 минут)
2. Добавляется в очередь
3. Скачивается в фоне (если есть место в кеше)
4. После прослушивания удаляется
