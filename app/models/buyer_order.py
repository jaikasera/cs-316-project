from flask import current_app as app


class BuyerOrderSummary:
    def __init__(self, order_id, total_amount, num_items, fulfilled, created_at):
        self.order_id = order_id
        self.total_amount = total_amount
        self.num_items = num_items
        self.fulfilled = fulfilled
        self.created_at = created_at


class BuyerOrderLineItem:
    def __init__(self, line_id, product_id, product_name, seller_id,
                 seller_firstname, seller_lastname, quantity, unit_price,
                 fulfilled, fulfilled_at):
        self.id = line_id
        self.product_id = product_id
        self.product_name = product_name
        self.seller_id = seller_id
        self.seller_name = f"{seller_firstname} {seller_lastname}"
        self.quantity = quantity
        self.unit_price = unit_price
        self.fulfilled = fulfilled
        self.fulfilled_at = fulfilled_at

    @property
    def line_total(self):
        return round(float(self.quantity) * float(self.unit_price), 2)


class BuyerOrder:

    @staticmethod
    def get_orders_by_user(user_id, page=1, per_page=20):
        count_rows = app.db.execute('''
SELECT COUNT(*) FROM orders WHERE user_id = :user_id
''', user_id=user_id)
        total_count = count_rows[0][0] if count_rows else 0

        offset = (page - 1) * per_page
        rows = app.db.execute('''
SELECT id, total_amount, num_items, fulfilled, created_at
FROM orders
WHERE user_id = :user_id
ORDER BY created_at DESC
LIMIT :per_page OFFSET :offset
''', user_id=user_id, per_page=per_page, offset=offset)

        orders = [BuyerOrderSummary(*row) for row in rows]
        return orders, total_count

    @staticmethod
    def get_order_detail(order_id, user_id):
        order_rows = app.db.execute('''
SELECT id, total_amount, num_items, fulfilled, created_at
FROM orders
WHERE id = :order_id AND user_id = :user_id
''', order_id=order_id, user_id=user_id)

        if not order_rows:
            return None, []

        order = BuyerOrderSummary(*order_rows[0])

        line_rows = app.db.execute('''
SELECT oi.id, oi.product_id, p.name, oi.seller_id,
       s.firstname, s.lastname,
       oi.quantity, oi.unit_price, oi.fulfilled, oi.fulfilled_at
FROM order_items oi
JOIN Products p ON p.id = oi.product_id
JOIN Users s ON s.id = oi.seller_id
WHERE oi.order_id = :order_id
ORDER BY oi.id ASC
''', order_id=order_id)

        line_items = [BuyerOrderLineItem(*row) for row in line_rows]
        return order, line_items
