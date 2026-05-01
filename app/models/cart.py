from flask import current_app as app


class CartItem:
    def __init__(self, user_id, product_id, seller_id, product_name,
                 product_image_url, product_available, seller_firstname, seller_lastname,
                 quantity, unit_price, added_at, saved=False, current_price=None,
                 available_stock=None):
        self.user_id = user_id
        self.product_id = product_id
        self.seller_id = seller_id
        self.product_name = product_name
        self.product_image_url = product_image_url
        self.product_available = product_available
        self.seller_name = f"{seller_firstname} {seller_lastname}"
        self.quantity = quantity
        self.unit_price = unit_price
        self.added_at = added_at
        self.saved = saved
        self.current_price = current_price
        self.available_stock = available_stock
        self.line_total = round(float(unit_price) * quantity, 2)

    @property
    def price_changed(self):
        if self.current_price is None:
            return False
        return round(float(self.current_price), 2) != round(float(self.unit_price), 2)

    @property
    def out_of_stock(self):
        return self.available_stock is not None and self.available_stock <= 0

    @property
    def insufficient_stock(self):
        return self.available_stock is not None and self.quantity > self.available_stock

    @staticmethod
    def get_items_by_user(user_id, saved=False):
        rows = app.db.execute('''
SELECT c.user_id, c.product_id, c.seller_id,
       p.name AS product_name,
       p.image_url,
       p.available,
       s.firstname AS seller_firstname,
       s.lastname AS seller_lastname,
       c.quantity, c.unit_price, c.added_at,
       c.saved,
       i.price AS current_price,
       COALESCE(i.quantity, 0) AS available_stock
FROM cart_items c
JOIN Products p ON p.id = c.product_id
JOIN Users s ON s.id = c.seller_id
LEFT JOIN Inventory i ON i.product_id = c.product_id AND i.seller_id = c.seller_id
WHERE c.user_id = :user_id AND c.saved = :saved
ORDER BY c.added_at DESC
''', user_id=user_id, saved=saved)

        return [CartItem(*row) for row in rows]

    @staticmethod
    def get_hud_totals(user_id):
        rows = app.db.execute('''
SELECT
    COALESCE(SUM(quantity), 0) AS item_count,
    COALESCE(SUM(quantity * unit_price), 0) AS subtotal
FROM cart_items
WHERE user_id = :user_id AND saved = FALSE
''', user_id=user_id)
        if not rows:
            return 0, 0.0
        return int(rows[0][0] or 0), float(rows[0][1] or 0.0)

    @staticmethod
    def get_inventory_snapshot(product_id, seller_id):
        rows = app.db.execute('''
SELECT p.available, p.name, i.quantity, i.price, u.firstname, u.lastname
FROM Inventory i
JOIN Products p ON p.id = i.product_id
JOIN Users u ON u.id = i.seller_id
WHERE i.product_id = :product_id AND i.seller_id = :seller_id
''', product_id=product_id, seller_id=seller_id)
        return rows[0] if rows else None

    @staticmethod
    def get_inventory_snapshots(product_seller_pairs):
        if not product_seller_pairs:
            return {}

        unique_pairs = []
        seen = set()
        for product_id, seller_id in product_seller_pairs:
            key = (int(product_id), int(seller_id))
            if key not in seen:
                seen.add(key)
                unique_pairs.append(key)

        clauses = []
        params = {}
        for index, (product_id, seller_id) in enumerate(unique_pairs):
            pid_key = f'pid_{index}'
            sid_key = f'sid_{index}'
            clauses.append(f'(i.product_id = :{pid_key} AND i.seller_id = :{sid_key})')
            params[pid_key] = product_id
            params[sid_key] = seller_id

        rows = app.db.execute(f'''
SELECT i.product_id, i.seller_id, p.available, p.name, i.quantity, i.price, u.firstname, u.lastname
FROM Inventory i
JOIN Products p ON p.id = i.product_id
JOIN Users u ON u.id = i.seller_id
WHERE {' OR '.join(clauses)}
''', **params)

        snapshots = {}
        for row in rows:
            snapshots[(row[0], row[1])] = row[2:]
        return snapshots

    @staticmethod
    def get_item_quantity(user_id, product_id, seller_id):
        rows = app.db.execute('''
SELECT quantity
FROM cart_items
WHERE user_id = :user_id AND product_id = :product_id AND seller_id = :seller_id
''', user_id=user_id, product_id=product_id, seller_id=seller_id)
        return rows[0][0] if rows else 0

    @staticmethod
    def add_item(user_id, product_id, seller_id, quantity):
        """
        Adds item to cart. If already exists, increment quantity.
        Uses inventory price at time of adding.
        """
        app.db.execute('''
INSERT INTO cart_items (user_id, product_id, seller_id, quantity, unit_price, saved)
SELECT :user_id, :product_id, :seller_id, :quantity, i.price, FALSE
FROM Inventory i
WHERE i.product_id = :product_id AND i.seller_id = :seller_id

ON CONFLICT (user_id, product_id, seller_id)
DO UPDATE SET
    quantity = cart_items.quantity + EXCLUDED.quantity,
    unit_price = EXCLUDED.unit_price,
    saved = FALSE,
    added_at = CURRENT_TIMESTAMP
''',
        user_id=user_id,
        product_id=product_id,
        seller_id=seller_id,
        quantity=quantity)

    @staticmethod
    def update_quantity(user_id, product_id, seller_id, quantity):
        app.db.execute('''
UPDATE cart_items
SET quantity = :quantity, added_at = CURRENT_TIMESTAMP
WHERE user_id = :user_id AND product_id = :product_id AND seller_id = :seller_id
''', user_id=user_id, product_id=product_id, seller_id=seller_id, quantity=quantity)

    @staticmethod
    def remove_item(user_id, product_id, seller_id):
        app.db.execute('''
DELETE FROM cart_items
WHERE user_id = :user_id AND product_id = :product_id AND seller_id = :seller_id
''', user_id=user_id, product_id=product_id, seller_id=seller_id)

    @staticmethod
    def save_for_later(user_id, product_id, seller_id):
        app.db.execute('''
UPDATE cart_items SET saved = TRUE
WHERE user_id = :user_id AND product_id = :product_id AND seller_id = :seller_id
''', user_id=user_id, product_id=product_id, seller_id=seller_id)

    @staticmethod
    def move_to_cart(user_id, product_id, seller_id):
        app.db.execute('''
UPDATE cart_items SET saved = FALSE
WHERE user_id = :user_id AND product_id = :product_id AND seller_id = :seller_id
''', user_id=user_id, product_id=product_id, seller_id=seller_id)

    @staticmethod
    def update_price(user_id, product_id, seller_id):
        """Update the cart item's unit_price to the current inventory price."""
        app.db.execute('''
UPDATE cart_items
SET unit_price = (SELECT price FROM Inventory WHERE product_id = :product_id AND seller_id = :seller_id)
WHERE user_id = :user_id AND product_id = :product_id AND seller_id = :seller_id
''', user_id=user_id, product_id=product_id, seller_id=seller_id)

    @staticmethod
    def reorder(user_id, order_id):
        """
        Copy items from a previous order back into the cart.
        Uses current inventory prices. Returns (added_count, skipped_items).
        """
        from sqlalchemy import text

        added = 0
        skipped = []

        with app.db.engine.begin() as conn:
            # Verify the order belongs to this user
            order_check = conn.execute(text('''
SELECT id FROM orders WHERE id = :order_id AND user_id = :user_id
'''), {'order_id': order_id, 'user_id': user_id}).fetchone()

            if order_check is None:
                return 0, ['Order not found.']

            items = conn.execute(text('''
SELECT oi.product_id, oi.seller_id, oi.quantity,
       p.name AS product_name,
       i.quantity AS stock, i.price AS current_price,
       p.available
FROM order_items oi
JOIN Products p ON p.id = oi.product_id
LEFT JOIN Inventory i ON i.product_id = oi.product_id AND i.seller_id = oi.seller_id
WHERE oi.order_id = :order_id
'''), {'order_id': order_id}).fetchall()

            for item in items:
                product_id, seller_id, qty, product_name, stock, current_price, available = item
                if stock is None or stock <= 0 or not available or current_price is None:
                    skipped.append(product_name)
                    continue

                actual_qty = min(qty, stock)
                conn.execute(text('''
INSERT INTO cart_items (user_id, product_id, seller_id, quantity, unit_price, saved)
VALUES (:user_id, :product_id, :seller_id, :quantity, :price, FALSE)
ON CONFLICT (user_id, product_id, seller_id)
DO UPDATE SET
    quantity = cart_items.quantity + EXCLUDED.quantity,
    unit_price = EXCLUDED.unit_price,
    saved = FALSE,
    added_at = CURRENT_TIMESTAMP
'''), {'user_id': user_id, 'product_id': product_id, 'seller_id': seller_id,
       'quantity': actual_qty, 'price': float(current_price)})
                added += 1

        return added, skipped

    @staticmethod
    def merge_guest_cart(user_id, guest_cart):
        """
        Merge a guest session cart into the user's persistent DB cart.
        guest_cart is a list of dicts: [{product_id, seller_id, quantity}, ...]
        """
        from sqlalchemy import text

        if not guest_cart:
            return

        with app.db.engine.begin() as conn:
            for item in guest_cart:
                # Get current inventory price
                inv = conn.execute(text('''
SELECT price, quantity FROM Inventory
WHERE product_id = :pid AND seller_id = :sid AND quantity > 0
'''), {'pid': item['product_id'], 'sid': item['seller_id']}).fetchone()

                if inv is None:
                    continue

                price = float(inv[0])
                stock = inv[1]
                qty = min(item['quantity'], stock)
                if qty <= 0:
                    continue

                conn.execute(text('''
INSERT INTO cart_items (user_id, product_id, seller_id, quantity, unit_price, saved)
VALUES (:uid, :pid, :sid, :qty, :price, FALSE)
ON CONFLICT (user_id, product_id, seller_id)
DO UPDATE SET
    quantity = cart_items.quantity + EXCLUDED.quantity,
    unit_price = EXCLUDED.unit_price,
    saved = FALSE,
    added_at = CURRENT_TIMESTAMP
'''), {'uid': user_id, 'pid': item['product_id'], 'sid': item['seller_id'],
       'qty': qty, 'price': price})

    @staticmethod
    def checkout(user_id, coupon_code=None, discount_amount=0.0):
        """
        Submit active (non-saved) cart items as one order in a single SERIALIZABLE transaction.
        Returns (order_id, None) on success or (None, error_message) on failure.
        """
        from sqlalchemy import text

        try:
            with app.db.engine.begin() as conn:
                # 1. Get active cart items with row locks
                rows = conn.execute(text('''
SELECT c.product_id, c.seller_id, c.quantity, c.unit_price
FROM cart_items c
WHERE c.user_id = :user_id AND c.saved = FALSE
FOR UPDATE
'''), {'user_id': user_id}).fetchall()

                if not rows:
                    return None, 'Your cart is empty.'

                cart = [{'product_id': r[0], 'seller_id': r[1],
                         'quantity': r[2], 'unit_price': float(r[3])} for r in rows]

                total_amount = sum(item['unit_price'] * item['quantity'] for item in cart)
                num_items = sum(item['quantity'] for item in cart)

                # Validate and apply coupon if provided
                discount = max(0.0, min(float(discount_amount or 0), total_amount))
                coupon_id = None
                if coupon_code:
                    coupon_row = conn.execute(text('''
SELECT id, discount_type, discount_value, min_order_amount, max_uses,
       expiry_date, applicable_product_id
FROM coupons WHERE code = :code
'''), {'code': coupon_code.strip().upper()}).fetchone()

                    if coupon_row is None:
                        raise ValueError('Invalid coupon code.')

                    coupon_id = coupon_row[0]
                    discount_type = coupon_row[1]
                    discount_value = float(coupon_row[2])
                    min_order = float(coupon_row[3])
                    max_uses = coupon_row[4]
                    expiry = coupon_row[5]
                    applicable_pid = coupon_row[6]

                    if expiry and expiry < __import__('datetime').datetime.now():
                        raise ValueError('This coupon has expired.')

                    if total_amount < min_order:
                        raise ValueError(f'Order must be at least ${min_order:.2f} to use this coupon.')

                    if max_uses is not None:
                        use_count = conn.execute(text('''
SELECT COUNT(*) FROM coupon_uses WHERE coupon_id = :cid
'''), {'cid': coupon_id}).fetchone()[0]
                        if use_count >= max_uses:
                            raise ValueError('This coupon has reached its maximum number of uses.')

                    if applicable_pid is not None:
                        applicable_total = sum(
                            item['unit_price'] * item['quantity']
                            for item in cart if item['product_id'] == applicable_pid
                        )
                        if applicable_total == 0:
                            raise ValueError('This coupon does not apply to any items in your cart.')
                        base_for_discount = applicable_total
                    else:
                        base_for_discount = total_amount

                    if discount_type == 'percentage':
                        discount = round(base_for_discount * discount_value / 100, 2)
                    else:
                        discount = min(discount_value, base_for_discount)

                final_amount = round(total_amount - discount, 2)
                if final_amount < 0:
                    final_amount = 0

                # 2. Check inventory for every line
                for item in cart:
                    inv = conn.execute(text('''
SELECT quantity FROM Inventory
WHERE seller_id = :sid AND product_id = :pid
FOR UPDATE
'''), {'sid': item['seller_id'], 'pid': item['product_id']}).fetchone()

                    if inv is None or inv[0] < item['quantity']:
                        raise ValueError(
                            f"Insufficient inventory for product {item['product_id']} "
                            f"from seller {item['seller_id']}.")

                # 3. Check buyer balance
                buyer = conn.execute(text('''
SELECT balance FROM Users WHERE id = :uid FOR UPDATE
'''), {'uid': user_id}).fetchone()

                if buyer is None or float(buyer[0]) < final_amount:
                    raise ValueError('Insufficient balance to complete this order.')

                # 4. Create order
                order_row = conn.execute(text('''
INSERT INTO orders (user_id, total_amount, num_items)
VALUES (:uid, :total, :num)
RETURNING id
'''), {'uid': user_id, 'total': final_amount, 'num': num_items}).fetchone()
                order_id = order_row[0]

                # 5. Insert order_items, 6. Decrement inventory, aggregate seller credits
                seller_credits = {}
                for item in cart:
                    conn.execute(text('''
INSERT INTO order_items (order_id, product_id, seller_id, quantity, unit_price)
VALUES (:oid, :pid, :sid, :qty, :price)
'''), {'oid': order_id, 'pid': item['product_id'],
       'sid': item['seller_id'], 'qty': item['quantity'],
       'price': item['unit_price']})

                    conn.execute(text('''
UPDATE Inventory
SET quantity = quantity - :qty, updated_at = CURRENT_TIMESTAMP
WHERE seller_id = :sid AND product_id = :pid
'''), {'qty': item['quantity'], 'sid': item['seller_id'],
       'pid': item['product_id']})

                    line_total = item['unit_price'] * item['quantity']
                    seller_credits[item['seller_id']] = seller_credits.get(item['seller_id'], 0) + line_total

                # If there's a discount, proportionally reduce seller credits
                if discount > 0 and total_amount > 0:
                    discount_ratio = discount / total_amount
                    for sid in seller_credits:
                        reduction = round(seller_credits[sid] * discount_ratio, 2)
                        seller_credits[sid] = round(seller_credits[sid] - reduction, 2)

                # 7. Debit buyer
                conn.execute(text('''
UPDATE Users SET balance = balance - :amount WHERE id = :uid
'''), {'amount': final_amount, 'uid': user_id})

                # 8. Credit each seller
                for sid, credit in seller_credits.items():
                    conn.execute(text('''
UPDATE Users SET balance = balance + :amount WHERE id = :sid
'''), {'amount': round(credit, 2), 'sid': sid})

                # 9. Record coupon use
                if coupon_id is not None:
                    conn.execute(text('''
INSERT INTO coupon_uses (coupon_id, user_id, order_id)
VALUES (:cid, :uid, :oid)
'''), {'cid': coupon_id, 'uid': user_id, 'oid': order_id})

                # 10. Clear active cart items (keep saved items)
                conn.execute(text('''
DELETE FROM cart_items WHERE user_id = :uid AND saved = FALSE
'''), {'uid': user_id})

                return order_id, None

        except ValueError as e:
            return None, str(e)
        except Exception:
            return None, 'An error occurred while processing your order. Please try again.'
