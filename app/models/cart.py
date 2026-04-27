from flask import current_app as app


class CartItem:
    def __init__(
        self,
        user_id,
        product_id,
        seller_id,
        product_name,
        product_image_url,
        product_available,
        seller_firstname,
        seller_lastname,
        quantity,
        unit_price,
        added_at,
    ):
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
        self.line_total = round(float(unit_price) * quantity, 2)

    @staticmethod
    def get_items_by_user(user_id):
        rows = app.db.execute('''
SELECT c.user_id, c.product_id, c.seller_id,
       p.name AS product_name,
       p.image_url,
       p.available,
       s.firstname AS seller_firstname,
       s.lastname AS seller_lastname,
       c.quantity, c.unit_price, c.added_at
FROM cart_items c
JOIN Products p ON p.id = c.product_id
JOIN Users s ON s.id = c.seller_id
WHERE c.user_id = :user_id
ORDER BY c.added_at DESC
''', user_id=user_id)

        return [CartItem(*row) for row in rows]

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
INSERT INTO cart_items (user_id, product_id, seller_id, quantity, unit_price)
SELECT :user_id, :product_id, :seller_id, :quantity, i.price
FROM Inventory i
WHERE i.product_id = :product_id AND i.seller_id = :seller_id

ON CONFLICT (user_id, product_id, seller_id)
DO UPDATE SET
    quantity = cart_items.quantity + EXCLUDED.quantity,
    unit_price = EXCLUDED.unit_price,
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
    def checkout(user_id, discount_amount=0.0):
        """
        Submit the entire cart as one order in a single SERIALIZABLE transaction.
        Returns (order_id, None) on success or (None, error_message) on failure.
        """
        from sqlalchemy import text

        try:
            with app.db.engine.begin() as conn:
                # 1. Get cart items with row locks
                rows = conn.execute(text('''
SELECT c.product_id, c.seller_id, c.quantity, c.unit_price
FROM cart_items c
WHERE c.user_id = :user_id
FOR UPDATE
'''), {'user_id': user_id}).fetchall()

                if not rows:
                    return None, 'Your cart is empty.'

                cart = [{'product_id': r[0], 'seller_id': r[1],
                         'quantity': r[2], 'unit_price': float(r[3])} for r in rows]

                subtotal = sum(item['unit_price'] * item['quantity'] for item in cart)
                discount_amount = max(0.0, min(float(discount_amount or 0), subtotal))
                total_amount = subtotal - discount_amount
                num_items = sum(item['quantity'] for item in cart)

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

                if buyer is None or float(buyer[0]) < total_amount:
                    raise ValueError('Insufficient balance to complete this order.')

                # 4. Create order
                order_row = conn.execute(text('''
INSERT INTO orders (user_id, total_amount, num_items)
VALUES (:uid, :total, :num)
RETURNING id
'''), {'uid': user_id, 'total': round(total_amount, 2), 'num': num_items}).fetchone()
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

                # 7. Debit buyer
                conn.execute(text('''
UPDATE Users SET balance = balance - :amount WHERE id = :uid
'''), {'amount': round(total_amount, 2), 'uid': user_id})

                # 8. Credit each seller
                for sid, credit in seller_credits.items():
                    conn.execute(text('''
UPDATE Users SET balance = balance + :amount WHERE id = :sid
'''), {'amount': round(credit, 2), 'sid': sid})

                # 9. Clear cart
                conn.execute(text('''
DELETE FROM cart_items WHERE user_id = :uid
'''), {'uid': user_id})

                return order_id, None

        except ValueError as e:
            return None, str(e)
        except Exception:
            return None, 'An error occurred while processing your order. Please try again.'
