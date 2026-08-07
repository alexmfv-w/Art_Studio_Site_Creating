# Страница «О студии» — план реализации

> **Для агентов-исполнителей:** ОБЯЗАТЕЛЬНЫЙ САБ-СКИЛЛ: используйте superpowers:subagent-driven-development (рекомендуется) или superpowers:executing-plans для выполнения плана задача за задачей. Шаги отмечены чекбоксами (`- [ ]`) для отслеживания.

**Цель:** наполнить маршрут `/o-studii` реальным контентом по одобренной спеке (`docs/superpowers/specs/2026-08-07-o-studii-page-design.md`) — вступление, сетка карточек доверия, секция формата занятий, CTA, лёгкие scroll-reveal и hover-анимации.

**Архитектура:** два новых переиспользуемых `.astro`-компонента (`TrustGrid`, `PhotoPlaceholder`) + один общий CSS-файл с анимацией появления при скролле, подключаемый в `BaseLayout` рядом с `tokens.css`/`global.css`. Страница `o-studii.astro` собирает их вместе. Никакого нового JS — то же правило, что и во всём каркасе (единственный существующий `<script>` в проекте — фича-детект попап-полифиллов в `BaseLayout.astro`, он не трогается).

**Тех-стек:** Astro (`.astro`-компоненты), обычный CSS с custom properties из `tokens.css`, нативные CSS scroll-driven animations (`animation-timeline: view()`) за `@supports`-фича-детектом.

## Global Constraints

- Никакого Tailwind/UI-фреймворков — только `.astro` + обычный CSS (проектное правило, не пересматривается).
- Все цвета/шрифты/отступы — из уже существующих токенов `site/src/styles/tokens.css`. Новых токенов эта работа не добавляет.
- Анимации — только CSS, обёрнуты в `@media (prefers-reduced-motion: no-preference)` и (для scroll-reveal) `@supports ((animation-timeline: view()) and (animation-range: entry))`. Без `scroll-timeline-polyfill` — эффект декоративный, для браузеров без поддержки (сейчас Firefox) контент показывается сразу без анимации.
- Автотеста в привычном pytest/vitest-смысле в проекте нет (нет тестового раннера в `package.json` — только `astro`, `@astrojs/check`). Как и в плане каркаса сайта, эквивалент теста — `npm run build` (ловит синтаксические ошибки/сломанные импорты) на каждом шаге, плюс финальная браузерная проверка.
- Факты, которых нет в источнике (имя художницы, точный год основания, адрес) — не придумывать. Текст ниже уже составлен без них (безличное «мы»), это решение зафиксировано в спеке, тут просто переносится в код.
- Не выводить секцию отзывов — контента для неё пока нет (см. спеку, раздел «Отзывы»).

---

## Структура файлов

```
site/
├── src/
│   ├── styles/
│   │   └── animations.css        # новый — .reveal keyframes + класс
│   ├── layouts/
│   │   └── BaseLayout.astro      # правка — подключить animations.css
│   ├── components/
│   │   ├── TrustGrid.astro       # новый
│   │   └── PhotoPlaceholder.astro # новый
│   └── pages/
│       └── o-studii.astro        # правка — вся страница целиком
```

---

### Task 1: Общий стиль scroll-reveal анимации

**Что и зачем.** Класс `.reveal` будет навешен на несколько независимых блоков (вступление, каждая карточка `TrustGrid`, секция формата). Если держать `@keyframes`/`@supports`-блок в каждом компоненте отдельно (Astro `<style>` скопирован в каждый файл), это дублирование на ровном месте — при следующей странице придётся копировать снова. Один общий файл, подключённый в `BaseLayout` рядом с `tokens.css`/`global.css`, даёт класс `.reveal`, который переиспользуется где угодно на сайте.

**Files:**
- Create: `site/src/styles/animations.css`
- Modify: `site/src/layouts/BaseLayout.astro`

**Interfaces:**
- Produces: CSS-класс `.reveal` — вешается на любой блок-уровневый элемент, глобально доступен на всех страницах после этой задачи.

- [ ] **Step 1: Написать animations.css**

```css
/* site/src/styles/animations.css */
@media (prefers-reduced-motion: no-preference) {
  @supports ((animation-timeline: view()) and (animation-range: entry)) {
    @keyframes reveal {
      from {
        opacity: 0;
        translate: 0 16px;
      }
    }

    .reveal {
      animation: reveal auto linear;
      animation-timeline: view();
      animation-range: entry 0% entry 40%;
    }
  }
}
```

- [ ] **Step 2: Подключить в BaseLayout**

В `site/src/layouts/BaseLayout.astro` заменить блок импортов:

```astro
import SiteHeader from '../components/SiteHeader.astro';
import SiteFooter from '../components/SiteFooter.astro';
import '../styles/tokens.css';
import '../styles/global.css';
```

на:

```astro
import SiteHeader from '../components/SiteHeader.astro';
import SiteFooter from '../components/SiteFooter.astro';
import '../styles/tokens.css';
import '../styles/global.css';
import '../styles/animations.css';
```

- [ ] **Step 3: Проверить сборку**

```bash
cd site && npm run build
```
Ожидается: сборка проходит без ошибок (класс `.reveal` пока нигде не используется — это нормально, синтаксис CSS уже проверяем).

- [ ] **Step 4: Commit**

```bash
git add site/src/styles/animations.css site/src/layouts/BaseLayout.astro
git commit -m "feat: shared scroll-reveal animation class"
```

---

### Task 2: Компонент PhotoPlaceholder

**Что и зачем.** Реальных фото пока нет (художница пришлёт позже), но вёрстка не должна ждать. Компонент без `src` рисует мягкий брендовый градиентный блок нужных пропорций вместо фото; когда фото появятся — передаём `src`, разметка страницы не меняется.

**Files:**
- Create: `site/src/components/PhotoPlaceholder.astro`

**Interfaces:**
- Produces: компонент `<PhotoPlaceholder alt="..." src?="..." />`. Пропы: `alt: string` (обязательный), `src?: string` (необязательный). Без `src` — плейсхолдер-блок, с `src` — обычный `<img>`. В обоих случаях у корневого элемента класс `photo` с фиксированным `aspect-ratio: 4 / 3` — компонент-потребитель может полагаться на одинаковые размеры независимо от наличия фото.

- [ ] **Step 1: Написать компонент**

```astro
---
// site/src/components/PhotoPlaceholder.astro
interface Props {
  alt: string;
  src?: string;
}
const { alt, src } = Astro.props;
---
{src ? (
  <img class="photo" src={src} alt={alt} />
) : (
  <div class="photo photo-placeholder" role="img" aria-label={alt}></div>
)}

<style>
  .photo {
    display: block;
    width: 100%;
    aspect-ratio: 4 / 3;
    border-radius: var(--radius-md);
    object-fit: cover;
  }
  .photo-placeholder {
    background: linear-gradient(135deg, var(--adult-bg) 0%, var(--paper) 100%);
    transition: filter 150ms ease-out;
  }
  .photo-placeholder:hover {
    filter: brightness(0.95);
  }
</style>
```

- [ ] **Step 2: Проверить сборку и закоммитить**

```bash
cd site && npm run build
git add site/src/components/PhotoPlaceholder.astro
git commit -m "feat: photo placeholder component with real-photo swap-in"
```

---

### Task 3: Компонент TrustGrid

**Что и зачем.** Сетка карточек «Почему у нас» — единственное на этой странице место с несколькими однотипными элементами, поэтому, в отличие от `Hero` (без пропов), компонент принимает данные снаружи: `heading` и массив `points`. Так тот же компонент можно позже вызвать на `/detyam` с другим набором пунктов, без копирования вёрстки. Карточка использует паттерн из дизайн-системы (`--card` фон, `--line` рамка, `--radius-md`, акцентная полоса 6px сверху) — тот же приём, что уже применён в `AudienceSplit.pane .bar`, только цвет полосы нейтральный (`--forest`), а не «взрослый»/«детский», потому что страница не делит аудиторию.

**Files:**
- Create: `site/src/components/TrustGrid.astro`

**Interfaces:**
- Consumes: класс `.reveal` из `animations.css` (Task 1).
- Produces: компонент `<TrustGrid heading="..." points={[{title, text}, ...]} />`. Пропы: `heading: string`, `points: { title: string; text: string }[]`.

- [ ] **Step 1: Написать компонент**

```astro
---
// site/src/components/TrustGrid.astro
interface TrustPoint {
  title: string;
  text: string;
}
interface Props {
  heading: string;
  points: TrustPoint[];
}
const { heading, points } = Astro.props;
---
<section class="trust-grid">
  <h2>{heading}</h2>
  <div class="cards">
    {points.map((point) => (
      <div class="trust-card reveal">
        <div class="bar"></div>
        <h4>{point.title}</h4>
        <p>{point.text}</p>
      </div>
    ))}
  </div>
</section>

<style>
  .trust-grid {
    padding: var(--space-7) var(--space-6);
  }
  .trust-grid h2 {
    font-size: var(--text-h2);
    margin: 0 0 var(--space-6);
  }
  .cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: var(--space-5);
  }
  .trust-card {
    position: relative;
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: var(--radius-md);
    padding: var(--space-5);
    transition: transform 150ms ease-out, border-color 150ms ease-out;
  }
  .trust-card .bar {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 6px;
    background: var(--forest);
    border-radius: var(--radius-md) var(--radius-md) 0 0;
  }
  .trust-card h4 {
    font-size: var(--text-h4);
    font-weight: 600;
    margin: var(--space-2) 0 var(--space-2);
  }
  .trust-card p {
    font-size: var(--text-small);
    color: var(--ink-soft);
  }
  .trust-card:hover,
  .trust-card:focus-within {
    border-color: var(--forest);
  }
  @media (prefers-reduced-motion: no-preference) {
    .trust-card:hover,
    .trust-card:focus-within {
      transform: translateY(-2px);
    }
  }
</style>
```

- [ ] **Step 2: Проверить сборку и закоммитить**

```bash
cd site && npm run build
git add site/src/components/TrustGrid.astro
git commit -m "feat: trust grid component for studio credibility points"
```

---

### Task 4: Собрать страницу o-studii.astro

**Что и зачем.** Здесь всё соединяется: вступление (фото + текст, двухколоночная раскладка, как у `AudienceSplit`, тот же брейкпоинт 768px), `TrustGrid` с пятью пунктами из спеки, секция формата занятий (зеркальная раскладка — фото слева) и завершающая CTA-кнопка «Записаться» на `/kontakty`, чтобы страница не обрывалась без следующего шага для читателя.

**Files:**
- Modify: `site/src/pages/o-studii.astro`

**Interfaces:**
- Consumes: `BaseLayout` (пропы не меняются), `TrustGrid` и `PhotoPlaceholder` (Tasks 2–3), класс `.reveal` (Task 1).

- [ ] **Step 1: Написать страницу**

```astro
---
// site/src/pages/o-studii.astro
import BaseLayout from '../layouts/BaseLayout.astro';
import TrustGrid from '../components/TrustGrid.astro';
import PhotoPlaceholder from '../components/PhotoPlaceholder.astro';

const trustPoints = [
  {
    title: 'Опыт',
    text: 'Больше 10 лет практики как художник и больше 10 лет преподавания — материал объясняется понятно ученику любого возраста.',
  },
  {
    title: 'Мини-группы',
    text: '3–5 человек в группе — внимание к темпу и особенностям каждого, а не общий поток.',
  },
  {
    title: 'Обратная связь',
    text: 'После каждого занятия — видео и фото с пояснениями педагога, видно, как продвигается ученик.',
  },
  {
    title: 'Честная цена',
    text: 'Занятия проходят в мастерской на дому у художника — в стоимость не закладывается аренда помещения, только материалы и работа педагога.',
  },
  {
    title: 'Отношение',
    text: 'Уважительное и внимательное отношение к ученикам и родителям.',
  },
];
---
<BaseLayout title="О студии">
  <section class="intro reveal">
    <div class="intro-text">
      <h1>О студии</h1>
      <p>
        Частная студия «Кисть и Перо» — изостудия в Краснодаре. Мы учим
        видеть и работать руками: живопись, каллиграфия, керамика — для тех,
        кто хочет попробовать, и для тех, кто занимается регулярно.
      </p>
    </div>
    <PhotoPlaceholder alt="Художница за работой в мастерской" />
  </section>

  <TrustGrid heading="Почему у нас" points={trustPoints} />

  <section class="format reveal">
    <PhotoPlaceholder alt="Мастерская — рабочая комната" />
    <div class="format-text">
      <h2>Где и как проходят занятия</h2>
      <p>
        Просторная комната с большим окном, со сплит-системой. Занимаемся и
        за столами, и на мольбертах — формат зависит от техники.
      </p>
    </div>
  </section>

  <section class="cta">
    <a class="btn" href="/kontakty">Записаться</a>
  </section>
</BaseLayout>

<style>
  .intro,
  .format {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-6);
    align-items: center;
    padding: var(--space-7) var(--space-6);
  }
  .intro-text h1 {
    font-size: var(--text-hero);
    margin: 0 0 var(--space-4);
  }
  .intro-text p,
  .format-text p {
    color: var(--ink-soft);
    font-size: var(--text-body);
  }
  .format-text h2 {
    font-size: var(--text-h2);
    margin: 0 0 var(--space-3);
  }
  .cta {
    display: flex;
    justify-content: center;
    padding: var(--space-7) var(--space-6);
  }
  .btn {
    display: inline-block;
    text-decoration: none;
    font-weight: 700;
    font-size: var(--text-small);
    padding: var(--space-3) var(--space-5);
    background: var(--forest);
    color: #F3F1E4;
    border-radius: var(--radius-sm);
    transition: background-color 150ms ease-out;
  }
  .btn:hover {
    background: var(--forest-mid);
  }
  @media (prefers-reduced-motion: no-preference) {
    .btn {
      transition: background-color 150ms ease-out, transform 150ms ease-out;
    }
    .btn:hover {
      transform: translateY(-1px);
    }
  }

  @media (max-width: 768px) {
    .intro,
    .format {
      grid-template-columns: 1fr;
    }
  }
</style>
```

- [ ] **Step 2: Проверить сборку**

```bash
cd site && npm run build
```
Ожидается: 7 страниц собираются без ошибок, `/o-studii/index.html` содержит новый контент (вступление, 5 карточек, секцию формата, кнопку «Записаться»).

- [ ] **Step 3: Commit**

```bash
git add site/src/pages/o-studii.astro
git commit -m "feat: content and layout for o-studii page"
```

---

### Task 5: Браузерная проверка и публикация

**Что и зачем.** Прошлый раз чек-лист доступности каркаса проверялся агентом без реального браузера (см. `site/docs/manual-verification-checklist.md`) — часть пунктов осталась неподтверждённой вживую. Теперь доступен скилл `claude-in-chrome`, которым можно реально открыть страницу, изменить размер окна и посмотреть на результат — грех не воспользоваться, раз уж страница добавляет новую адаптивную вёрстку и анимации, которые стоит увидеть глазами, а не только по CSS-правилам.

**Files:** нет новых/изменяемых файлов — только проверка и публикация.

- [ ] **Step 1: Запустить дев-сервер**

```bash
cd site && npm run dev
```

- [ ] **Step 2: Открыть /o-studii через claude-in-chrome**

Сначала вызвать скилл `claude-in-chrome` (обязательно перед использованием любых `mcp__claude-in-chrome__*` инструментов — так требует сам скилл). Затем:
- Открыть `http://localhost:4321/o-studii` в новой вкладке.
- Проверить на широком окне (≥1024px): вступление в две колонки (текст + фото-плейсхолдер), пять карточек «Почему у нас» в сетке, секция формата зеркальная (фото слева), кнопка «Записаться» по центру внизу.
- Сузить окно до <768px: все секции складываются в одну колонку.
- Навести курсор на карточку — лёгкий сдвиг вверх и более яркая рамка. Навести на кнопку «Записаться» — фон темнеет (`--forest` → `--forest-mid`).
- Сделать скриншот широкого и узкого варианта для собственной проверки (не обязательно показывать пользователю, если всё в порядке).
- Проверить консоль браузера на ошибки — ожидается пусто.

- [ ] **Step 3: Обновить чек-лист**

Добавить в `site/docs/manual-verification-checklist.md` короткую запись о том, что пункты по `/o-studii` (адаптив, hover, отсутствие консольных ошибок) подтверждены вживую через `claude-in-chrome`, с датой.

- [ ] **Step 4: Commit и push**

```bash
git add site/docs/manual-verification-checklist.md
git commit -m "docs: verify o-studii page in real browser via claude-in-chrome"
git push origin main
```

---

## Что дальше

После этой страницы — по одному такому же циклу (спека, если нужна доработка контента → план → реализация) на каждую из оставшихся пяти: `/detyam`, `/vzroslym`, `/master-klassy`, `/vitrina`, `/kontakty`. Контент для них уже частично собран из присланного текста ВК (см. распределение в спеке `2026-08-07-o-studii-page-design.md` и в истории диалога) — следующий цикл может начинаться сразу с плана, без повторного брейнсторминга структуры, если материала достаточно.
