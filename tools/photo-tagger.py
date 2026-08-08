#!/usr/bin/env python3
"""Локальный тэггер фотографий: пролистывать папку и писать описания в TSV.

Запуск:
    python3 tools/photo-tagger.py ~/Pictures/kistpero
"""
import argparse
import csv
import json
import struct
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import unquote, urlparse

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
TSV_HEADER = ["file", "description", "tags", "width", "height", "orientation"]

# Группы — только для раскладки кнопок в интерфейсе; в файле теги лежат плоским
# списком через ';', поэтому новый тег можно добавить, не меняя формат TSV.
# Обычно список берётся из tools/tags.json; это запасной вариант на случай,
# если конфига рядом не оказалось.
DEFAULT_TAG_GROUPS = [
    ("Аудитория", ["взрослые", "дети", "подростки", "общее"]),
    ("Направление", [
        "живопись", "рисунок", "каллиграфия пером", "каллиграфия брашпеном",
        "керамика", "лепка/пластилинография", "скетчинг", "леттеринг", "роспись",
    ]),
    ("В кадре", [
        "процесс/руки", "готовая работа", "мастерская",
        "преподаватель", "ученики", "материалы/инструменты",
    ]),
    ("Пометки", ["★ на главную", "не публиковать"]),
]
DEFAULT_TAGS_FILE = Path(__file__).resolve().parent / "tags.json"


def parse_tag_groups(data):
    """Проверяет структуру конфига тегов и возвращает список пар (группа, теги).

    Кидает ValueError с понятным текстом — конфиг правит человек руками,
    поэтому ошибка должна прямо говорить, что именно не так.
    """
    if not isinstance(data, dict):
        raise ValueError(
            'ожидался объект вида {"Название группы": ["тег", "тег"]}'
        )
    groups = []
    seen = {}
    for group, tags in data.items():
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
            raise ValueError(
                'группа «{}»: ожидался список строк'.format(group)
            )
        cleaned = [t.strip() for t in tags if t.strip()]
        if not cleaned:
            continue
        for tag in cleaned:
            if tag in seen:
                raise ValueError(
                    'тег «{}» встречается и в группе «{}», и в «{}» — '
                    'теги должны быть уникальными'.format(tag, seen[tag], group)
                )
            seen[tag] = group
        groups.append((group, cleaned))
    if not groups:
        raise ValueError("в конфиге не нашлось ни одного тега")
    return groups


def load_tag_groups(path):
    """Читает конфиг тегов; если файла нет — возвращает встроенный список."""
    p = Path(path)
    if not p.exists():
        return list(DEFAULT_TAG_GROUPS)
    with open(p, "r", encoding="utf-8") as f:
        return parse_tag_groups(json.load(f))


def unknown_tags(photos, known):
    """Считает теги из разметки, которых больше нет в конфиге.

    Нужно, чтобы заказчик заметил, если убрал тег из tags.json уже после
    того, как проставил его части фотографий.
    """
    known_set = set(known)
    counts = {}
    for photo in photos:
        for tag in (photo.get("tags") or "").split(";"):
            if tag and tag not in known_set:
                counts[tag] = counts.get(tag, 0) + 1
    return counts


def image_size(path) -> Optional[Tuple[int, int]]:
    """Читает (ширина, высота) из заголовка PNG или JPEG.

    Возвращает None, если формат не распознан или файл повреждён.
    Намеренно не использует Pillow — ради двух чисел зависимость избыточна.
    """
    try:
        with open(path, "rb") as f:
            head = f.read(26)
            if len(head) < 2:
                return None

            # PNG: сигнатура, затем чанк IHDR, в котором ширина и высота
            # лежат по фиксированным смещениям 16..24.
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                if len(head) < 24:
                    return None
                width, height = struct.unpack(">II", head[16:24])
                return (width, height)

            # JPEG: идём по цепочке маркеров до SOF (start of frame),
            # где после длины сегмента и байта точности лежат высота и ширина.
            # Заголовок JPEG может быть короче 26 байт, поэтому длину не требуем.
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


def sanitize(text: str) -> str:
    """Убирает из описания то, что могло бы сломать TSV: табы и переводы строк."""
    return text.replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()


def clean_tags(tags, known) -> str:
    """Оставляет только теги из конфига и склеивает через ';'.

    Порядок берётся из конфига, а не из порядка кликов — так значение
    в файле не зависит от того, в каком порядке заказчик нажимал кнопки.
    """
    chosen = set(tags or [])
    return ";".join(t for t in known if t in chosen)


def load_entries(tsv_path) -> dict:
    """Читает сохранённые описания и теги, чтобы разметку можно было продолжить.

    Возвращает пустой словарь, если файла ещё нет. Файлы от ранней версии
    инструмента (без колонки tags) читаются корректно — теги будут пустыми.
    """
    path = Path(tsv_path)
    if not path.exists():
        return {}
    entries = {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            name = row.get("file")
            if name:
                entries[name] = {
                    "description": row.get("description") or "",
                    "tags": row.get("tags") or "",
                }
    return entries


def save_rows(tsv_path, rows) -> None:
    """Перезаписывает TSV целиком — так не появятся дубликаты строк для файла."""
    with open(tsv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(TSV_HEADER)
        for row in rows:
            writer.writerow(row)


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
  #tags { margin-top: 10px; display: flex; flex-direction: column; gap: 7px; }
  .tag-group { display: flex; align-items: center; gap: 7px; flex-wrap: wrap; }
  .tag-group > .glabel {
    color: #6f7660; font-size: 11.5px; text-transform: uppercase;
    letter-spacing: .05em; min-width: 92px; flex-shrink: 0;
  }
  .tag {
    font: inherit; font-size: 13px; padding: 4px 11px; border-radius: 999px;
    border: 1px solid #454f38; background: transparent; color: #C7CBA6; cursor: pointer;
  }
  .tag:hover { border-color: #6d7a55; }
  .tag.on { background: #D98A2E; border-color: #D98A2E; color: #262B1F; font-weight: 600; }
  .tag:focus-visible { outline: 2px solid #ECEEDF; outline-offset: 1px; }
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
  <div id="tags"></div>
  <div class="row">
    <button id="prev">← Назад</button>
    <button id="next">Вперёд →</button>
    <span class="hint">Описание сохраняется само при переходе. Стрелки на клавиатуре тоже работают.</span>
    <span id="status"></span>
  </div>
</footer>
<script>
let photos = [];
let groups = [];
let i = 0;
let loadedDesc = "";
let loadedTags = "";
let selected = new Set();

const $ = (id) => document.getElementById(id);

function renderTagButtons() {
  const box = $("tags");
  box.innerHTML = "";
  groups.forEach(([label, tags]) => {
    const row = document.createElement("div");
    row.className = "tag-group";
    const lbl = document.createElement("span");
    lbl.className = "glabel";
    lbl.textContent = label;
    row.appendChild(lbl);
    tags.forEach((tag) => {
      const b = document.createElement("button");
      b.className = "tag";
      b.type = "button";
      b.textContent = tag;
      b.dataset.tag = tag;
      b.addEventListener("click", () => {
        if (selected.has(tag)) { selected.delete(tag); } else { selected.add(tag); }
        b.classList.toggle("on", selected.has(tag));
      });
      row.appendChild(b);
    });
    box.appendChild(row);
  });
}

function paintTags() {
  document.querySelectorAll(".tag").forEach((b) => {
    b.classList.toggle("on", selected.has(b.dataset.tag));
  });
}

function currentTags() { return Array.from(selected); }

async function boot() {
  const [photosRes, tagsRes] = await Promise.all([
    fetch("/api/photos"), fetch("/api/tags")
  ]);
  photos = await photosRes.json();
  groups = await tagsRes.json();
  renderTagButtons();
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
  loadedTags = p.tags || "";
  selected = new Set(loadedTags ? loadedTags.split(";") : []);
  paintTags();
  $("counter").textContent = (i + 1) + " / " + photos.length;
  $("name").textContent = p.file + " · " + p.width + "×" + p.height + " · " + p.orientation;
  $("prev").disabled = i === 0;
  $("next").disabled = i === photos.length - 1;
  $("desc").focus();
}

async function persist() {
  const value = $("desc").value;
  const tagsNow = currentTags().join(";");
  if (value === loadedDesc && tagsNow === loadedTags) return;
  photos[i].description = value;
  photos[i].tags = tagsNow;
  $("status").textContent = "сохраняю…";
  try {
    await fetch("/api/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file: photos[i].file, description: value, tags: currentTags() })
    });
    loadedDesc = value;
    loadedTags = tagsNow;
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
  const tagsNow = currentTags().join(";");
  if (photos.length && (value !== loadedDesc || tagsNow !== loadedTags)) {
    navigator.sendBeacon("/api/save", new Blob(
      [JSON.stringify({ file: photos[i].file, description: value, tags: currentTags() })],
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
    """Собирает отсортированный список изображений с размерами, описаниями и тегами."""
    folder = Path(folder)
    saved = load_entries(folder / "photos.tsv")
    photos = []
    for path in sorted(folder.iterdir()):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        size = image_size(path)
        width, height = size if size else (0, 0)
        entry = saved.get(path.name, {})
        photos.append({
            "file": path.name,
            "description": entry.get("description", ""),
            "tags": entry.get("tags", ""),
            "width": width,
            "height": height,
            "orientation": orientation(width, height) if size else "unknown",
        })
    return photos


def make_handler(folder, photos, lock, tag_groups):
    tsv_path = Path(folder) / "photos.tsv"
    known = [t for _, tags in tag_groups for t in tags]

    def write_tsv():
        rows = [
            (p["file"], p["description"], p["tags"],
             p["width"], p["height"], p["orientation"])
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
            elif route == "/api/tags":
                body = json.dumps(tag_groups, ensure_ascii=False).encode("utf-8")
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
                        p["tags"] = clean_tags(payload.get("tags") or [], known)
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
    parser.add_argument(
        "--tags",
        default=str(DEFAULT_TAGS_FILE),
        help="файл со списком тегов (по умолчанию tools/tags.json)",
    )
    args = parser.parse_args()

    folder = Path(args.folder).expanduser().resolve()
    if not folder.is_dir():
        raise SystemExit("Папки не существует: {}".format(folder))

    tags_file = Path(args.tags).expanduser()
    try:
        tag_groups = load_tag_groups(tags_file)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            "Не удалось разобрать {}: {}\n"
            "Проверьте запятые и кавычки — это должен быть корректный JSON.".format(
                tags_file, exc
            )
        )
    except ValueError as exc:
        raise SystemExit("Ошибка в {}: {}".format(tags_file, exc))

    if not tags_file.exists():
        print("Файла {} нет — использую встроенный список тегов.".format(tags_file))
    known = [t for _, tags in tag_groups for t in tags]
    print("Тегов в конфиге: {} в {} группах".format(len(known), len(tag_groups)))

    photos = scan_folder(folder)
    print("Фотографий найдено: {}".format(len(photos)))
    if not photos:
        print("В папке нет .jpg/.jpeg/.png — проверьте путь.")

    stale = unknown_tags(photos, known)
    if stale:
        print("\nВнимание: в разметке есть теги, которых нет в конфиге:")
        for tag, count in sorted(stale.items(), key=lambda kv: -kv[1]):
            print("  «{}» — на {} фото".format(tag, count))
        print("Если сохранить такое фото заново, эти теги пропадут.")
        print("Верните их в {} или снимите осознанно.\n".format(tags_file))

    lock = threading.Lock()
    server = HTTPServer(
        ("127.0.0.1", args.port), make_handler(folder, photos, lock, tag_groups)
    )
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
