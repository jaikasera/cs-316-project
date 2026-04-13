from flask import current_app as app


class CartItem:
    def __init__(self, user_id, product_id, seller_id, product_name,
                 seller_firstname, seller_lastname, quantity, unit_price, added_at):
        self.user_id = user_id
        self.product_id = product_id
        self.seller_id = seller_id
        self.product_name = product_name
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