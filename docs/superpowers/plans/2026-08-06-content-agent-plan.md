# Контент-агент: план реализации (учебная версия)

> **Для агентов-исполнителей:** ОБЯЗАТЕЛЬНЫЙ САБ-СКИЛЛ: используйте superpowers:subagent-driven-development (рекомендуется) или superpowers:executing-plans для выполнения плана задача за задачей. Шаги отмечены чекбоксами (`- [ ]`) для отслеживания.

**Цель:** собрать рабочий Telegram-бот, который принимает черновик поста от художника, правит его через LLM в её голосе, показывает на согласование и публикует в VK и Telegram (либо готовит текст для ручной публикации в Дзен/MAX).

**Архитектура:** один постоянно работающий Python-процесс на VPS с long polling к Telegram, SQLite как единственное хранилище, прямые HTTP-вызовы к VK API и Anthropic API. Подробности — в дизайн-документе `docs/superpowers/specs/2026-08-06-content-agent-design.md`.

**Технологии:** Python 3.11+, `python-telegram-bot` (асинхронный фреймворк для Telegram-ботов), `anthropic` (официальный SDK Claude), `requests` (прямые HTTP-вызовы к VK API — специально без SDK-обёртки, чтобы было видно, что происходит на уровне HTTP), встроенный `sqlite3` (без ORM — чтобы SQL-схема оставалась читаемой и её было видно целиком), `pytest`.

## Как читать этот план

План специально написан подробнее, чем требуется опытному инженеру — по вашей просьбе каждая задача начинается с блока **«Что и зачем»**, объясняющего концепцию до того, как появится код. Если какая-то технология вам знакома — этот блок можно пропускать, код от этого не изменится.

## Global Constraints

- Long polling для Telegram, не webhook — не нужен домен и TLS (design.md, раздел «Архитектура»).
- Публикация в VK и Telegram — только после ручного подтверждения художником, без исключений на первом этапе (design.md, раздел «Разбивка площадок»).
- Дзен и MAX-каналы — агент только готовит текст, публикация вручную; кода для авто-публикации туда не пишем.
- Планирование VK — через нативный `publish_date` в `wall.post`; своего планировщика для VK не строим.
- Планирование Telegram — своя очередь (`scheduled_jobs`) и периодическая проверка, так как Bot API не поддерживает отложенные сообщения.
- LLM не анализирует и не меняет медиа — только текст.
- `posts` и `publish_results` — разные таблицы: сбой одной площадки не должен блокировать или дублировать другие.
- Секреты (токены VK/Telegram/Anthropic) — только в `.env`, никогда не в коде и не в git.

---

## Структура файлов

```
content-agent/
├── .env.example
├── requirements.txt
├── README.md
├── src/
│   ├── __init__.py
│   ├── config.py           # чтение .env
│   ├── db.py                # SQLite: схема + функции доступа к данным
│   ├── media_buffer.py      # склейка альбомов Telegram (media_group_id)
│   ├── dialogue_state.py    # машина состояний одного черновика
│   ├── llm.py                # промпт + вызов Claude + разбор ответа
│   ├── vk_client.py          # обёртка над VK API (текст + медиа + расписание)
│   └── telegram_bot.py       # обработчики Telegram, склейка всех модулей
├── scripts/
│   └── collect_voice_profile.py   # разовый сбор профиля голоса из VK
├── tests/
│   ├── test_media_buffer.py
│   ├── test_dialogue_state.py
│   ├── test_llm.py
│   └── test_db_resume.py
└── docs/
    └── manual-test-checklist.md
```

Каждый файл в `src/` отвечает ровно за одну вещь из дизайн-документа: `db.py` — за хранение, `media_buffer.py` и `dialogue_state.py` — за чистую логику без сети (поэтому их проще всего тестировать), `llm.py` и `vk_client.py` — за общение с конкретным внешним API, `telegram_bot.py` — единственное место, где всё это соединяется в реальный диалог.

---

### Task 1: Окружение проекта и секреты

**Что и зачем.** Прежде чем писать логику, нужно место, куда класть код, и способ безопасно хранить токены (VK, Telegram, Anthropic) — их нельзя коммитить в git, иначе они попадут в историю репозитория навсегда, даже если потом удалить файл. Стандартный приём — файл `.env` с реальными значениями (он в `.gitignore`) и `.env.example` с именами переменных без значений (он в git, чтобы было понятно, что вообще нужно завести). Виртуальное окружение (`venv`) изолирует зависимости проекта от остальной системы — без него `pip install` ставит пакеты глобально, и разные проекты на компьютере начинают конфликтовать по версиям библиотек.

**Files:**
- Create: `content-agent/requirements.txt`
- Create: `content-agent/.env.example`
- Create: `content-agent/.gitignore`
- Create: `content-agent/src/config.py`
- Create: `content-agent/src/__init__.py`
- Test: `content-agent/tests/test_config.py`

**Interfaces:**
- Produces: `config.Settings` — объект с полями `telegram_bot_token: str`, `telegram_channel_id: str`, `vk_access_token: str`, `vk_group_id: int`, `anthropic_api_key: str`, `db_path: str`. Функция `config.load_settings() -> Settings`.

- [ ] **Step 1: Создать структуру проекта и виртуальное окружение**

```bash
mkdir -p content-agent/src content-agent/scripts content-agent/tests content-agent/docs
cd content-agent
python3 -m venv .venv
source .venv/bin/activate
touch src/__init__.py
```

- [ ] **Step 2: Написать requirements.txt**

```
python-telegram-bot==21.6
anthropic==0.39.0
requests==2.32.3
python-dotenv==1.0.1
pytest==8.3.2
pytest-asyncio==0.24.0
```

Установить:
```bash
pip install -r requirements.txt
```

- [ ] **Step 3: Завести .env.example и .gitignore**

`.env.example`:
```
TELEGRAM_BOT_TOKEN=
TELEGRAM_ARTIST_CHAT_ID=
TELEGRAM_CHANNEL_ID=
VK_ACCESS_TOKEN=
VK_GROUP_ID=
ANTHROPIC_API_KEY=
DB_PATH=content_agent.db
```

Пояснение, откуда берётся каждое значение (впишите в комментарий в `.env`, себе на память):
- `TELEGRAM_BOT_TOKEN` — создаётся у `@BotFather` в Telegram командой `/newbot`.
- `TELEGRAM_ARTIST_CHAT_ID` — узнаётся после первого сообщения боту (Task 5 покажет, как).
- `TELEGRAM_CHANNEL_ID` — id канала студии, бот должен быть добавлен туда администратором.
- `VK_ACCESS_TOKEN` — в настройках сообщества ВК: «Управление» → «Работа с API» → «Ключи доступа», права `wall`, `photos`.
- `VK_GROUP_ID` — числовой id сообщества (без минуса, минус добавляем в коде для `wall.post`).
- `ANTHROPIC_API_KEY` — в консоли console.anthropic.com.

`.gitignore`:
```
.venv/
__pycache__/
*.db
.env
```

- [ ] **Step 4: Написать failing-тест на загрузку конфига**

```python
# tests/test_config.py
import os
from src.config import load_settings


def test_load_settings_reads_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_ARTIST_CHAT_ID", "111")
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "-100222")
    monkeypatch.setenv("VK_ACCESS_TOKEN", "vk-token")
    monkeypatch.setenv("VK_GROUP_ID", "333")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key")
    monkeypatch.setenv("DB_PATH", "test.db")

    settings = load_settings()

    assert settings.telegram_bot_token == "test-token"
    assert settings.vk_group_id == 333
```

- [ ] **Step 5: Запустить тест и убедиться, что падает**

```bash
pytest tests/test_config.py -v
```
Ожидается: `FAIL` — `ModuleNotFoundError: No module named 'src.config'` (файла ещё нет).

- [ ] **Step 6: Написать минимальную реализацию**

```python
# src/config.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    telegram_bot_token: str
    telegram_artist_chat_id: int
    telegram_channel_id: str
    vk_access_token: str
    vk_group_id: int
    anthropic_api_key: str
    db_path: str


def load_settings() -> Settings:
    return Settings(
        telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
        telegram_artist_chat_id=int(os.environ["TELEGRAM_ARTIST_CHAT_ID"]),
        telegram_channel_id=os.environ["TELEGRAM_CHANNEL_ID"],
        vk_access_token=os.environ["VK_ACCESS_TOKEN"],
        vk_group_id=int(os.environ["VK_GROUP_ID"]),
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
        db_path=os.environ.get("DB_PATH", "content_agent.db"),
    )
```

- [ ] **Step 7: Запустить тест и убедиться, что проходит**

```bash
pytest tests/test_config.py -v
```
Ожидается: `PASS`.

- [ ] **Step 8: Инициализировать git и закоммитить**

```bash
git init
git add requirements.txt .env.example .gitignore src/ tests/
git commit -m "chore: project scaffolding and config loader"
```

---

### Task 2: Слой данных — SQLite-схема

**Что и зачем.** Вся история постов и статусов публикаций живёт в одном файле SQLite — это не «игрушечная» база: она честно поддерживает транзакции, у неё нет отдельного сервера, который надо администрировать, и для одного пользователя с несколькими постами в неделю её производительности хватит с огромным запасом. Мы намеренно не берём ORM (например, SQLAlchemy) — с сырым SQL видно ровно ту схему, что описана в дизайн-документе, без слоя абстракции поверх. `posts` и `publish_results` — разные таблицы (объяснение см. в дизайн-документе, раздел «Модель данных»): пост один, а результатов публикации у него может быть несколько (по одному на площадку), и они не должны друг друга блокировать.

**Files:**
- Create: `content-agent/src/db.py`
- Test: `content-agent/tests/test_db.py`

**Interfaces:**
- Consumes: `config.Settings.db_path`
- Produces: `db.init_db(path)`, `db.create_post(conn, **fields) -> int`, `db.get_post(conn, post_id) -> dict | None`, `db.update_post(conn, post_id, **fields)`, `db.create_publish_result(conn, post_id, target, status="pending") -> int`, `db.update_publish_result(conn, result_id, **fields)`, `db.get_pending_publish_results(conn) -> list[dict]`, `db.create_scheduled_job(conn, post_id, target, fire_at) -> int`, `db.get_due_scheduled_jobs(conn, now_iso) -> list[dict]`, `db.save_voice_profile(conn, tone_description, examples)`, `db.get_voice_profile(conn) -> dict | None`.

- [ ] **Step 1: Написать failing-тест на создание и чтение поста**

```python
# tests/test_db.py
import sqlite3
from src.db import init_db, create_post, get_post


def test_create_and_get_post():
    conn = sqlite3.connect(":memory:")
    init_db(conn)

    post_id = create_post(
        conn,
        audience="adults",
        raw_text="Черновик",
        targets=["vk_wall", "telegram"],
    )

    post = get_post(conn, post_id)
    assert post["audience"] == "adults"
    assert post["raw_text"] == "Черновик"
    assert post["targets"] == ["vk_wall", "telegram"]
    assert post["status"] == "draft"
```

- [ ] **Step 2: Запустить и увидеть падение**

```bash
pytest tests/test_db.py -v
```
Ожидается: `FAIL` — модуля `src.db` ещё нет.

- [ ] **Step 3: Реализовать схему и базовые функции**

```python
# src/db.py
import json
import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    audience TEXT,
    raw_text TEXT,
    edited_text TEXT,
    media TEXT NOT NULL DEFAULT '[]',
    targets TEXT NOT NULL DEFAULT '[]',
    scheduled_at TEXT
);

CREATE TABLE IF NOT EXISTS publish_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL REFERENCES posts(id),
    target TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    external_id TEXT,
    error TEXT,
    attempted_at TEXT
);

CREATE TABLE IF NOT EXISTS voice_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tone_description TEXT NOT NULL,
    examples TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scheduled_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL REFERENCES posts(id),
    target TEXT NOT NULL,
    fire_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
);
"""


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_post(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "status": row["status"],
        "audience": row["audience"],
        "raw_text": row["raw_text"],
        "edited_text": row["edited_text"],
        "media": json.loads(row["media"]),
        "targets": json.loads(row["targets"]),
        "scheduled_at": row["scheduled_at"],
    }


def create_post(conn, audience=None, raw_text=None, media=None, targets=None) -> int:
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "INSERT INTO posts (created_at, status, audience, raw_text, media, targets) "
        "VALUES (?, 'draft', ?, ?, ?, ?)",
        (_now(), audience, raw_text, json.dumps(media or []), json.dumps(targets or [])),
    )
    conn.commit()
    return cur.lastrowid


def get_post(conn, post_id: int) -> dict | None:
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    return _row_to_post(row) if row else None


def update_post(conn, post_id: int, **fields) -> None:
    if "media" in fields:
        fields["media"] = json.dumps(fields["media"])
    if "targets" in fields:
        fields["targets"] = json.dumps(fields["targets"])
    columns = ", ".join(f"{key} = ?" for key in fields)
    conn.execute(f"UPDATE posts SET {columns} WHERE id = ?", (*fields.values(), post_id))
    conn.commit()


def create_publish_result(conn, post_id: int, target: str, status: str = "pending") -> int:
    cur = conn.execute(
        "INSERT INTO publish_results (post_id, target, status) VALUES (?, ?, ?)",
        (post_id, target, status),
    )
    conn.commit()
    return cur.lastrowid


def update_publish_result(conn, result_id: int, **fields) -> None:
    fields["attempted_at"] = _now()
    columns = ", ".join(f"{key} = ?" for key in fields)
    conn.execute(f"UPDATE publish_results SET {columns} WHERE id = ?", (*fields.values(), result_id))
    conn.commit()


def get_pending_publish_results(conn) -> list[dict]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM publish_results WHERE status = 'pending' AND external_id IS NULL"
    ).fetchall()
    return [dict(row) for row in rows]


def create_scheduled_job(conn, post_id: int, target: str, fire_at: str) -> int:
    cur = conn.execute(
        "INSERT INTO scheduled_jobs (post_id, target, fire_at) VALUES (?, ?, ?)",
        (post_id, target, fire_at),
    )
    conn.commit()
    return cur.lastrowid


def get_due_scheduled_jobs(conn, now_iso: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM scheduled_jobs WHERE status = 'pending' AND fire_at <= ?",
        (now_iso,),
    ).fetchall()
    return [dict(row) for row in rows]


def save_voice_profile(conn, tone_description: str, examples: list[str]) -> None:
    conn.execute(
        "INSERT INTO voice_profile (tone_description, examples, updated_at) VALUES (?, ?, ?)",
        (tone_description, json.dumps(examples), _now()),
    )
    conn.commit()


def get_voice_profile(conn) -> dict | None:
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM voice_profile ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if not row:
        return None
    return {
        "tone_description": row["tone_description"],
        "examples": json.loads(row["examples"]),
        "updated_at": row["updated_at"],
    }
```

- [ ] **Step 4: Запустить тест и убедиться, что проходит**

```bash
pytest tests/test_db.py -v
```
Ожидается: `PASS`.

- [ ] **Step 5: Добавить тест на publish_results и отложенные задания, реализовать при необходимости (уже реализовано выше — тест должен пройти сразу)**

```python
# tests/test_db.py (добавить в конец файла)
from src.db import (
    create_publish_result, update_publish_result, get_pending_publish_results,
    create_scheduled_job, get_due_scheduled_jobs,
)


def test_publish_result_lifecycle():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    post_id = create_post(conn, raw_text="x", targets=["vk_wall"])

    result_id = create_publish_result(conn, post_id, "vk_wall")
    assert len(get_pending_publish_results(conn)) == 1

    update_publish_result(conn, result_id, status="sent", external_id="wall123_45")
    assert len(get_pending_publish_results(conn)) == 0


def test_scheduled_jobs_due_filter():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    post_id = create_post(conn, raw_text="x", targets=["telegram"])
    create_scheduled_job(conn, post_id, "telegram", fire_at="2026-08-06T10:00:00+00:00")

    due_now = get_due_scheduled_jobs(conn, "2026-08-06T10:05:00+00:00")
    due_before = get_due_scheduled_jobs(conn, "2026-08-06T09:00:00+00:00")

    assert len(due_now) == 1
    assert len(due_before) == 0
```

```bash
pytest tests/test_db.py -v
```
Ожидается: `PASS` для всех тестов.

- [ ] **Step 6: Commit**

```bash
git add src/db.py tests/test_db.py
git commit -m "feat: sqlite schema and data access layer"
```

---

### Task 3: Склейка альбомов Telegram (media_buffer.py)

**Что и зачем.** Как объяснялось в обсуждении дизайна: когда художник присылает несколько фото одним альбомом, Telegram доставляет их бота отдельными сообщениями с общим `media_group_id`, и только одно из них несёт подпись. Если реагировать на каждое сообщение сразу, черновик развалится на части. Решение — копить сообщения с одинаковым `media_group_id` и забирать группу целиком только тогда, когда новых сообщений по ней не было какое-то время (окно ожидания). Мы пишем эту логику как чистый класс без Telegram и без реальных таймеров внутри — только «дай мне текущее время, я скажу, что уже готово». Это именно то разделение, которое делает код тестируемым: тест сам решает, «прошло» время или нет, а не ждёт реальные секунды.

**Files:**
- Create: `content-agent/src/media_buffer.py`
- Test: `content-agent/tests/test_media_buffer.py`

**Interfaces:**
- Produces: `class MediaGroupBuffer` c методами `add(group_id: str, item: dict, now: float) -> None` и `pop_ready(now: float, window_seconds: float = 1.5) -> list[list[dict]]` (возвращает список готовых групп, каждая — список item'ов в порядке добавления; готовые группы удаляются из буфера).

- [ ] **Step 1: Написать failing-тест**

```python
# tests/test_media_buffer.py
from src.media_buffer import MediaGroupBuffer


def test_group_not_ready_before_window_passes():
    buf = MediaGroupBuffer()
    buf.add("group-1", {"file_id": "a"}, now=100.0)
    buf.add("group-1", {"file_id": "b"}, now=100.5)

    ready = buf.pop_ready(now=101.0, window_seconds=1.5)

    assert ready == []  # с последнего сообщения прошло всего 0.5с


def test_group_ready_after_window_passes():
    buf = MediaGroupBuffer()
    buf.add("group-1", {"file_id": "a"}, now=100.0)
    buf.add("group-1", {"file_id": "b"}, now=100.5)

    ready = buf.pop_ready(now=102.1, window_seconds=1.5)

    assert len(ready) == 1
    assert [item["file_id"] for item in ready[0]] == ["a", "b"]


def test_ready_group_is_removed_after_pop():
    buf = MediaGroupBuffer()
    buf.add("group-1", {"file_id": "a"}, now=100.0)
    buf.pop_ready(now=102.0, window_seconds=1.5)

    assert buf.pop_ready(now=200.0, window_seconds=1.5) == []


def test_single_message_without_group_id_is_ready_immediately():
    buf = MediaGroupBuffer()
    buf.add(None, {"file_id": "solo"}, now=100.0)

    ready = buf.pop_ready(now=100.0, window_seconds=1.5)

    assert len(ready) == 1
    assert ready[0][0]["file_id"] == "solo"
```

- [ ] **Step 2: Запустить и увидеть падение**

```bash
pytest tests/test_media_buffer.py -v
```
Ожидается: `FAIL` — модуля нет.

- [ ] **Step 3: Реализовать**

```python
# src/media_buffer.py
import itertools

_solo_counter = itertools.count()


class MediaGroupBuffer:
    """Копит сообщения одного альбома по media_group_id, пока не пройдёт окно тишины.

    Сообщения без media_group_id (одиночное фото или просто текст) считаются
    готовыми немедленно — им не с кем склеиваться.
    """

    def __init__(self) -> None:
        self._groups: dict[str, dict] = {}

    def add(self, group_id: str | None, item: dict, now: float) -> None:
        key = group_id if group_id is not None else f"__solo_{next(_solo_counter)}"
        if key not in self._groups:
            self._groups[key] = {"items": [], "last_seen": now}
        self._groups[key]["items"].append(item)
        self._groups[key]["last_seen"] = now

    def pop_ready(self, now: float, window_seconds: float = 1.5) -> list[list[dict]]:
        ready_keys = [
            key for key, group in self._groups.items()
            if now - group["last_seen"] >= window_seconds
        ]
        ready = [self._groups.pop(key)["items"] for key in ready_keys]
        return ready
```

- [ ] **Step 4: Запустить тесты**

```bash
pytest tests/test_media_buffer.py -v
```
Ожидается: `PASS` (все 4 теста).

- [ ] **Step 5: Commit**

```bash
git add src/media_buffer.py tests/test_media_buffer.py
git commit -m "feat: media group buffering for telegram albums"
```

---

### Task 4: Машина состояний диалога (dialogue_state.py)

**Что и зачем.** У одного черновика есть чёткая последовательность этапов (получен → выбрана аудитория → выбраны площадки → идёт правка LLM → показан на согласование → опубликован/отложен/отменён), и в каждый момент допустимы только определённые переходы — нельзя, например, опубликовать пост, для которого ещё не выбраны площадки. Если размазать эту логику по обработчикам Telegram, легко получить состояние, в которое можно попасть «случайно» (баг, который трудно найти). Явная машина состояний — отдельный класс, который сам решает, какие переходы разрешены, и кидает понятную ошибку на недопустимый переход. Как и буфер альбомов, она не знает про Telegram — это чистая логика, которую я тестирую без единого сетевого вызова.

**Files:**
- Create: `content-agent/src/dialogue_state.py`
- Test: `content-agent/tests/test_dialogue_state.py`

**Interfaces:**
- Produces: `class PostDraft` с полями `state: str`, `audience: str | None`, `targets: list[str]`, `raw_text: str`, `edited_text: str | None`; методами `set_audience(audience)`, `set_targets(targets)`, `mark_in_review(edited_text)`, `request_rewrite()`, `approve()`, `cancel()`. Каждый метод меняет `state` либо кидает `InvalidTransition`.

- [ ] **Step 1: Написать failing-тест**

```python
# tests/test_dialogue_state.py
import pytest
from src.dialogue_state import PostDraft, InvalidTransition


def test_happy_path_transitions():
    draft = PostDraft(raw_text="Новая ваза ручной лепки")
    assert draft.state == "draft_received"

    draft.set_audience("adults")
    draft.set_targets(["vk_wall", "telegram"])
    assert draft.state == "targets_selected"

    draft.mark_in_review(edited_text="Новая ваза ручной работы.")
    assert draft.state == "review"

    draft.approve()
    assert draft.state == "publishing"


def test_rewrite_loop_returns_to_review_state_via_targets_selected():
    draft = PostDraft(raw_text="Черновик")
    draft.set_audience("kids")
    draft.set_targets(["telegram"])
    draft.mark_in_review(edited_text="Правка 1")

    draft.request_rewrite()
    assert draft.state == "targets_selected"  # ждём новый вызов LLM

    draft.mark_in_review(edited_text="Правка 2")
    assert draft.state == "review"
    assert draft.edited_text == "Правка 2"


def test_cannot_approve_before_review():
    draft = PostDraft(raw_text="Черновик")
    draft.set_audience("adults")
    draft.set_targets(["vk_wall"])

    with pytest.raises(InvalidTransition):
        draft.approve()


def test_cancel_allowed_from_review():
    draft = PostDraft(raw_text="Черновик")
    draft.set_audience("adults")
    draft.set_targets(["vk_wall"])
    draft.mark_in_review(edited_text="Правка")

    draft.cancel()
    assert draft.state == "cancelled"
```

- [ ] **Step 2: Запустить и увидеть падение**

```bash
pytest tests/test_dialogue_state.py -v
```
Ожидается: `FAIL` — модуля нет.

- [ ] **Step 3: Реализовать**

```python
# src/dialogue_state.py
from dataclasses import dataclass, field

# Разрешённые переходы: из какого состояния в какое можно попасть по каждому методу.
_TRANSITIONS = {
    "set_audience": {"draft_received": "draft_received"},
    "set_targets": {"draft_received": "targets_selected"},
    "mark_in_review": {"targets_selected": "review"},
    "request_rewrite": {"review": "targets_selected"},
    "approve": {"review": "publishing"},
    "cancel": {"review": "cancelled", "targets_selected": "cancelled"},
}


class InvalidTransition(Exception):
    pass


@dataclass
class PostDraft:
    raw_text: str
    state: str = "draft_received"
    audience: str | None = None
    targets: list[str] = field(default_factory=list)
    edited_text: str | None = None

    def _transition(self, method: str) -> str:
        allowed = _TRANSITIONS[method]
        if self.state not in allowed:
            raise InvalidTransition(
                f"Нельзя вызвать {method} из состояния {self.state}"
            )
        return allowed[self.state]

    def set_audience(self, audience: str) -> None:
        self.state = self._transition("set_audience")
        self.audience = audience

    def set_targets(self, targets: list[str]) -> None:
        self.state = self._transition("set_targets")
        self.targets = targets

    def mark_in_review(self, edited_text: str) -> None:
        self.state = self._transition("mark_in_review")
        self.edited_text = edited_text

    def request_rewrite(self) -> None:
        self.state = self._transition("request_rewrite")

    def approve(self) -> None:
        self.state = self._transition("approve")

    def cancel(self) -> None:
        self.state = self._transition("cancel")
```

- [ ] **Step 4: Запустить тесты**

```bash
pytest tests/test_dialogue_state.py -v
```
Ожидается: `PASS` (все 4 теста).

- [ ] **Step 5: Commit**

```bash
git add src/dialogue_state.py tests/test_dialogue_state.py
git commit -m "feat: explicit state machine for draft dialogue"
```

---

### Task 5: Скелет Telegram-бота

**Что и зачем.** `python-telegram-bot` строится вокруг понятия `Application` — объекта, который запускает цикл long polling (сам ходит к Telegram и спрашивает «есть новые сообщения?») и раздаёт их обработчикам (`handlers`) по типу события. `MessageHandler` реагирует на входящие сообщения (текст, фото), `CallbackQueryHandler` — на нажатия инлайн-кнопок (это будет в Task 8). Здесь мы делаем самый скромный работающий кусок: бот отвечает только на сообщения от одного конкретного человека (художника) — id её чата мы жёстко зашиваем в конфиг после первого сообщения, остальных бот игнорирует. Это уже реальная защита: без такой проверки кто угодно, узнав имя бота, мог бы слать в него черновики.

**Files:**
- Create: `content-agent/src/telegram_bot.py`
- Modify: `content-agent/README.md`

**Interfaces:**
- Consumes: `config.load_settings()`, `media_buffer.MediaGroupBuffer`, `dialogue_state.PostDraft`, `db.init_db`, `db.create_post`
- Produces: функция `build_application(settings) -> telegram.ext.Application`, точка входа `main()`, обработчики `handle_text_draft`, `handle_media_draft`, `flush_media_groups`, общий помощник `send_audience_question(bot, chat_id, context, post_id)`.

- [ ] **Step 1: Узнать свой chat_id (ручной шаг, не автотест)**

Временно добавить в `src/telegram_bot.py` обработчик-заглушку, который печатает `update.effective_chat.id` в консоль, написать боту любое сообщение, увидеть id в логах, вписать его в `.env` как `TELEGRAM_ARTIST_CHAT_ID`. Это разовое действие, не часть кода, который останется в проекте.

- [ ] **Step 2: Написать основной обработчик текстовых черновиков**

```python
# src/telegram_bot.py
import logging
import sqlite3

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from src.config import load_settings
from src.db import init_db, create_post
from src.media_buffer import MediaGroupBuffer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _only_artist(settings):
    async def check(update: Update) -> bool:
        allowed = update.effective_chat.id == settings.telegram_artist_chat_id
        if not allowed:
            logger.warning("Игнорирую сообщение от чужого chat_id=%s", update.effective_chat.id)
        return allowed
    return check


async def send_audience_question(bot, chat_id: int, context: ContextTypes.DEFAULT_TYPE, post_id: int) -> None:
    context.chat_data["current_post_id"] = post_id
    await bot.send_message(chat_id, "Черновик получен. Для кого этот пост?")


async def handle_text_draft(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = context.bot_data["settings"]
    if update.effective_chat.id != settings.telegram_artist_chat_id:
        return

    conn = context.bot_data["conn"]
    post_id = create_post(conn, raw_text=update.message.text, media=[], targets=[])
    await send_audience_question(context.bot, update.effective_chat.id, context, post_id)


def build_application(settings) -> Application:
    conn = sqlite3.connect(settings.db_path, check_same_thread=False)
    init_db(conn)

    application = Application.builder().token(settings.telegram_bot_token).build()
    application.bot_data["settings"] = settings
    application.bot_data["conn"] = conn
    application.bot_data["media_buffer"] = MediaGroupBuffer()

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_draft))
    return application


def main() -> None:
    settings = load_settings()
    application = build_application(settings)
    application.run_polling()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Ручная проверка текстового пути**

```bash
python -m src.telegram_bot
```
Написать боту в личку текстовое сообщение → ожидается ответ «Черновик получен. Для кого этот пост?» и новая строка в таблице `posts` (проверить: `sqlite3 content_agent.db "select id, raw_text from posts;"`).

- [ ] **Step 4: Приём фото/видео через буфер альбомов**

**Что и зачем.** Текстовый путь показывает общий каркас, но черновики с фото устроены иначе: сообщение с фото может быть частью альбома (см. Task 3), и его нельзя обрабатывать сразу — сначала оно копится в `MediaGroupBuffer`, а решает, что группа собрана целиком, периодическая проверка (раз в секунду, через `JobQueue.run_repeating`), а не сам обработчик входящих сообщений. Здесь `MediaGroupBuffer`, заведённый в `build_application` ещё в Step 2, наконец используется по назначению.

```python
# src/telegram_bot.py (добавить к существующему файлу)
import time


async def handle_media_draft(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = context.bot_data["settings"]
    if update.effective_chat.id != settings.telegram_artist_chat_id:
        return

    message = update.message
    file_id = message.photo[-1].file_id if message.photo else message.video.file_id
    item = {
        "file_id": file_id,
        "kind": "photo" if message.photo else "video",
        "caption": message.caption,
        "chat_id": update.effective_chat.id,
    }
    buffer: MediaGroupBuffer = context.bot_data["media_buffer"]
    buffer.add(message.media_group_id, item, now=time.time())


async def flush_media_groups(context: ContextTypes.DEFAULT_TYPE) -> None:
    buffer: MediaGroupBuffer = context.bot_data["media_buffer"]
    conn = context.bot_data["conn"]

    for group in buffer.pop_ready(now=time.time(), window_seconds=1.5):
        caption = next((item["caption"] for item in group if item["caption"]), "")
        # Храним не просто file_id, а словари с kind — в Task 11 это понадобится,
        # чтобы знать, каким методом Telegram API отправлять файл дальше (фото или видео).
        media = [{"file_id": item["file_id"], "kind": item["kind"]} for item in group]
        chat_id = group[0]["chat_id"]

        post_id = create_post(conn, raw_text=caption, media=media, targets=[])
        await send_audience_question(context.bot, chat_id, context, post_id)
```

Зарегистрировать в `build_application` (добавить рядом с уже существующим `add_handler`):
```python
application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, handle_media_draft))
application.job_queue.run_repeating(flush_media_groups, interval=1, first=1)
```

- [ ] **Step 5: Ручная проверка медиа-пути**

```bash
python -m src.telegram_bot
```
Отправить одно фото с подписью → вопрос «Для кого этот пост?» приходит не раньше чем примерно через 1.5 секунды, в `posts` — одна строка с непустым `media`. Затем отправить альбом из 3 фото с подписью на первом фото → убедиться, что создаётся один пост с тремя `file_id` в `media`, а не три отдельных поста.

- [ ] **Step 6: Commit**

```bash
git add src/telegram_bot.py
git commit -m "feat: telegram bot skeleton, text and media draft intake with album buffering"
```

---

### Task 6: Сбор профиля голоса из VK

**Что и зачем.** Чтобы LLM правила текст «в голосе художника», а не в безликом усреднённом стиле, ей нужны реальные примеры — так называемый few-shot: несколько настоящих постов, показанных прямо в промпте как образец. Это разовый скрипт, не часть постоянно работающего бота: запускается вручную, тянет последние посты со стены сообщества через VK API (`wall.get`), просит вас коротко описать тон словами и сохраняет всё в таблицу `voice_profile`. При необходимости запустить его повторно позже, если голос студии изменится или наберётся больше показательных постов.

**Files:**
- Create: `content-agent/scripts/collect_voice_profile.py`

**Interfaces:**
- Consumes: `db.save_voice_profile`, `config.load_settings`
- Produces: исполняемый скрипт, вызываемый из терминала.

- [ ] **Step 1: Написать скрипт**

```python
# scripts/collect_voice_profile.py
"""Разовый сбор примеров стиля из постов ВК. Запускать вручную:
    python -m scripts.collect_voice_profile
"""
import sqlite3

import requests

from src.config import load_settings
from src.db import init_db, save_voice_profile

VK_API_VERSION = "5.199"  # проверьте актуальную версию в dev.vk.com перед запуском


def fetch_recent_wall_posts(settings, count: int = 20) -> list[str]:
    response = requests.get(
        "https://api.vk.com/method/wall.get",
        params={
            "owner_id": -settings.vk_group_id,
            "count": count,
            "access_token": settings.vk_access_token,
            "v": VK_API_VERSION,
        },
        timeout=10,
    )
    data = response.json()
    if "error" in data:
        raise RuntimeError(f"VK API error: {data['error']}")
    return [item["text"] for item in data["response"]["items"] if item.get("text")]


def main() -> None:
    settings = load_settings()
    conn = sqlite3.connect(settings.db_path)
    init_db(conn)

    posts = fetch_recent_wall_posts(settings)
    print(f"Найдено {len(posts)} постов с текстом. Первые 3 для проверки:\n")
    for text in posts[:3]:
        print("---")
        print(text[:300])

    print("\nВыберите до 8 самых характерных постов из вывода выше "
          "(в реальном проекте — вручную отредактируйте список ниже перед сохранением).")

    tone_description = input(
        "\nОпишите тон в двух-трёх предложениях "
        "(например: тёплый, немного шутливый тон, короткие предложения, обращение на «ты»): "
    )

    save_voice_profile(conn, tone_description=tone_description, examples=posts[:8])
    print("Профиль голоса сохранён в voice_profile.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Запустить вручную и проверить результат**

```bash
python -m scripts.collect_voice_profile
sqlite3 content_agent.db "select tone_description from voice_profile order by id desc limit 1;"
```
Ожидается: непустая строка с описанием тона.

- [ ] **Step 3: Commit**

```bash
git add scripts/collect_voice_profile.py
git commit -m "feat: one-off script to collect voice profile from VK wall posts"
```

---

### Task 7: Интеграция с LLM (llm.py)

**Что и зачем.** Один вызов Claude должен одновременно поправить орфографию/стиль черновика и подготовить варианты под выбранные площадки (по решению из дизайн-документа — один текст с лёгкой подгонкой, а не совсем разные тексты). Чтобы результат было легко и надёжно разобрать кодом, мы просим модель вернуть строго определённый JSON, а не свободный текст, который потом пришлось бы парсить регулярками. Это стандартный приём: system-промпт с примерами голоса плюс явная инструкция про формат ответа. `build_prompt` — чистая функция (легко тестировать без сети: даём вход, проверяем текст промпта), `call_llm` — единственное место, где мы реально ходим в Anthropic API.

**Files:**
- Create: `content-agent/src/llm.py`
- Test: `content-agent/tests/test_llm.py`

**Interfaces:**
- Consumes: `db.get_voice_profile()`
- Produces: `build_prompt(voice_profile: dict, raw_text: str, targets: list[str]) -> str`, `class LLMOutputError(Exception)`, `parse_llm_output(raw_json: str) -> dict`, `call_llm(client, voice_profile, raw_text, targets) -> dict` (возвращает `{"edited_text": str, "variants": {target: str}}`).

- [ ] **Step 1: Написать failing-тест на сборку промпта и разбор ответа**

```python
# tests/test_llm.py
import pytest
from src.llm import build_prompt, parse_llm_output, LLMOutputError

VOICE_PROFILE = {
    "tone_description": "Тёплый, простой тон, обращение на «ты»",
    "examples": ["Сегодня обжигали вазы — получилось..."],
}


def test_build_prompt_includes_tone_and_targets():
    prompt = build_prompt(VOICE_PROFILE, "черновик текста", ["vk_wall", "dzen_text"])

    assert "Тёплый, простой тон" in prompt
    assert "vk_wall" in prompt
    assert "dzen_text" in prompt
    assert "черновик текста" in prompt


def test_parse_llm_output_valid_json():
    raw = '{"edited_text": "Готовый текст.", "variants": {"vk_wall": "Готовый текст."}}'

    result = parse_llm_output(raw)

    assert result["edited_text"] == "Готовый текст."
    assert result["variants"]["vk_wall"] == "Готовый текст."


def test_parse_llm_output_invalid_json_raises():
    with pytest.raises(LLMOutputError):
        parse_llm_output("это не json")
```

- [ ] **Step 2: Запустить и увидеть падение**

```bash
pytest tests/test_llm.py -v
```
Ожидается: `FAIL` — модуля нет.

- [ ] **Step 3: Реализовать**

```python
# src/llm.py
import json

SYSTEM_PROMPT_TEMPLATE = """Ты — редактор постов художественной студии «Кисть и Перо».
Твоя задача: исправить орфографию и структуру черновика, сохранив голос автора.

Голос автора: {tone_description}

Примеры настоящих постов автора (ориентируйся на них, но не копируй дословно):
{examples}

Правила:
- Не меняй факты и не добавляй ничего, чего не было в черновике.
- Не работай с фото/видео — только с текстом.
- Для площадок vk_wall, vk_donut, telegram — можно использовать эмодзи и хэштеги, если это в духе автора.
- Для площадок dzen_text, max_general_text, max_pottery_text — текст должен быть чистым для копирования: без хэштегов и служебных пометок.

Ответь СТРОГО в формате JSON без пояснений вокруг:
{{"edited_text": "...", "variants": {{"<target>": "..."}}}}
где <target> — каждая из площадок: {targets}.
"""


class LLMOutputError(Exception):
    pass


def build_prompt(voice_profile: dict, raw_text: str, targets: list[str]) -> str:
    examples_block = "\n---\n".join(voice_profile["examples"])
    system = SYSTEM_PROMPT_TEMPLATE.format(
        tone_description=voice_profile["tone_description"],
        examples=examples_block,
        targets=", ".join(targets),
    )
    return f"{system}\n\nЧерновик:\n{raw_text}"


def parse_llm_output(raw_json: str) -> dict:
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise LLMOutputError(f"LLM вернула не-JSON: {raw_json[:200]}") from exc

    if "edited_text" not in data or "variants" not in data:
        raise LLMOutputError(f"В ответе нет обязательных полей: {data}")

    return data


def call_llm(client, voice_profile: dict, raw_text: str, targets: list[str]) -> dict:
    prompt = build_prompt(voice_profile, raw_text, targets)

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw_text_response = response.content[0].text
    return parse_llm_output(raw_text_response)
```

- [ ] **Step 4: Запустить тесты**

```bash
pytest tests/test_llm.py -v
```
Ожидается: `PASS` (все 3 теста).

- [ ] **Step 5: Commit**

```bash
git add src/llm.py tests/test_llm.py
git commit -m "feat: LLM prompt construction and structured output parsing"
```

---

### Task 8: Экран согласования в боте

**Что и зачем.** Здесь впервые появляются инлайн-кнопки Telegram — это не отдельные сообщения, а разметка (`InlineKeyboardMarkup`), прикреплённая к сообщению; нажатие кнопки прилетает боту не новым сообщением, а событием `CallbackQuery` с закодированным в кнопке значением (`callback_data`). Мы используем это, чтобы закодировать, к какому посту и какому действию относится нажатие — например, `approve:42`. Здесь же соединяются все чистые модули из прошлых задач: `MediaGroupBuffer` решает, когда черновик собран целиком, `PostDraft` — на каком мы этапе, `llm.call_llm` — что показать художнику.

**Files:**
- Modify: `content-agent/src/telegram_bot.py`

**Interfaces:**
- Consumes: `dialogue_state.PostDraft`, `llm.call_llm`, `db.update_post`
- Produces: обработчики `handle_audience_choice`, `handle_targets_done`, `handle_review_action` (callback_data вида `audience:<value>`, `target_toggle:<name>`, `targets_done`, `approve`, `rewrite`, `cancel`).

- [ ] **Step 1: Добавить клавиатуры выбора аудитории и площадок**

```python
# src/telegram_bot.py (добавить к существующему файлу)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler

ALL_TARGETS = ["vk_wall", "vk_donut", "telegram", "dzen_text", "max_general_text", "max_pottery_text"]
TARGET_LABELS = {
    "vk_wall": "VK-лента", "vk_donut": "VK Donut", "telegram": "Telegram",
    "dzen_text": "Дзен (текст)", "max_general_text": "MAX общий (текст)",
    "max_pottery_text": "MAX гончарный (текст)",
}


def audience_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🎨 Взрослым", callback_data="audience:adults"),
        InlineKeyboardButton("🧒 Детям", callback_data="audience:kids"),
        InlineKeyboardButton("👥 Оба", callback_data="audience:both"),
    ]])


def targets_keyboard(selected: set[str]) -> InlineKeyboardMarkup:
    rows = []
    for target in ALL_TARGETS:
        mark = "✅ " if target in selected else ""
        rows.append([InlineKeyboardButton(f"{mark}{TARGET_LABELS[target]}", callback_data=f"target_toggle:{target}")])
    rows.append([InlineKeyboardButton("Готово", callback_data="targets_done")])
    return InlineKeyboardMarkup(rows)


def review_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Опубликовать", callback_data="approve"),
        InlineKeyboardButton("✏️ Переписать", callback_data="rewrite"),
        InlineKeyboardButton("❌ Отмена", callback_data="cancel"),
    ]])
```

- [ ] **Step 2: Подключить клавиатуру к уже существующему `send_audience_question`**

В Task 5 `send_audience_question` отправляла обычный текст — она вызывается и из `handle_text_draft`, и из `flush_media_groups`, поэтому один правленый вариант сразу чинит оба пути. Заменить функцию из Task 5 на:

```python
async def send_audience_question(bot, chat_id: int, context: ContextTypes.DEFAULT_TYPE, post_id: int) -> None:
    context.chat_data["current_post_id"] = post_id
    context.chat_data["selected_targets"] = set()
    await bot.send_message(chat_id, "Для кого этот пост?", reply_markup=audience_keyboard())
```

- [ ] **Step 3: Обработчик callback-кнопок**

```python
async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()  # обязательно — иначе кнопка "крутится" у пользователя
    conn = context.bot_data["conn"]
    post_id = context.chat_data.get("current_post_id")

    if query.data.startswith("audience:"):
        audience = query.data.split(":", 1)[1]
        update_post(conn, post_id, audience=audience)
        context.chat_data["selected_targets"] = set()
        await query.edit_message_text(
            "Куда публикуем?", reply_markup=targets_keyboard(set())
        )

    elif query.data.startswith("target_toggle:"):
        target = query.data.split(":", 1)[1]
        selected = context.chat_data["selected_targets"]
        selected.symmetric_difference_update({target})
        await query.edit_message_reply_markup(reply_markup=targets_keyboard(selected))

    elif query.data == "targets_done":
        targets = list(context.chat_data["selected_targets"])
        update_post(conn, post_id, targets=targets)
        await query.edit_message_text("Обрабатываю текст...")

        post = get_post(conn, post_id)
        voice_profile = get_voice_profile(conn)
        client = context.bot_data["anthropic_client"]
        result = call_llm(client, voice_profile, post["raw_text"], targets)

        update_post(conn, post_id, edited_text=result["edited_text"], status="review")
        context.chat_data["llm_result"] = result

        auto_targets = [t for t in targets if t in ("vk_wall", "vk_donut", "telegram")]
        manual_targets = [t for t in targets if t not in auto_targets]

        if auto_targets:
            await context.bot.send_message(
                update.effective_chat.id,
                result["edited_text"],
                reply_markup=review_keyboard(),
            )
        for target in manual_targets:
            await context.bot.send_message(
                update.effective_chat.id,
                f"Текст для {TARGET_LABELS[target]}:\n\n<code>{result['variants'].get(target, result['edited_text'])}</code>",
                parse_mode="HTML",
            )

    elif query.data == "rewrite":
        await query.edit_message_text("Что поправить? Напишите коротко.")
        context.chat_data["awaiting_feedback"] = True

    elif query.data == "cancel":
        update_post(conn, post_id, status="cancelled")
        await query.edit_message_text("Отменено.")

    elif query.data == "approve":
        # Публикация — предмет Task 9-11. Здесь только меняем статус.
        update_post(conn, post_id, status="publishing")
        await query.edit_message_text("Публикую...")
```

- [ ] **Step 4: Зарегистрировать обработчик и импорты**

```python
# в build_application добавить:
application.bot_data["anthropic_client"] = Anthropic(api_key=settings.anthropic_api_key)
application.add_handler(CallbackQueryHandler(handle_callback))
```
Добавить импорты `from anthropic import Anthropic`, `from src.db import update_post, get_post, get_voice_profile`, `from src.llm import call_llm` в начало файла.

- [ ] **Step 5: Ручная проверка**

```bash
python -m src.telegram_bot
```
Пройти весь путь в Telegram: черновик → аудитория → площадки (в т.ч. хотя бы одну ручную вроде Дзен) → увидеть текст на согласование и отдельным сообщением моноширинный текст для Дзен → нажать «Переписать», написать правку, убедиться что пришёл новый вариант.

- [ ] **Step 6: Commit**

```bash
git add src/telegram_bot.py
git commit -m "feat: audience/target selection and LLM review screen"
```

---

### Task 9: Публикация в VK — текст

**Что и зачем.** VK API — классический REST поверх HTTP: каждый метод (`wall.post`, `photos.getWallUploadServer` и т.д.) — это `GET`/`POST`-запрос на `https://api.vk.com/method/<имя>` с параметрами и токеном доступа, а ответ — JSON. Мы заворачиваем это в маленькую функцию `vk_api_call`, чтобы не повторять сборку URL в каждом месте. Отдельно стоит параметр `publish_date` — если его передать (unix-время в будущем), VK сам отложит публикацию и сам её выполнит в срок; никакого собственного планировщика для VK нам писать не нужно (в отличие от Telegram — Task 11). Для маркировки поста как контента VK Donut используется параметр `donut_paid_duration`; перед боевым использованием стоит свериться с актуальной документацией на `dev.vk.com/method/wall.post`, так как VK время от времени меняет детали API.

**Files:**
- Create: `content-agent/src/vk_client.py`
- Test: `content-agent/tests/test_vk_client.py`

**Interfaces:**
- Produces: `class VKAPIError(Exception)`, `vk_api_call(method: str, params: dict) -> dict`, `wall_post(settings, message: str, target: str, publish_date: int | None = None, attachments: list[str] | None = None) -> str` (возвращает `external_id` вида `wall-<group>_<post_id>`).

- [ ] **Step 1: Написать failing-тест с подменой HTTP-вызова**

```python
# tests/test_vk_client.py
from unittest.mock import patch, MagicMock
import pytest
from src.vk_client import vk_api_call, wall_post, VKAPIError


@patch("src.vk_client.requests.get")
def test_vk_api_call_returns_response_field(mock_get):
    mock_get.return_value = MagicMock(json=lambda: {"response": {"post_id": 45}})

    result = vk_api_call("wall.post", {"owner_id": -333, "message": "hi"}, access_token="tok", version="5.199")

    assert result == {"post_id": 45}


@patch("src.vk_client.requests.get")
def test_vk_api_call_raises_on_error(mock_get):
    mock_get.return_value = MagicMock(json=lambda: {"error": {"error_msg": "Access token invalid"}})

    with pytest.raises(VKAPIError):
        vk_api_call("wall.post", {}, access_token="bad", version="5.199")


@patch("src.vk_client.vk_api_call")
def test_wall_post_builds_external_id(mock_call):
    mock_call.return_value = {"post_id": 45}
    settings = MagicMock(vk_group_id=333, vk_access_token="tok")

    external_id = wall_post(settings, "текст", target="vk_wall")

    assert external_id == "wall-333_45"
    called_params = mock_call.call_args.args[1]
    assert called_params["owner_id"] == -333
    assert "donut_paid_duration" not in called_params


@patch("src.vk_client.vk_api_call")
def test_wall_post_donut_sets_paid_duration(mock_call):
    mock_call.return_value = {"post_id": 46}
    settings = MagicMock(vk_group_id=333, vk_access_token="tok")

    wall_post(settings, "текст", target="vk_donut")

    called_params = mock_call.call_args.args[1]
    assert called_params["donut_paid_duration"] == 0
```

- [ ] **Step 2: Запустить и увидеть падение**

```bash
pytest tests/test_vk_client.py -v
```
Ожидается: `FAIL` — модуля нет.

- [ ] **Step 3: Реализовать**

```python
# src/vk_client.py
import requests

VK_API_VERSION = "5.199"  # сверяйте с dev.vk.com перед боевым использованием


class VKAPIError(Exception):
    pass


def vk_api_call(method: str, params: dict, access_token: str, version: str = VK_API_VERSION) -> dict:
    response = requests.get(
        f"https://api.vk.com/method/{method}",
        params={**params, "access_token": access_token, "v": version},
        timeout=15,
    )
    data = response.json()
    if "error" in data:
        raise VKAPIError(data["error"])
    return data["response"]


def wall_post(settings, message: str, target: str, publish_date: int | None = None,
              attachments: list[str] | None = None) -> str:
    params = {
        "owner_id": -settings.vk_group_id,
        "message": message,
        "from_group": 1,
    }
    if attachments:
        params["attachments"] = ",".join(attachments)
    if publish_date is not None:
        params["publish_date"] = publish_date
    if target == "vk_donut":
        # 0 = пост остаётся доступен только подписчикам Donut бессрочно.
        # Свериться с текущей семантикой параметра в документации VK перед первым боевым постом.
        params["donut_paid_duration"] = 0

    result = vk_api_call("wall.post", params, access_token=settings.vk_access_token)
    return f"wall-{settings.vk_group_id}_{result['post_id']}"
```

- [ ] **Step 4: Запустить тесты**

```bash
pytest tests/test_vk_client.py -v
```
Ожидается: `PASS` (4 теста).

- [ ] **Step 5: Ручная проверка на тестовой группе ВК**

Завести тестовое сообщество (даже пустое, только для разработки), получить его токен и id, временно указать их в `.env`, вызвать `wall_post` из Python-консоли вручную:
```bash
python -c "
from src.config import load_settings
from src.vk_client import wall_post
settings = load_settings()
print(wall_post(settings, 'Тестовый пост от content-agent', target='vk_wall'))
"
```
Ожидается: в тестовой группе появляется пост, в консоли — `wall-<id>_<n>`.

- [ ] **Step 6: Commit**

```bash
git add src/vk_client.py tests/test_vk_client.py
git commit -m "feat: VK wall.post integration with immediate and scheduled publishing"
```

---

### Task 10: Публикация в VK — медиа

**Что и зачем.** VK не принимает файлы напрямую в `wall.post` — сначала файл нужно загрузить на специальный загрузочный сервер VK (адрес которого сам VK и выдаёт на каждый запрос через `photos.getWallUploadServer`), затем подтвердить загрузку методом `photos.saveWallPhoto`, который возвращает идентификатор вида `photo<owner>_<id>` — вот его уже можно подставить в `attachments` у `wall.post`. Это трёхшаговый танец, специфичный именно для VK (Telegram в Task 11 устроен проще). Так как исходный файл лежит в Telegram, а не у нас на диске, добавляется четвёртый шаг в самом начале — скачать байты через Telegram Bot API (`getFile` → прямая ссылка на файл).

**Осознанное ограничение объёма.** VK для видео использует отдельный метод (`video.save`) с другой, более сложной схемой загрузки (устойчивой к обрывам, потоковой) — это отдельный и не такой уж маленький кусок работы. В этом плане реализуем только фото в VK; если среди медиа поста есть видео, при публикации в VK (Task 11) оно не прикрепляется, а художнику приходит явное предупреждение об этом — то есть ограничение видно ей сразу, а не тонет молча. В Telegram фото и видео работают одинаково просто (Task 11) — там ограничения нет.

**Files:**
- Modify: `content-agent/src/vk_client.py`
- Test: `content-agent/tests/test_vk_client.py`

**Interfaces:**
- Produces: `upload_photo_to_vk(settings, photo_bytes: bytes) -> str` (возвращает строку вложения `photo<owner>_<id>`), обновлённый `wall_post(..., attachments=[...])` уже поддерживает это с Task 9.

- [ ] **Step 1: Написать failing-тест на функцию загрузки фото**

```python
# tests/test_vk_client.py (добавить)
from unittest.mock import patch, MagicMock
from src.vk_client import upload_photo_to_vk


@patch("src.vk_client.vk_api_call")
@patch("src.vk_client.requests.post")
def test_upload_photo_to_vk_returns_attachment_string(mock_post, mock_call):
    mock_call.side_effect = [
        {"upload_url": "https://upload.vk.com/xyz"},  # photos.getWallUploadServer
        [{"id": 999, "owner_id": -333}],  # photos.saveWallPhoto
    ]
    mock_post.return_value = MagicMock(
        json=lambda: {"server": 1, "photo": "[]", "hash": "abc"}
    )
    settings = MagicMock(vk_group_id=333, vk_access_token="tok")

    attachment = upload_photo_to_vk(settings, photo_bytes=b"fake-image-bytes")

    assert attachment == "photo-333_999"
```

- [ ] **Step 2: Запустить и увидеть падение**

```bash
pytest tests/test_vk_client.py -v -k upload_photo
```
Ожидается: `FAIL` — функции нет.

- [ ] **Step 3: Реализовать**

```python
# src/vk_client.py (добавить)
def upload_photo_to_vk(settings, photo_bytes: bytes) -> str:
    upload_server = vk_api_call(
        "photos.getWallUploadServer",
        {"group_id": settings.vk_group_id},
        access_token=settings.vk_access_token,
    )

    upload_response = requests.post(
        upload_server["upload_url"],
        files={"photo": ("photo.jpg", photo_bytes)},
        timeout=30,
    ).json()

    saved = vk_api_call(
        "photos.saveWallPhoto",
        {
            "group_id": settings.vk_group_id,
            "server": upload_response["server"],
            "photo": upload_response["photo"],
            "hash": upload_response["hash"],
        },
        access_token=settings.vk_access_token,
    )
    photo = saved[0]
    return f"photo{photo['owner_id']}_{photo['id']}"
```

- [ ] **Step 4: Запустить тесты**

```bash
pytest tests/test_vk_client.py -v
```
Ожидается: `PASS` (все тесты файла).

- [ ] **Step 5: Функция скачивания файла из Telegram (используется перед загрузкой в VK)**

```python
# src/telegram_bot.py (добавить)
async def download_telegram_file(bot, file_id: str) -> bytes:
    file = await bot.get_file(file_id)
    return bytes(await file.download_as_bytearray())
```

- [ ] **Step 6: Ручная проверка сквозного пути**

В Python-консоли (с реальными тестовыми токенами VK и Telegram): скачать файл по `file_id` любого фото, отправленного боту вручную, прогнать через `upload_photo_to_vk`, подставить результат в `wall_post(..., attachments=[attachment])`, убедиться, что фото появилось в тестовой группе VK.

- [ ] **Step 7: Commit**

```bash
git add src/vk_client.py src/telegram_bot.py tests/test_vk_client.py
git commit -m "feat: VK media upload flow for wall attachments"
```

---

### Task 11: Публикация в Telegram и планировщик

**Что и зачем.** У Telegram Bot API нет параметра «опубликовать позже» — это единственная асимметрия с VK, о которой шла речь в дизайн-документе. Поэтому для отложенных постов в Telegram мы сами кладём задание в `scheduled_jobs` и сами же проверяем раз в минуту, не пора ли его выполнить. `python-telegram-bot` для этого не нужно ничего писать с нуля — в состав библиотеки входит `JobQueue` (обёртка над APScheduler), которая умеет выполнять функцию по расписанию внутри того же процесса, что уже крутит long polling.

**Files:**
- Modify: `content-agent/src/telegram_bot.py`

**Interfaces:**
- Consumes: `vk_client.upload_photo_to_vk`, `telegram_bot.download_telegram_file` (оба из Task 10) — для прикрепления фото к VK-посту
- Produces: `telegram_publish(bot, channel_id, text: str, media: list[dict] | None = None) -> str` (возвращает `external_id` в виде id сообщения), `publish_single_target(conn, bot, settings, post, target, fire_at=None)` — публикация или планирование одной площадки вместе с её медиа, переиспользуется в Task 12 для повторов, `check_due_scheduled_jobs(context)` — функция для `JobQueue.run_repeating`, обработчик команды `/otlozhennye`.

- [ ] **Step 1: Функция немедленной публикации в канал — с поддержкой медиа**

Одно фото/видео отправляется через `send_photo`/`send_video`, несколько — через `send_media_group` (подпись прикрепляется только к первому элементу, так же как в самом Telegram при отправке альбома пользователем):

```python
# src/telegram_bot.py (добавить)
from telegram import InputMediaPhoto, InputMediaVideo


async def telegram_publish(bot, channel_id: str, text: str, media: list[dict] | None = None) -> str:
    if not media:
        message = await bot.send_message(chat_id=channel_id, text=text)
        return str(message.message_id)

    if len(media) == 1:
        item = media[0]
        if item["kind"] == "video":
            message = await bot.send_video(chat_id=channel_id, video=item["file_id"], caption=text)
        else:
            message = await bot.send_photo(chat_id=channel_id, photo=item["file_id"], caption=text)
        return str(message.message_id)

    grouped = []
    for index, item in enumerate(media):
        media_cls = InputMediaVideo if item["kind"] == "video" else InputMediaPhoto
        grouped.append(media_cls(media=item["file_id"], caption=text if index == 0 else None))
    messages = await bot.send_media_group(chat_id=channel_id, media=grouped)
    return str(messages[0].message_id)
```

- [ ] **Step 2: Дописать ветку `approve` в `handle_callback` — выбор времени**

Добавить в начало `telegram_bot.py`: `from src.vk_client import wall_post, upload_photo_to_vk` и `from src.db import create_publish_result, update_publish_result, create_scheduled_job, update_post`.

Логику публикации одной площадки выносим в отдельную функцию `publish_single_target` — не потому что она где-то повторно вызывается прямо сейчас, а потому что в Task 12 её нужно будет вызвать второй раз из обработчика «Повторить», и дублировать этот блок кода там нежелательно. Для VK она же собирает вложения из медиа поста (см. ограничение из Task 10 — видео в VK не прикрепляется, только фото):

```python
# src/telegram_bot.py (добавить)
async def publish_single_target(conn, bot, settings, post: dict, target: str, fire_at=None) -> None:
    if target in ("vk_wall", "vk_donut"):
        attachments = []
        skipped_video = False
        for item in post["media"]:
            if item["kind"] == "video":
                skipped_video = True
                continue
            photo_bytes = await download_telegram_file(bot, item["file_id"])
            attachments.append(upload_photo_to_vk(settings, photo_bytes))

        publish_date = int(fire_at.timestamp()) if fire_at else None
        external_id = wall_post(
            settings, post["edited_text"], target=target,
            publish_date=publish_date, attachments=attachments or None,
        )
        result_id = create_publish_result(conn, post["id"], target, status="sent")
        update_publish_result(conn, result_id, external_id=external_id)

        if skipped_video:
            await bot.send_message(
                settings.telegram_artist_chat_id,
                f"⚠️ Видео не прикреплено к посту в {target} — загрузка видео в VK пока не реализована. "
                f"При необходимости прикрепите его вручную через интерфейс VK.",
            )
    elif target == "telegram":
        if fire_at is None:
            external_id = await telegram_publish(
                bot, settings.telegram_channel_id, post["edited_text"], media=post["media"]
            )
            result_id = create_publish_result(conn, post["id"], target, status="sent")
            update_publish_result(conn, result_id, external_id=external_id)
        else:
            create_publish_result(conn, post["id"], target, status="pending")
            create_scheduled_job(conn, post["id"], target, fire_at=fire_at.isoformat())
```

```python
# заменить ветку elif query.data == "approve" на:
elif query.data == "approve":
    await query.edit_message_text(
        "Когда публикуем?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Сейчас", callback_data="when:now")],
            [InlineKeyboardButton("Через 1 час", callback_data="when:1h")],
            [InlineKeyboardButton("Завтра в 10:00", callback_data="when:tomorrow_10")],
        ]),
    )

elif query.data.startswith("when:"):
    from datetime import datetime, timedelta, timezone

    choice = query.data.split(":", 1)[1]
    now = datetime.now(timezone.utc)
    fire_at = None
    if choice == "1h":
        fire_at = now + timedelta(hours=1)
    elif choice == "tomorrow_10":
        tomorrow = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        fire_at = tomorrow

    post = get_post(conn, post_id)
    settings = context.bot_data["settings"]

    for target in post["targets"]:
        await publish_single_target(conn, context.bot, settings, post, target, fire_at=fire_at)

    update_post(conn, post_id, status="scheduled" if fire_at else "published")
    await query.edit_message_text("Готово: " + ("запланировано" if fire_at else "опубликовано"))
```

Примечание: обработка свободного текста «Указать время» сознательно не включена в этот шаг — три пресета покрывают основной сценарий и не требуют парсинга произвольных дат. Если понадобится, это отдельная небольшая задача поверх готового плана: добавить кнопку `when:custom`, попросить текст вида «15.08 18:00» и разобрать его `datetime.strptime`.

- [ ] **Step 3: Фоновая проверка отложенных Telegram-постов**

```python
# src/telegram_bot.py (добавить)
from datetime import datetime, timezone
from src.db import get_due_scheduled_jobs

async def check_due_scheduled_jobs(context):
    conn = context.bot_data["conn"]
    settings = context.bot_data["settings"]
    now_iso = datetime.now(timezone.utc).isoformat()

    for job in get_due_scheduled_jobs(conn, now_iso):
        post = get_post(conn, job["post_id"])
        external_id = await telegram_publish(
            context.bot, settings.telegram_channel_id, post["edited_text"], media=post["media"]
        )
        conn.execute("UPDATE scheduled_jobs SET status='sent' WHERE id=?", (job["id"],))
        conn.execute(
            "UPDATE publish_results SET status='sent', external_id=? WHERE post_id=? AND target='telegram'",
            (external_id, job["post_id"]),
        )
        conn.commit()
```

Зарегистрировать в `build_application`:
```python
application.job_queue.run_repeating(check_due_scheduled_jobs, interval=60, first=10)
```

- [ ] **Step 4: Команда /otlozhennye**

```python
# src/telegram_bot.py (добавить)
from telegram.ext import CommandHandler

async def list_scheduled(update, context):
    conn = context.bot_data["conn"]
    conn.row_factory = None
    rows = conn.execute(
        "SELECT id, post_id, target, fire_at FROM scheduled_jobs WHERE status='pending' ORDER BY fire_at"
    ).fetchall()
    if not rows:
        await update.message.reply_text("Отложенных постов нет.")
        return
    for row in rows:
        job_id, post_id, target, fire_at = row
        await update.message.reply_text(
            f"#{post_id} → {target}, в {fire_at}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Отменить", callback_data=f"cancel_job:{job_id}")
            ]]),
        )
```

И ветку отмены в `handle_callback`:
```python
elif query.data.startswith("cancel_job:"):
    job_id = int(query.data.split(":", 1)[1])
    conn.execute("UPDATE scheduled_jobs SET status='cancelled' WHERE id=?", (job_id,))
    conn.commit()
    await query.edit_message_text("Отменено.")
```

Регистрация: `application.add_handler(CommandHandler("otlozhennye", list_scheduled))`.

- [ ] **Step 5: Ручная проверка**

Запланировать пост «через 1 час» в Telegram, убедиться, что появилась строка в `scheduled_jobs`; для проверки не ждать час — временно передвинуть `fire_at` в прошлое напрямую в базе (`sqlite3 content_agent.db "update scheduled_jobs set fire_at='2020-01-01T00:00:00+00:00'"`), подождать следующий тик `JobQueue` (до 60 секунд) и убедиться, что пост опубликовался. Проверить `/otlozhennye` до и после.

- [ ] **Step 6: Commit**

```bash
git add src/telegram_bot.py
git commit -m "feat: telegram publishing, scheduling queue, and /otlozhennye command"
```

---

### Task 12: Устойчивость к сбоям

**Что и зачем.** Дизайн-документ требует трёх конкретных вещей на случай, если что-то пошло не так: (1) повтор публикации только для упавшей площадки, не трогая успешные; (2) при перезапуске сервиса — доделать зависшие публикации, а не тихо их потерять; (3) при перезапуске — сразу выполнить просроченные отложенные посты и явно предупредить об опоздании. Всё это уже подготовлено структурой данных из Task 2 (`external_id IS NULL` как признак «реально не опубликовано») — здесь мы просто пишем код, который использует это при старте и по кнопке.

**Files:**
- Modify: `content-agent/src/telegram_bot.py`
- Test: `content-agent/tests/test_startup_resume.py`

**Interfaces:**
- Consumes: `telegram_bot.publish_single_target` (Task 11)
- Produces: `publish_target_safely(conn, bot, settings, post, target, fire_at=None)`, `resume_pending_publications(conn, bot, settings)` — вызывается один раз при старте.

- [ ] **Step 1: Написать failing-тест на выбор того, что нужно доделать**

```python
# tests/test_startup_resume.py
import sqlite3
from src.db import init_db, create_post, create_publish_result, get_pending_publish_results


def test_resume_only_picks_results_without_external_id():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    post_id = create_post(conn, raw_text="x", targets=["vk_wall", "telegram"])

    vk_result_id = create_publish_result(conn, post_id, "vk_wall")
    conn.execute(
        "UPDATE publish_results SET status='sent', external_id='wall-1_1' WHERE id=?",
        (vk_result_id,),
    )
    create_publish_result(conn, post_id, "telegram")  # так и не отправился
    conn.commit()

    pending = get_pending_publish_results(conn)

    assert len(pending) == 1
    assert pending[0]["target"] == "telegram"
```

- [ ] **Step 2: Запустить тест**

```bash
pytest tests/test_startup_resume.py -v
```
Ожидается: `PASS` — эта логика уже реализована в Task 2 через SQL-фильтр `external_id IS NULL`; тест фиксирует и защищает это поведение от случайной поломки в будущем.

- [ ] **Step 3: Обернуть публикацию в try/except и добавить кнопку «Повторить» на упавшую площадку**

Добавить в начало `telegram_bot.py`: `from src.vk_client import VKAPIError`.

Обернуть цикл `for target in post["targets"]: await publish_single_target(...)` из Task 11 Step 2 — и в ветке `when:`, и в новой ветке `retry:` ниже — в try/except с одним и тем же поведением при ошибке, поэтому оформим его отдельной функцией `publish_target_safely`, которую вызывают уже оба места:

```python
# src/telegram_bot.py (добавить)
async def publish_target_safely(conn, bot, settings, post: dict, target: str, fire_at=None) -> None:
    try:
        await publish_single_target(conn, bot, settings, post, target, fire_at=fire_at)
    except VKAPIError as exc:
        result_id = create_publish_result(conn, post["id"], target, status="failed")
        update_publish_result(conn, result_id, error=str(exc))
        await bot.send_message(
            settings.telegram_artist_chat_id,
            f"❌ Не удалось опубликовать в {target}: {exc}\nОстальные площадки не затронуты.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Повторить", callback_data=f"retry:{post['id']}:{target}")
            ]]),
        )
```

В Task 11 Step 2 в цикле заменить `await publish_single_target(conn, context.bot, settings, post, target, fire_at=fire_at)` на `await publish_target_safely(conn, context.bot, settings, post, target, fire_at=fire_at)`.

Добавить ветку `retry` в `handle_callback`:
```python
elif query.data.startswith("retry:"):
    _, retry_post_id, retry_target = query.data.split(":", 2)
    retry_post = get_post(conn, int(retry_post_id))
    settings = context.bot_data["settings"]
    await publish_target_safely(conn, context.bot, settings, retry_post, retry_target)
    await query.edit_message_text(f"Повторил публикацию в {retry_target}.")
```

- [ ] **Step 4: Функция доделывания зависшего при старте**

```python
# src/telegram_bot.py (добавить)
async def resume_pending_publications(conn, bot, settings):
    pending = get_pending_publish_results(conn)
    if not pending:
        return
    for result in pending:
        post = get_post(conn, result["post_id"])
        await bot.send_message(
            settings.telegram_artist_chat_id,
            f"⚠️ После перезапуска нашёл незавершённую публикацию: пост #{post['id']} → {result['target']}. "
            f"Нажмите «Повторить», если она так и не вышла.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Повторить", callback_data=f"retry:{post['id']}:{result['target']}")
            ]]),
        )
```

Вызвать один раз при старте, после `application.initialize()`, до `run_polling()` — конкретное место интеграции зависит от версии `python-telegram-bot`; проще всего — через `post_init` callback:
```python
application.post_init = lambda app: resume_pending_publications(
    app.bot_data["conn"], app.bot, app.bot_data["settings"]
)
```

- [ ] **Step 5: Доделывание просроченных отложенных Telegram-постов**

`check_due_scheduled_jobs` из Task 11 уже решает эту задачу без изменений: если сервис не работал и время прошло, при первом тике `JobQueue` после запуска (через 10 секунд по конфигу `first=10`) все просроченные задания будут найдены и выполнены. Добавить только явное предупреждение об опоздании:

```python
# в check_due_scheduled_jobs, после публикации:
from datetime import datetime as _dt
scheduled_time = _dt.fromisoformat(job["fire_at"])
delay = datetime.now(timezone.utc) - scheduled_time
if delay.total_seconds() > 120:
    await context.bot.send_message(
        settings.telegram_artist_chat_id,
        f"⚠️ Отложенный пост #{job['post_id']} вышел с опозданием на {int(delay.total_seconds() // 60)} мин.",
    )
```

- [ ] **Step 6: Ручная проверка**

Создать пост, руками испортить VK-токен в `.env`, попробовать опубликовать — убедиться, что приходит понятное сообщение об ошибке с кнопкой «Повторить», а не тишина или падение бота целиком. Вернуть токен, нажать «Повторить», убедиться, что публикация проходит.

- [ ] **Step 7: Commit**

```bash
git add src/telegram_bot.py tests/test_startup_resume.py
git commit -m "feat: crash recovery, per-target retry, and late-schedule warnings"
```

---

### Task 13: Ручной end-to-end чек-лист

**Что и зачем.** Часть поведения (реальная доставка в VK/Telegram, поведение при реальном обрыве сети, миллисекундная точность альбомов) невозможно и не нужно покрывать автотестами для инструмента на одного пользователя — дешевле и надёжнее один раз пройти по чек-листу руками на тестовых аккаунтах перед тем, как переключиться на боевые VK-группу и Telegram-канал студии.

**Files:**
- Create: `content-agent/docs/manual-test-checklist.md`

- [ ] **Step 1: Написать чек-лист**

```markdown
# Ручной чек-лист перед переключением на боевые каналы

Прогонять на тестовой VK-группе и тестовом Telegram-канале, не на боевых.

- [ ] Текстовый черновик без медиа → публикуется в VK и Telegram сразу
- [ ] Один черновик с фото + подписью → фото и текст приходят на согласование вместе
- [ ] Альбом из 3-4 фото с одной подписью → собирается в один черновик, не в несколько
- [ ] Пост с фото, опубликованный в VK → фото реально прикреплено к посту на стене
- [ ] Пост с видео, опубликованный в VK → видео не прикреплено, приходит явное предупреждение об этом; в Telegram то же видео публикуется нормально
- [ ] Выбраны только ручные площадки (Дзен, MAX) → приходит текст без кнопки публикации
- [ ] Смешанный выбор (VK + Дзен) → VK публикуется, текст для Дзен приходит отдельно
- [ ] «Переписать» с уточнением → приходит новый вариант, старый не публикуется
- [ ] «Отмена» → пост помечен cancelled, ничего никуда не уходит
- [ ] Отложенный пост в VK → появляется в VK точно в заданное время
- [ ] Отложенный пост в Telegram → появляется в канале в заданное время (± 1 минута из-за цикла проверки)
- [ ] `/otlozhennye` показывает все ожидающие посты и позволяет отменить
- [ ] Временно испорченный VK-токен → приходит понятная ошибка с кнопкой «Повторить», Telegram-публикация (если была) не блокируется
- [ ] Убить процесс бота посреди публикации (после VK, до Telegram) → при перезапуске приходит предупреждение именно про Telegram, VK не дублируется
- [ ] Сервис не работал во время срабатывания отложенного поста → после перезапуска пост выходит с пометкой об опоздании
```

- [ ] **Step 2: Пройти чек-лист один раз перед первым боевым использованием, отметить результаты**

- [ ] **Step 3: Commit**

```bash
git add docs/manual-test-checklist.md
git commit -m "docs: manual end-to-end verification checklist"
```

---

## Что дальше

После прохождения всех задач у вас рабочий бот для одного пользователя (художника), покрывающий весь дизайн-документ, кроме трёх вещей, сознательно отложенных как отдельные, не блокирующие расширения:
- свободный ввод времени («Указать время») вместо трёх пресетов;
- разнос по отдельным каналам ВК/Telegram для детской и взрослой аудитории (сейчас это только метка для аналитики);
- загрузка видео в VK (`video.save` с потоковой загрузкой) — сейчас видео прикрепляется только в Telegram, в VK публикуется пост без него с явным предупреждением художнику.

Все три — небольшие, самодостаточные доработки поверх готовой системы, каждую можно оформить отдельным мини-планом по той же схеме, когда до них дойдёт очередь.
