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


## JSON Structure

Each media item in `kittens.json` includes a `stage` field:

```json
{
  "type": "image",
  "stage": "big_big_world",
  "thumb": "https://.../thumb.jpg",
  "full": "https://.../full.jpg",
  "title": "Week 7: On top of carrier — Chandler Pond",
  "alt": "Kitten looks pensively on top of the carrier"
}
