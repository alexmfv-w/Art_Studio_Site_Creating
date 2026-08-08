# Тэггер фотографий — план реализации

> **Для агентов-исполнителей:** ОБЯЗАТЕЛЬНЫЙ САБ-СКИЛЛ: используйте superpowers:subagent-driven-development (рекомендуется) или superpowers:executing-plans для выполнения плана задача за задачей. Шаги отмечены чекбоксами (`- [ ]`) для отслеживания.

**Цель:** локальный инструмент для разметки фотографий студии — пролистывать фото из указанной папки, писать к каждой описание, сохранять в TSV.

**Архитектура:** один файл `tools/photo-tagger.py` на стандартной библиотеке Python. Три ответственности с чёткими границами: чистая функция чтения размеров изображения из байтов заголовка, чистые функции чтения/записи TSV, и HTTP-слой со встроенной HTML-страницей. Первые две покрыты автотестами, третья проверяется вручную.

**Тех-стек:** Python 3.9 (на машине 3.9.6), только стандартная библиотека — `http.server`, `csv`, `json`, `pathlib`, `webbrowser`, `unittest`.

## Global Constraints

- **Никаких внешних зависимостей.** Pillow не установлен и ставиться не должен — размеры изображений читаются парсингом заголовков файлов.
- **Python 3.9-совместимый синтаксис.** Не использовать `match`, `X | Y` в аннотациях типов (только `Optional[...]`/`Union[...]` из `typing`), и другие возможности 3.10+.
- **Разделитель TSV — таб.** При сохранении табы и переводы строк внутри описания заменяются пробелом, чтобы формат не мог сломаться.
- Колонки TSV строго в порядке: `file`, `description`, `width`, `height`, `orientation`.
- `orientation` принимает ровно одно из трёх значений: `landscape`, `portrait`, `square`.
- Путь к папке с фотографиями — обязательный позиционный аргумент командной строки.
- Фотографии живут вне репозитория; в git попадает только сам скрипт.
- Тесты запускаются как `python3 -m unittest discover -s tools -p "test_*.py"`.

---

## Структура файлов

```
tools/
├── photo-tagger.py        # весь инструмент: размеры, TSV, HTTP-слой, встроенный HTML
└── test_photo_tagger.py   # автотесты чистых частей (размеры, TSV)
```

Инструмент вспомогательный и одноразовый — дробить на модули не нужно, но чистые функции внутри файла отделены от HTTP-слоя, чтобы их можно было тестировать без сети.

---

### Task 1: Чтение размеров изображения из заголовков

**Что и зачем.** Нужны ширина и высота каждой фотографии, чтобы при вёрстке понимать, годится ли фото в широкий блок или только в узкую колонку. Pillow ради двух чисел ставить избыточно, поэтому читаем заголовки сами: у PNG размеры лежат в фиксированных байтах 16-24 после сигнатуры, у JPEG нужно пройти по цепочке маркеров до SOF-маркера (кадрового), где размеры записаны следом за длиной сегмента.

**Files:**
- Create: `tools/photo-tagger.py`
- Test: `tools/test_photo_tagger.py`

**Interfaces:**
- Produces: `image_size(path) -> Optional[Tuple[int, int]]` — возвращает `(width, height)` или `None`, если формат не распознан/файл битый. `orientation(width, height) -> str` — возвращает `'landscape'`, `'portrait'` или `'square'`.

- [ ] **Step 1: Написать падающий тест**

```python
# tools/test_photo_tagger.py
import importlib.util
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "photo_tagger", Path(__file__).parent / "photo-tagger.py"
)
photo_tagger = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(photo_tagger)


def make_png(path, width, height):
    """Собирает минимальный валидный PNG заданного размера."""
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr_body = b"IHDR" + struct.pack(">II", width, height) + bytes([8, 2, 0, 0, 0])
    ihdr = struct.pack(">I", len(ihdr_body) - 4) + ihdr_body
    ihdr += struct.pack(">I", zlib.crc32(ihdr_body) & 0xFFFFFFFF)
    path.write_bytes(sig + ihdr)


def make_jpeg(path, width, height):
    """Собирает минимальный JPEG с SOF0-маркером заданного размера."""
    soi = b"\xff\xd8"
    sof_body = bytes([8]) + struct.pack(">HH", height, width) + bytes([3])
    sof = b"\xff\xc0" + struct.pack(">H", len(sof_body) + 2) + sof_body
    path.write_bytes(soi + sof + b"\xff\xd9")


class TestImageSize(unittest.TestCase):
    def test_png_size(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.png"
            make_png(p, 4032, 3024)
            self.assertEqual(photo_tagger.image_size(p), (4032, 3024))

    def test_jpeg_size(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.jpg"
            make_jpeg(p, 1920, 1080)
            self.assertEqual(photo_tagger.image_size(p), (1920, 1080))

    def test_unknown_format_returns_none(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.txt"
            p.write_bytes(b"not an image at all")
            self.assertIsNone(photo_tagger.image_size(p))

    def test_orientation(self):
        self.assertEqual(photo_tagger.orientation(4032, 3024), "landscape")
        self.assertEqual(photo_tagger.orientation(3024, 4032), "portrait")
        self.assertEqual(photo_tagger.orientation(1000, 1000), "square")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Запустить и увидеть падение**

```bash
cd /Users/alex/work/art_site_creating
python3 -m unittest discover -s tools -p "test_*.py" -v
```
Ожидается: `FileNotFoundError` или ошибка загрузки модуля — файла `tools/photo-tagger.py` ещё нет.

- [ ] **Step 3: Реализовать**

```python
#!/usr/bin/env python3
"""Локальный тэггер фотографий: пролистывать папку и писать описания в TSV.

Запуск:
    python3 tools/photo-tagger.py ~/Pictures/kistpero
"""
import struct
from pathlib import Path
from typing import Optional, Tuple

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def image_size(path) -> Optional[Tuple[int, int]]:
    """Читает (ширина, высота) из заголовка PNG или JPEG.

    Возвращает None, если формат не распознан или файл повреждён.
    Намеренно не использует Pillow — ради двух чисел зависимость избыточна.
    """
    try:
        with open(path, "rb") as f:
            head = f.read(26)
            if len(head) < 26:
                return None

            # PNG: сигнатура, затем чанк IHDR, в котором ширина и высота
            # лежат по фиксированным смещениям 16..24.
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                width, height = struct.unpack(">II", head[16:24])
                return (width, height)

            # JPEG: идём по цепочке маркеров до SOF (start of frame),
            # где после длины сегмента и байта точности лежат высота и ширина.
            if head[:2] == b"\xff\xd8":
                f.seek(2)
                while True:
                    marker = f.read(2)
                    if len(marker) < 2 or marker[0] != 0xFF:
                        return None
                    code = marker[1]
                    # SOF0..SOF15, кроме DHT(c4), JPGA(c8) и DAC(cc)
                    if 0xC0 <= code <= 0xCF and code not in (0xC4, 0xC8, 0xCC):
                        f.read(3)  # длина сегмента (2 байта) + точность (1 байт)
                        dims = f.read(4)
                        if len(dims) < 4:
                            return None
                        height, width = struct.unpack(">HH", dims)
                        return (width, height)
                    length_bytes = f.read(2)
                    if len(length_bytes) < 2:
                        return None
                    (length,) = struct.unpack(">H", length_bytes)
                    if length < 2:
                        return None
                    f.seek(length - 2, 1)
    except OSError:
        return None
    return None


def orientation(width: int, height: int) -> str:
    """Классифицирует пропорции — по этому полю видно, куда фото годится в вёрстке."""
    if width > height:
        return "landscape"
    if height > width:
        return "portrait"
    return "square"
```

- [ ] **Step 4: Запустить тесты**

```bash
python3 -m unittest discover -s tools -p "test_*.py" -v
```
Ожидается: 4 теста проходят.

- [ ] **Step 5: Commit**

```bash
git add tools/photo-tagger.py tools/test_photo_tagger.py
git commit -m "feat: read image dimensions from JPEG/PNG headers without Pillow"
```

---

### Task 2: Чтение и запись TSV

**Что и зачем.** Результат разметки должен переживать перезапуск: при повторном открытии уже введённые описания подставляются в поле. Поэтому нужны две симметричные функции — прочитать существующий файл в словарь «имя файла → описание» и записать полный набор строк обратно. Запись всегда переписывает файл целиком (а не дописывает) — так проще гарантировать, что не появятся дубликаты строк для одного файла.

**Files:**
- Modify: `tools/photo-tagger.py`
- Modify: `tools/test_photo_tagger.py`

**Interfaces:**
- Consumes: `orientation(width, height) -> str` из Task 1.
- Produces: `load_descriptions(tsv_path) -> Dict[str, str]` — словарь «имя файла → описание», пустой если файла нет. `sanitize(text) -> str` — заменяет табы и переводы строк на пробел. `save_rows(tsv_path, rows)` — пишет TSV с заголовком, где `rows` это список кортежей `(file, description, width, height, orientation)`.

- [ ] **Step 1: Написать падающий тест**

Добавить в конец `tools/test_photo_tagger.py`, перед блоком `if __name__ == "__main__":`

```python
class TestTsvStorage(unittest.TestCase):
    def test_load_missing_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(photo_tagger.load_descriptions(Path(d) / "nope.tsv"), {})

    def test_save_then_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            tsv = Path(d) / "photos.tsv"
            rows = [
                ("IMG_001.jpg", "руки за гончарным кругом", 4032, 3024, "landscape"),
                ("IMG_002.jpg", "готовая ваза, синяя глазурь", 3024, 4032, "portrait"),
            ]
            photo_tagger.save_rows(tsv, rows)
            loaded = photo_tagger.load_descriptions(tsv)
            self.assertEqual(loaded["IMG_001.jpg"], "руки за гончарным кругом")
            self.assertEqual(loaded["IMG_002.jpg"], "готовая ваза, синяя глазурь")

    def test_header_and_column_order(self):
        with tempfile.TemporaryDirectory() as d:
            tsv = Path(d) / "photos.tsv"
            photo_tagger.save_rows(tsv, [("a.jpg", "описание", 100, 200, "portrait")])
            lines = tsv.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[0], "file\tdescription\twidth\theight\torientation")
            self.assertEqual(lines[1], "a.jpg\tописание\t100\t200\tportrait")

    def test_sanitize_strips_tabs_and_newlines(self):
        self.assertEqual(photo_tagger.sanitize("две\tчасти"), "две части")
        self.assertEqual(photo_tagger.sanitize("строка\nвторая"), "строка вторая")
        self.assertEqual(photo_tagger.sanitize("  обрезка  "), "обрезка")

    def test_saved_description_with_tab_does_not_break_format(self):
        with tempfile.TemporaryDirectory() as d:
            tsv = Path(d) / "photos.tsv"
            photo_tagger.save_rows(
                tsv, [("a.jpg", photo_tagger.sanitize("а\tб"), 10, 10, "square")]
            )
            loaded = photo_tagger.load_descriptions(tsv)
            self.assertEqual(loaded["a.jpg"], "а б")
```

- [ ] **Step 2: Запустить и увидеть падение**

```bash
python3 -m unittest discover -s tools -p "test_*.py" -v
```
Ожидается: `AttributeError: module 'photo_tagger' has no attribute 'load_descriptions'`.

- [ ] **Step 3: Реализовать**

Добавить в `tools/photo-tagger.py` после функции `orientation`, и дописать `import csv` к импортам в начале файла:

```python
TSV_HEADER = ["file", "description", "width", "height", "orientation"]


def sanitize(text: str) -> str:
    """Убирает из описания то, что могло бы сломать TSV: табы и переводы строк."""
    return text.replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()


def load_descriptions(tsv_path) -> dict:
    """Читает уже сохранённые описания, чтобы разметку можно было продолжить.

    Возвращает пустой словарь, если файла ещё нет.
    """
    path = Path(tsv_path)
    if not path.exists():
        return {}
    descriptions = {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            name = row.get("file")
            if name:
                descriptions[name] = row.get("description") or ""
    return descriptions


def save_rows(tsv_path, rows) -> None:
    """Перезаписывает TSV целиком — так не появятся дубликаты строк для файла."""
    with open(tsv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(TSV_HEADER)
        for row in rows:
            writer.writerow(row)
```

- [ ] **Step 4: Запустить тесты**

```bash
python3 -m unittest discover -s tools -p "test_*.py" -v
```
Ожидается: 9 тестов проходят (4 из Task 1 + 5 новых).

- [ ] **Step 5: Commit**

```bash
git add tools/photo-tagger.py tools/test_photo_tagger.py
git commit -m "feat: TSV load/save with tab-safe descriptions"
```

---

### Task 3: HTTP-слой и страница разметки

**Что и зачем.** Здесь чистые части соединяются в работающий инструмент. Сервер отдаёт три вещи: HTML-страницу, JSON со списком фотографий и их описаниями, и сами файлы изображений; плюс принимает POST с описанием. Страница держит весь список в памяти браузера и сохраняет описание при каждом переходе к соседней фотографии — отдельной кнопки «сохранить» нет по решению заказчика. Сохранение идёт на сервер сразу, а не в конце, чтобы закрытая вкладка не потеряла работу.

**Files:**
- Modify: `tools/photo-tagger.py`

**Interfaces:**
- Consumes: `image_size`, `orientation`, `load_descriptions`, `save_rows`, `sanitize`, `IMAGE_EXTENSIONS`, `TSV_HEADER` из Tasks 1-2.
- Produces: исполняемый скрипт с точкой входа `main()`; HTTP-эндпоинты `GET /` (страница), `GET /api/photos` (JSON), `GET /photo/<имя>` (файл изображения), `POST /api/save` (JSON `{"file": ..., "description": ...}`).

- [ ] **Step 1: Дописать серверную часть**

Добавить в конец `tools/photo-tagger.py`, и дописать к импортам в начале файла: `import argparse`, `import json`, `import threading`, `import webbrowser`, `from http.server import BaseHTTPRequestHandler, HTTPServer`, `from urllib.parse import unquote, urlparse`

```python
PAGE = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Разметка фотографий</title>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0; background: #1c1f18; color: #ECEEDF;
    font: 15px/1.5 ui-sans-serif, -apple-system, "Segoe UI", Roboto, sans-serif;
    display: flex; flex-direction: column; height: 100vh;
  }
  header {
    padding: 10px 18px; background: #2C3323; display: flex;
    align-items: center; gap: 16px; flex-shrink: 0;
  }
  #counter { font-variant-numeric: tabular-nums; color: #C7CBA6; }
  #name { color: #8b9178; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  #stage { flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; padding: 14px; }
  #stage img { max-width: 100%; max-height: 100%; object-fit: contain; }
  footer { padding: 12px 18px 18px; background: #23271d; flex-shrink: 0; }
  #desc {
    width: 100%; padding: 11px 13px; font: inherit; border-radius: 4px;
    border: 1px solid #454f38; background: #ECEEDF; color: #262B1F;
  }
  #desc:focus { outline: 2px solid #D98A2E; outline-offset: 1px; }
  .row { display: flex; gap: 10px; margin-top: 10px; align-items: center; }
  button {
    font: inherit; padding: 9px 18px; border-radius: 4px; border: none;
    background: #3E4A2E; color: #F3F1DE; cursor: pointer;
  }
  button:hover:not(:disabled) { background: #4b5a38; }
  button:disabled { opacity: .4; cursor: default; }
  #status { color: #8b9178; font-size: 13px; margin-left: auto; }
  .hint { color: #6f7660; font-size: 12.5px; }
</style>
</head>
<body>
<header>
  <strong>Разметка фотографий</strong>
  <span id="counter">— / —</span>
  <span id="name"></span>
</header>
<div id="stage"><img id="photo" alt=""></div>
<footer>
  <input id="desc" placeholder="Что на фото? Например: руки за гончарным кругом" autocomplete="off">
  <div class="row">
    <button id="prev">← Назад</button>
    <button id="next">Вперёд →</button>
    <span class="hint">Описание сохраняется само при переходе. Стрелки на клавиатуре тоже работают.</span>
    <span id="status"></span>
  </div>
</footer>
<script>
let photos = [];
let i = 0;
let loadedDesc = "";

const $ = (id) => document.getElementById(id);

async function boot() {
  const res = await fetch("/api/photos");
  photos = await res.json();
  if (!photos.length) {
    $("counter").textContent = "нет изображений в папке";
    $("desc").disabled = true;
    $("prev").disabled = true;
    $("next").disabled = true;
    return;
  }
  show(0);
}

function show(index) {
  i = index;
  const p = photos[i];
  $("photo").src = "/photo/" + encodeURIComponent(p.file);
  $("photo").alt = p.file;
  $("desc").value = p.description || "";
  loadedDesc = p.description || "";
  $("counter").textContent = (i + 1) + " / " + photos.length;
  $("name").textContent = p.file + " · " + p.width + "×" + p.height + " · " + p.orientation;
  $("prev").disabled = i === 0;
  $("next").disabled = i === photos.length - 1;
  $("desc").focus();
}

async function persist() {
  const value = $("desc").value;
  if (value === loadedDesc) return;
  photos[i].description = value;
  $("status").textContent = "сохраняю…";
  try {
    await fetch("/api/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file: photos[i].file, description: value })
    });
    loadedDesc = value;
    $("status").textContent = "сохранено";
    setTimeout(() => { $("status").textContent = ""; }, 1200);
  } catch (e) {
    $("status").textContent = "не сохранилось — проверь, запущен ли скрипт";
  }
}

async function go(delta) {
  const target = i + delta;
  if (target < 0 || target >= photos.length) return;
  await persist();
  show(target);
}

$("prev").addEventListener("click", () => go(-1));
$("next").addEventListener("click", () => go(1));
document.addEventListener("keydown", (e) => {
  if (e.key === "ArrowLeft") go(-1);
  if (e.key === "ArrowRight" || e.key === "Enter") go(1);
});
window.addEventListener("beforeunload", () => {
  const value = $("desc").value;
  if (photos.length && value !== loadedDesc) {
    navigator.sendBeacon("/api/save", new Blob(
      [JSON.stringify({ file: photos[i].file, description: value })],
      { type: "application/json" }
    ));
  }
});
boot();
</script>
</body>
</html>
"""


def scan_folder(folder):
    """Собирает отсортированный список изображений с размерами и описаниями."""
    folder = Path(folder)
    tsv_path = folder / "photos.tsv"
    saved = load_descriptions(tsv_path)
    photos = []
    for path in sorted(folder.iterdir()):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        size = image_size(path)
        width, height = size if size else (0, 0)
        photos.append({
            "file": path.name,
            "description": saved.get(path.name, ""),
            "width": width,
            "height": height,
            "orientation": orientation(width, height) if size else "unknown",
        })
    return photos


def make_handler(folder, photos, lock):
    tsv_path = Path(folder) / "photos.tsv"

    def write_tsv():
        rows = [
            (p["file"], p["description"], p["width"], p["height"], p["orientation"])
            for p in photos
        ]
        save_rows(tsv_path, rows)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # не засорять терминал строкой на каждый запрос

        def _send(self, code, content_type, body):
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            route = urlparse(self.path).path
            if route == "/":
                self._send(200, "text/html; charset=utf-8", PAGE.encode("utf-8"))
            elif route == "/api/photos":
                body = json.dumps(photos, ensure_ascii=False).encode("utf-8")
                self._send(200, "application/json; charset=utf-8", body)
            elif route.startswith("/photo/"):
                name = unquote(route[len("/photo/"):])
                target = (Path(folder) / name).resolve()
                # не выпускать за пределы папки с фотографиями
                if Path(folder).resolve() not in target.parents or not target.is_file():
                    self._send(404, "text/plain; charset=utf-8", b"not found")
                    return
                suffix = target.suffix.lower()
                mime = "image/png" if suffix == ".png" else "image/jpeg"
                self._send(200, mime, target.read_bytes())
            else:
                self._send(404, "text/plain; charset=utf-8", b"not found")

        def do_POST(self):
            if urlparse(self.path).path != "/api/save":
                self._send(404, "text/plain; charset=utf-8", b"not found")
                return
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            name = payload.get("file")
            description = sanitize(payload.get("description") or "")
            with lock:
                for p in photos:
                    if p["file"] == name:
                        p["description"] = description
                        break
                write_tsv()
            self._send(200, "application/json; charset=utf-8", b'{"ok":true}')

    return Handler


def main():
    parser = argparse.ArgumentParser(
        description="Разметка фотографий: пролистать папку и записать описания в photos.tsv"
    )
    parser.add_argument("folder", help="путь к папке с фотографиями")
    parser.add_argument("--port", type=int, default=8765, help="порт (по умолчанию 8765)")
    args = parser.parse_args()

    folder = Path(args.folder).expanduser().resolve()
    if not folder.is_dir():
        raise SystemExit("Папки не существует: {}".format(folder))

    photos = scan_folder(folder)
    print("Фотографий найдено: {}".format(len(photos)))
    if not photos:
        print("В папке нет .jpg/.jpeg/.png — проверьте путь.")

    lock = threading.Lock()
    server = HTTPServer(("127.0.0.1", args.port), make_handler(folder, photos, lock))
    url = "http://127.0.0.1:{}/".format(args.port)
    print("Открываю {}".format(url))
    print("Результат пишется в {}".format(folder / "photos.tsv"))
    print("Остановить — Ctrl+C")
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nГотово.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Проверить, что автотесты не сломались**

```bash
python3 -m unittest discover -s tools -p "test_*.py" -v
```
Ожидается: те же 9 тестов проходят — серверная часть не должна была затронуть чистые функции.

- [ ] **Step 3: Проверить эндпоинты на тестовой папке**

```bash
mkdir -p /tmp/tagger-check
python3 - <<'EOF'
import struct, zlib
from pathlib import Path
d = Path("/tmp/tagger-check")
for name, w, h in [("one.png", 800, 600), ("two.png", 600, 800)]:
    sig = b"\x89PNG\r\n\x1a\n"
    body = b"IHDR" + struct.pack(">II", w, h) + bytes([8, 2, 0, 0, 0])
    chunk = struct.pack(">I", len(body) - 4) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
    (d / name).write_bytes(sig + chunk)
print("тестовые картинки созданы")
EOF

python3 tools/photo-tagger.py /tmp/tagger-check --port 8799 &
sleep 2
echo "--- список фотографий ---"
curl -s http://127.0.0.1:8799/api/photos
echo ""
echo "--- сохранение описания ---"
curl -s -X POST http://127.0.0.1:8799/api/save \
  -H 'Content-Type: application/json' \
  -d '{"file":"one.png","description":"тестовое описание"}'
echo ""
echo "--- получившийся TSV ---"
cat /tmp/tagger-check/photos.tsv
pkill -f "photo-tagger.py" || true
```
Ожидается: JSON содержит обе картинки с верными размерами (`800×600` → `landscape`, `600×800` → `portrait`); TSV содержит заголовок и строку `one.png` с описанием «тестовое описание».

- [ ] **Step 4: Проверить возобновляемость**

```bash
python3 tools/photo-tagger.py /tmp/tagger-check --port 8799 &
sleep 2
curl -s http://127.0.0.1:8799/api/photos
pkill -f "photo-tagger.py" || true
rm -rf /tmp/tagger-check
```
Ожидается: у `one.png` в JSON уже стоит `"description": "тестовое описание"` — то есть при перезапуске разметка подхватилась.

- [ ] **Step 5: Commit**

```bash
git add tools/photo-tagger.py
git commit -m "feat: local HTTP photo tagger UI"
```

---

## Что дальше

После разметки заказчиком: `photos.tsv` копируется в репозиторий, и по нему планируется подстановка реальных фотографий в `PhotoPlaceholder` на страницах — отдельный цикл спека → план → реализация.
