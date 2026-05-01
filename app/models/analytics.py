from flask import current_app as app


class OrderAnalytics:

    @staticmethod
    def get_spending_summary(user_id):
        """Returns dict with total_spent, order_count, avg_order_value."""
        rows = app.db.execute('''
SELECT COUNT(*) AS order_count,
       COALESCE(SUM(total_amount), 0) AS total_spent,
       COALESCE(AVG(total_amount), 0) AS avg_order_value
FROM orders
WHERE user_id = :user_id AND cancelled = FALSE
''', user_id=user_id)
        row = rows[0]
        return {
            'order_count': row[0],
            'total_spent': round(float(row[1]), 2),
            'avg_order_value': round(float(row[2]), 2),
        }

    @staticmethod
    def get_monthly_spending(user_id):
        """Returns list of (month_label, total_spent, order_count)."""
        rows = app.db.execute('''
SELECT TO_CHAR(o.created_at, 'YYYY-MM') AS month,
       SUM(o.total_amount) AS total_spent,
       COUNT(*) AS order_count
FROM orders o
WHERE o.user_id = :user_id AND o.cancelled = FALSE
GROUP BY month
ORDER BY month DESC
LIMIT 12
''', user_id=user_id)
        return [{'month': r[0], 'total_spent': round(float(r[1]), 2), 'order_count': r[2]} for r in rows]

    @staticmethod
    def get_top_products(user_id, limit=10):
        """Returns most frequently purchased products."""
        rows = app.db.execute('''
SELECT p.id, p.name, SUM(oi.quantity) AS total_qty,
       SUM(oi.quantity * oi.unit_price) AS total_spent
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN Products p ON p.id = oi.product_id
WHERE o.user_id = :user_id AND o.cancelled = FALSE
GROUP BY p.id, p.name
ORDER BY total_qty DESC
LIMIT :limit
''', user_id=user_id, limit=limit)
        return [{'product_id': r[0], 'name': r[1], 'total_qty': r[2],
                 'total_spent': round(float(r[3]), 2)} for r in rows]

    @staticmethod
    def get_top_sellers(user_id, limit=10):
        """Returns sellers the user has purchased from most."""
        rows = app.db.execute('''
SELECT s.id, s.firstname, s.lastname,
       SUM(oi.quantity) AS total_qty,
       SUM(oi.quantity * oi.unit_price) AS total_spent
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN Users s ON s.id = oi.seller_id
WHERE o.user_id = :user_id AND o.cancelled = FALSE
GROUP BY s.id, s.firstname, s.lastname
ORDER BY total_spent DESC
LIMIT :limit
''', user_id=user_id, limit=limit)
        return [{'seller_id': r[0], 'name': f'{r[1]} {r[2]}', 'total_qty': r[3],
                 'total_spent': round(float(r[4]), 2)} for r in rows]

    @staticmethod
    def get_category_breakdown(user_id):
        """Returns spending breakdown by product category."""
        rows = app.db.execute('''
SELECT c.name AS category,
       SUM(oi.quantity) AS total_qty,
       SUM(oi.quantity * oi.unit_price) AS total_spent
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN Products p ON p.id = oi.product_id
JOIN Categories c ON c.id = p.category_id
WHERE o.user_id = :user_id AND o.cancelled = FALSE
GROUP BY c.name
ORDER BY total_spent DESC
''', user_id=user_id)
        return [{'category': r[0], 'total_qty': r[1],
                 'total_spent': round(float(r[2]), 2)} for r in rows]
