-- B-tree индекс пользователя по юзернейму (часто используется в WHERE, точный поиск)
CREATE INDEX idx_users_username ON users (username);

-- GIN индекс по полю comment (для полнотекстового поиска)
CREATE INDEX idx_reviews_comment_gin ON reviews
USING GIN (to_tsvector('russian', comment));

-- BRIN индекс по дате отзыва (для ускорения диапазонных запросов по дате)
CREATE INDEX idx_orders_order_date_brin ON orders
USING BRIN (order_date);