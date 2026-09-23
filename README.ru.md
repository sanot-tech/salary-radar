# Vibe Coder Salary Radar — локальная памятка (RU)

> Ежедневный сбор данных об удалённых IT-зарплатах с англоязычных джоб-бордов.
> Главная цель — найти направления, где реально быстро стартовать на пути
> **вайб-кодера** (суперуниверсал: 🏗️ архитектор + 💻 программист + 💼 бизнесмен).
> No-code — это только трамплин; вайб — пункт назначения.

Весь код и README репозитория — на английском. Этот файл — локальная шпаргалка.

## Команды

```bash
env python3 main.py run            # живой запуск (если сеть упадёт — возьмёт фикстуры)
env python3 main.py run --sample   # всегда офлайн (фикстуры data/sample)
env python3 main.py collect        # только сбор в SQLite
env python3 main.py report         # только отчёт (dashboard + csv/json)
env python3 main.py report --tracks agents,prompt   # тумблеры под-треков
env python3 main.py bot --dry      # распечатать vibe-дайджест
# бот шлёт в Telegram, если заданы TG_BOT_TOKEN и TG_CHAT_ID (secrets/gitignored)
```

Зависимостей нет (только стандартная библиотека Python ≥ 3.10).

## Источники (все англоязычные)

| Источник | API | Нужен ключ |
|---|---|---|
| RemoteOK | https://remoteok.com/api | нет |
| Remotive | https://remotive.com/api/remote-jobs | нет |
| Jobicy | https://jobicy.com/api/v2/remote-jobs | нет |
| Arc.dev | https://www.arc.dev/api/public/jobs | нет |
| Himalayas | https://himalayas.app/jobs-api | нет |
| AI Dev Board | https://aidevboard.com/api/v1/jobs | нет |
| NoCodeJobs | https://nocodejobs.org/jobs.json | нет |
| Working Nomads | https://www.workingnomads.com/api/exposed_jobs/ | нет |

Новый источник = запись в `config.SOURCE_CONFIG` + нормализатор в `sources.py` +
фикстура в `data/sample/`. Если источник недоступен — берётся фикстура, пайплайн не падает.

## Vibe под-треки (карточки на дашборде)

| Трек | Эмодзи | Что это |
|---|---|---|
| AI Agents / Automation | 🤖 | n8n, MCP, агентные пайплайны |
| Prompt & AI Interfaces | 🗣️ | промпт-дизайн, RAG, LLM |
| Visual / Low-Code Builders | 🧱 | Bubble, Webflow, Airtable |
| Generative Creative | 🎨 | Midjourney, AI-видео/картинки |
| AI Product (Super-Universal) | 🚀 | архитектор+программист+бизнесмен |

## Тесты

```bash
env python3 -m unittest discover -s tests -v
```

## Автозапуск

В `.github/workflows/daily.yml` пайплайн собирает свежие данные, регенерирует
дашборд и коммитит их `auto-chore: refresh daily report`. Отчёт живёт на
GitHub Pages: https://sanot-tech.github.io/salary-radar/

## Гит-ритуал (важно!)

1. Перед каждым запуском: `git pull --rebase origin main`
2. После правок: `git add -A && git commit -m "..."` 
3. Пуш с ретраем: `git push origin main` (если конфликт — `git pull --rebase` снова)

`activity.yml` пишет ~100+ тикетов/день от owner-email, чтобы зелёный квадратик
был тёмно-зелёным. Токены/секреты в git не кладём.