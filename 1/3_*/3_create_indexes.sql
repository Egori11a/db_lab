-- Создаем индекс для быстрого поиска по name в таблице products
CREATE INDEX trgm_idx_products_name ON products USING gin (name gin_trgm_ops);
-- Индекс для поиска по имени пользователей
CREATE INDEX trgm_idx_users_username ON users USING gin (username gin_trgm_ops);

-- Создаем индекс для поиска по биграммам для поля name в таблице products
--CREATE INDEX bigm_idx_products_name ON products USING gin (name gin_bigm_ops);

-- Обновляем таблицу users, чтобы хранить хешированные пароли
UPDATE users
SET hashed_password = pgp_sym_encrypt(hashed_password, 'encryption_key');