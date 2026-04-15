from flask import current_app as app


class SellerOrderLine:
    def __init__(self, line_id, order_id, product_id, product_name, quantity, unit_price, fulfilled, fulfilled_at):
        self.id = line_id
        self.order_id = order_id
        self.product_id = product_id
        self.product_name = product_name
        self.quantity = quantity
        self.unit_price = unit_price
        self.fulfilled = fulfilled
        self.fulfilled_at = fulfilled_at

    @property
    def line_total(self):
        return float(self.quantity) * float(self.unit_price)


class SellerOrderSummary:
    def __init__(
        self,
        order_id,
        created_at,
        buyer_id,
        buyer_firstname,
        buyer_lastname,
        buyer_email,
        buyer_address,
        seller_subtotal,
        seller_units,
        seller_all_fulfilled,
    ):
        self.order_id = order_id
        self.created_at = created_at
        self.buyer_id = buyer_id
        self.buyer_firstname = buyer_firstname
        self.buyer_lastname = buyer_lastname
        self.buyer_email = buyer_email
        self.buyer_address = buyer_address
        self.seller_subtotal = seller_subtotal
        self.seller_units = seller_units
        self.seller_all_fulfilled = seller_all_fulfilled


class SellerOrder:
    """Orders as seen by one seller (only their order_items; no other sellers' lines)."""

    @staticmethod
    def list_orders_for_seller(
        seller_id: int,
        keyword: str = '',
        status: str = 'all',
        page: int = 1,
        per_page: int = 10,
    ):
        if status not in ('all', 'pending', 'complete'):
            status = 'all'

        kw = f'%{keyword}%' if keyword else None
        order_id_match = None
        if keyword and keyword.isdigit():
            order_id_match = int(keyword)

        if status == 'pending':
            having = 'HAVING NOT BOOL_AND(oi.fulfilled)'
        elif status == 'complete':
            having = 'HAVING BOOL_AND(oi.fulfilled)'
        else:
            having = ''

        count_rows = app.db.execute(f'''
WITH grouped AS (
    SELECT o.id
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.id AND oi.seller_id = :seller_id
    JOIN Users u ON u.id = o.user_id
    WHERE (
        :kw IS NULL
        OR u.firstname ILIKE :kw
        OR u.lastname ILIKE :kw
        OR u.email ILIKE :kw
        OR (:order_id_match IS NOT NULL AND o.id = :order_id_match)
    )
    GROUP BY o.id
    {having}
)
SELECT COUNT(*)
FROM grouped
''', seller_id=seller_id, kw=kw, order_id_match=order_id_match)
        total_count = count_rows[0][0] if count_rows else 0

        offset = (page - 1) * per_page
        rows = app.db.execute(f'''
SELECT
    o.id,
    o.created_at,
    o.user_id,
    u.firstname,
    u.lastname,
    u.email,
    u.address,
    COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS seller_subtotal,
    COALESCE(SUM(oi.quantity), 0) AS seller_units,
    BOOL_AND(oi.fulfilled) AS seller_all_fulfilled
FROM orders o
JOIN order_items oi ON oi.order_id = o.id AND oi.seller_id = :seller_id
JOIN Users u ON u.id = o.user_id
WHERE (
    :kw IS NULL
    OR u.firstname ILIKE :kw
    OR u.lastname ILIKE :kw
    OR u.email ILIKE :kw
    OR (:order_id_match IS NOT NULL AND o.id = :order_id_match)
)
GROUP BY o.id, o.created_at, o.user_id, u.firstname, u.lastname, u.email, u.address
{having}
ORDER BY o.created_at DESC
LIMIT :per_page
OFFSET :offset
''', seller_id=seller_id, kw=kw, order_id_match=order_id_match, per_page=per_page, offset=offset)

        summaries = [
            SellerOrderSummary(
                row[0], row[1], row[2], row[3], row[4], row[5], row[6],
                row[7], row[8], row[9],
            )
            for row in rows
        ]
        return summaries, total_count

    @staticmethod
    def lines_for_orders(seller_id: int, order_ids: list):
        if not order_ids:
            return []
        ids_sql = ','.join(str(int(i)) for i in order_ids)
        rows = app.db.execute(f'''
SELECT
    oi.id,
    oi.order_id,
    oi.product_id,
    p.name,
    oi.quantity,
    oi.unit_price,
    oi.fulfilled,
    oi.fulfilled_at
FROM order_items oi
JOIN Products p ON p.id = oi.product_id
WHERE oi.seller_id = :seller_id AND oi.order_id IN ({ids_sql})
ORDER BY oi.order_id DESC, oi.id ASC
''', seller_id=seller_id)
        return [SellerOrderLine(*row) for row in rows]

    @staticmethod
    def fulfill_line_item(line_id: int, seller_id: int):
        """Mark one line fulfilled. Does not change Inventory (stock was adjusted at checkout)."""
        return app.db.execute('''
UPDATE order_items
SET fulfilled = TRUE, fulfilled_at = CURRENT_TIMESTAMP
WHERE id = :line_id AND seller_id = :seller_id AND fulfilled = FALSE
''', line_id=line_id, seller_id=seller_id)
