# Строка-этикетка и регистры — план реализации

> **Для агентов-исполнителей:** ОБЯЗАТЕЛЬНЫЙ САБ-СКИЛЛ: используйте superpowers:subagent-driven-development (рекомендуется) или superpowers:executing-plans для выполнения плана задача за задачей. Шаги отмечены чекбоксами (`- [ ]`) для отслеживания.

**Цель:** заменить сетку карточек `TrustGrid` на две разные подачи — строку-этикетку для списков направлений и связный текст от первого лица для блока «почему у нас» — и развести взрослый и детский регистры токенами поверх общего скелета.

**Архитектура:** два новых компонента (`LabelList`, `FounderNote`) вместо одного `TrustGrid`. Детский регистр — scoped-переопределение CSS custom properties на контейнере страницы, а не отдельная вёрстка: структура строк одна и та же, меняются гарнитура заголовков, акцентный цвет и допустимость «аппликационного» декора. Детская пара шрифтов подключается отдельным CSS-файлом, импортируемым только детской страницей.

**Тех-стек:** Astro, обычный CSS, самохостимые woff2.

## Global Constraints

- Второй цикл из трёх по спеке `docs/superpowers/specs/2026-08-08-visual-redesign-direction.md`. Переход-шторку (цикл 3) не трогаем.
- **Никаких рамок, фоновых плашек и теней у элементов списка.** Иерархия держится типографикой, отступами и разделительной линией — в этом весь смысл замены.
- **Ничего не выдумывать.** Колонка «медиум» заполняется только тем, что есть в исходном тексте студии. Для живописи и рисунка конкретные материалы в источнике не названы — ставится «разные техники и материалы» дословно из источника, а не придуманный список красок.
- Детская пара `Comfortaa` (заголовки) + `Nunito` (текст) грузится **только** на детских страницах, не глобально.
- Подмножества шрифтов только `cyrillic` + `latin`, `font-display: swap`, самохостинг без внешних CDN — как в цикле 1.
- Проверка: `npm run build` и `npm run check`, оба с нулём ошибок.
- `TrustGrid.astro` удаляется в конце цикла, когда не останется потребителей. Оставлять мёртвый компонент нельзя.

---

## Структура файлов

```
site/
├── public/fonts/                      # + comfortaa-*.woff2, nunito-*.woff2
├── src/styles/
│   ├── fonts-kids.css                 # новый — @font-face только детской пары
│   └── tokens.css                      # правка — семантические токены регистра
├── src/components/
│   ├── LabelList.astro                # новый — строка-этикетка
│   ├── FounderNote.astro              # новый — текст от первого лица
│   └── TrustGrid.astro                # удаляется в Task 5
└── src/pages/{o-studii,vzroslym,detyam}.astro   # правка
```

---

### Task 1: Компонент LabelList

**Что и зачем.** Замена карточной сетки. Три колонки: слева «медиум» (материалы и техника мелким лейблом в верхнем регистре с разрядкой — как подпись у картины в музее), в центре название и описание, справа короткая мета. Ни рамок, ни плашек: разделяет строки только тонкая линия, а первая строка отделена линией потолще, чтобы список читался как единый блок, а не как набор равнозначных полос.

Акцентный цвет приходит извне через `--accent` — тот же приём, что уже отработан в `TrustGrid`/`PhotoPlaceholder`: кастомные свойства наследуются по DOM независимо от скоупинга стилей Astro.

**Files:**
- Create: `site/src/components/LabelList.astro`

**Interfaces:**
- Produces: `<LabelList heading="..." items={[{medium, title, text, meta?}, ...]} accent?="..." />`. Поля `medium`, `title`, `text` обязательны, `meta` необязательно. `accent` по умолчанию `var(--forest)`.

- [ ] **Step 1: Написать компонент**

```astro
---
// site/src/components/LabelList.astro
interface LabelItem {
  medium: string;
  title: string;
  text: string;
  meta?: string;
}
interface Props {
  heading: string;
  items: LabelItem[];
  accent?: string;
}
const { heading, items, accent = 'var(--forest)' } = Astro.props;
---
<section class="label-list" style={`--accent: ${accent}`}>
  <h2>{heading}</h2>
  <div class="rows">
    {items.map((item) => (
      <div class="row reveal">
        <p class="medium">{item.medium}</p>
        <div class="body">
          <h3>{item.title}</h3>
          <p>{item.text}</p>
        </div>
        {item.meta && <p class="meta">{item.meta}</p>}
      </div>
    ))}
  </div>
</section>

<style>
  .label-list {
    padding: var(--space-7) var(--space-6);
  }
  .label-list h2 {
    font-size: var(--text-h2);
    margin: 0 0 var(--space-5);
  }
  .row {
    display: grid;
    grid-template-columns: 130px 1fr auto;
    gap: var(--space-5);
    align-items: baseline;
    padding: var(--space-5) 0;
    border-top: 1px solid var(--line);
  }
  /* Более толстая верхняя граница собирает строки в один блок,
     иначе список читается как набор равнозначных полос. */
  .row:first-child {
    border-top: 2px solid var(--accent, var(--forest));
  }
  .medium {
    font-family: var(--font-label);
    font-size: var(--text-label);
    text-transform: uppercase;
    letter-spacing: .06em;
    color: var(--ink-soft);
    line-height: 1.5;
    margin: 0;
  }
  .body h3 {
    font-family: var(--font-display);
    font-weight: 400;
    font-size: var(--text-h3);
    margin: 0 0 var(--space-2);
  }
  .body p {
    font-size: var(--text-small);
    color: var(--ink-soft);
    margin: 0;
    max-width: 52ch;
  }
  .meta {
    font-size: var(--text-small);
    color: var(--accent, var(--forest));
    white-space: nowrap;
    margin: 0;
  }

  @media (max-width: 700px) {
    .row {
      grid-template-columns: 1fr;
      gap: var(--space-2);
    }
    .meta { order: -1; }
  }
</style>
```

- [ ] **Step 2: Проверить сборку и закоммитить**

```bash
cd site && npm run build && npm run check
git add src/components/LabelList.astro
git commit -m "feat: LabelList component — museum-label rows instead of card grid"
```

---

### Task 2: Компонент FounderNote

**Что и зачем.** Блок «почему у нас» перестаёт быть сеткой из четырёх одинаковых карточек и становится связным текстом голосом преподавателя. Приём подтверждён дважды независимо в исследовании (`docs/research/`): и у levisirin.ru, и у kolokol.school доверие держится на личном рассказе с подписью, а не на буллетах с иконками.

Фотография принимается тем же `PhotoPlaceholder`, что и везде, — когда появятся реальные снимки, разметка не изменится.

**Files:**
- Create: `site/src/components/FounderNote.astro`

**Interfaces:**
- Consumes: `PhotoPlaceholder` (`alt`, необязательные `src`/`tint`).
- Produces: `<FounderNote text="..." signature="..." accent?="..." photoAlt?="..." photoTint?="..." />`.

- [ ] **Step 1: Написать компонент**

```astro
---
// site/src/components/FounderNote.astro
import PhotoPlaceholder from './PhotoPlaceholder.astro';

interface Props {
  text: string;
  signature: string;
  accent?: string;
  photoAlt?: string;
  photoTint?: string;
}
const {
  text,
  signature,
  accent = 'var(--adult)',
  photoAlt = 'Преподаватель студии',
  photoTint,
} = Astro.props;
---
<section class="founder reveal" style={`--accent: ${accent}`}>
  <div class="portrait">
    <PhotoPlaceholder alt={photoAlt} tint={photoTint} />
  </div>
  <div class="note">
    <p>{text}</p>
    <p class="sig">{signature}</p>
  </div>
</section>

<style>
  .founder {
    display: grid;
    grid-template-columns: 200px 1fr;
    gap: var(--space-6);
    align-items: start;
    padding: var(--space-7) var(--space-6);
  }
  .note {
    border-left: 3px solid var(--accent, var(--adult));
    padding-left: var(--space-5);
  }
  .note p {
    font-size: var(--text-body);
    margin: 0;
    max-width: 58ch;
  }
  .sig {
    font-family: var(--font-display);
    color: var(--accent, var(--adult));
    margin-top: var(--space-4) !important;
    font-size: var(--text-small);
  }

  @media (max-width: 700px) {
    .founder { grid-template-columns: 1fr; }
    .portrait { max-width: 200px; }
  }
</style>
```

- [ ] **Step 2: Проверить сборку и закоммитить**

```bash
cd site && npm run build && npm run check
git add src/components/FounderNote.astro
git commit -m "feat: FounderNote component — first-person trust block"
```

---

### Task 3: Перевести /vzroslym и /o-studii

**Что и зачем.** Взрослый и нейтральный регистры переходят на новые компоненты первыми — они строгие, без декора, и на них видно, работает ли приём сам по себе.

Колонка «медиум» заполняется **только сведениями из исходного текста студии**: керамика — «глина, обжиг»; каллиграфия — «острое перо»; для живописи и рисунка конкретные материалы в источнике не названы, поэтому ставится «разные техники и материалы» дословно. Придумывать «масло, акварель» нельзя — это выдуманный факт.

**Files:**
- Modify: `site/src/pages/vzroslym.astro`
- Modify: `site/src/pages/o-studii.astro`

**Interfaces:**
- Consumes: `LabelList` (Task 1), `FounderNote` (Task 2).

- [ ] **Step 1: `/vzroslym` — заменить импорт и данные**

Заменить `import TrustGrid from '../components/TrustGrid.astro';` на:
```astro
import LabelList from '../components/LabelList.astro';
import FounderNote from '../components/FounderNote.astro';
```

Заменить массив `courses` на:
```js
const courses = [
  {
    medium: 'Разные техники и материалы',
    title: 'Живопись и рисунок',
    text: 'Для тех, кто только начинает, и для тех, кто продолжает.',
  },
  {
    medium: 'Острое перо',
    title: 'Каллиграфия острым пером',
    text: 'Классическая техника, требует терпения и точности.',
    meta: '12+',
  },
  {
    medium: 'Натура, референсы',
    title: 'Скетчинг',
    text: 'Рисование для отдыха и развития глаза.',
  },
  {
    medium: 'Глина, обжиг',
    title: 'Керамика',
    text: 'Лепка из глины, обжиг готовых работ.',
  },
];
```

Удалить массив `trustPoints` целиком — его заменяет текст от первого лица.

Заменить оба вызова `<TrustGrid ... />` на:
```astro
  <LabelList heading="Чем занимаемся" items={courses} accent="var(--adult)" />

  <FounderNote
    accent="var(--adult)"
    photoAlt="Преподаватель студии за работой"
    text="Я веду студию больше десяти лет — и столько же занимаюсь живописью сама. Беру в группу трёх-пяти человек, не больше: иначе не получается видеть каждого. После занятия снимаю видео с разбором, чтобы вы могли вернуться к нему дома. Занимаемся в моей мастерской — поэтому в цене нет аренды, только материалы и работа."
    signature="— студия «Кисть и Перо», Краснодар"
  />
```

- [ ] **Step 2: `/o-studii` — заменить сетку на текст от первого лица**

Заменить `import TrustGrid from '../components/TrustGrid.astro';` на:
```astro
import FounderNote from '../components/FounderNote.astro';
```

Удалить массив `trustPoints`, заменить `<TrustGrid heading="Почему у нас" points={trustPoints} />` на:
```astro
  <FounderNote
    photoAlt="Преподаватель студии за работой"
    text="Я веду студию больше десяти лет — и столько же занимаюсь живописью сама. Беру в группу трёх-пяти человек, в детских — до четырёх: иначе не получается видеть каждого. После занятия снимаю видео с разбором, чтобы можно было вернуться к нему дома. Занимаемся в моей мастерской — поэтому в цене нет аренды, только материалы и работа."
    signature="— студия «Кисть и Перо», Краснодар"
  />
```

Здесь размер групп указан в одном предложении для обоих контуров — это снимает расхождение, которое финальное ревью `/detyam` уже ловило между страницами.

- [ ] **Step 3: Проверить**

```bash
cd site && npm run build && npm run check
grep -c "trust-card" dist/vzroslym/index.html dist/o-studii/index.html
grep -o "label-list\|founder" dist/vzroslym/index.html | sort -u
```
Ожидается: сборка и проверка типов чистые; `trust-card` больше не встречается на этих двух страницах; присутствуют `label-list` и `founder`.

- [ ] **Step 4: Commit**

```bash
git add site/src/pages/vzroslym.astro site/src/pages/o-studii.astro
git commit -m "feat: label rows and founder note on vzroslym and o-studii"
```

---

### Task 4: Детский регистр

**Что и зачем.** Детская страница получает свою пару шрифтов и свой акцент, но **ту же структуру строк** — по принципу Фроста: общий скелет, переопределяются только токены. Расхождение структуры между регистрами — самая частая причина, по которой такие системы превращаются в два разных сайта.

Шрифты детской пары грузятся отдельным файлом, импортируемым только этой страницей, чтобы взрослые страницы не тянули лишние 90 КБ.

**Files:**
- Create: `site/public/fonts/comfortaa-cyrillic.woff2`, `comfortaa-latin.woff2`, `nunito-cyrillic.woff2`, `nunito-latin.woff2`
- Create: `site/src/styles/fonts-kids.css`
- Modify: `site/src/pages/detyam.astro`

- [ ] **Step 1: Скачать детскую пару**

```bash
cd site
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
curl -s -A "$UA" "https://fonts.googleapis.com/css2?family=Comfortaa:wght@400;700&family=Nunito:wght@400;700&display=swap" -o /tmp/gfk.css
python3 - <<'PY'
import re, urllib.request
from pathlib import Path
out = Path("public/fonts")
css = Path("/tmp/gfk.css").read_text(encoding="utf-8")
targets = {
    ("Comfortaa", "cyrillic"): "comfortaa-cyrillic.woff2",
    ("Comfortaa", "latin"): "comfortaa-latin.woff2",
    ("Nunito", "cyrillic"): "nunito-cyrillic.woff2",
    ("Nunito", "latin"): "nunito-latin.woff2",
}
seen = set()
for subset, body in re.findall(r'/\* (\S+) \*/\s*@font-face\s*\{([^}]+)\}', css):
    fam = re.search(r"font-family:\s*'([^']+)'", body).group(1)
    key = (fam, subset)
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

- [ ] **Step 2: Написать fonts-kids.css**

Тот же формат, что `fonts.css` из цикла 1: по два `@font-face` на семейство (кириллица и латиница), `font-weight: 400 700`, `font-display: swap`, те же `unicode-range` — кириллический `U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116`, латинский `U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD`. Семейства — `Comfortaa` и `Nunito`, пути `/fonts/comfortaa-*.woff2` и `/fonts/nunito-*.woff2`.

- [ ] **Step 3: Переписать detyam.astro**

Импорты: добавить `import '../styles/fonts-kids.css';`, `import LabelList from '../components/LabelList.astro';`, `import FounderNote from '../components/FounderNote.astro';`, убрать импорт `TrustGrid`.

Заменить `courses` на структуру с `medium` (только сведения из источника):
```js
const courses = [
  {
    medium: 'Глина, обжиг',
    title: 'Керамика',
    text: 'Лепка из глины, обжиг готовых работ.',
    meta: '8+',
  },
  {
    medium: 'Пластилин, глина',
    title: 'Лепка и пластилинография',
    text: 'Особенно полезны детям с задержкой развития речи.',
  },
  {
    medium: 'Брашпен',
    title: 'Каллиграфия брашпеном',
    text: 'Ручка-кисть — понятный формат для первого знакомства с каллиграфией.',
    meta: '8+',
  },
  {
    medium: 'Бумага, маркеры',
    title: 'Скетчинг и леттеринг',
    text: 'Для подростков — рисование и надписи в популярном сегодня стиле.',
  },
];
```

Удалить `trustPoints`. Обернуть содержимое в контейнер регистра и заменить вызовы:
```astro
<BaseLayout title="Детям">
  <div class="kids">
    <section class="intro reveal">…без изменений…</section>

    <LabelList heading="Чем занимаемся" items={courses} accent="var(--kid)" />

    <FounderNote
      accent="var(--kid)"
      photoAlt="Ребёнок на занятии в студии"
      photoTint="var(--kid)"
      text="Беру в детскую группу до четырёх человек — так видно каждого ребёнка и можно идти в его темпе. После занятия снимаю видео и фото, чтобы вы видели, как продвигается ваш художник."
      signature="— студия «Кисть и Перо», Краснодар"
    />

    <section class="cta">…без изменений…</section>
  </div>
</BaseLayout>
```

Добавить в `<style>` переопределение токенов регистра:
```css
  /* Детский регистр: тот же скелет, другие токены.
     Переопределение scoped на контейнере, а не отдельная вёрстка. */
  .kids {
    --font-display: 'Comfortaa', 'Bitter', Georgia, serif;
    --font-body: 'Nunito', 'Golos Text', ui-sans-serif, sans-serif;
    --font-label: 'Nunito', 'Golos Text', ui-sans-serif, sans-serif;
  }
```

- [ ] **Step 4: Проверить**

```bash
cd site && npm run build && npm run check
echo "--- детские шрифты только на detyam ---"
grep -c "Comfortaa" dist/detyam/index.html dist/_astro/*.css 2>/dev/null
grep -c "Comfortaa" dist/vzroslym/index.html || echo "на vzroslym нет — верно"
```
Ожидается: сборка чистая; `Comfortaa` присутствует в CSS детской страницы. Если Astro сложил весь CSS в один общий файл, зафиксировать это как известное ограничение — тогда экономия достигается тем, что браузер всё равно скачивает `.woff2` только при фактическом использовании гарнитуры, благодаря `unicode-range` и ленивой загрузке шрифтов.

- [ ] **Step 5: Commit**

```bash
git add site/public/fonts site/src/styles/fonts-kids.css site/src/pages/detyam.astro
git commit -m "feat: kid register — Comfortaa/Nunito and label rows on detyam"
```

---

### Task 5: Удалить TrustGrid и зафиксировать проверку

**Что и зачем.** После Task 3-4 у `TrustGrid` не остаётся потребителей. Мёртвый компонент оставлять нельзя — он будет сбивать с толку при следующей правке.

**Files:**
- Delete: `site/src/components/TrustGrid.astro`
- Modify: `site/docs/manual-verification-checklist.md`

- [ ] **Step 1: Убедиться, что потребителей нет**

```bash
cd site && grep -rn "TrustGrid" src/ || echo "потребителей нет — можно удалять"
```
Ожидается: ни одного вхождения. Если есть — сначала перевести оставшуюся страницу, удалять нельзя.

- [ ] **Step 2: Удалить и пересобрать**

```bash
rm src/components/TrustGrid.astro
npm run build && npm run check
```

- [ ] **Step 3: Дописать секцию в чек-лист**

Секция «Результаты прохода: строка-этикетка и регистры (дата)» по формату предыдущих: что подтверждено статически (сборка, проверка типов, отсутствие `trust-card` в выводе, наличие `label-list`, детские шрифты), и что требует живого глаза — читаются ли строки как единый список, не разъезжается ли трёхколоночная сетка на средних ширинах, работает ли схлопывание на 700px, и как смотрится Comfortaa рядом с Bitter в одном макете.

- [ ] **Step 4: Commit и push**

```bash
git add -A site/
git commit -m "refactor: drop TrustGrid, verification pass for label list cycle"
git push origin main
```

---

## Что дальше

Цикл 3 — переход-шторка на cross-document View Transitions между главной и страницами направлений.
