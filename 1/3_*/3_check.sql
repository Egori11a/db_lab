-- pg_trgm индекс используется GIN + gin_trgm_ops
-- поиск с использованием pg_bigm
EXPLAIN ANALYZE
SELECT * FROM products
WHERE name LIKE '%Adaptive zero administration conglomeration%';
