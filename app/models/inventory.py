from flask import current_app as app


class InventoryItem:
    def __init__(self, product_id, name, product_price, available, quantity, inventory_price):
        self.product_id = product_id
        self.name = name
        self.product_price = product_price
        self.available = available
        self.quantity = quantity
        self.inventory_price = inventory_price

    @staticmethod
    def get_products_for_seller(seller_id: int):
        # Only using id and name in route, getting rest as eventually will need that
        rows = app.db.execute('''
            SELECT p.id, p.name, p.price AS product_price, p.available, i.quantity, i.price AS inventory_price
            FROM Inventory i
            JOIN Products p ON p.id = i.product_id
            WHERE i.seller_id = :seller_id
            ORDER BY p.price DESC, p.id ASC
        ''', seller_id=seller_id)

        return [InventoryItem(*row) for row in rows]