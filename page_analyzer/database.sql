-- Создаем таблицу urls
CREATE TABLE urls(
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(255) NOT NULL,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP
);
