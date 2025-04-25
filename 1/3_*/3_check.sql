CREATE EXTENSION IF NOT EXISTS pg_trgm;

INSERT INTO users (username, email) VALUES
    ('john_doe', 'john@example.com'),             -- короткое
    ('jon_doe', 'jon@example.com'),               -- похожее на 'john_doe'
    ('longusernameuser12345', 'long@example.com'), -- длинное
    ('johndoe123456789', 'johndoe123456789@example.com'), -- очень длинное
    ('janet', 'janet@example.com'),               -- короткое, но другое
    ('completelydifferentusername', 'completelydifferent@example.com'); -- сильно отличающееся

INSERT INTO products (name, description) VALUES
    ('Apple iPhone 14', 'Latest iPhone model with A15 chip'), -- короткое
    ('iPhone 14 Pro Max', 'Pro Max version with enhanced camera'), -- похожее
    ('Samsung Galaxy S23', 'Flagship phone with AMOLED display'), -- среднее
    ('OnePlus 9 Pro', 'Premium smartphone with OxygenOS'), -- похожее
    ('VeryVeryLongProductNameToTestBigmAndTrgmMatching', 'Extremely long name to test large data'); -- длинное

-- Создаём индексы для `pg_trgm`
CREATE INDEX IF NOT EXISTS idx_users_username_trgm ON users USING gin (username gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_products_name_trgm ON products USING gin (name gin_trgm_ops);

-- Тесты для малых, средних и больших строк, похожих и непохожих

-- Тест 1: Короткие строки
EXPLAIN ANALYZE
SELECT username FROM users WHERE username % 'john_doe';

-- Тест 2: Средние строки
EXPLAIN ANALYZE
SELECT name FROM products WHERE name % 'iPhone 14';

-- Тест 3: Длинные строки
EXPLAIN ANALYZE
SELECT name FROM products WHERE name % 'VeryVeryLongProductNameToTestBigmAndTrgmMatching';

-- Тест 4: Очень похожие строки
EXPLAIN ANALYZE
SELECT username FROM users WHERE username % 'jon_doe';

-- Тест 5: Непохожие строки
EXPLAIN ANALYZE
SELECT username FROM users WHERE username % 'completelydifferentusername';

-- Поиск похожих значений: john_doe и jon_doe (pg_trgm)
SELECT username, similarity(username, 'john_doe') AS sim
FROM users
WHERE username % 'john_doe'
ORDER BY sim DESC
LIMIT 5;

-- Поиск непохожих значений: completelydifferentusername (pg_trgm)
SELECT username, similarity(username, 'completelydifferentusername') AS sim
FROM users
WHERE username % 'completelydifferentusername'
ORDER BY sim DESC
LIMIT 5;

-- Удаляем индексы для `pg_trgm`
DROP INDEX IF EXISTS idx_users_username_trgm;
DROP INDEX IF EXISTS idx_products_name_trgm;

-- Создаём индексы для `pg_bigm`
CREATE INDEX IF NOT EXISTS idx_users_username_bigm ON users USING gin (username gin_bigm_ops);
CREATE INDEX IF NOT EXISTS idx_products_name_bigm ON products USING gin (name gin_bigm_ops);

-- Тесты для `pg_bigm` (аналогичные запросы)
-- Тест 1: Короткие строки (похожее)
EXPLAIN ANALYZE
SELECT username FROM users WHERE username % 'john_doe';

-- Тест 2: Средние строки (похожее)
EXPLAIN ANALYZE
SELECT name FROM products WHERE name % 'iPhone 14';

-- Тест 3: Длинные строки (похожее)
EXPLAIN ANALYZE
SELECT name FROM products WHERE name % 'VeryVeryLongProductNameToTestBigmAndTrgmMatching';

-- Тест 4: Очень похожие строки (непохожие)
EXPLAIN ANALYZE
SELECT username FROM users WHERE username % 'jon_doe';

-- Тест 5: Непохожие строки
EXPLAIN ANALYZE
SELECT username FROM users WHERE username % 'completelydifferentusername';

-- Поиск похожих значений: john_doe и jon_doe (pg_bigm)
SELECT username, similarity(username, 'john_doe') AS sim
FROM users
WHERE username % 'john_doe'
ORDER BY sim DESC
LIMIT 5;

-- Поиск непохожих значений: completelydifferentusername (pg_bigm)
SELECT username, similarity(username, 'completelydifferentusername') AS sim
FROM users
WHERE username % 'completelydifferentusername'
ORDER BY sim DESC
LIMIT 5;
