# Типографика — план реализации

> **Для агентов-исполнителей:** ОБЯЗАТЕЛЬНЫЙ САБ-СКИЛЛ: используйте superpowers:subagent-driven-development (рекомендуется) или superpowers:executing-plans для выполнения плана задача за задачей. Шаги отмечены чекбоксами (`- [ ]`) для отслеживания.

**Цель:** заменить системные шрифтовые стеки на осознанно подобранную пару Bitter + Golos Text, самохостить их подмножествами, и выставить интерлиньяж, выбранный заказчиком на реальном русском тексте.

**Архитектура:** файлы `.woff2` кладутся в `site/public/fonts/` (Astro отдаёт содержимое `public/` как есть по корневым путям). Объявления `@font-face` — в отдельном `site/src/styles/fonts.css`, подключаемом в `BaseLayout` рядом с `tokens.css`. Значения токенов `--font-display`/`--font-body`/`--font-label` меняются в `tokens.css` — все пять мест использования в коде идут через них, поэтому больше ничего править не нужно.

**Тех-стек:** Astro, обычный CSS, woff2.

## Global Constraints

- Первый цикл из трёх (типографика; строка-этикетка и регистры; переход-шторка) по спеке `docs/superpowers/specs/2026-08-08-visual-redesign-direction.md`. **Строку-этикетку и детские шрифты в этом цикле не трогаем** — `TrustGrid` остаётся карточным, `Comfortaa`/`Nunito` не подключаются.
- Гарнитуры: `Bitter` — заголовки, `Golos Text` — текст и лейблы. Обе с настоящей кириллицей (проверено).
- Подмножества только `cyrillic` + `latin`. Другие подмножества (`cyrillic-ext`, `vietnamese`, `latin-ext`, `greek`) не подключаются — сайт русскоязычный.
- Начертания: Bitter 400 и 700, Golos Text 400, 600, 700. Больше не заводить — лишний вес.
- `font-display: swap` на всех объявлениях: текст должен читаться, пока грузится шрифт.
- Интерлиньяж основного текста — **1.7** (выбор заказчика из сравнения 1.5/1.7 на реальном русском абзаце).
- Никаких ссылок на внешние CDN шрифтов — только самохостинг.
- Проверка: `npm run build` и `npm run check`, оба с нулём ошибок.

---

## Структура файлов

```
site/
├── public/fonts/           # новые .woff2 (отдаются по /fonts/...)
│   ├── bitter-cyrillic.woff2
│   ├── bitter-latin.woff2
│   ├── golos-text-cyrillic.woff2
│   └── golos-text-latin.woff2
├── src/styles/
│   ├── fonts.css           # новый — только @font-face
│   ├── tokens.css          # правка — значения трёх шрифтовых токенов
│   └── global.css          # правка — line-height
└── src/layouts/BaseLayout.astro  # правка — импорт fonts.css
```

---

### Task 1: Положить шрифты и объявить @font-face

**Что и зачем.** Google Fonts отдаёт шрифт нарезанным по подмножествам (`cyrillic`, `latin`, `latin-ext` и т.д.), каждое своим файлом с собственным `unicode-range`. Берём только два нужных подмножества — так браузер скачает кириллический файл для русского текста и не тронет остальные. `unicode-range` обязателен: без него браузер не поймёт, какой файл под какие символы, и скачает лишнее.

Bitter и Golos Text — вариативные шрифты, у них одно физическое подмножество обслуживает диапазон начертаний, поэтому файлов четыре, а не десять.

**Files:**
- Create: `site/public/fonts/bitter-cyrillic.woff2`
- Create: `site/public/fonts/bitter-latin.woff2`
- Create: `site/public/fonts/golos-text-cyrillic.woff2`
- Create: `site/public/fonts/golos-text-latin.woff2`
- Create: `site/src/styles/fonts.css`
- Modify: `site/src/layouts/BaseLayout.astro`

**Interfaces:**
- Produces: семейства `Bitter` (вес 400–700) и `Golos Text` (вес 400–700), доступные во всём CSS сайта.

- [ ] **Step 1: Скачать подмножества**

```bash
cd /Users/alex/work/art_site_creating/site
mkdir -p public/fonts
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
curl -s -A "$UA" "https://fonts.googleapis.com/css2?family=Bitter:wght@400;700&family=Golos+Text:wght@400;600;700&display=swap" -o /tmp/gf.css

python3 - <<'PY'
import re, urllib.request
from pathlib import Path

out = Path("public/fonts")
css = Path("/tmp/gf.css").read_text(encoding="utf-8")
blocks = re.findall(r'/\* (\S+) \*/\s*@font-face\s*\{([^}]+)\}', css)

targets = {
    ("Bitter", "cyrillic"): "bitter-cyrillic.woff2",
    ("Bitter", "latin"): "bitter-latin.woff2",
    ("Golos Text", "cyrillic"): "golos-text-cyrillic.woff2",
    ("Golos Text", "latin"): "golos-text-latin.woff2",
}
seen = set()
for subset, body in blocks:
    family = re.search(r"font-family:\s*'([^']+)'", body).group(1)
    key = (family, subset)
    if key not in targets or key in seen:
        continue
    seen.add(key)
    url = re.search(r"url\(([^)]+)\)", body).group(1)
    data = urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    ).read()
    (out / targets[key]).write_bytes(data)
    print("{:<26} {:>7.1f} KB".format(targets[key], len(data) / 1024))

missing = set(targets) - seen
if missing:
    raise SystemExit("не скачалось: {}".format(missing))
PY
```
Ожидается: четыре файла, суммарно порядка 110 КБ.

- [ ] **Step 2: Написать fonts.css**

```css
/* site/src/styles/fonts.css
   Самохостинг: подмножества cyrillic + latin, без обращений к внешним CDN.
   unicode-range обязателен — по нему браузер решает, какой файл вообще качать. */

@font-face {
  font-family: 'Bitter';
  font-style: normal;
  font-weight: 400 700;
  font-display: swap;
  src: url('/fonts/bitter-cyrillic.woff2') format('woff2');
  unicode-range: U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116;
}
@font-face {
  font-family: 'Bitter';
  font-style: normal;
  font-weight: 400 700;
  font-display: swap;
  src: url('/fonts/bitter-latin.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}

@font-face {
  font-family: 'Golos Text';
  font-style: normal;
  font-weight: 400 700;
  font-display: swap;
  src: url('/fonts/golos-text-cyrillic.woff2') format('woff2');
  unicode-range: U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116;
}
@font-face {
  font-family: 'Golos Text';
  font-style: normal;
  font-weight: 400 700;
  font-display: swap;
  src: url('/fonts/golos-text-latin.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
```

- [ ] **Step 3: Подключить в BaseLayout**

В `site/src/layouts/BaseLayout.astro` заменить блок импортов стилей:
```astro
import '../styles/tokens.css';
import '../styles/global.css';
import '../styles/animations.css';
```
на:
```astro
import '../styles/fonts.css';
import '../styles/tokens.css';
import '../styles/global.css';
import '../styles/animations.css';
```
(`fonts.css` идёт первым: объявления `@font-face` должны быть известны до того, как токены на них сошлются.)

- [ ] **Step 4: Проверить сборку**

```bash
cd site && npm run build && npm run check
```
Ожидается: 7 страниц, 0 ошибок сборки, 0 ошибок проверки типов. Файлы шрифтов копируются в `dist/fonts/` — проверить:
```bash
ls dist/fonts/
```

- [ ] **Step 5: Commit**

```bash
git add site/public/fonts site/src/styles/fonts.css site/src/layouts/BaseLayout.astro
git commit -m "feat: self-host Bitter and Golos Text (cyrillic + latin subsets)"
```

---

### Task 2: Переключить токены и интерлиньяж

**Что и зачем.** Здесь смена гарнитур становится видимой. Все пять мест в коде, где шрифт задаётся, ходят через токены `--font-display`/`--font-body`/`--font-label`, поэтому правка одного файла меняет весь сайт. Интерлиньяж 1.7 выбран заказчиком на реальном русском абзаце: у кириллицы меньше выносных элементов, чем у латиницы, и «англоязычные» 1.5 читались плотнее, чем нужно.

`--font-label` переводится на Golos Text, а не на моноширинный: пятая гарнитура добавила бы вес ради лейблов, а служебный характер даёт сам приём — верхний регистр, разрядка, мелкий кегль.

**Files:**
- Modify: `site/src/styles/tokens.css`
- Modify: `site/src/styles/global.css`

**Interfaces:**
- Consumes: семейства `Bitter` и `Golos Text` из Task 1.

- [ ] **Step 1: Заменить значения токенов**

В `site/src/styles/tokens.css` заменить три строки:
```css
  --font-display: Charter, "Bitstream Charter", "Sitka Text", Cambria, serif;
  --font-body: ui-sans-serif, -apple-system, "Segoe UI", Roboto, sans-serif;
  --font-label: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
```
на:
```css
  --font-display: 'Bitter', Charter, Cambria, Georgia, serif;
  --font-body: 'Golos Text', ui-sans-serif, -apple-system, "Segoe UI", Roboto, sans-serif;
  --font-label: 'Golos Text', ui-sans-serif, -apple-system, "Segoe UI", Roboto, sans-serif;
```
Системные стеки остаются запасными — если шрифт не догрузился, текст всё равно наберётся близкой по характеру гарнитурой, а не дефолтной.

- [ ] **Step 2: Поднять интерлиньяж**

В `site/src/styles/global.css` в правиле `body` заменить `line-height: 1.5;` на:
```css
  line-height: 1.7;
```

- [ ] **Step 3: Проверить сборку и вывод**

```bash
cd site && npm run build && npm run check
grep -o "font-family:[^;]*Bitter[^;]*" dist/index.html | head -2
grep -o "line-height:1.7" dist/index.html | head -1
```
Ожидается: сборка и проверка типов без ошибок; в собранном CSS фигурирует `Bitter` и `line-height:1.7`.

- [ ] **Step 4: Commit**

```bash
git add site/src/styles/tokens.css site/src/styles/global.css
git commit -m "feat: switch to Bitter/Golos Text tokens, line-height 1.7"
```

---

### Task 3: Проверка и фиксация

**Что и зачем.** Смена гарнитуры меняет метрики: у Bitter другая высота строчных и другая ширина знака, чем у Charter, поэтому заголовки, заданные в пикселях, могут начать смотреться крупнее или мельче прежнего. Проверить это статически нельзя — нужен глаз, поэтому фиксируем состояние честно, как и в предыдущих циклах.

**Files:**
- Modify: `site/docs/manual-verification-checklist.md`

- [ ] **Step 1: Разобрать собранный вывод**

```bash
cd site && npm run build
echo "=== шрифты в dist ==="; ls dist/fonts/
echo "=== вес шрифтов ==="; du -ch dist/fonts/*.woff2 | tail -1
echo "=== нет ли обращений к внешним CDN ==="; grep -c "fonts.googleapis\|fonts.gstatic" dist/*.html dist/*/*.html || echo "внешних ссылок нет"
```
Ожидается: четыре файла шрифтов, суммарный вес порядка 110 КБ, ноль обращений к внешним CDN.

- [ ] **Step 2: Дописать секцию в чек-лист**

Добавить секцию «Результаты прохода: типографика (дата)» по формату предыдущих: что подтверждено статически (сборка, проверка типов, наличие файлов, отсутствие внешних ссылок), и что требует живого глаза — а именно: не стали ли заголовки визуально слишком крупными или мелкими после смены гарнитуры, и как выглядит интерлиньяж 1.7 на длинных абзацах в реальном окне. Отметить, что `claude-in-chrome` по-прежнему недоступен, если это так.

- [ ] **Step 3: Commit и push**

```bash
git add site/docs/manual-verification-checklist.md
git commit -m "docs: verification pass for typography cycle"
git push origin main
```

---

## Что дальше

Цикл 2 — строка-этикетка вместо карточной сетки и токены детского регистра (там же подключаются Comfortaa и Nunito, только на детских страницах). Цикл 3 — переход-шторка на View Transitions.
