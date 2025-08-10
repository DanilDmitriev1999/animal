-- AICODE-NOTE: Minimal seed data for local development
BEGIN;

-- Guest user bound to device id (replace on client if needed)
INSERT INTO users (device_id, name)
VALUES ('dev-device', 'Guest')
ON CONFLICT (device_id) DO NOTHING;

-- Single example track: Product Manager for AI Products
INSERT INTO tracks (slug, title, description, goal)
VALUES
  (
    'product-manager-ai-products',
    'Product Manager AI продуктов',
    'Практический курс о том, как продакт-менеджеру создавать и развивать AI‑продукты: от постановки ценности и гипотез до запуска MVP, экспериментов с LLM и метрик качества.',
    'Сформировать практические навыки продакт‑менеджмента для AI‑продуктов и собрать первый рабочий MVP.'
  )
ON CONFLICT (slug) DO NOTHING;

-- Roadmap items for Product Manager AI track
WITH t AS (
  SELECT id FROM tracks WHERE slug = 'product-manager-ai-products'
)
INSERT INTO track_roadmap_items (track_id, position, text, done)
SELECT t.id, x.pos, x.text, x.done
FROM t, (VALUES
  (1, 'Роль PM в AI‑продуктах и кейсы', TRUE),
  (2, 'Ценности, JTBD и гипотезы для AI‑фич', TRUE),
  (3, 'Данные и модели: что важно знать PM', FALSE),
  (4, 'Дискавери с LLM: прототипирование и промпт‑инжиниринг', FALSE),
  (5, 'Метрики качества (offline/online), риски и этика', FALSE),
  (6, 'MVP и запуск: план экспериментов и аналитика', FALSE)
) AS x(pos, text, done)
ON CONFLICT DO NOTHING;

-- Global default chat template
INSERT INTO chat_templates (scope, version, content)
VALUES ('global', 'v1', 'You are an AI learning mentor. Keep responses concise and actionable.')
ON CONFLICT DO NOTHING;

COMMIT;


