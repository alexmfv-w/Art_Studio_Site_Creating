# Детская доска и шрифт на главной — план реализации

> **Для агентов-исполнителей:** ОБЯЗАТЕЛЬНЫЙ САБ-СКИЛЛ: используйте superpowers:subagent-driven-development (рекомендуется) или superpowers:executing-plans для выполнения плана задача за задачей. Шаги отмечены чекбоксами (`- [ ]`) для отслеживания.

**Цель:** довести детский регистр до вида, который заказчик одобрил ещё во втором раунде макетов — приколотые карточки с лёгким наклоном и местом под фотографию — и починить недосмотр: на главной детская половина набрана взрослыми шрифтами.

**Архитектура:** новый компонент `PinBoard.astro` для детского списка направлений; `LabelList` остаётся для взрослого и нейтрального регистров без изменений. Токены детского регистра выносятся из страницы в переиспользуемый класс `.kids`, чтобы его можно было навесить и на половину блока на главной.

## Global Constraints

- Наклон карточек — **детерминированный, по индексу**, а не случайный: иначе каждая сборка давала бы другую вёрстку, и диффы стали бы нечитаемыми.
- Наклон мелкий (в пределах ±1.6°) — заказчик просил «чуть-чуть хаотично», а не коллаж.
- Каждая карточка принимает необязательное фото через уже существующий `PhotoPlaceholder` — когда появятся реальные снимки, разметка не меняется.
- «Аппликационный» язык (наклон, скотч, тень) — **только детский регистр**. Взрослый и нейтральный остаются строгими: это зафиксировано в спеке и подтверждено исследованием.
- Сдвиг карточки при наведении — под `@media (prefers-reduced-motion: no-preference)`. Сам наклон — статический `transform`, не анимация, его прятать не нужно.
- Текст на наклонённой карточке остаётся выровненным по левому краю и не наклоняется отдельно — наклоняется карточка целиком.
- Проверка: `npm run build` и `npm run check`, оба с нулём ошибок.

---

### Task 1: Вынести токены детского регистра в общий класс

**Что и зачем.** Сейчас переопределение шрифтов живёт в `<style>` страницы `detyam.astro` и потому недоступно на главной. Класс `.kids` переезжает в `global.css`, а объявления `@font-face` детской пары — туда, где их увидит и главная. Это чинит расхождение, которое заказчик заметил: на главной детская половина набрана Bitter/Golos Text вместо Comfortaa/Nunito.

Детская пара всё ещё не должна грузиться на взрослых страницах, но главная содержит детскую половину — значит, ей эти шрифты нужны. Импорт добавляется в `AudienceSplit.astro`: компонент используется только на главной, поэтому вес попадёт ровно туда, где он нужен.

**Files:**
- Modify: `site/src/styles/global.css`
- Modify: `site/src/components/AudienceSplit.astro`
- Modify: `site/src/pages/detyam.astro`

- [ ] **Step 1: Перенести класс в global.css**

Добавить в конец `site/src/styles/global.css`:
```css
/* Детский регистр: тот же скелет, другие гарнитуры.
   Класс навешивается либо на всю страницу (/detyam), либо на её часть
   (детская половина блока «Взрослым/Детям» на главной). */
.kids {
  --font-display: 'Comfortaa', 'Bitter', Georgia, serif;
  --font-body: 'Nunito', 'Golos Text', ui-sans-serif, sans-serif;
  --font-label: 'Nunito', 'Golos Text', ui-sans-serif, sans-serif;
}
```

- [ ] **Step 2: Убрать дубль из detyam.astro**

В `site/src/pages/detyam.astro` удалить из `<style>` блок `.kids { … }` целиком (вместе с комментарием над ним) — класс теперь глобальный. Обёртка `<div class="kids">` в разметке остаётся.

- [ ] **Step 3: Включить детский регистр на главной**

В `site/src/components/AudienceSplit.astro` добавить импорт шрифтов первой строкой после комментария:
```astro
import '../styles/fonts-kids.css';
```
и навесить класс на детскую панель — заменить:
```astro
    <div class:list={["pane", pane.key]}>
```
на:
```astro
    <div class:list={["pane", pane.key, pane.key === 'kid' && 'kids']}>
```

- [ ] **Step 4: Проверить**

```bash
cd site && npm run build && npm run check
echo "--- Comfortaa на главной ---"; grep -c "Comfortaa" dist/index.html
echo "--- класс kids на детской панели ---"; grep -o 'class="pane kid kids"' dist/index.html
echo "--- на взрослых страницах детских шрифтов нет ---"; grep -c "Comfortaa" dist/vzroslym/index.html
```
Ожидается: на главной `Comfortaa` присутствует и класс навешен; на `/vzroslym` — ноль.

- [ ] **Step 5: Commit**

```bash
git add site/src/styles/global.css site/src/components/AudienceSplit.astro site/src/pages/detyam.astro
git commit -m "fix: kid typography on homepage, hoist .kids register class to global"
```

---

### Task 2: Компонент PinBoard

**Что и зачем.** Детский список направлений возвращается к виду, одобренному во втором раунде: карточки с лёгким наклоном, полоской скотча сверху и мягкой тенью — как записки, приколотые к доске. Под каждую карточку добавляется место под фотографию: заказчик отметил, что это хороший вариант, и это же прямо отвечает главному выводу исследования — материальность несут снимки, а не CSS.

Наклон берётся из массива по индексу, а не случайным числом: сборка должна быть воспроизводимой.

**Files:**
- Create: `site/src/components/PinBoard.astro`

**Interfaces:**
- Consumes: `PhotoPlaceholder` (`alt`, необязательные `src`/`tint`).
- Produces: `<PinBoard heading="..." items={[{title, text, meta?, photoAlt?, photoSrc?}, ...]} accent?="..." />`.

- [ ] **Step 1: Написать компонент**

```astro
---
// site/src/components/PinBoard.astro
import PhotoPlaceholder from './PhotoPlaceholder.astro';

interface PinItem {
  title: string;
  text: string;
  meta?: string;
  photoAlt?: string;
  photoSrc?: string;
}
interface Props {
  heading: string;
  items: PinItem[];
  accent?: string;
}
const { heading, items, accent = 'var(--kid)' } = Astro.props;

// Наклон по индексу, а не случайный: сборка должна быть воспроизводимой,
// иначе каждый билд давал бы другую вёрстку и нечитаемые диффы.
const TILTS = ['-1.4deg', '0.9deg', '-0.6deg', '1.5deg', '-1.1deg', '0.5deg'];
---
<section class="pinboard" style={`--accent: ${accent}`}>
  <h2>{heading}</h2>
  <div class="cards">
    {items.map((item, i) => (
      <article class="pin reveal" style={`--tilt: ${TILTS[i % TILTS.length]}`}>
        <span class="tape" aria-hidden="true"></span>
        {item.meta && <span class="age">{item.meta}</span>}
        <div class="photo">
          <PhotoPlaceholder alt={item.photoAlt || item.title} src={item.photoSrc} tint="var(--kid)" />
        </div>
        <h3>{item.title}</h3>
        <p>{item.text}</p>
      </article>
    ))}
  </div>
</section>

<style>
  .pinboard {
    padding: var(--space-7) var(--space-6);
  }
  .pinboard h2 {
    font-size: var(--text-h2);
    margin: 0 0 var(--space-6);
  }
  .cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
    gap: var(--space-6) var(--space-5);
  }
  .pin {
    position: relative;
    background: var(--card);
    padding: var(--space-5) var(--space-4) var(--space-4);
    box-shadow: 0 3px 12px rgba(74, 59, 20, .16);
    transform: rotate(var(--tilt));
    transition: box-shadow 160ms ease-out;
  }
  /* Полоска скотча: чисто декоративная, поэтому скрыта от скринридера. */
  .pin .tape {
    position: absolute;
    top: -9px;
    left: 50%;
    width: 46px;
    height: 17px;
    transform: translateX(-50%) rotate(-4deg);
    background: color-mix(in srgb, var(--accent) 55%, transparent);
  }
  .pin .age {
    position: absolute;
    top: var(--space-3);
    right: var(--space-3);
    font-family: var(--font-label);
    font-size: var(--text-label);
    padding: 2px var(--space-2);
    border-radius: var(--radius-pill);
    background: var(--accent);
    color: var(--ink);
    font-weight: 700;
  }
  .pin .photo {
    margin-bottom: var(--space-3);
  }
  .pin h3 {
    font-family: var(--font-display);
    font-size: var(--text-h4);
    font-weight: 700;
    margin: 0 0 var(--space-2);
  }
  .pin p {
    font-size: var(--text-small);
    color: var(--ink-soft);
    margin: 0;
  }
  .pin:hover,
  .pin:focus-within {
    box-shadow: 0 6px 18px rgba(74, 59, 20, .22);
  }
  @media (prefers-reduced-motion: no-preference) {
    .pin {
      transition: box-shadow 160ms ease-out, transform 160ms ease-out;
    }
    /* Наведение выпрямляет карточку — как будто её поправили на доске. */
    .pin:hover,
    .pin:focus-within {
      transform: rotate(0deg) translateY(-2px);
    }
  }
</style>
```

- [ ] **Step 2: Проверить сборку и закоммитить**

```bash
cd site && npm run build && npm run check
git add src/components/PinBoard.astro
git commit -m "feat: PinBoard component — pinned cards with photo slot for kid register"
```

---

### Task 3: Поставить доску на /detyam

**Что и зачем.** Список «Чем занимаемся» на детской странице переходит с `LabelList` на `PinBoard`. `FounderNote` внизу остаётся без изменений — личный текст одинаково уместен в обоих регистрах.

Поля `medium` у детских направлений больше не нужны: на карточке роль «что это за материал» берёт на себя фотография, а дублировать её текстом — лишний шум.

**Files:**
- Modify: `site/src/pages/detyam.astro`

- [ ] **Step 1: Заменить компонент и данные**

Заменить импорт `LabelList` на `PinBoard`:
```astro
import PinBoard from '../components/PinBoard.astro';
```

Заменить массив `courses` на:
```js
const courses = [
  {
    title: 'Керамика',
    text: 'Лепка из глины, обжиг готовых работ.',
    meta: '8+',
    photoAlt: 'Детская работа из глины',
  },
  {
    title: 'Лепка и пластилинография',
    text: 'Особенно полезны детям с задержкой развития речи.',
    photoAlt: 'Ребёнок лепит из пластилина',
  },
  {
    title: 'Каллиграфия брашпеном',
    text: 'Ручка-кисть — понятный формат для первого знакомства с каллиграфией.',
    meta: '8+',
    photoAlt: 'Надпись, написанная брашпеном',
  },
  {
    title: 'Скетчинг и леттеринг',
    text: 'Для подростков — рисование и надписи в популярном сегодня стиле.',
    photoAlt: 'Скетч в блокноте',
  },
];
```

Заменить вызов:
```astro
  <LabelList heading="Чем занимаемся" items={courses} accent="var(--kid)" />
```
на:
```astro
  <PinBoard heading="Чем занимаемся" items={courses} accent="var(--kid)" />
```

- [ ] **Step 2: Проверить**

```bash
cd site && npm run build && npm run check
echo "--- доска на detyam ---"; grep -c "pinboard" dist/detyam/index.html
echo "--- четыре карточки ---"; grep -o 'class="pin reveal"' dist/detyam/index.html | wc -l
echo "--- наклоны детерминированы ---"; grep -o '\-\-tilt: [-0-9.]*deg' dist/detyam/index.html | tr '\n' ' '
echo "--- LabelList на взрослых остался ---"; grep -c "label-list" dist/vzroslym/index.html
```
Ожидается: доска и четыре карточки на `/detyam`; наклоны из фиксированного набора; `label-list` на `/vzroslym` по-прежнему есть.

- [ ] **Step 3: Пересобрать дважды и убедиться в воспроизводимости**

```bash
cd site && npm run build && cp dist/detyam/index.html /tmp/b1.html && npm run build && diff -q /tmp/b1.html dist/detyam/index.html && echo "сборка воспроизводима"
```
Ожидается: файлы совпадают — наклон не плавает от сборки к сборке.

- [ ] **Step 4: Commit**

```bash
git add site/src/pages/detyam.astro
git commit -m "feat: pinned board for kid course list"
```

---

### Task 4: Зафиксировать проверку

**Files:**
- Modify: `site/docs/manual-verification-checklist.md`

- [ ] **Step 1: Дописать секцию** «Результаты прохода: детская доска (дата)»: что подтверждено статически (сборка, проверка типов, наличие доски и карточек, детерминированность наклона, детский шрифт на главной, отсутствие детских шрифтов на взрослых страницах), и что требует глаза — читается ли «чуть-чуть хаотично» как задумано или как небрежность; не мешает ли наклон читать текст; как выглядит выпрямление карточки при наведении; не рвётся ли сетка при трёх карточках в ряду.

- [ ] **Step 2: Commit и push**

```bash
git add site/docs/manual-verification-checklist.md
git commit -m "docs: verification pass for kid pinboard"
git push origin main
```

---

## Что дальше

Цикл 3 — переход-шторка на cross-document View Transitions.
