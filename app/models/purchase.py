from flask import current_app as app


class Purchase:
    def __init__(self, id, uid, pid, time_purchased):
        self.id = id
        self.uid = uid
        self.pid = pid
        self.time_purchased = time_purchased

    @staticmethod
    def get(id):
        rows = app.db.execute('''
SELECT id, uid, pid, time_purchased
FROM Purchases
WHERE id = :id
''',
                              id=id)
        return Purchase(*(rows[0])) if rows else None

    @staticmethod
    def get_all_by_uid_since(uid, since):
        rows = app.db.execute('''
SELECT id, uid, pid, time_purchased
FROM Purchases
WHERE uid = :uid
AND time_purchased >= :since
ORDER BY time_purchased DESC
''',
                              uid=uid,
                              since=since)
        return [Purchase(*row) for row in rows]

    @staticmethod
    def get_all_by_uid(uid):
        rows = app.db.execute('''
            SELECT id, uid, pid, time_purchased
            FROM Purchases
            WHERE uid = :uid
            ORDER BY time_purchased DESC
            ''', uid=uid)  
        return [Purchase(*row) for row in rows]

    @staticmethod
    def get_all_by_uid_with_product(uid):
        rows = app.db.execute('''
            SELECT pu.id, pu.uid, pu.pid, pu.time_purchased, p.name AS product_name, inv.min_price AS product_price
            FROM Purchases pu
            LEFT JOIN Products p ON p.id = pu.pid
            LEFT JOIN LATERAL (
                SELECT MIN(i.price) FILTER (WHERE i.quantity > 0) AS min_price
                FROM Inventory i
                WHERE i.product_id = pu.pid
            ) inv ON TRUE
            WHERE pu.uid = :uid
            ORDER BY pu.time_purchased DESC
            ''', uid=uid)
        return rows
