SELECT
    c.country,
    count(DISTINCT c.customer_id) AS num_customers,
    coalesce(sum(o.amount), 0) AS revenue
FROM synthetic_shop.customers c
LEFT JOIN synthetic_shop.orders o
    ON o.customer_id = c.customer_id AND o.status = 'completed'
GROUP BY c.country