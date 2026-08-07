# Каркас сайта на Astro — план реализации

> **Для агентов-исполнителей:** ОБЯЗАТЕЛЬНЫЙ САБ-СКИЛЛ: используйте superpowers:subagent-driven-development (рекомендуется) или superpowers:executing-plans для выполнения плана задача за задачей. Шаги отмечены чекбоксами (`- [ ]`) для отслеживания.

**Цель:** собрать рабочий Astro-проект с общей оболочкой сайта (шапка с адаптивным меню, футер) и полностью готовой главной страницей по одобренному дизайну, плюс маршруты-заглушки для остальных разделов.

**Архитектура:** статический Astro-сайт без UI-фреймворков (React/Vue не нужны — все компоненты серверные `.astro`), обычный CSS с custom properties, мобильное меню на нативном Popover API с фидбек-полифиллом.

**Технологии:** Astro, HTML/CSS, ванильный JS (только фича-детект полифиллов, без своей логики кликов).

## Global Constraints

- Никакого Tailwind и UI-фреймворков — только `.astro`-компоненты и обычный CSS (design.md).
- Токены дизайн-системы (`2026-08-06-design-system-tokens.md`) — единственный источник цвета/шрифтов/отступов, новые значения не изобретаются.
- Мобильное меню — нативный `popover`/`command`/`commandfor`, с обязательным фича-детект полифиллом (`invokers-polyfill`, `@oddbird/popover-polyfill`) — без ручного JS-обработчика клика.
- Блок «Взрослым/Детям» сворачивается в одну колонку через медиа-запрос `max-width: 768px`.
- Landmarks (`header`/`nav`/`main`/`footer`), skip-link и `:focus-visible` — обязательны в каркасе с первого коммита, не «доделать потом».
- Маршруты-заглушки называются по схеме сайта: `/vzroslym`, `/detyam`, `/master-klassy`, `/vitrina`, `/o-studii`, `/kontakty`.

## Как читать этот план

Как и в плане контент-агента — каждая задача начинается с блока «Что и зачем», объясняющего решение до кода. Тестов в привычном pytest-смысле здесь мало (сайт без бизнес-логики), поэтому вместо TDD-цикла у каждой задачи — «собрать → `npm run build` как автоматическая проверка на синтаксис/рендер → глазами проверить в браузере», это и есть пропорциональный этому проекту эквивалент теста.

---

## Структура файлов

```
site/
├── astro.config.mjs
├── package.json
├── src/
│   ├── layouts/BaseLayout.astro
│   ├── styles/
│   │   ├── tokens.css
│   │   └── global.css
│   ├── components/
│   │   ├── SiteHeader.astro
│   │   ├── SiteFooter.astro
│   │   ├── Hero.astro
│   │   └── AudienceSplit.astro
│   └── pages/
│       ├── index.astro
│       ├── vzroslym.astro
│       ├── detyam.astro
│       ├── master-klassy.astro
│       ├── vitrina.astro
│       ├── o-studii.astro
│       └── kontakty.astro
```

---

### Task 1: Инициализация Astro-проекта

**Что и зачем.** Astro CLI сразу создаёт рабочий скелет (конфиг, `package.json`, `src/pages/index.astro`) — не нужно вручную собирать сборку с нуля. Проект живёт в подпапке `site/` рядом с `docs/`, как отдельный git-репозиторий (по той же логике, что и `content-agent/` в соседнем плане) — папка `docs/` документацией, а не кодом, отдельного репозитория не требует.

**Files:**
- Create: `site/` (весь скелет от Astro CLI)

- [ ] **Step 1: Запустить создание проекта**

```bash
cd /Users/alex/work/art_site_creating
npm create astro@latest site
```

Ответы на вопросы мастера (конкретная формулировка может отличаться в зависимости от версии CLI — ориентируйтесь по смыслу):
- Шаблон проекта → **Empty** (пустой, без демо-контента — вёрстку пишем сами по дизайну)
- Установить зависимости? → **Да**
- Инициализировать git-репозиторий? → **Да**
- TypeScript? → если спросит — **None/Relaxed** (проекту без сложной бизнес-логики строгая типизация не нужна)

- [ ] **Step 2: Проверить, что проект собирается**

```bash
cd site
npm run build
```
Ожидается: сборка проходит без ошибок (выводит `dist/`).

- [ ] **Step 3: Убедиться, что структура на месте**

```bash
ls src
```
Ожидается: видны `pages/` (со стартовым `index.astro` от CLI — его содержимое перепишем в Task 8) и, возможно, `assets/`/`components/` от шаблона.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: scaffold Astro project"
```

---

### Task 2: Токены и базовые стили

**Что и зачем.** Все цвета/шрифты/отступы сайта берутся из одного файла `tokens.css` — если студия решит чуть сдвинуть оттенок, правка в одном месте применится везде. `global.css` — минимальный сброс браузерных стилей по умолчанию (отступы `body`, `box-sizing`) плюс то, что нужно сразу для доступности: `.visually-hidden`, `.skip-link`, видимый `:focus-visible`.

**Files:**
- Create: `site/src/styles/tokens.css`
- Create: `site/src/styles/global.css`

**Interfaces:**
- Produces: custom properties `--forest`, `--forest-mid`, `--paper`, `--card`, `--ink`, `--ink-soft`, `--line`, `--adult`, `--adult-bg`, `--kid`, `--kid-bg`, `--font-display`, `--font-body`, `--font-label`, `--text-*`, `--space-1`…`--space-8`, `--radius-sm`, `--radius-md`, `--radius-pill` — используются во всех компонентах следующих задач.

- [ ] **Step 1: Написать tokens.css**

```css
/* site/src/styles/tokens.css */
:root {
  --forest: #2C3323;
  --forest-mid: #3A4530;
  --paper: #ECEEDF;
  --card: #FAFAF1;
  --ink: #262B1F;
  --ink-soft: #5B6350;
  --line: #D8DBC7;

  --adult: #3E4A2E;
  --adult-bg: #C7CBA6;
  --kid: #D98A2E;
  --kid-bg: #F3E3AE;

  --font-display: Charter, "Bitstream Charter", "Sitka Text", Cambria, serif;
  --font-body: ui-sans-serif, -apple-system, "Segoe UI", Roboto, sans-serif;
  --font-label: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;

  --text-hero: clamp(28px, 5vw, 40px);
  --text-h2: 28px;
  --text-h3: 20px;
  --text-h4: 16px;
  --text-body: 16px;
  --text-small: 14px;
  --text-label: 12px;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-7: 48px;
  --space-8: 64px;

  --radius-sm: 3px;
  --radius-md: 6px;
  --radius-pill: 999px;
}
```

- [ ] **Step 2: Написать global.css**

```css
/* site/src/styles/global.css */
*, *::before, *::after { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: var(--font-body);
  font-size: var(--text-body);
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

h1, h2 { font-family: var(--font-display); margin: 0; }
h3, h4 { font-family: var(--font-body); margin: 0; }
p { margin: 0; }
a { color: inherit; }

.visually-hidden:where(:not(:focus-within, :active)) {
  position: absolute !important;
  clip-path: inset(50%) !important;
  overflow: hidden !important;
  width: 1px !important;
  height: 1px !important;
  margin: -1px !important;
  padding: 0 !important;
  border: 0 !important;
  white-space: nowrap !important;
}

.skip-link {
  position: absolute;
  top: -100%;
  left: var(--space-4);
  background: var(--forest);
  color: #F3F1E4;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-sm);
  z-index: 1000;
  text-decoration: none;
}
.skip-link:focus {
  top: var(--space-2);
}

:where(a:any-link, button):focus-visible {
  outline: 3px solid var(--adult);
  outline-offset: 3px;
}
```

- [ ] **Step 3: Проверить сборку**

```bash
npm run build
```
Ожидается: без ошибок (стили пока никуда не подключены — это будет в Task 5, но синтаксис CSS уже проверяем).

- [ ] **Step 4: Commit**

```bash
git add src/styles
git commit -m "feat: design tokens and base styles"
```

---

### Task 3: Шапка сайта с адаптивным меню

**Что и зачем.** Здесь впервые используется нативный Popover API вместо своего JS: кнопка с `command="toggle-popover"` и `commandfor="mobile-nav"` открывает/закрывает `<nav popover>` без единого обработчика клика — браузер сам ставит `aria-expanded` на кнопку и управляет фокусом. На широких экранах popover-версия скрыта медиа-запросом, видна обычная строка ссылок.

**Files:**
- Create: `site/src/components/SiteHeader.astro`

**Interfaces:**
- Consumes: токены из `tokens.css` (глобально подключены в Task 5)
- Produces: компонент `<SiteHeader />` без пропов, используется в `BaseLayout.astro` (Task 5)

- [ ] **Step 1: Написать компонент**

```astro
---
// site/src/components/SiteHeader.astro
const links = [
  { href: "/vzroslym", label: "Взрослым" },
  { href: "/detyam", label: "Детям" },
  { href: "/vitrina", label: "Витрина" },
  { href: "/master-klassy", label: "Мастер-классы" },
];
---
<header class="site-header">
  <a href="/" class="brand">
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 20L16 8" stroke="#EDE9D8" stroke-width="3" stroke-linecap="round" />
      <path d="M20 4L9 15l1.5 1.5L21.5 5.5z" fill="#EDE9D8" />
    </svg>
    Кисть и Перо
  </a>

  <nav aria-label="Основная" class="nav-desktop">
    <ul>
      {links.map((link) => (
        <li><a href={link.href}>{link.label}</a></li>
      ))}
    </ul>
  </nav>

  <button command="toggle-popover" commandfor="mobile-nav" class="menu-btn" aria-label="Открыть меню">
    ☰
  </button>

  <nav id="mobile-nav" popover aria-label="Основная (мобильная)" class="nav-mobile">
    <ul>
      {links.map((link) => (
        <li><a href={link.href}>{link.label}</a></li>
      ))}
    </ul>
  </nav>
</header>

<style>
  .site-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--space-4) var(--space-6);
    background: var(--forest);
    color: #EDE9D8;
  }
  .brand {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 17px;
    text-decoration: none;
  }
  .nav-desktop ul {
    display: flex;
    gap: var(--space-5);
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .nav-desktop a {
    text-decoration: none;
    font-size: var(--text-small);
  }
  .menu-btn {
    display: none;
    background: none;
    border: none;
    color: inherit;
    font-size: 22px;
    cursor: pointer;
    padding: var(--space-2);
  }
  .nav-mobile {
    border: none;
    border-radius: var(--radius-md);
    padding: var(--space-4);
    background: var(--forest);
    color: #EDE9D8;
    margin: var(--space-2) auto auto auto;
  }
  .nav-mobile ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
  }
  .nav-mobile a {
    color: inherit;
    text-decoration: none;
    font-size: var(--text-h4);
  }

  @media (max-width: 768px) {
    .nav-desktop { display: none; }
    .menu-btn { display: block; }
  }
</style>
```

- [ ] **Step 2: Проверить сборку**

```bash
npm run build
```
Ожидается: без ошибок. Полноценно кнопка заработает только когда компонент подключат в `BaseLayout` (Task 5) — на этом шаге проверяем только валидность синтаксиса.

- [ ] **Step 3: Commit**

```bash
git add src/components/SiteHeader.astro
git commit -m "feat: site header with native popover mobile menu"
```

---

### Task 4: Футер сайта

**Что и зачем.** Минимальная структура — по объёму этого этапа полноценные контакты и соцсети появятся при наполнении страницы «Контакты», сейчас футер только держит layout и даёт ссылку на существующую страницу ВК.

**Files:**
- Create: `site/src/components/SiteFooter.astro`

**Interfaces:**
- Produces: компонент `<SiteFooter />` без пропов, используется в `BaseLayout.astro` (Task 5)

- [ ] **Step 1: Написать компонент**

```astro
---
// site/src/components/SiteFooter.astro
---
<footer class="site-footer">
  <p>© 2026 Кисть и Перо, Краснодар</p>
  <nav aria-label="Соцсети и мессенджеры">
    <a href="https://vk.ru/kistpero">ВКонтакте</a>
  </nav>
</footer>

<style>
  .site-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: var(--space-3);
    padding: var(--space-5) var(--space-6);
    border-top: 1px solid var(--line);
    color: var(--ink-soft);
    font-size: var(--text-small);
  }
  .site-footer a { color: var(--ink-soft); }
</style>
```

- [ ] **Step 2: Проверить сборку и закоммитить**

```bash
npm run build
git add src/components/SiteFooter.astro
git commit -m "feat: site footer"
```

---

### Task 5: Общая оболочка (BaseLayout)

**Что и зачем.** `BaseLayout.astro` — единственное место, где объявлены `<html lang="ru">`, meta-теги, подключение `tokens.css`/`global.css`, skip-link и сама структура landmarks (`header`/`main`/`footer`). Здесь же — единственный на весь сайт скрипт: фича-детект полифиллов Popover/Invoker Commands, который грузит запасной код только в браузерах без нативной поддержки.

**Files:**
- Create: `site/src/layouts/BaseLayout.astro`

**Interfaces:**
- Consumes: `SiteHeader.astro` (Task 3), `SiteFooter.astro` (Task 4), `tokens.css`/`global.css` (Task 2)
- Produces: layout `<BaseLayout title="...">`, принимает `<slot />` для содержимого страницы — используется всеми страницами из `src/pages/`

- [ ] **Step 1: Написать layout**

```astro
---
// site/src/layouts/BaseLayout.astro
import SiteHeader from '../components/SiteHeader.astro';
import SiteFooter from '../components/SiteFooter.astro';
import '../styles/tokens.css';
import '../styles/global.css';

interface Props {
  title: string;
}
const { title } = Astro.props;
---
<!doctype html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title} · Кисть и Перо</title>
  </head>
  <body>
    <a href="#content" class="skip-link">Перейти к содержимому</a>
    <SiteHeader />
    <main id="content" tabindex="-1">
      <slot />
    </main>
    <SiteFooter />

    <script type="module">
      if (!('commandForElement' in HTMLButtonElement.prototype)) {
        import('https://esm.run/invokers-polyfill');
      }
      if (!('popover' in HTMLElement.prototype)) {
        import('https://unpkg.com/@oddbird/popover-polyfill@latest/dist/popover.min.js');
      }
    </script>
  </body>
</html>
```

- [ ] **Step 2: Временно подключить layout к стартовой странице, чтобы проверить сборку**

Заменить содержимое `src/pages/index.astro` (сгенерированное CLI) на:
```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
---
<BaseLayout title="Главная">
  <p>Черновая проверка каркаса</p>
</BaseLayout>
```

- [ ] **Step 3: Запустить дев-сервер и проверить вручную**

```bash
npm run dev
```
Открыть адрес из вывода (обычно `http://localhost:4321`). Проверить:
- Шапка тёмно-зелёная, лого и ссылки на месте
- На узком окне браузера (или через DevTools → Toggle device toolbar) вместо ссылок — кнопка ☰, клик по ней открывает выпадающее меню
- Клик по `Tab` с самого начала страницы — первая остановка фокуса показывает скрытую ссылку «Перейти к содержимому», при фокусе она становится видимой

- [ ] **Step 4: Commit**

```bash
git add src/layouts/BaseLayout.astro src/pages/index.astro
git commit -m "feat: base layout with skip-link and popover polyfill loader"
```

---

### Task 6: Компонент героя

**Что и зачем.** Тёмно-зелёный градиентный герой с заголовком — статичный компонент без логики, переносит уже одобренный текст и цвета один в один из макета направления A.

**Files:**
- Create: `site/src/components/Hero.astro`

**Interfaces:**
- Produces: компонент `<Hero />` без пропов, используется в `index.astro` (Task 8)

- [ ] **Step 1: Написать компонент**

```astro
---
// site/src/components/Hero.astro
---
<section class="hero">
  <h1>Учим видеть руками</h1>
  <p>Живопись, каллиграфия и керамика в Краснодаре — очно в мастерской и на видеокурсах дома.</p>
</section>

<style>
  .hero {
    padding: var(--space-8) var(--space-6) var(--space-7);
    background: linear-gradient(135deg, var(--forest) 0%, var(--forest-mid) 55%, #4B5A3B 100%);
  }
  .hero h1 {
    font-size: var(--text-hero);
    line-height: 1.15;
    color: #F4F1E4;
    max-width: 12ch;
    margin: 0 0 var(--space-4);
  }
  .hero p {
    color: #D6D9C4;
    max-width: 42ch;
    font-size: var(--text-body);
  }
</style>
```

- [ ] **Step 2: Проверить сборку и закоммитить**

```bash
npm run build
git add src/components/Hero.astro
git commit -m "feat: hero component"
```

---

### Task 7: Блок «Взрослым/Детям»

**Что и зачем.** Единственный компонент с настоящей адаптивной логикой на этом этапе: `display: grid` с двумя колонками, которые схлопываются в одну через медиа-запрос на 768px — так и было решено на этапе дизайна (это композиция уровня страницы, поэтому медиа-запрос, а не container query).

**Files:**
- Create: `site/src/components/AudienceSplit.astro`

**Interfaces:**
- Produces: компонент `<AudienceSplit />` без пропов, используется в `index.astro` (Task 8)

- [ ] **Step 1: Написать компонент**

```astro
---
// site/src/components/AudienceSplit.astro
const panes = [
  {
    key: 'adult',
    title: 'Взрослым',
    text: 'Живопись, каллиграфия острым пером, скетчинг, керамика — индивидуально и в мини-группах.',
    href: '/vzroslym',
  },
  {
    key: 'kid',
    title: 'Детям',
    text: 'Лепка, пластилинография, брашпен 8+, керамика — с учётом возраста.',
    href: '/detyam',
  },
];
---
<section class="audience-split">
  {panes.map((pane) => (
    <div class:list={["pane", pane.key]}>
      <div class="bar"></div>
      <h3>{pane.title}</h3>
      <p>{pane.text}</p>
      <a class="btn" href={pane.href}>Выбрать направление</a>
    </div>
  ))}
</section>

<style>
  .audience-split {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
  .pane {
    padding: var(--space-6) var(--space-5) var(--space-5);
    position: relative;
  }
  .pane .bar {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 6px;
  }
  .pane h3 {
    font-size: var(--text-h3);
    font-weight: 600;
    margin: 0 0 var(--space-2);
  }
  .pane p {
    font-size: var(--text-small);
    margin: 0 0 var(--space-4);
    max-width: 30ch;
  }
  .btn {
    display: inline-block;
    text-decoration: none;
    font-weight: 700;
    font-size: var(--text-small);
    padding: var(--space-3) var(--space-4);
  }
  .pane.adult { background: var(--adult-bg); color: var(--ink); }
  .pane.adult .bar { background: var(--adult); }
  .pane.adult .btn { background: var(--adult); color: #F3F1DE; border-radius: var(--radius-sm); }

  .pane.kid { background: var(--kid-bg); color: #4A3B14; }
  .pane.kid .bar { background: var(--kid); }
  .pane.kid .btn { background: var(--kid); color: #FFF7E8; border-radius: var(--radius-pill); }

  @media (max-width: 768px) {
    .audience-split { grid-template-columns: 1fr; }
  }
</style>
```

- [ ] **Step 2: Проверить сборку и закоммитить**

```bash
npm run build
git add src/components/AudienceSplit.astro
git commit -m "feat: audience split component with responsive collapse"
```

---

### Task 8: Сборка главной страницы

**Что и зачем.** Здесь герой и блок «Взрослым/Детям» впервые соединяются в реальную страницу поверх оболочки — до этого момента каждый компонент проверялся только на валидность синтаксиса по отдельности.

**Files:**
- Modify: `site/src/pages/index.astro`

- [ ] **Step 1: Собрать страницу**

```astro
---
// site/src/pages/index.astro
import BaseLayout from '../layouts/BaseLayout.astro';
import Hero from '../components/Hero.astro';
import AudienceSplit from '../components/AudienceSplit.astro';
---
<BaseLayout title="Главная">
  <Hero />
  <AudienceSplit />
</BaseLayout>
```

- [ ] **Step 2: Проверить вручную в браузере**

```bash
npm run dev
```
Проверить на широком экране: герой тёмно-зелёный, заголовок серифом, ниже — две панели разного цвета (оливковая/охра) с полосой и кнопкой. Сузить окно ниже ~768px — панели встают друг под друга, каждая на полную ширину. Кликнуть кнопку «Выбрать направление» на любой панели — должно вести на `/vzroslym` или `/detyam` (страницы появятся в Task 9, пока будет 404 — это ожидаемо).

- [ ] **Step 3: Commit**

```bash
git add src/pages/index.astro
git commit -m "feat: assemble homepage from hero and audience-split"
```

---

### Task 9: Страницы-заглушки остальных разделов

**Что и зачем.** Чтобы ссылки в шапке и на главной никуда не вели в пустоту, у каждого раздела схемы сайта должен быть реальный (пусть пока пустой) маршрут — так навигация уже сейчас кликабельна целиком, а наполнение конкретным контентом становится отдельной, изолированной задачей на будущее.

**Files:**
- Create: `site/src/pages/vzroslym.astro`
- Create: `site/src/pages/detyam.astro`
- Create: `site/src/pages/master-klassy.astro`
- Create: `site/src/pages/vitrina.astro`
- Create: `site/src/pages/o-studii.astro`
- Create: `site/src/pages/kontakty.astro`

- [ ] **Step 1: Написать одинаковый шаблон для каждой страницы**

```astro
---
// site/src/pages/vzroslym.astro
import BaseLayout from '../layouts/BaseLayout.astro';
---
<BaseLayout title="Взрослым">
  <div style="padding: var(--space-6);">
    <h1>Взрослым</h1>
    <p>Раздел в разработке.</p>
  </div>
</BaseLayout>
```

Повторить с заменой `title` и заголовка `<h1>` для остальных пяти файлов:
- `detyam.astro` → title/`h1`: «Детям»
- `master-klassy.astro` → «Мастер-классы»
- `vitrina.astro` → «Витрина»
- `o-studii.astro` → «О студии»
- `kontakty.astro` → «Контакты»

- [ ] **Step 2: Проверить, что все ссылки рабочие**

```bash
npm run dev
```
Пройти по всем ссылкам в шапке (десктоп и мобильное меню) и по обеим кнопкам блока «Взрослым/Детям» — каждая должна открывать соответствующую страницу-заглушку без 404.

- [ ] **Step 3: Commit**

```bash
git add src/pages/vzroslym.astro src/pages/detyam.astro src/pages/master-klassy.astro src/pages/vitrina.astro src/pages/o-studii.astro src/pages/kontakty.astro
git commit -m "feat: stub routes for remaining site sections"
```

---

### Task 10: Ручная проверка доступности и адаптива

**Что и зачем.** Автоматическая сборка (`npm run build`) ловит синтаксические ошибки, но не проверяет, действительно ли клавиатурная навигация и скринридер-разметка работают как задумано — это может подтвердить только ручной проход, аналогично чек-листу в плане контент-агента.

**Files:**
- Create: `site/docs/manual-verification-checklist.md` (не влияет на сборку — рабочий чек-лист для этого и будущих этапов)

- [ ] **Step 1: Написать чек-лист**

```markdown
# Ручная проверка каркаса перед следующим этапом

- [ ] Skip-link: первый Tab на любой странице показывает «Перейти к содержимому», Enter переносит фокус на `<main>`
- [ ] Клавиатурная навигация: Tab проходит по всем ссылкам шапки в видимом порядке слева направо
- [ ] Мобильное меню (окно уже 768px): кнопка ☰ видна, клик открывает меню, повторный клик или клик вне меню — закрывает
- [ ] Мобильное меню через клавиатуру: Tab доходит до кнопки ☰, Enter открывает, Tab продолжает по пунктам меню, Esc закрывает
- [ ] `aria-expanded` на кнопке ☰ в DevTools (вкладка Elements) меняется с `false` на `true` при открытии — без единой строчки нашего JS для этого
- [ ] Блок «Взрослым/Детям»: на широком экране — две колонки, на узком (< 768px) — одна под другой на всю ширину
- [ ] Контраст текста: `--ink-soft` на `--paper` и `--card` — проверить любым онлайн-контраст-чекером на соответствие 4.5:1
- [ ] Все 6 ссылок навигации и 2 кнопки блока «Взрослым/Детям» ведут на реальные страницы без 404
```

- [ ] **Step 2: Пройти чек-лист один раз, отметить результаты**

- [ ] **Step 3: Commit**

```bash
git add docs/manual-verification-checklist.md
git commit -m "docs: manual verification checklist for site frame"
```

---

## Что дальше

Каркас и главная страница готовы. Наполнение страниц-заглушек реальным контентом (направления, курсы, витрина, мастер-классы, контакты), личный кабинет и интеграции — самостоятельные следующие этапы, каждый по той же схеме: спека → план → реализация.
