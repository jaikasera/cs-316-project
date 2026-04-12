from flask import current_app as app


class InventoryItem:
    def __init__(self, product_id, name, description, image_url, available, quantity, inventory_price):
        self.product_id = product_id
        self.name = name
        self.description = description
        self.image_url = image_url
        self.available = available
        self.quantity = quantity
        self.inventory_price = inventory_price

    @staticmethod
    def get_products_for_seller(seller_id: int):
        rows = app.db.execute('''
SELECT
    p.id,
    p.name,
    p.description,
    p.image_url,
    p.available,
    i.quantity,
    i.price AS inventory_price
FROM Inventory i
JOIN Products p ON p.id = i.product_id
WHERE i.seller_id = :seller_id
ORDER BY i.price DESC, p.id ASC
''', seller_id=seller_id)

        return [InventoryItem(*row) for row in rows]

    @staticmethod
    def get_sellers_for_product(product_id: int):
        return app.db.execute('''
SELECT
    i.seller_id,
    u.firstname,
    u.lastname,
    i.quantity,
    i.price,
    i.updated_at,
    CASE
        WHEN i.price = (
            SELECT MIN(i2.price)
            FROM Inventory i2
            WHERE i2.product_id = :product_id AND i2.quantity > 0
        ) THEN TRUE
        ELSE FALSE
    END AS is_cheapest
FROM Inventory i
JOIN Users u ON u.id = i.seller_id
WHERE i.product_id = :product_id
ORDER BY i.price ASC, i.quantity DESC
''', product_id=product_id)