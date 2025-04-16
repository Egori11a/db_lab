                                                             QUERY PLAN                                                             
------------------------------------------------------------------------------------------------------------------------------------
 Bitmap Heap Scan on products  (cost=861.39..1053.94 rows=50 width=242) (actual time=14.018..14.020 rows=1 loops=1)
   Recheck Cond: ((name)::text ~~ '%Adaptive zero administration conglomeration%'::text)
   Heap Blocks: exact=1
   ->  Bitmap Index Scan on trgm_idx_products_name  (cost=0.00..861.38 rows=50 width=0) (actual time=13.572..13.573 rows=1 loops=1)
         Index Cond: ((name)::text ~~ '%Adaptive zero administration conglomeration%'::text)
 Planning Time: 1.857 ms
 Execution Time: 14.144 ms
(7 rows)

                                                             QUERY PLAN                                                              
-------------------------------------------------------------------------------------------------------------------------------------
 Bitmap Heap Scan on products  (cost=1210.75..1403.31 rows=50 width=242) (actual time=19.224..19.226 rows=1 loops=1)
   Recheck Cond: ((name)::text ~~ '%Adaptive zero administration conglomeration%'::text)
   Heap Blocks: exact=1
   ->  Bitmap Index Scan on bigm_idx_products_name  (cost=0.00..1210.74 rows=50 width=0) (actual time=19.207..19.208 rows=1 loops=1)
         Index Cond: ((name)::text ~~ '%Adaptive zero administration conglomeration%'::text)
 Planning Time: 0.684 ms
 Execution Time: 19.353 ms
(7 rows)

### Сравнение запросов с использованием индексов `pg_trgm` и `pg_bigm`

| **Индекс**      | **pg_trgm**                                  | **pg_bigm**                                  |
|-----------------|----------------------------------------------|----------------------------------------------|
| **Тип индекса** | GIN с использованием `gin_trgm_ops`         | GIN с использованием `gin_bigm_ops`          |
| **План запроса** | Bitmap Heap Scan, Bitmap Index Scan (trgm_idx_products_name) | Bitmap Heap Scan, Bitmap Index Scan (bigm_idx_products_name) |
| **Стоимость**   | 861.39..1053.94                              | 1210.75..1403.31                             |
| **Фактическое время** | 14.018..14.020 мс                         | 19.224..19.226 мс                            |
| **Количество строк** | 1                                        | 1                                            |
| **Блоки кучи**  | exact=1                                      | exact=1                                      |
| **Время планирования** | 1.857 мс                                 | 0.684 мс                                     |
| **Время выполнения** | 14.144 мс                                 | 19.353 мс                                    |

### Вывод:
1. **Использование индекса**: В обоих случаях используется GIN-индекс для поиска по подстроке, но с разными операторами: для `pg_trgm` используется `gin_trgm_ops`, а для `pg_bigm` — `gin_bigm_ops`.
2. **Производительность**: Запрос с индексом `pg_trgm` показывает быстрее время выполнения (14.144 мс против 19.353 мс для `pg_bigm`), что может свидетельствовать о том, что для данного типа поиска индекс `pg_trgm` работает более эффективно.
3. **Стоимость**: Запрос с `pg_trgm` имеет более низкую стоимость (861.39 против 1210.75 для `pg_bigm`), что также может быть связано с более быстрым поиском при использовании триграмм.
4. **Время планирования**: Время планирования запроса для `pg_trgm` чуть выше, но это не оказывает значительного влияния на общий результат выполнения запроса.

Таким образом, в данном случае индекс `pg_trgm` продемонстрировал лучшие результаты по времени выполнения и стоимости запроса, чем `pg_bigm`.
