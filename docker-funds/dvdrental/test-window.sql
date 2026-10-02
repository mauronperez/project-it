--1. 

SELECT
    film_id,
    title,
    rating,
    length,
    ROW_NUMBER() OVER (PARTITION BY rating ORDER BY length DESC) AS nro_en_rating
FROM public.film;

--2. 
WITH ranked AS (
    SELECT
        title,
        rating,
        length,
        ROW_NUMBER() OVER (PARTITION BY rating ORDER BY length DESC, title) AS rn
    FROM public.film
)
SELECT title, rating, length
FROM ranked
WHERE rn <= 3
ORDER BY rating, rn;

--3. 
SELECT
    film_id,
    title,
    replacement_cost,
    SUM(replacement_cost) OVER (ORDER BY film_id) AS costo_acumulado
FROM public.film;

--4. 
SELECT
    title,
    rating,
    rental_rate,
    SUM(rental_rate) OVER (PARTITION BY rating) AS total_rating,
    ROUND(100 * rental_rate / SUM(rental_rate) OVER (PARTITION BY rating), 2) AS pct_del_rating
FROM public.film;

--5.
SELECT
    title,
    length,
    LAG(length) OVER (ORDER BY length, film_id) AS length_anterior,
    length - LAG(length) OVER (ORDER BY length, film_id) AS diferencia
FROM public.film;

--6. 
SELECT
    title,
    rental_rate,
    RANK()       OVER (ORDER BY rental_rate DESC) AS rank,
    DENSE_RANK() OVER (ORDER BY rental_rate DESC) AS dense_rank,
    LEAD(title)  OVER (ORDER BY rental_rate DESC, film_id) AS siguiente_pelicula
FROM public.film;