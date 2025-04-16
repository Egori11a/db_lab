-- Поиск пользователя по юзернейму
EXPLAIN ANALYZE
SELECT *
FROM users
WHERE username = 'john_doe';

-- Поиск комментария
EXPLAIN ANALYZE
SELECT * FROM reviews
WHERE to_tsvector('russian', comment) @@ plainto_tsquery('russian', 'качественный товар');

-- Поиск по дате
EXPLAIN ANALYZE
SELECT * FROM orders
WHERE order_date >= '2024-01-01' AND order_date < '2025-01-01';
