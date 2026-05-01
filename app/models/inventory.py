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
    def get_products_for_seller(seller_id: int, page: int = 1, per_page: int = 25):
        offset = (page - 1) * per_page
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
LIMIT :per_page
OFFSET :offset
''', seller_id=seller_id, per_page=per_page, offset=offset)

        return [InventoryItem(*row) for row in rows]

    @staticmethod
    def get_product_count_for_seller(seller_id: int):
        rows = app.db.execute('''
SELECT COUNT(*)
FROM Inventory i
WHERE i.seller_id = :seller_id
''', seller_id=seller_id)
        return rows[0][0] if rows else 0

    @staticmethod
    def add_item_to_inventory(seller_id: int, product_id: int, quantity: int, price: float):
        """Add or update quantity/price for (seller_id, product_id)."""
        app.db.execute('''
INSERT INTO Inventory (seller_id, product_id, quantity, price)
VALUES (:seller_id, :product_id, :quantity, :price)
ON CONFLICT (seller_id, product_id) DO UPDATE SET quantity = EXCLUDED.quantity,
    price = EXCLUDED.price,
    updated_at = CURRENT_TIMESTAMP
''', seller_id=seller_id, product_id=product_id, quantity=quantity, price=price)

    @staticmethod
    def get_inventory_item_for_seller(seller_id: int, product_id: int):
        rows = app.db.execute('''
SELECT
    p.id,
    p.name,
    p.description,
    p.image_url,
    p.available,
    p.category_id,
    c.name AS category_name,
    p.creator_id,
    i.quantity,
    i.price,
    i.updated_at
FROM Inventory i
JOIN Products p ON p.id = i.product_id
JOIN Categories c ON c.id = p.category_id
WHERE i.seller_id = :seller_id AND i.product_id = :product_id
''', seller_id=seller_id, product_id=product_id)

        return InventoryItemDetail(*rows[0]) if rows else None

    @staticmethod
    def update_inventory_item_quantity(seller_id: int, product_id: int, quantity: int):
        return app.db.execute('''
UPDATE Inventory
SET quantity = :quantity, updated_at = CURRENT_TIMESTAMP
WHERE seller_id = :seller_id AND product_id = :product_id
''', seller_id=seller_id, product_id=product_id, quantity=quantity)

    @staticmethod
    def remove_inventory_item(seller_id: int, product_id: int):
        return app.db.execute('''
DELETE FROM Inventory
WHERE seller_id = :seller_id AND product_id = :product_id
''', seller_id=seller_id, product_id=product_id)

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


class InventoryItemDetail:
    """One seller's listing for a product, joined with catalog fields."""

    def __init__(
        self,
        product_id,
        name,
        description,
        image_url,
        available,
        category_id,
        category_name,
        creator_id,
        quantity,
        price,
        updated_at,
    ):
        self.product_id = product_id
        self.name = name
        self.description = description
        self.image_url = image_url
        self.available = available
        self.category_id = category_id
        self.category_name = category_name
        self.creator_id = creator_id
        self.quantity = quantity
        self.price = price
        self.updated_at = updated_at
