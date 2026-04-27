from flask import current_app as app


class WishlistItem:
    def __init__(self, user_id, product_id, product_name, category_name,
                 image_url, lowest_price, total_stock, added_at):
        self.user_id = user_id
        self.product_id = product_id
        self.product_name = product_name
        self.category_name = category_name
        self.image_url = image_url
        self.lowest_price = lowest_price
        self.total_stock = total_stock
        self.added_at = added_at

    @property
    def in_stock(self):
        return self.total_stock is not None and self.total_stock > 0


class Wishlist:

    @staticmethod
    def get_items(user_id):
        rows = app.db.execute('''
SELECT w.user_id, w.product_id, p.name, c.name AS category_name,
       p.image_url,
       MIN(i.price) AS lowest_price,
       COALESCE(SUM(i.quantity), 0) AS total_stock,
       w.added_at
FROM wishlist w
JOIN Products p ON p.id = w.product_id
JOIN Categories c ON c.id = p.category_id
LEFT JOIN Inventory i ON i.product_id = w.product_id AND i.quantity > 0
WHERE w.user_id = :user_id
GROUP BY w.user_id, w.product_id, p.name, c.name, p.image_url, w.added_at
ORDER BY w.added_at DESC
''', user_id=user_id)
        return [WishlistItem(*row) for row in rows]

    @staticmethod
    def add(user_id, product_id):
        app.db.execute('''
INSERT INTO wishlist (user_id, product_id)
VALUES (:user_id, :product_id)
ON CONFLICT (user_id, product_id) DO NOTHING
''', user_id=user_id, product_id=product_id)

    @staticmethod
    def remove(user_id, product_id):
        app.db.execute('''
DELETE FROM wishlist
WHERE user_id = :user_id AND product_id = :product_id
''', user_id=user_id, product_id=product_id)

    @staticmethod
    def is_in_wishlist(user_id, product_id):
        rows = app.db.execute('''
SELECT 1 FROM wishlist
WHERE user_id = :user_id AND product_id = :product_id
''', user_id=user_id, product_id=product_id)
        return len(rows) > 0
