# Monobank Donation - Архитектура

## Общая схема

```
┌─────────────────┐     ┌───────────────────┐     ┌─────────────────┐
│  MonobankClient │────>│  DonationPoller   │────>│ NotificationSvc │
│  (API запросы)  │     │  (каждые 60 сек)  │     │  (алерты)       │
└─────────────────┘     └───────────────────┘     └────────┬────────┘
                                                           │
                                                           v
┌─────────────────┐     ┌───────────────────┐     ┌─────────────────┐
│     Config      │────>│     WebHost       │<────│   MediaPlayer   │
│  (настройки)    │     │  (HTTP сервер)    │     │ (выбор медиа)   │
└─────────────────┘     └───────────────────┘     └─────────────────┘
                                │
                                v
                        ┌───────────────────┐
                        │    OBS Browser    │
                        │     Source        │
                        └───────────────────┘
```

---

## Классы и их методы

### 1. Config

**Файл:** `src/config.py`

**Описание:** Загрузка и хранение конфигурации из YAML/JSON файла.

```python
class Config:
    def __init__(self, config_path: str = "config.yaml")

    # Геттеры
    def get_port(self) -> int
    def get_monobank_token(self) -> str
    def get_jar_id(self) -> str  # ID банки
    def get_poll_interval(self) -> int  # секунды между запросами
    def get_media_path(self) -> str  # путь к папке media
    def get_media_rules(self) -> list[MediaRule]  # правила сумма->медиа

    # Перезагрузка конфига
    def reload(self) -> None
```

---

### 2. WebHost

**Файл:** `src/web_host.py`

**Описание:** HTTP сервер для OBS. Отдает HTML страницу с WebSocket подключением.

```python
class WebHost:
    def __init__(self, config: Config)

    # Управление сервером
    def start(self) -> None
    def stop(self) -> None
    def is_running(self) -> bool

    # Получить URL для OBS
    def get_url(self) -> str  # например "http://localhost:8080"

    # Отправка контента на страницу (через WebSocket)
    def show_image(self, image_path: str, duration_ms: int = 5000) -> None
    def show_gif(self, gif_path: str, duration_ms: int = 5000) -> None
    def show_media(self, image_path: str, audio_path: str | None = None) -> None
    def clear(self) -> None
```

**Эндпоинты:**
- `GET /` - HTML страница для OBS
- `GET /media/<path>` - статические файлы (картинки, звуки)
- `WebSocket /ws` - реалтайм обновления

---

### 3. MediaPlayer

**Файл:** `src/media_player.py`

**Описание:** Выбор медиа-файлов на основе суммы доната и правил из конфига.

```python
@dataclass
class MediaRule:
    min_amount: int
    max_amount: int | None
    images: list[str]  # пути к картинкам/гифкам
    sounds: list[str]  # пути к звукам

@dataclass
class MediaSelection:
    image_path: str
    audio_path: str | None

class MediaPlayer:
    def __init__(self, config: Config)

    # Выбор медиа для суммы
    def select_media(self, amount: int) -> MediaSelection

    # Рандомный выбор из папки
    def get_random_image(self) -> str
    def get_random_audio(self) -> str

    # Перезагрузка списка файлов
    def reload_media_list(self) -> None
```

---

### 4. NotificationService

**Файл:** `src/notification_service.py`

**Описание:** Центральный сервис для отображения уведомлений о донатах.

```python
@dataclass
class Donation:
    amount: int  # в копейках
    currency: str  # "UAH"
    comment: str | None
    timestamp: datetime
    donor_name: str | None

class NotificationService:
    def __init__(self, web_host: WebHost, media_player: MediaPlayer)

    # Показать уведомление о донате
    def notify(self, donation: Donation) -> None

    # Тестовый донат
    def test_donation(self, amount: int = 10000) -> None  # 100 грн по умолчанию

    # Очередь уведомлений (если пришло несколько сразу)
    def queue_notification(self, donation: Donation) -> None
    def process_queue(self) -> None
```

---

### 5. MonobankClient

**Файл:** `src/monobank_client.py`

**Описание:** Обертка над python-monobank для работы с API банки.

```python
@dataclass
class JarTransaction:
    id: str
    amount: int
    currency: str
    comment: str | None
    timestamp: datetime

class MonobankClient:
    def __init__(self, config: Config)

    # Получить список банок
    def get_jars(self) -> list[dict]

    # Получить транзакции банки
    def get_jar_transactions(self, jar_id: str, from_time: datetime | None = None) -> list[JarTransaction]

    # Получить текущий баланс банки
    def get_jar_balance(self, jar_id: str) -> int
```

---

### 6. DonationPoller

**Файл:** `src/donation_poller.py`

**Описание:** Периодическая проверка новых донатов и вызов NotificationService.

```python
class DonationPoller:
    def __init__(self, monobank_client: MonobankClient, notification_service: NotificationService, config: Config)

    # Управление поллингом
    def start(self) -> None
    def stop(self) -> None
    def is_running(self) -> bool

    # Ручная проверка
    def poll_once(self) -> list[Donation]

    # Callback при новом донате
    def on_new_donation(self, callback: Callable[[Donation], None]) -> None
```

---

### 7. Application (главный класс)

**Файл:** `src/app.py`

**Описание:** Точка входа, инициализация всех компонентов.

```python
class Application:
    def __init__(self, config_path: str = "config.yaml")

    # Запуск приложения
    def run(self) -> None

    # Остановка
    def shutdown(self) -> None

    # Доступ к компонентам
    @property
    def notification_service(self) -> NotificationService

    # Тестовый донат
    def test_donation(self, amount: int = 10000) -> None
```

---

## Структура проекта

```
monobank_donation/
├── config.yaml              # Конфигурация
├── requirements.txt         # Зависимости
├── main.py                  # Точка входа
├── src/
│   ├── __init__.py
│   ├── app.py               # Application
│   ├── config.py            # Config
│   ├── web_host.py          # WebHost
│   ├── media_player.py      # MediaPlayer
│   ├── notification_service.py  # NotificationService
│   ├── monobank_client.py   # MonobankClient
│   └── donation_poller.py   # DonationPoller
├── templates/
│   └── overlay.html         # HTML для OBS
├── static/
│   ├── css/
│   │   └── overlay.css
│   └── js/
│       └── overlay.js       # WebSocket клиент
└── media/                   # Картинки и звуки
    ├── video/
    └── audio/
```

---

## Пример config.yaml

```yaml
server:
  port: 8080

monobank:
  token: "your_token_here"
  jar_id: "your_jar_id"
  poll_interval: 60  # секунды

media:
  path: "./media"
  default_duration: 5000  # мс

  # Правила: какие медиа для каких сумм
  rules:
    - min: 0
      max: 4999
      images: ["video/200.gif"]
      sounds: ["audio/donat_gitara.mp3"]
    - min: 5000
      max: 9999
      images: ["video/bebra.gif"]
      sounds: ["audio/donat_gitara.mp3"]
    - min: 10000
      max: null  # без ограничения
      images: ["video/a021d7d1c9c83486f22fb3579ff07780.gif"]
      sounds: ["audio/donat_gitara.mp3"]
```

---

## Порядок реализации

1. **Фаза 1: Базовый сервер**
   - [ ] Config (базовая версия: порт)
   - [ ] WebHost (start/stop, статическая страница)
   - [ ] HTML/CSS/JS для overlay

2. **Фаза 2: Отображение медиа**
   - [ ] MediaPlayer (рандомный выбор)
   - [ ] WebHost.show_media() через WebSocket
   - [ ] NotificationService.notify()

3. **Фаза 3: Тестирование**
   - [ ] NotificationService.test_donation()
   - [ ] CLI команда для теста

4. **Фаза 4: Monobank интеграция**
   - [ ] MonobankClient
   - [ ] DonationPoller
   - [ ] Интеграция с NotificationService

5. **Фаза 5: Конфигурация медиа**
   - [ ] MediaRule в конфиге
   - [ ] MediaPlayer.select_media() по сумме
