# Sunny Tabbies

```
sunnytabbies/
├── site/
│   ├── index.html
│   ├── src/
│   │   ├── main.js              # entry point
│   │   ├── gallery/
│   │   │   └── gallery.js
│   │   └── utils/
│   │       └── kittens.js
│   ├── assets/
│   │   └── kittens/
│   └── style.css
├── backend/                     # optional future FastAPI
└── .gitignore
```

# Sunny Tabbies — Gallery Stage Mapping

This project groups all photos and videos into **four storytelling stages** based on
their development and behavior:

1. **first_moves** — Early coordination, first play, tiny world.
2. **each_other** — Sibling bonding, wrestling, pair/trio dynamics.
3. **big_big_world** — Exploring rooms, hallways, outdoors, new environments.
4. **ready_for_launch** — (Reserved for Week 10–12 content): final portraits, confident solo moments.

For all current media, the following **week-to-stage mapping** is used:

## Week → Stage

| Folder name                                         | Stage             |
| --------------------------------------------------- | ----------------- |
| `week_4_oct_05_to_oct_11_crawling`                  | `first_moves`     |
| `week_5_oct_12_to_oct_18_socialization`             | `first_moves`     |
| `week_6_oct_19_to_oct_25_exploration`               | `each_other`      |
| `week_7_oct_26_to_nov_01_meet_outside`              | `big_big_world`   |
| `week_8_nov_02_to_nov_08_personalities`             | `big_big_world`   |
| `week_9_nov_09_to_nov_15_personalities`             | `big_big_world`   |
| `week_9_nov_09_to_nov_15_personalities`             | `big_big_world`   |
| `week_10_nov_16_to_nov_22_personalities`            | `big_big_world`   |
| `week_11_nov_23_to_nov_29_personalities`            | `big_big_world`   |
| `week_12_nov_30_to_dec_06_ready_for_new_homes`      | `ready_for_launch`|
| `week_13_dec_07_to_dec_13_ready_for_new_homes`      | `ready_for_launch`|
| `week_14_dec_14_to_dec_20_ready_for_new_homes`      | `ready_for_launch`|
| ...                                                 | `ready_for_launch`|

## JSON Structure

Each media item in `kittens.json` includes a `stage` field:

```json
{
  "type": "image",
  "stage": "big_big_world",
  "thumb": "https://.../thumb.jpg",
  "full": "https://.../full.jpg",
  "title": "Week 7: On top of carrier — Chandler Pond",
  "alt": "Kitten looks pensively on top of the carrier",
  "stage": "first_moves"
}


````md
# YouTube-Style Stage Jump Navigation (In-Page Tabs)

This project adds a **YouTube-style horizontal stage navigation bar** to a long, vertically scrollable media feed.

The bar is:
- **In-page anchor navigation** (jump/shortcut), not filtering/pagination.
- **Mobile swipeable** (horizontal scroll), while the main page remains a **continuous vertical scroll**.

---

## Goal

Improve navigation of a long gallery by letting users **jump directly to each stage section** (older/newer stages) without hiding or reordering content.

---

## What We Built

### 1) HTML Mount Point (Sticky Wrapper + Inner Container)

We created a full-width sticky wrapper with a normal-width inner container:

```html
<!-- Stage jump nav (JS builds tabs from existing stage sections) -->
<section id="stage-nav" class="stage-nav-wrap">
  <div class="container" id="stage-nav-inner"></div>
</section>
````

This gives us:

* a **full-width background** and sticky behavior (`.stage-nav-wrap`)
* a centered content area (`#stage-nav-inner`) aligned with the rest of the site

---

### 2) Stage Sections (Source of Truth)

Stages already exist on the page as:

```html
<section class="gallery-stage" data-stage="first_moves">...</section>
<section class="gallery-stage" data-stage="each_other">...</section>
...
```

Each stage contains a grid with a stable id:

```html
<div class="gallery-grid" id="stage-first_moves"></div>
```

We treat these sections as the canonical list of stages — **no hard-coded stage list**.

---

### 3) JavaScript: Build Tabs Automatically + Smooth Scroll

We generate tabs at runtime by scanning:

* `section.gallery-stage[data-stage]` for stage keys and labels
* `h2` inside each stage section for the user-visible tab text

We then attach click handlers that do:

* `scrollIntoView({ behavior: "smooth" })`
* **Prefer scrolling the stage section** so the heading is visible

**Important:** We mount into `#stage-nav-inner`:

```js
function buildStageNav() {
  const mount = document.getElementById("stage-nav-inner");
  if (!mount) return;

  const stageSections = Array.from(
    document.querySelectorAll("section.gallery-stage[data-stage]")
  );
  if (!stageSections.length) return;

  const nav = document.createElement("div");
  nav.className = "stage-nav";

  stageSections.forEach((sec) => {
    const stageKey = (sec.getAttribute("data-stage") || "").trim();
    if (!stageKey) return;

    const gridEl = document.getElementById(`stage-${stageKey}`);
    const toScroll = (gridEl && gridEl.closest("section.gallery-stage")) || sec;

    const label = (sec.querySelector("h2")?.textContent || stageKey).trim();

    const btn = document.createElement("button");
    btn.className = "stage-tab";
    btn.type = "button";
    btn.textContent = label;

    btn.addEventListener("click", () => {
      toScroll.scrollIntoView({ behavior: "smooth", block: "start" });
    });

    nav.appendChild(btn);
  });

  mount.innerHTML = "";
  mount.appendChild(nav);
}
```

We call `buildStageNav()` **after the gallery is rendered**, inside `DOMContentLoaded`, so stage DOM is present.

---

# CSS: Tabs + Sticky Behavior

## Horizontal Tabs (Swipeable on Mobile)

```css
.stage-nav {
  display: flex;
  gap: 10px;
  overflow-x: auto;                 /* horizontal swipe */
  -webkit-overflow-scrolling: touch; /* smooth iOS */
  scrollbar-width: none;            /* Firefox hide */
  padding: 8px 4px;
}

.stage-nav::-webkit-scrollbar {
  display: none; /* Chrome/Safari hide */
}

.stage-tab {
  flex: 0 0 auto;   /* single row, no wrapping */
  white-space: nowrap;
  border-radius: 999px;
  padding: 8px 12px;
}
```

## Sticky Wrapper

```css
.stage-nav-wrap {
  position: sticky;
  top: 0;
  z-index: 1000;
  background: var(--bg, #fff);
  box-shadow: 0 8px 20px rgba(0,0,0,.06);
  margin: 0;
}

/* avoid `.container` vertical margins affecting the sticky area */
#stage-nav-inner {
  margin-top: 0 !important;
  margin-bottom: 0 !important;
  padding-top: 6px;
  padding-bottom: 6px;
}
```

## Prevent “scroll-to” landing behind the sticky bar

```css
.gallery-stage {
  scroll-margin-top: 90px;
}
```

---

## Overflow Principles (Why Sticky Initially Failed)

### Sticky depends on the scrolling/overflow context

`position: sticky` works relative to its nearest scrolling ancestor. If an ancestor creates an overflow/scroll container (often via `overflow: hidden/auto/scroll`), sticky can stop behaving like “stick to viewport”.

### The specific issue we hit

We originally had:

```css
html, body { overflow-x: hidden; }
```

Even though it’s only `overflow-x`, some browsers treat this as creating an overflow context that interferes with sticky.

### Proof and diagnosis

Adding:

```css
html, body, .container { overflow: visible !important; }
```

made sticky work, confirming overflow context was the culprit.

### The correct long-term approach

* Avoid creating overflow contexts on page roots when using sticky.
* If you must prevent sideways scrolling, prefer modern approaches that don’t break sticky.

(Implementation choice depends on browser support; we used the scoped fixes around the sticky bar and removed/avoided global overflow rules that disabled sticky.)

---

## Final Behavior

✅ Horizontal stage tabs appear near the top
✅ Tabs are swipeable on mobile (single row, no wrap)
✅ Clicking a tab smooth-scrolls to the correct stage section
✅ Vertical scrolling remains continuous (no filtering / pagination)
✅ Nav can remain visible while scrolling (sticky)
✅ Stages/tabs are generated automatically from existing sections

---

## Non-Goals (Explicit)

* No dropdown menus
* No pagination
* No filtering/hiding content
* No reactive framework
* No backend changes

```
```
