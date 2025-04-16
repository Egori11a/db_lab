-- ГРЯЗНОЕ ЧТЕНИЕ (чтение незафиксированных данных из другой транзакции, которые могут быть отменены)
-- (теоретически при уровне Read Uncommitted)
-- Сессия 1
BEGIN;
UPDATE products SET price = 1000 WHERE product_id = '8149336b-96c9-4d36-9763-5f02900d2d20';
-- Изменили, но НЕ коммитили

-- Сессия 2
BEGIN ISOLATION LEVEL READ UNCOMMITTED;
SELECT price FROM products WHERE product_id = '8149336b-96c9-4d36-9763-5f02900d2d20';
-- В PostgreSQL всё равно увидит старую цену (368.50), не незафиксированную (1000)

-- Сессия 1
ROLLBACK; -- Откатываем изменения


-- НЕВТОРЯЮЩЕЕСЯ ЧТЕНИЕ (получение разных результатов при повторном чтении одних и тех же данных в рамках одной транзакции)
-- Сессия 1
BEGIN ISOLATION LEVEL READ COMMITTED;
SELECT price FROM products WHERE product_id = '8149336b-96c9-4d36-9763-5f02900d2d20';
-- Вернулось 368.50

-- Сессия 2
BEGIN;
UPDATE products SET price = 150 WHERE product_id = '8149336b-96c9-4d36-9763-5f02900d2d20';
COMMIT;

-- Сессия 1
SELECT price FROM products WHERE product_id = '8149336b-96c9-4d36-9763-5f02900d2d20';
-- Теперь вернётся 150 - это и есть non-repeatable read
COMMIT;


-- ФАНТОМНОЕ ЧТЕНИЕ (появление новых строк при повторном выполнении одного и того же запроса)
-- Сессия 1
BEGIN ISOLATION LEVEL READ COMMITTED;
SELECT COUNT(*) 
FROM products p
JOIN categories c ON p.category_id = c.category_id
WHERE c.name = 'Electronics';
-- Вернулось 2

-- Сессия 2
BEGIN;
INSERT INTO products (name, category_id, price, stock, manufacturer)
SELECT 'Headphones', category_id, 149.99, 20, 'Sony'
FROM categories WHERE name = 'Electronics';

COMMIT;

-- Сессия 1
-- Повторный запрос
SELECT COUNT(*) 
FROM products p
JOIN categories c ON p.category_id = c.category_id
WHERE c.name = 'Electronics';
-- Теперь результат изменится (увеличится на 1) - это фантомное чтение
-- В READ COMMITTED новые строки, добавленные другими транзакциями, становятся видимыми

COMMIT;