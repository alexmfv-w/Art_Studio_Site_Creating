# Наполнение главной, фаза A — план реализации

> **Для агентов-исполнителей:** ОБЯЗАТЕЛЬНЫЙ САБ-СКИЛЛ: используйте superpowers:subagent-driven-development (рекомендуется) или superpowers:executing-plans для выполнения плана задача за задачей. Шаги отмечены чекбоксами (`- [ ]`) для отслеживания.

**Цель:** снять разрыв в пути «Записаться» (`/kontakty` — заглушка), добавить на главную секцию «Как проходит занятие» и анонс услуг на заказ, дать честный мостик к видеоурокам — весь контент, который не требует фотографий.

**Архитектура:** один новый компонент `Steps.astro` (пронумерованная последовательность — честно другой случай, чем параллельные списки `LabelList`); анонс услуг переиспользует уже существующий `LabelList` без изменений; `/kontakty` и `/vitrina` — обычные страницы по образцу уже собранных.

**Тех-стек:** Astro, обычный CSS, существующие токены.

## Global Constraints

- Спека: `docs/superpowers/specs/2026-08-09-homepage-phase-a-design.md`.
- Ничего не выдумывать. Телефон, мессенджеры, список услуг — дословно из уже подтверждённых фактов студии.
- Адрес мастерской не публикуется — вместо него «адрес пришлём после записи» (осознанное решение из спеки, не факт из источника).
- Нумерация шагов оправдана только в `Steps` (реальная последовательность) — `LabelList` для услуг остаётся без номеров, это по-прежнему параллельный список.
- Проверка: `npm run build` и `npm run check`, оба с нулём ошибок.

---

## Структура файлов

```
site/src/
├── components/
│   └── Steps.astro           # новый
└── pages/
    ├── kontakty.astro         # правка — из заглушки в контент
    ├── vitrina.astro          # правка — короткая заглушка с анонсом услуг
    └── index.astro             # правка — две новые секции + мостик
```

---

### Task 1: Страница /kontakty

**Что и зачем.** Каждая кнопка «Записаться» на сайте ведёт сюда. Сейчас там заглушка — это единственная задача цикла, которая чинит уже действующий путь, а не просто добавляет контент.

**Files:**
- Modify: `site/src/pages/kontakty.astro`

- [ ] **Step 1: Написать страницу**

```astro
---
// site/src/pages/kontakty.astro
import BaseLayout from '../layouts/BaseLayout.astro';
import Button from '../components/Button.astro';
---
<BaseLayout title="Контакты">
  <section class="contacts reveal">
    <h1>Контакты</h1>
    <p class="lead">
      Занимаемся в мастерской на дому у художника — адрес пришлём после
      записи. Проще всего написать заранее.
    </p>
    <div class="channels">
      <div class="channel">
        <p class="label">Телефон, MAX</p>
        <p class="value">8 953 071 67 85</p>
      </div>
      <div class="channel">
        <p class="label">ВКонтакте</p>
        <p class="value">
          <a href="https://vk.ru/kistpero">vk.ru/kistpero</a>
        </p>
      </div>
      <div class="channel">
        <p class="label">Сообщения ВКонтакте</p>
        <p class="value">
          <a href="https://vk.me/kistpero">vk.me/kistpero</a>
        </p>
      </div>
    </div>
    <Button href="https://vk.me/kistpero">Написать в ВКонтакте</Button>
  </section>
</BaseLayout>

<style>
  .contacts {
    max-width: 640px;
    padding: var(--space-7) var(--space-6);
  }
  .contacts h1 {
    font-size: var(--text-hero);
    margin: 0 0 var(--space-4);
  }
  .lead {
    color: var(--ink-soft);
    max-width: 60ch;
    margin: 0 0 var(--space-6);
  }
  .channels {
    display: grid;
    gap: var(--space-4);
    margin-bottom: var(--space-6);
  }
  .channel {
    border-top: 1px solid var(--line);
    padding-top: var(--space-3);
  }
  .channel .label {
    font-family: var(--font-label);
    font-size: var(--text-label);
    text-transform: uppercase;
    letter-spacing: .06em;
    color: var(--ink-soft);
    margin: 0 0 var(--space-1);
  }
  .channel .value {
    font-size: var(--text-h4);
    margin: 0;
  }
  .channel .value a {
    text-decoration: none;
  }
  .channel .value a:hover {
    text-decoration: underline;
  }
</style>
```

- [ ] **Step 2: Проверить**

```bash
cd site && npm run build && npm run check
grep -c "8 953 071 67 85" dist/kontakty/index.html
```
Ожидается: сборка и проверка типов чистые; телефон присутствует в собранном HTML.

- [ ] **Step 3: Commit**

```bash
git add site/src/pages/kontakty.astro
git commit -m "feat: content for kontakty page — closes the booking path"
```

---

### Task 2: Компонент Steps

**Что и зачем.** Единственный блок на сайте, где нумерация оправдана содержанием, а не декором: это реальная последовательность действий («написать → договориться → позаниматься → получить видео»), а не список параллельных пунктов, как в `LabelList`. Отдельный компонент, а не переиспользование `LabelList` с добавленной нумерацией — потому что смысл списка принципиально другой, и путать эти два случая в одном компоненте значило бы держать в нём условную логику «когда с номерами, когда без».

**Files:**
- Create: `site/src/components/Steps.astro`

**Interfaces:**
- Produces: `<Steps heading="..." items={[{title, text}, ...]} accent?="..." />`.

- [ ] **Step 1: Написать компонент**

```astro
---
// site/src/components/Steps.astro
interface StepItem {
  title: string;
  text: string;
}
interface Props {
  heading: string;
  items: StepItem[];
  accent?: string;
}
const { heading, items, accent = 'var(--forest)' } = Astro.props;
---
<section class="steps" style={`--accent: ${accent}`}>
  <h2>{heading}</h2>
  <ol class="list">
    {items.map((item, i) => (
      <li class="step reveal">
        <span class="n">{i + 1}</span>
        <div class="body">
          <h3>{item.title}</h3>
          <p>{item.text}</p>
        </div>
      </li>
    ))}
  </ol>
</section>

<style>
  .steps {
    padding: var(--space-7) var(--space-6);
  }
  .steps h2 {
    font-size: var(--text-h2);
    margin: 0 0 var(--space-6);
  }
  .list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--space-6) var(--space-5);
  }
  .step {
    display: flex;
    gap: var(--space-3);
  }
  .n {
    font-family: var(--font-display);
    font-size: var(--text-h2);
    color: var(--accent, var(--forest));
    line-height: 1;
    flex-shrink: 0;
  }
  .body h3 {
    font-family: var(--font-body);
    font-size: var(--text-h4);
    font-weight: 600;
    margin: 0 0 var(--space-2);
  }
  .body p {
    font-size: var(--text-small);
    color: var(--ink-soft);
    margin: 0;
  }
</style>
```

- [ ] **Step 2: Проверить сборку и закоммитить**

```bash
cd site && npm run build && npm run check
git add src/components/Steps.astro
git commit -m "feat: Steps component — numbered sequence, distinct from parallel LabelList"
```

---

### Task 3: Секции на главной

**Что и зачем.** Здесь всё соединяется: после существующего сплита «Взрослым/Детям» встают «Как проходит занятие», анонс услуг на заказ и строка-мостик к видеоурокам. Порядок — по рекомендации ресёрча (`docs/research/homepage/homepage-architecture.md`), с пропуском блоков фазы B, которые ждут фотографий.

**Files:**
- Modify: `site/src/pages/index.astro`

**Interfaces:**
- Consumes: `Steps` (Task 2), `LabelList` (уже существует, без изменений).

- [ ] **Step 1: Переписать index.astro**

```astro
---
// site/src/pages/index.astro
import BaseLayout from '../layouts/BaseLayout.astro';
import Hero from '../components/Hero.astro';
import AudienceSplit from '../components/AudienceSplit.astro';
import Steps from '../components/Steps.astro';
import LabelList from '../components/LabelList.astro';

const steps = [
  {
    title: 'Написать',
    text: 'В MAX или сообщество ВКонтакте — кому интересно (взрослому или ребёнку) и какое направление.',
  },
  {
    title: 'Договориться о времени',
    text: 'Мини-группа до 5 человек, в детской — до 4.',
  },
  {
    title: 'Позаниматься в мастерской',
    text: 'За столом или на мольберте — зависит от техники.',
  },
  {
    title: 'Получить видео с разбором',
    text: 'После занятия — можно вернуться к уроку дома.',
  },
];

const services = [
  {
    medium: 'Стены, интерьер',
    title: 'Роспись стен',
    text: 'Под ваш интерьер и сюжет.',
  },
  {
    medium: 'Гипс, рельеф',
    title: 'Барельеф',
    text: 'Объёмная роспись и лепной декор.',
  },
  {
    medium: 'Глина, обжиг',
    title: 'Авторская керамика',
    text: 'Изделия на заказ.',
  },
  {
    medium: 'Холст, под заказ',
    title: 'Картина под интерьер',
    text: 'Живопись под конкретное пространство.',
  },
  {
    medium: 'Текстиль',
    title: 'Роспись одежды',
    text: 'Ручная роспись на заказ.',
  },
];
---
<BaseLayout title="Главная">
  <Hero />
  <AudienceSplit />

  <Steps heading="Как проходит занятие" items={steps} />

  <LabelList heading="Услуги на заказ" items={services} />
  <p class="services-note">Цена — по запросу.</p>

  <section class="video-bridge reveal">
    <p>
      Не в Краснодаре? <a href="https://vk.ru/kistpero">Видеоуроки по подписке</a> —
      можно заниматься из дома.
    </p>
  </section>
</BaseLayout>

<style>
  .services-note {
    padding: 0 var(--space-6) var(--space-6);
    margin: calc(var(--space-6) * -1) 0 0;
    font-size: var(--text-small);
    color: var(--ink-soft);
  }
  .video-bridge {
    padding: var(--space-6);
    text-align: center;
    border-top: 1px solid var(--line);
  }
  .video-bridge p {
    font-size: var(--text-body);
    color: var(--ink-soft);
    margin: 0;
  }
  .video-bridge a {
    color: var(--forest);
    font-weight: 700;
    text-decoration: none;
  }
  .video-bridge a:hover {
    text-decoration: underline;
  }
</style>
```

- [ ] **Step 2: Проверить**

```bash
cd site && npm run build && npm run check
echo "--- новые секции на главной ---"
grep -c "class=\"steps\"\|class=\"label-list\"\|video-bridge" dist/index.html
echo "--- нумерация шагов 1..4 ---"
grep -o 'class="n"[^<]*<[^>]*>[1-4]' dist/index.html | wc -l
echo "--- телефон нигде не продублирован на главной (его там не должно быть) ---"
grep -c "8 953" dist/index.html
```
Ожидается: сборка и проверка типов чистые; секции присутствуют; 4 шага пронумерованы; телефона на главной нет — эти данные только на `/kontakty`.

- [ ] **Step 3: Commit**

```bash
git add site/src/pages/index.astro
git commit -m "feat: homepage — steps, services teaser, video subscription bridge"
```

---

### Task 4: Заглушка /vitrina с анонсом услуг

**Что и зачем.** Строка-мостик и секция услуг на главной ссылаются на `/vitrina`. Сейчас там «Раздел в разработке» — переход не должен упираться в пустоту, как было с `/kontakty` до Task 1. Полноценное наполнение «Витрины» (фото работ) — фаза B; здесь только текстовая заглушка с тем же списком услуг, без дублирования вёрстки.

**Files:**
- Modify: `site/src/pages/vitrina.astro`

- [ ] **Step 1: Написать страницу**

```astro
---
// site/src/pages/vitrina.astro
import BaseLayout from '../layouts/BaseLayout.astro';
import LabelList from '../components/LabelList.astro';

const services = [
  {
    medium: 'Стены, интерьер',
    title: 'Роспись стен',
    text: 'Под ваш интерьер и сюжет.',
  },
  {
    medium: 'Гипс, рельеф',
    title: 'Барельеф',
    text: 'Объёмная роспись и лепной декор.',
  },
  {
    medium: 'Глина, обжиг',
    title: 'Авторская керамика',
    text: 'Изделия на заказ.',
  },
  {
    medium: 'Холст, под заказ',
    title: 'Картина под интерьер',
    text: 'Живопись под конкретное пространство.',
  },
  {
    medium: 'Текстиль',
    title: 'Роспись одежды',
    text: 'Ручная роспись на заказ.',
  },
];
---
<BaseLayout title="Витрина">
  <div style="padding: var(--space-6) var(--space-6) 0;">
    <h1>Витрина</h1>
    <p style="color: var(--ink-soft); max-width: 60ch;">
      Работы на заказ. Фотографии готовых работ появятся здесь позже —
      пока список направлений.
    </p>
  </div>
  <LabelList heading="Что можно заказать" items={services} />
</BaseLayout>
```

- [ ] **Step 2: Проверить**

```bash
cd site && npm run build && npm run check
```

- [ ] **Step 3: Commit**

```bash
git add site/src/pages/vitrina.astro
git commit -m "feat: vitrina stub with services list, no more empty page"
```

---

### Task 5: Зафиксировать проверку

**Files:**
- Modify: `site/docs/manual-verification-checklist.md`

- [ ] **Step 1: Дописать секцию** «Результаты прохода: главная, фаза A (дата)» — что подтверждено статически (сборка, проверка типов, контакты на `/kontakty`, отсутствие телефона на главной, нумерация шагов, ссылки услуг и мостика), и что требует глаза: читаются ли четыре шага как последовательность на разных ширинах экрана, не путается ли `LabelList` без порядка с `Steps` с порядком при вёрстке рядом друг с другом.

- [ ] **Step 2: Commit и push**

```bash
git add site/docs/manual-verification-checklist.md
git commit -m "docs: verification pass for homepage phase A"
git push origin main
```

---

## Что дальше

Фаза B — блоки, которым нужны фотографии: полоса-передышка после сплита, мозаика работ, компактный блок «о мастере» с портретом. Начинается после разметки фото тэггером (`tools/photo-tagger.py`).
