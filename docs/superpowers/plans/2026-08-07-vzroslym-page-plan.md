# Страница «Взрослым» — план реализации

> **Для агентов-исполнителей:** ОБЯЗАТЕЛЬНЫЙ САБ-СКИЛЛ: используйте superpowers:subagent-driven-development (рекомендуется) или superpowers:executing-plans для выполнения плана задача за задачей. Шаги отмечены чекбоксами (`- [ ]`) для отслеживания.

**Цель:** наполнить маршрут `/vzroslym` по спеке `docs/superpowers/specs/2026-08-07-vzroslym-page-design.md` — вступление в взрослом регистре, две сетки `TrustGrid`, CTA через `Button`.

**Архитектура:** без новых компонентов — третье переиспользование уже отработанного на `/detyam` паттерна (`TrustGrid` дважды + `PhotoPlaceholder` + `Button`, все с взрослым регистром).

## Global Constraints

- Никакого Tailwind/UI-фреймворков.
- Все цвета — из существующих токенов `tokens.css`.
- `TrustGrid`/`PhotoPlaceholder`/`Button` используются без изменений интерфейса (не модифицируются в этом плане).
- Бейджи возраста на этой странице не используются ни у одного пункта (в отличие от `/detyam`) — поля `badge` не передаются.
- Нет тестового раннера — `npm run build` и `npm run check` (появился после рефакторинга Button) — established эквивалент теста, оба гоняются на каждом шаге проверки.

---

### Task 1: Собрать страницу vzroslym.astro

**Files:**
- Modify: `site/src/pages/vzroslym.astro`

**Interfaces:**
- Consumes: `TrustGrid` (`heading`, `points: {title, text}[]`, `accent?`), `PhotoPlaceholder` (`alt`, без `tint` — дефолт `var(--adult-bg)` уже подходит), `Button` (`href`, `register?`, без `size` — дефолт `cta` подходит).

- [ ] **Step 1: Написать страницу**

```astro
---
// site/src/pages/vzroslym.astro
import BaseLayout from '../layouts/BaseLayout.astro';
import TrustGrid from '../components/TrustGrid.astro';
import PhotoPlaceholder from '../components/PhotoPlaceholder.astro';
import Button from '../components/Button.astro';

const courses = [
  {
    title: 'Живопись и рисунок',
    text: 'Разные техники и материалы — для тех, кто только начинает, и для тех, кто продолжает.',
  },
  {
    title: 'Каллиграфия острым пером',
    text: 'Классическая техника, требует терпения и точности.',
  },
  {
    title: 'Скетчинг',
    text: 'Рисование с натуры и по референсам — для отдыха и развития глаза.',
  },
  {
    title: 'Керамика',
    text: 'Лепка из глины, обжиг готовых работ.',
  },
];

const trustPoints = [
  {
    title: 'Опыт',
    text: 'Больше 10 лет практики как художник и больше 10 лет преподавания.',
  },
  {
    title: 'Индивидуальный формат',
    text: 'Можно заниматься индивидуально, в удобное для вас время — не только в группе.',
  },
  {
    title: 'Обратная связь',
    text: 'После каждого занятия — видео и фото, видно свой прогресс.',
  },
  {
    title: 'Честная цена',
    text: 'В стоимость не закладывается аренда помещения — только материалы и работа педагога.',
  },
];
---
<BaseLayout title="Взрослым">
  <section class="intro reveal">
    <div class="intro-text">
      <h1>Взрослым</h1>
      <p>
        Живопись, каллиграфия, скетчинг, керамика — индивидуально и в
        мини-группах.
      </p>
    </div>
    <PhotoPlaceholder alt="Взрослый на занятии живописью в студии" />
  </section>

  <TrustGrid heading="Чем занимаемся" points={courses} accent="var(--adult)" />

  <TrustGrid heading="Почему у нас" points={trustPoints} accent="var(--adult)" />

  <section class="cta">
    <Button href="/kontakty" register="adult">Записаться</Button>
  </section>
</BaseLayout>

<style>
  .intro {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-6);
    align-items: center;
    padding: var(--space-7) var(--space-6);
    background: var(--adult-bg);
  }
  .intro-text h1 {
    font-size: var(--text-hero);
    margin: 0 0 var(--space-4);
  }
  .intro-text p {
    color: var(--ink);
    font-size: var(--text-body);
    max-width: 60ch;
  }
  .cta {
    display: flex;
    justify-content: center;
    padding: var(--space-7) var(--space-6);
  }

  @media (max-width: 768px) {
    .intro {
      grid-template-columns: 1fr;
    }
  }
</style>
```

- [ ] **Step 2: Проверить сборку и типы**

```bash
cd site
npm run build
npm run check
```
Ожидается: 7 страниц без ошибок сборки, `npm run check` — 0 ошибок (не считая уже существующего 1 hint в `BaseLayout.astro`, не связанного с этой работой). Разобрать `dist/vzroslym/index.html`: `<h1>Взрослым`, два `<h2>` («Чем занимаемся», «Почему у нас»), 8×`<h3>` карточек, кнопка «Записаться» на `/kontakty`, ни одного элемента `class="badge"` (бейджи здесь не нужны).

- [ ] **Step 3: Commit**

```bash
git add site/src/pages/vzroslym.astro
git commit -m "feat: content and layout for vzroslym page"
```

---

### Task 2: Проверка и публикация

**Files:**
- Modify: `site/docs/manual-verification-checklist.md`

- [ ] **Step 1: Разобрать собранный HTML и добавить секцию в чек-лист**

По тому же формату, что и секции `/o-studii`/`/detyam` — что подтверждено статически (структура, отсутствие бейджей, CTA), что не проверено вживую (тот же открытый пункт — `claude-in-chrome` недоступен последние 3 сессии подряд, если ситуация не изменилась — зафиксировать честно).

- [ ] **Step 2: Commit и push**

```bash
git add site/docs/manual-verification-checklist.md
git commit -m "docs: verification pass for vzroslym page"
git push origin main
```

---

## Что дальше

Осталось 3 страницы: `/master-klassy`, `/vitrina`, `/kontakty`. У `/kontakty` наименьший контент-риск (телефон, ссылка на ВК) — хороший кандидат на следующий короткий цикл.
