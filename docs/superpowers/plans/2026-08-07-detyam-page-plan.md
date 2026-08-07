# Страница «Детям» — план реализации

> **Для агентов-исполнителей:** ОБЯЗАТЕЛЬНЫЙ САБ-СКИЛЛ: используйте superpowers:subagent-driven-development (рекомендуется) или superpowers:executing-plans для выполнения плана задача за задачей. Шаги отмечены чекбоксами (`- [ ]`) для отслеживания.

**Цель:** наполнить маршрут `/detyam` реальным контентом по спеке `docs/superpowers/specs/2026-08-07-detyam-page-design.md` — вступление в кид-регистре, две сетки карточек (направления + пункты доверия) через переиспользуемый `TrustGrid`, CTA.

**Архитектура:** точечное обратно-совместимое расширение уже существующего `TrustGrid.astro` (два новых опциональных пропа: `accent`, `badge` на пункт) вместо нового компонента — карточка курса и карточка доверия визуально идентичны, дублировать CSS не нужно. Страница `detyam.astro` использует `TrustGrid` дважды с разным контентом и `accent="var(--kid)"`.

**Тех-стек:** тот же, что и на `/o-studii` — Astro-компоненты, обычный CSS с токенами, уже существующий класс `.reveal`.

## Global Constraints

- Никакого Tailwind/UI-фреймворков — только `.astro` + обычный CSS (не пересматривается).
- Все цвета/шрифты/отступы — из существующих токенов `site/src/styles/tokens.css`. Новых токенов эта работа не добавляет.
- Расширение `TrustGrid` должно быть **строго обратно совместимым** — вызов на `/o-studii` (`<TrustGrid heading="Почему у нас" points={trustPoints} />`, без `accent`/`badge`) обязан рендериться и выглядеть идентично тому, что уже смёржено в `main` (accent по умолчанию `var(--forest)`, badge не рендерится, если поле отсутствует).
- Кнопка CTA — «детский» регистр кнопки: `background: var(--kid)`, `color: var(--ink)`, `border-radius: var(--radius-pill)`, `font-weight: 800` — скопировано дословно с уже отгруженного `AudienceSplit.pane.kid .btn` (не с формулировки в документе токенов, которая слегка расходится — приоритет у уже смёрженного прецедента).
- Возрастной бейдж не проставляется там, где возраст не указан в источнике («Лепка и пластилинография», «Скетчинг и леттеринг») — не выдумывать диапазон.
- Анимации — переиспользуется существующий класс `.reveal` из `site/src/styles/animations.css`, новый CSS для анимаций не пишется.
- Нет тестового раннера в проекте — `npm run build` является established эквивалентом теста.

---

## Структура файлов

```
site/
├── src/
│   ├── components/
│   │   └── TrustGrid.astro     # правка — новые опциональные пропы accent, badge
│   └── pages/
│       └── detyam.astro        # правка — вся страница целиком
```

---

### Task 1: Расширить TrustGrid пропами accent и badge

**Что и зачем.** Финальное ревью `/o-studii` заранее предупредило: `TrustGrid` зашивает `var(--forest)` и не параметризуем снаружи из-за Astro-скоупинга стилей — этот момент настал при переиспользовании на `/detyam`. Вместо нового почти дублирующего компонента добавляются два опциональных пропа: `accent` (цвет акцентной полосы/рамки, кастомное CSS-свойство `--accent` наследуется по DOM независимо от скоупинга) и `badge` на отдельный пункт (короткая метка вроде «8+», в уже существующем визуальном стиле бейджа «Доступ» из дизайн-системы — контурная рамка, не заливка).

**Files:**
- Modify: `site/src/components/TrustGrid.astro`

**Interfaces:**
- Produces (изменённый контракт): `<TrustGrid heading="..." points={[{title, text, badge?}, ...]} accent?="..." />`. Оба новых пропа опциональны — существующий вызов на `/o-studii` без них обязан продолжать работать без изменений в выводе.

- [ ] **Step 1: Заменить содержимое компонента**

```astro
---
// site/src/components/TrustGrid.astro
interface TrustPoint {
  title: string;
  text: string;
  badge?: string;
}
interface Props {
  heading: string;
  points: TrustPoint[];
  accent?: string;
}
const { heading, points, accent = 'var(--forest)' } = Astro.props;
---
<section class="trust-grid" style={`--accent: ${accent}`}>
  <h2>{heading}</h2>
  <div class="cards">
    {points.map((point) => (
      <div class="trust-card reveal">
        <div class="bar"></div>
        {point.badge && <span class="badge">{point.badge}</span>}
        <h3>{point.title}</h3>
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
    background: var(--accent);
    border-radius: var(--radius-md) var(--radius-md) 0 0;
  }
  .badge {
    display: inline-block;
    border: 1px solid var(--ink-soft);
    color: var(--ink-soft);
    font-family: var(--font-label);
    font-size: var(--text-label);
    text-transform: uppercase;
    letter-spacing: .06em;
    padding: 2px var(--space-2);
    border-radius: var(--radius-pill);
    margin: 0 0 var(--space-1);
  }
  .trust-card h3 {
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
    border-color: var(--accent);
  }
  @media (prefers-reduced-motion: no-preference) {
    .trust-card:hover,
    .trust-card:focus-within {
      transform: translateY(-2px);
    }
  }
</style>
```

- [ ] **Step 2: Проверить сборку**

```bash
cd site && npm run build
```
Ожидается: 7 страниц собираются без ошибок. Разобрать `dist/o-studii/index.html` и подтвердить, что вывод для этой страницы не изменился по существу — акцентная полоса карточек по-прежнему рисуется цветом `--forest` (проверить строку `background:var(--forest)` заменилась на использование кастомного свойства, но при отсутствии `accent`-пропа переданное значение по умолчанию `var(--forest)` даёт тот же итоговый цвет):
```bash
grep -o '\-\-accent:[^"]*' dist/o-studii/index.html | head -3
```
Ожидается: везде `--accent: var(--forest)` (проп не передавался на `/o-studii`, сработало значение по умолчанию).

- [ ] **Step 3: Commit**

```bash
git add site/src/components/TrustGrid.astro
git commit -m "feat: parametrize TrustGrid accent color and per-point badge"
```

---

### Task 2: Собрать страницу detyam.astro

**Что и зачем.** Здесь всё соединяется: вступление в кид-регистре (фон `--kid-bg`, как у `AudienceSplit.pane.kid`), две сетки `TrustGrid` (направления с бейджами возраста там, где он известен, и пункты доверия без бейджей) — обе с `accent="var(--kid)"`, и CTA-кнопка в кид-регистре (скруглённая, жирный текст).

**Files:**
- Modify: `site/src/pages/detyam.astro`

**Interfaces:**
- Consumes: `TrustGrid` с новым контрактом из Task 1, `PhotoPlaceholder` (без изменений, тот же компонент, что и на `/o-studii`).

- [ ] **Step 1: Написать страницу**

```astro
---
// site/src/pages/detyam.astro
import BaseLayout from '../layouts/BaseLayout.astro';
import TrustGrid from '../components/TrustGrid.astro';
import PhotoPlaceholder from '../components/PhotoPlaceholder.astro';

const courses = [
  {
    title: 'Керамика',
    badge: '8+',
    text: 'Лепка из глины, обжиг готовых работ.',
  },
  {
    title: 'Лепка и пластилинография',
    text: 'Особенно полезны детям с задержкой развития речи.',
  },
  {
    title: 'Каллиграфия брашпеном',
    badge: '8+',
    text: 'Ручка-кисть — понятный формат для первого знакомства с каллиграфией.',
  },
  {
    title: 'Скетчинг и леттеринг',
    text: 'Для подростков — рисование и надписи в популярном сегодня стиле.',
  },
];

const trustPoints = [
  {
    title: 'Опыт',
    text: 'Больше 10 лет практики как художник и больше 10 лет преподавания.',
  },
  {
    title: 'Мини-группы',
    text: 'До 4 человек в группе — учитываем возраст и темп каждого ребёнка.',
  },
  {
    title: 'Обратная связь',
    text: 'После каждого занятия — видео и фото с занятия, вы видите прогресс ребёнка.',
  },
  {
    title: 'Честная цена',
    text: 'В стоимость не закладывается аренда помещения — только материалы и работа педагога.',
  },
];
---
<BaseLayout title="Детям">
  <section class="intro reveal">
    <div class="intro-text">
      <h1>Детям</h1>
      <p>
        Раскрываем творческие способности ребёнка, развиваем мелкую
        моторику, усидчивость, воображение. Прививаем любовь к искусству.
      </p>
    </div>
    <PhotoPlaceholder alt="Ребёнок на занятии в студии" />
  </section>

  <TrustGrid heading="Чем занимаемся" points={courses} accent="var(--kid)" />

  <TrustGrid heading="Почему у нас" points={trustPoints} accent="var(--kid)" />

  <section class="cta">
    <a class="btn" href="/kontakty">Записаться</a>
  </section>
</BaseLayout>

<style>
  .intro {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-6);
    align-items: center;
    padding: var(--space-7) var(--space-6);
    background: var(--kid-bg);
  }
  .intro-text h1 {
    font-size: var(--text-hero);
    margin: 0 0 var(--space-4);
  }
  .intro-text p {
    color: #4A3B14;
    font-size: var(--text-body);
    max-width: 60ch;
  }
  .cta {
    display: flex;
    justify-content: center;
    padding: var(--space-7) var(--space-6);
  }
  .btn {
    display: inline-block;
    text-decoration: none;
    font-weight: 800;
    font-size: var(--text-small);
    padding: var(--space-3) var(--space-5);
    background: var(--kid);
    color: var(--ink);
    border-radius: var(--radius-pill);
    transition: filter 150ms ease-out;
  }
  .btn:hover {
    filter: brightness(1.08);
  }
  @media (prefers-reduced-motion: no-preference) {
    .btn {
      transition: filter 150ms ease-out, transform 150ms ease-out;
    }
    .btn:hover {
      transform: translateY(-1px);
    }
  }

  @media (max-width: 768px) {
    .intro {
      grid-template-columns: 1fr;
    }
  }
</style>
```

- [ ] **Step 2: Проверить сборку**

```bash
cd site && npm run build
```
Ожидается: 7 страниц без ошибок. `dist/detyam/index.html` содержит: `<h1>Детям`, два `<h2>` («Чем занимаемся», «Почему у нас»), 8 `<h3>` карточек суммарно (4+4), 2 бейджа «8+», кнопку «Записаться» на `/kontakty`.

- [ ] **Step 3: Commit**

```bash
git add site/src/pages/detyam.astro
git commit -m "feat: content and layout for detyam page"
```

---

### Task 3: Проверка и публикация

**Что и зачем.** Тот же завершающий шаг, что и на `/o-studii` — статическая проверка сборки и разбор `dist/`, попытка живой браузерной проверки через `claude-in-chrome`, честная фиксация результата в чек-листе (в прошлой сессии расширение оказалось недоступно — если ситуация не изменилась, снова зафиксировать это явно, не выдумывать «подтверждено вживую»).

**Files:**
- Modify: `site/docs/manual-verification-checklist.md`

- [ ] **Step 1: Разобрать собранный HTML**

```bash
cd site
npm run build
echo "=== headings ===" && grep -oE '<h[123][^>]*>[^<]*' dist/detyam/index.html
echo "=== badges ===" && grep -o 'class="badge">[^<]*' dist/detyam/index.html
echo "=== CTA ===" && grep -oE '<a class="btn"[^>]*>[^<]*' dist/detyam/index.html
echo "=== no invented age for lepka/sketching ===" && grep -B2 'Лепка и пластилинография\|Скетчинг и леттеринг' dist/detyam/index.html | grep -c 'badge'
```
Ожидается: заголовки в правильном порядке, 2 бейджа «8+» (не 4 — лепка и скетчинг намеренно без бейджа), CTA на `/kontakty`, последняя проверка возвращает `0` (нет бейджа рядом с этими двумя карточками).

- [ ] **Step 2: Попытаться живую браузерную проверку**

Вызвать скилл `claude-in-chrome` (если недоступен в этой сессии — зафиксировать это честно в чек-листе, как и в прошлый раз, не имитировать проверку).

- [ ] **Step 3: Обновить чек-лист**

Добавить короткую секцию «Результаты прохода `/detyam` (дата)» по тому же формату, что и секция `/o-studii` — что подтверждено статически, что нет.

- [ ] **Step 4: Commit и push**

```bash
git add site/docs/manual-verification-checklist.md
git commit -m "docs: verification pass for detyam page"
git push origin main
```

---

## Что дальше

Осталось 4 страницы: `/vzroslym`, `/master-klassy`, `/vitrina`, `/kontakty`. `/vzroslym` — вероятно, следующий кандидат на переиспользование того же расширённого `TrustGrid` (взрослый регистр `accent="var(--adult)"`), контент для неё уже частично собран из источника ВК.
