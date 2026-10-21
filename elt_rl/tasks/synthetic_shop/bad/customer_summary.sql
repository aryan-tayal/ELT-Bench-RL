SELECT
    c.customer_id,
    c.name,
    count(o.order_id) AS num_orders,
    sum(o.amount) AS total_amount
FROM synthetic_shop.customers c
LEFT JOIN synthetic_shop.orders o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name