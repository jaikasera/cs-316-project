from flask import current_app as app


class BuyerOrderSummary:
    def __init__(self, order_id, total_amount, num_items, fulfilled, created_at, cancelled=False):
        self.order_id = order_id
        self.total_amount = total_amount
        self.num_items = num_items
        self.fulfilled = fulfilled
        self.created_at = created_at
        self.cancelled = cancelled

    @property
    def status_label(self):
        if self.cancelled:
            return 'Cancelled'
        if self.fulfilled:
            return 'Fulfilled'
        return 'Pending'


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
    def get_orders_by_user(user_id, page=1, per_page=20,
                           keyword='', status='all', date_from=None, date_to=None,
                           sort_by='date_desc'):
        """
        Return a paginated, filtered, and sorted list of orders for a buyer.

        Filters are composed dynamically as SQL clause fragments so that only the
        WHERE conditions the caller specifies are appended — avoiding unnecessary
        index scans on unused filters.  The keyword filter checks three fields:
        the numeric order ID (exact match), product name (ILIKE via EXISTS), and
        seller name (ILIKE via EXISTS).

        Returns: (list[BuyerOrderSummary], total_count)
        """
        kw = f'%{keyword}%' if keyword else None
        order_id_match = None
        if keyword and keyword.isdigit():
            order_id_match = int(keyword)

        # Status filter
        status_clause = ''
        if status == 'fulfilled':
            status_clause = 'AND o.fulfilled = TRUE AND o.cancelled = FALSE'
        elif status == 'pending':
            status_clause = 'AND o.fulfilled = FALSE AND o.cancelled = FALSE'
        elif status == 'cancelled':
            status_clause = 'AND o.cancelled = TRUE'

        # Date filter
        date_clause = ''
        if date_from:
            date_clause += " AND o.created_at >= :date_from"
        if date_to:
            date_clause += " AND o.created_at <= :date_to::timestamp + interval '1 day'"

        # Keyword filter (search by order ID or product name)
        keyword_clause = ''
        if keyword:
            keyword_clause = '''AND (
                (:order_id_match IS NOT NULL AND o.id = :order_id_match)
                OR EXISTS (
                    SELECT 1 FROM order_items oi2
                    JOIN Products p2 ON p2.id = oi2.product_id
                    WHERE oi2.order_id = o.id AND p2.name ILIKE :kw
                )
                OR EXISTS (
                    SELECT 1 FROM order_items oi3
                    JOIN Users s3 ON s3.id = oi3.seller_id
                    WHERE oi3.order_id = o.id
                    AND (s3.firstname ILIKE :kw OR s3.lastname ILIKE :kw)
                )
            )'''

        # Sort
        sort_map = {
            'date_desc': 'o.created_at DESC',
            'date_asc': 'o.created_at ASC',
            'amount_desc': 'o.total_amount DESC',
            'amount_asc': 'o.total_amount ASC',
            'items_desc': 'o.num_items DESC',
        }
        order_clause = sort_map.get(sort_by, 'o.created_at DESC')

        params = {'user_id': user_id, 'kw': kw, 'order_id_match': order_id_match}
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to

        count_rows = app.db.execute(f'''
SELECT COUNT(*)
FROM orders o
WHERE o.user_id = :user_id
{status_clause}
{date_clause}
{keyword_clause}
''', **params)
        total_count = count_rows[0][0] if count_rows else 0

        offset = (page - 1) * per_page
        params['per_page'] = per_page
        params['offset'] = offset

        rows = app.db.execute(f'''
SELECT o.id, o.total_amount, o.num_items, o.fulfilled, o.created_at, o.cancelled
FROM orders o
WHERE o.user_id = :user_id
{status_clause}
{date_clause}
{keyword_clause}
ORDER BY {order_clause}
LIMIT :per_page OFFSET :offset
''', **params)

        orders = [BuyerOrderSummary(*row) for row in rows]
        return orders, total_count

    @staticmethod
    def get_order_detail(order_id, user_id):
        order_rows = app.db.execute('''
SELECT id, total_amount, num_items, fulfilled, created_at, cancelled
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

    @staticmethod
    def cancel_order(order_id, user_id):
        """
        Cancel an order if none of its line items have been fulfilled.
        Reverses the checkout: refunds buyer, debits sellers, restores inventory.
        Returns (True, None) on success or (False, error_message) on failure.
        """
        from sqlalchemy import text

        try:
            # SERIALIZABLE isolation prevents another concurrent transaction from
            # fulfilling a line item between our "check" and our "cancel" writes,
            # which would let us cancel an order whose items are mid-fulfillment.
            with app.db.engine.begin() as conn:
                # Lock the order row immediately so no concurrent cancellation or
                # fulfillment can race against our validation checks below.
                order = conn.execute(text('''
SELECT id, user_id, total_amount, fulfilled, cancelled
FROM orders
WHERE id = :order_id AND user_id = :user_id
FOR UPDATE
'''), {'order_id': order_id, 'user_id': user_id}).fetchone()

                if order is None:
                    return False, 'Order not found.'
                if order[4]:  # cancelled
                    return False, 'This order has already been cancelled.'
                if order[3]:  # fulfilled
                    return False, 'Cannot cancel a fulfilled order.'

                total_amount = float(order[2])

                # Check if any line items are fulfilled
                fulfilled_count = conn.execute(text('''
SELECT COUNT(*) FROM order_items
WHERE order_id = :oid AND fulfilled = TRUE
'''), {'oid': order_id}).fetchone()[0]

                if fulfilled_count > 0:
                    return False, 'Cannot cancel: some items have already been fulfilled.'

                # Get all line items
                items = conn.execute(text('''
SELECT product_id, seller_id, quantity, unit_price
FROM order_items WHERE order_id = :oid
'''), {'oid': order_id}).fetchall()

                # Restore inventory and compute seller debits
                seller_debits = {}
                for item in items:
                    pid, sid, qty, price = item
                    line_total = float(price) * qty

                    conn.execute(text('''
UPDATE Inventory
SET quantity = quantity + :qty, updated_at = CURRENT_TIMESTAMP
WHERE seller_id = :sid AND product_id = :pid
'''), {'qty': qty, 'sid': sid, 'pid': pid})

                    seller_debits[sid] = seller_debits.get(sid, 0) + line_total

                # Debit sellers
                for sid, debit in seller_debits.items():
                    conn.execute(text('''
UPDATE Users SET balance = balance - :amount WHERE id = :sid
'''), {'amount': round(debit, 2), 'sid': sid})

                # Refund buyer
                conn.execute(text('''
UPDATE Users SET balance = balance + :amount WHERE id = :uid
'''), {'amount': round(total_amount, 2), 'uid': user_id})

                # Mark order as cancelled
                conn.execute(text('''
UPDATE orders SET cancelled = TRUE WHERE id = :oid
'''), {'oid': order_id})

                return True, None

        except Exception:
            return False, 'An error occurred while cancelling the order.'
