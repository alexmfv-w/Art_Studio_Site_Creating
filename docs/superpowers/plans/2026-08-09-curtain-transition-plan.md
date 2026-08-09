# Переход-шторка — план реализации

> **Для агентов-исполнителей:** ОБЯЗАТЕЛЬНЫЙ САБ-СКИЛЛ: используйте superpowers:subagent-driven-development (рекомендуется) или superpowers:executing-plans для выполнения плана задача за задачей. Шаги отмечены чекбоксами (`- [ ]`) для отслеживания.

**Цель:** при переходе с главной на раздел панель «Взрослым»/«Детям» разворачивается в цветную шапку соответствующей страницы, а не сменяется мгновенным скачком.

**Архитектура:** нативные cross-document View Transitions — чистый CSS, без единой строки своего JS. Обе стороны перехода объявляют `@view-transition { navigation: auto }`, а парные элементы получают одинаковый `view-transition-name` — браузер сам интерполирует положение, размер и фон между ними. Компонент Astro `<ViewTransitions />` сознательно **не** используется: он подключает клиентский роутер на JS, а нам нужен именно нативный механизм.

**Тех-стек:** Astro, обычный CSS.

## Global Constraints

- Третий, последний цикл по спеке `docs/superpowers/specs/2026-08-08-visual-redesign-direction.md`.
- **Никакого своего JS.** Единственный скрипт на сайте — условный загрузчик полифиллов попапа в `BaseLayout`, он не трогается.
- Всё под `@media (prefers-reduced-motion: no-preference)`: кто просил меньше движения, получает обычный мгновенный переход.
- Прогрессивное улучшение. Cross-document View Transitions поддерживают Chrome/Edge 126+ и Safari 18.2+; **Firefox не поддерживает** и получит обычную навигацию. Полифилл не подключается — эффект декоративный.
- `view-transition-name` обязан быть уникальным в пределах документа. На главной две панели — значит два разных имени.
- Фоны парных элементов уже совпадают (`--adult-bg` на панели и на intro `/vzroslym`, `--kid-bg` на детских) — специально ничего подгонять не нужно.
- Проверка: `npm run build` и `npm run check`, оба с нулём ошибок.

---

### Task 1: Включить переходы и связать парные элементы

**Что и зачем.** `@view-transition { navigation: auto }` должен стоять на **обеих** сторонах перехода, иначе браузер его не запустит — поэтому правило кладётся в общий `global.css`, а не в отдельные страницы. Далее панель на главной и цветная intro-секция раздела получают одно и то же имя: по совпадению имён браузер понимает, что это «один и тот же» элемент, и морфит его между документами.

Шапке даётся собственное имя, чтобы она не участвовала в общем кросс-фейде корня: иначе при каждом переходе она моргала бы, хотя визуально не меняется.

**Files:**
- Modify: `site/src/styles/global.css`
- Modify: `site/src/components/AudienceSplit.astro`
- Modify: `site/src/components/SiteHeader.astro`
- Modify: `site/src/pages/vzroslym.astro`
- Modify: `site/src/pages/detyam.astro`

**Interfaces:**
- Produces: имена переходов `adult-panel`, `kid-panel`, `site-header` — общие для всех страниц, участвующих в переходе.

- [ ] **Step 1: Включить механизм глобально**

Добавить в конец `site/src/styles/global.css`:
```css
/* Cross-document View Transitions.
   Правило нужно на обеих сторонах перехода, поэтому лежит в общих стилях.
   Не поддерживается в Firefox — там просто обычная навигация. */
@media (prefers-reduced-motion: no-preference) {
  @view-transition {
    navigation: auto;
  }

  /* Морф панели в секцию чуть медленнее дефолтных 250мс:
     на большой площади быстрый переход читается как рывок. */
  ::view-transition-group(adult-panel),
  ::view-transition-group(kid-panel) {
    animation-duration: 420ms;
    animation-timing-function: cubic-bezier(.65, 0, .35, 1);
  }
}
```

- [ ] **Step 2: Назвать панели на главной**

В `site/src/components/AudienceSplit.astro` добавить в `<style>`:
```css
  /* Парный элемент перехода: разворачивается в intro-секцию раздела. */
  .pane.adult { view-transition-name: adult-panel; }
  .pane.kid { view-transition-name: kid-panel; }
```

- [ ] **Step 3: Назвать intro-секции разделов**

В `site/src/pages/vzroslym.astro` в правило `.intro` добавить строку:
```css
    view-transition-name: adult-panel;
```

В `site/src/pages/detyam.astro` в правило `.intro` добавить строку:
```css
    view-transition-name: kid-panel;
```

- [ ] **Step 4: Стабилизировать шапку**

В `site/src/components/SiteHeader.astro` в правило `.site-header` добавить:
```css
    view-transition-name: site-header;
```

- [ ] **Step 5: Проверить**

```bash
cd site && npm run build && npm run check
echo "--- правило включения ---"; grep -c "@view-transition" dist/_astro/*.css
echo "--- имена на главной ---"; grep -o "view-transition-name:[a-z-]*" dist/index.html dist/_astro/*.css | sort -u
echo "--- имя на vzroslym ---"; grep -o "view-transition-name:adult-panel" dist/vzroslym/index.html | head -1
echo "--- имя на detyam ---"; grep -o "view-transition-name:kid-panel" dist/detyam/index.html | head -1
```
Ожидается: `@view-transition` присутствует; на главной есть оба имени панелей; на `/vzroslym` — `adult-panel`, на `/detyam` — `kid-panel`. Имена должны совпадать дословно, иначе морфа не будет и переход тихо станет обычным кросс-фейдом.

- [ ] **Step 6: Commit**

```bash
git add site/src/styles/global.css site/src/components/AudienceSplit.astro site/src/components/SiteHeader.astro site/src/pages/vzroslym.astro site/src/pages/detyam.astro
git commit -m "feat: cross-document view transitions — panel morphs into section intro"
```

---

### Task 2: Возврат на главную с раздела

**Что и зачем.** Заказчик просил при обсуждении шторок, чтобы «всегда можно было вернуться». Ссылка на главную есть в шапке (логотип), но она не читается как «назад» — это переход по бренду, а не по иерархии. Добавляется явная короткая ссылка в начале цветной intro-секции обоих разделов.

Ссылка ставится внутрь именованного элемента перехода, поэтому уезжает вместе с ним и не создаёт отдельной анимации.

**Files:**
- Modify: `site/src/pages/vzroslym.astro`
- Modify: `site/src/pages/detyam.astro`
- Modify: `site/src/styles/global.css`

- [ ] **Step 1: Общий стиль ссылки**

Добавить в `site/src/styles/global.css`:
```css
/* Возврат на главную с раздела. Цвет наследуется от регистра страницы,
   поэтому одна и та же ссылка уместна и в оливковом, и в охристом контуре. */
.back-home {
  display: inline-block;
  font-size: var(--text-small);
  color: inherit;
  opacity: .75;
  text-decoration: none;
  margin-bottom: var(--space-3);
}
.back-home:hover { opacity: 1; text-decoration: underline; }
```

- [ ] **Step 2: Вставить ссылку в оба раздела**

В `site/src/pages/vzroslym.astro` и `site/src/pages/detyam.astro` внутри `<div class="intro-text">` первой строкой, перед `<h1>`:
```astro
      <a class="back-home" href="/">← На главную</a>
```

- [ ] **Step 3: Проверить**

```bash
cd site && npm run build && npm run check
grep -o 'class="back-home" href="/"' dist/vzroslym/index.html dist/detyam/index.html
```
Ожидается: ссылка на обеих страницах.

- [ ] **Step 4: Commit**

```bash
git add site/src/pages/vzroslym.astro site/src/pages/detyam.astro site/src/styles/global.css
git commit -m "feat: explicit back-to-home link on section pages"
```

---

### Task 3: Зафиксировать проверку

**Files:**
- Modify: `site/docs/manual-verification-checklist.md`

- [ ] **Step 1: Дописать секцию** «Результаты прохода: переход-шторка (дата)»: что подтверждено статически (сборка, проверка типов, наличие `@view-transition`, совпадение имён на обеих сторонах, ссылка возврата, отсутствие своего JS), и что принципиально требует браузера — сам морф, его скорость, поведение при возврате назад, отсутствие моргания шапки, и корректная деградация в Firefox до обычной навигации.

Отдельно отметить: это единственный из трёх циклов, где статическая проверка почти ничего не доказывает — переход существует только в рантайме. Все прошлые циклы можно было проверить по разметке, этот нельзя.

- [ ] **Step 2: Commit и push**

```bash
git add site/docs/manual-verification-checklist.md
git commit -m "docs: verification pass for curtain transition"
git push origin main
```

---

## Что дальше

Все три цикла пересмотра визуала закрыты. Осталось внешнее ограничение из спеки — реальные фотографии: слоты под них готовы во всех компонентах (`PhotoPlaceholder` принимает `src`), разметка при подстановке не меняется. Дальше — либо наполнение оставшихся трёх страниц-заглушек (`/master-klassy`, `/vitrina`, `/kontakty`), либо подстановка фотографий по размеченному `photos.tsv`.
