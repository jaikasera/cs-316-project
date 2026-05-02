from flask import current_app as app


class SellerPortalAnalytics:
    """
    Sellers Portal metrics: products that appear in this seller's inventory OR
    have been sold by this seller (non-cancelled orders only). Aggregates are
    scoped to order_items where this user is the seller.
    """

    @staticmethod
    def get_summary(seller_id: int):
        rows = app.db.execute('''
SELECT
    COALESCE(SUM(oi.quantity), 0) AS total_units,
    COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total_revenue,
    COUNT(DISTINCT oi.order_id) AS order_count
FROM order_items oi
JOIN orders o ON o.id = oi.order_id AND o.cancelled = FALSE
WHERE oi.seller_id = :seller_id
''', seller_id=seller_id)
        row = rows[0]
        return {
            'total_units': int(row[0] or 0),
            'total_revenue': round(float(row[1] or 0), 2),
            'order_count': int(row[2] or 0),
        }

    @staticmethod
    def get_sales_by_product(seller_id: int):
        rows = app.db.execute('''
WITH seller_products AS (
    SELECT i.product_id
    FROM Inventory i
    WHERE i.seller_id = :seller_id
    UNION
    SELECT oi.product_id
    FROM order_items oi
    JOIN orders o ON o.id = oi.order_id AND o.cancelled = FALSE
    WHERE oi.seller_id = :seller_id
)
SELECT
    p.id,
    p.name,
    p.available,
    COALESCE(inv.quantity, 0)::int AS stock_on_hand,
    COALESCE(a.units_sold, 0)::bigint AS units_sold,
    COALESCE(a.order_count, 0)::bigint AS order_count,
    COALESCE(a.revenue, 0)::numeric AS revenue,
    COALESCE(a.orders_last_30d, 0)::bigint AS orders_last_30d,
    rev.avg_rating,
    rev.review_count
FROM seller_products sp
JOIN Products p ON p.id = sp.product_id
LEFT JOIN Inventory inv
    ON inv.seller_id = :seller_id AND inv.product_id = p.id
LEFT JOIN (
    SELECT
        oi.product_id,
        SUM(oi.quantity) AS units_sold,
        COUNT(DISTINCT oi.order_id) AS order_count,
        SUM(oi.quantity * oi.unit_price) AS revenue,
        COUNT(DISTINCT CASE
            WHEN o.created_at >= (CURRENT_TIMESTAMP - INTERVAL '30 days')
            THEN oi.order_id
        END) AS orders_last_30d
    FROM order_items oi
    JOIN orders o ON o.id = oi.order_id AND o.cancelled = FALSE
    WHERE oi.seller_id = :seller_id
    GROUP BY oi.product_id
) a ON a.product_id = p.id
LEFT JOIN LATERAL (
    SELECT AVG(pr.rating)::float AS avg_rating,
           COUNT(*)::int AS review_count
    FROM ProductReviews pr
    WHERE pr.product_id = p.id
) rev ON TRUE
ORDER BY COALESCE(a.units_sold, 0) DESC, p.name ASC
''', seller_id=seller_id)

        out = []
        for r in rows:
            avg = r[8]
            rc = r[9]
            out.append({
                'product_id': r[0],
                'name': r[1],
                'available': r[2],
                'stock_on_hand': int(r[3] or 0),
                'units_sold': int(r[4] or 0),
                'order_count': int(r[5] or 0),
                'revenue': round(float(r[6] or 0), 2),
                'orders_last_30d': int(r[7] or 0),
                'avg_rating': round(float(avg), 2) if avg is not None else None,
                'review_count': int(rc or 0),
            })
        return out

    @staticmethod
    def get_monthly_trend(seller_id: int, months: int = 6):
        rows = app.db.execute('''
SELECT
    TO_CHAR(date_trunc('month', o.created_at), 'YYYY-MM') AS ym,
    TO_CHAR(date_trunc('month', o.created_at), 'Mon YYYY') AS label,
    SUM(oi.quantity)::int AS units,
    SUM(oi.quantity * oi.unit_price)::numeric AS revenue
FROM order_items oi
JOIN orders o ON o.id = oi.order_id AND o.cancelled = FALSE
WHERE oi.seller_id = :seller_id
GROUP BY 1, 2
ORDER BY ym DESC
LIMIT :months
''', seller_id=seller_id, months=months)
        items = [
            {
                'ym': r[0],
                'label': r[1],
                'units': int(r[2] or 0),
                'revenue': round(float(r[3] or 0), 2),
            }
            for r in rows
        ]
        items.reverse()
        return items
