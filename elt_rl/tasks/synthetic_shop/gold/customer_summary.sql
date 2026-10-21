WITH completed AS (
    SELECT customer_id, count(*) AS n, sum(amount) AS total
    FROM synthetic_shop.orders
    WHERE status = 'completed'
    GROUP BY customer_id
),
refunded AS (
    SELECT DISTINCT o.customer_id
    FROM synthetic_shop.refunds r
    JOIN synthetic_shop.orders o ON o.order_id = r.order_id
),
base AS (
    SELECT
        c.customer_id,
        c.name,
        coalesce(p.n, 0) AS num_orders,
        coalesce(p.total, 0) AS total_amount,
        CASE WHEN r.customer_id IS NOT NULL THEN 1 ELSE 0 END AS has_refund
    FROM synthetic_shop.customers c
    LEFT JOIN completed p ON p.customer_id = c.customer_id
    LEFT JOIN refunded r ON r.customer_id = c.customer_id
)
SELECT *,
    CASE WHEN total_amount > (SELECT avg(total_amount) FROM base) THEN 1 ELSE 0 END AS above_avg_spend
FROM base