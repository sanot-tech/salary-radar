# Salary Radar — локальная памятка (RU)

> Ежедневный сбор данных о удалённых IT-зарплатах с англоязычных джоб-бордов.
> Главная цель — найти направления, куда реально войти **без лайвкодинга**
> (QA, аналитик, поддержка, сисадмин, дизайн, продажи, маркетинг).

Весь код и README репозитория — на английском. Этот файл — локальная шпаргалка.

## Команды

```bash
env python3 main.py run            # живой запуск (если сеть упадёт — возьмёт фикстуры)
env python3 main.py run --sample   # всегда офлайн (фикстуры data/sample)
env python3 main.py collect        # только сбор в SQLite
env python3 main.py report         # только отчёт (dashboard + csv/json)
```

Зависимостей нет (только стандартная библиотека Python ≥ 3.10).

## Источники (все англоязычные)

| Источник | API | Нужен ключ |
|---|---|---|
| RemoteOK | https://remoteok.com/api | нет |
| Remotive | https://remotive.com/api/remote-jobs | нет |
| Jobicy | https://jobicy.com/api/v2/remote-jobs | нет |
| Arc.dev | https://www.arc.dev/api/public/jobs | нет |

Новый источник = запись в `config.SOURCE_CONFIG` + нормализатор в `sources.py` +
фикстура в `data/sample/`. Если источник недоступен — берётся фикстура, пайплайн не падает.

## Тесты

```bash
env python3 -m unittest discover -s tests -v
```

## Автозапуск

GitHub Actions (~/.github/workflows/daily.yml): каждый день в 06:00 UTC собирает
данные, перегенерирует дашборд и коммитит изменения в репозиторий
(`auto-chore: refresh daily report`). Репо приватное.

## Как читать результат

- `outputs/index.html` — дашборд: медианы зарплат по ролям, колонка **no-code**,
  свежие вакансии, тренд за 14 дней.
- `outputs/jobs.csv` — полный датасет.
- В дашборде колонка ✓ (no-code) = роль достижима без лайвкодинга — цель поиска.

## Правила проекта

- Код, комментарии, README.md, коммиты — на английском (репо).
- README.ru.md и заметки — на русском (локально).
- Никаких секретов в git.