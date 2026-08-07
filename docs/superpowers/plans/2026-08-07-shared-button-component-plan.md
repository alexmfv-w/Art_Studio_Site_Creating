# Общий компонент кнопки — план реализации

> **Для агентов-исполнителей:** ОБЯЗАТЕЛЬНЫЙ САБ-СКИЛЛ: используйте superpowers:subagent-driven-development (рекомендуется) или superpowers:executing-plans для выполнения плана задача за задачей. Шаги отмечены чекбоксами (`- [ ]`) для отслеживания.

**Цель:** вынести три независимо продублированных блока `.btn`-стилей (`AudienceSplit.astro`, `o-studii.astro`, `detyam.astro`) в один компонент `Button.astro` с тремя регистрами (`neutral`/`adult`/`kid`) и двумя размерами (`cta`/`compact`), прежде чем на `/vzroslym` появится четвёртая копия. Рекомендовано финальным ревью `/detyam`.

**Архитектура:** `Button.astro` — тонкий `<a class:list={['btn', register, size]}>` с CSS-регистрами по классам, без кастомных свойств (в отличие от `TrustGrid`/`PhotoPlaceholder` — здесь всего 3 фиксированных регистра, а не произвольный цвет, `class:list` проще и понятнее). Побочный эффект: у взрослого и детского регистров впервые появляется hover-состояние (в `AudienceSplit` раньше не было ни у одной кнопки) — небольшое, безопасное улучшение к первоначальному запросу «оживить сайт минимальными анимациями», не отдельная задача.

**Тех-стек:** тот же, что и везде — Astro-компонент, обычный CSS с токенами.

## Global Constraints

- Никакого Tailwind/UI-фреймворков.
- Все цвета — из существующих токенов `tokens.css`, кроме уже задокументированных прецедентов `#F3F1E4`/`#F3F1DE` (кремовый текст на тёмном/зелёном фоне — те же значения, что уже были в `o-studii.astro`/`AudienceSplit.astro` до рефакторинга, переносятся как есть, не трогаем отдельным фиксом токенов в рамках этой задачи).
- **Визуальный результат на всех трёх существующих страницах (`/`, `/o-studii`, `/detyam`) должен остаться неизменным**, кроме одного намеренного улучшения — hover на кнопках `AudienceSplit` (взрослый и детский регистры), которого раньше не было. Это регрессионный рефакторинг, не редизайн.
- Нет тестового раннера — `npm run build` есть established эквивалент теста.

---

## Структура файлов

```
site/
├── src/
│   ├── components/
│   │   ├── Button.astro           # новый
│   │   └── AudienceSplit.astro    # правка — использует Button
│   └── pages/
│       ├── o-studii.astro         # правка — использует Button
│       └── detyam.astro           # правка — использует Button
```

---

### Task 1: Компонент Button

**Что и зачем.** Три регистра (`neutral` — нейтральный `--forest`, `adult` — `--adult`, `kid` — `--kid`, скруглённый и жирнее) и два размера (`cta` — отступы `space-3 space-5` для отдельно стоящей кнопки-призыва, `compact` — `space-3 space-4` для кнопки внутри карточки, как в `AudienceSplit`). Хвостовой слот `<slot />` вместо пропа `label`, чтобы вызов оставался таким же читаемым, как обычная ссылка: `<Button href="...">Текст</Button>`.

**Files:**
- Create: `site/src/components/Button.astro`

**Interfaces:**
- Produces: `<Button href="..." register?="neutral"|"adult"|"kid" size?="cta"|"compact"><slot /></Button>`. По умолчанию `register="neutral"`, `size="cta"`.

- [ ] **Step 1: Написать компонент**

```astro
---
// site/src/components/Button.astro
interface Props {
  href: string;
  register?: 'neutral' | 'adult' | 'kid';
  size?: 'cta' | 'compact';
}
const { href, register = 'neutral', size = 'cta' } = Astro.props;
---
<a class:list={['btn', register, size]} href={href}>
  <slot />
</a>

<style>
  .btn {
    display: inline-block;
    text-decoration: none;
    font-size: var(--text-small);
    transition: background-color 150ms ease-out, filter 150ms ease-out;
  }
  @media (prefers-reduced-motion: no-preference) {
    .btn {
      transition: background-color 150ms ease-out, filter 150ms ease-out, transform 150ms ease-out;
    }
    .btn:hover {
      transform: translateY(-1px);
    }
  }

  .btn.cta {
    padding: var(--space-3) var(--space-5);
  }
  .btn.compact {
    padding: var(--space-3) var(--space-4);
  }

  .btn.neutral {
    font-weight: 700;
    background: var(--forest);
    color: #F3F1E4;
    border-radius: var(--radius-sm);
  }
  .btn.neutral:hover {
    background: var(--forest-mid);
  }

  .btn.adult {
    font-weight: 700;
    background: var(--adult);
    color: #F3F1DE;
    border-radius: var(--radius-sm);
  }
  .btn.adult:hover {
    filter: brightness(1.1);
  }

  .btn.kid {
    font-weight: 800;
    background: var(--kid);
    color: var(--ink);
    border-radius: var(--radius-pill);
  }
  .btn.kid:hover {
    filter: brightness(1.08);
  }
</style>
```

- [ ] **Step 2: Проверить сборку и закоммитить**

```bash
cd site && npm run build
git add src/components/Button.astro
git commit -m "feat: shared Button component with neutral/adult/kid registers"
```

---

### Task 2: Переключить AudienceSplit, o-studii, detyam на Button

**Что и зачем.** Три существующих места переключаются на новый компонент, старые `.btn`-блоки в их `<style>` удаляются. `AudienceSplit` использует `size="compact"` (как было — отступы `space-3 space-4`), обе страницы — `size="cta"` (по умолчанию, отступы `space-3 space-5`, как было). `pane.key` в `AudienceSplit` уже принимает значения `'adult'`/`'kid'` — совпадает с `register` дословно, можно передать напрямую.

**Files:**
- Modify: `site/src/components/AudienceSplit.astro`
- Modify: `site/src/pages/o-studii.astro`
- Modify: `site/src/pages/detyam.astro`

**Interfaces:**
- Consumes: `Button` из Task 1.

- [ ] **Step 1: AudienceSplit.astro**

Добавить импорт в начало frontmatter:
```astro
import Button from './Button.astro';
```

Заменить:
```astro
      <a class="btn" href={pane.href}>Выбрать направление</a>
```
на:
```astro
      <Button href={pane.href} register={pane.key} size="compact">Выбрать направление</Button>
```

Удалить из `<style>` блока правила `.btn { ... }`, `.pane.adult .btn { ... }`, `.pane.kid .btn { ... }` целиком (три правила, стили теперь в `Button.astro`). Остальные правила (`.pane`, `.bar`, `h3`, `p`, `.pane.adult`, `.pane.kid` без `.btn`-части) не трогать.

- [ ] **Step 2: o-studii.astro**

Добавить импорт:
```astro
import Button from '../components/Button.astro';
```

Заменить:
```astro
    <a class="btn" href="/kontakty">Записаться</a>
```
на:
```astro
    <Button href="/kontakty">Записаться</Button>
```

Удалить из `<style>` весь блок `.btn { ... }` и `.btn:hover { ... }` и вложенный `@media (prefers-reduced-motion: no-preference) { .btn { ... } .btn:hover { ... } }` — вся эта логика переехала в `Button.astro`. `.cta { display:flex; justify-content:center; padding: ...; }` (обёртка-секция, не сама кнопка) — оставить без изменений.

- [ ] **Step 3: detyam.astro**

Добавить импорт:
```astro
import Button from '../components/Button.astro';
```

Заменить:
```astro
    <a class="btn" href="/kontakty">Записаться</a>
```
на:
```astro
    <Button href="/kontakty" register="kid">Записаться</Button>
```

Удалить из `<style>` весь блок `.btn { ... }`, `.btn:hover { ... }` и вложенный `@media (prefers-reduced-motion: no-preference) { ... }` для кнопки — переехало в `Button.astro`. `.cta` (секция-обёртка) — оставить.

- [ ] **Step 4: Проверить сборку и визуально сверить вывод**

```bash
cd site && npm run build
```
Ожидается: 7 страниц без ошибок. Сверить, что в `dist/index.html`, `dist/o-studii/index.html`, `dist/detyam/index.html` кнопки сохранили прежние классы регистров (`neutral`/`adult`/`kid` дают тот же итоговый цвет/радиус/жирность, что были захардкожены раньше — задача регрессионная, не редизайн).

- [ ] **Step 5: Commit**

```bash
git add site/src/components/AudienceSplit.astro site/src/pages/o-studii.astro site/src/pages/detyam.astro
git commit -m "refactor: use shared Button component across AudienceSplit, o-studii, detyam"
```

---

## Что дальше

`/vzroslym` — следующая страница по тому же паттерну `TrustGrid`/`PhotoPlaceholder`, теперь и `Button` с `register="adult"`.
