from flask import current_app as app


class ProductReview:
    @staticmethod
    def get_for_product(product_id):
        return app.db.execute('''
SELECT
    pr.id,
    pr.user_id,
    pr.product_id,
    pr.rating,
    pr.review,
    pr.created_at,
    u.firstname,
    u.lastname
FROM ProductReviews pr
JOIN Users u ON u.id = pr.user_id
WHERE pr.product_id = :product_id
ORDER BY pr.created_at DESC
''', product_id=product_id)

    @staticmethod
    def average_for_product(product_id):
        rows = app.db.execute('''
SELECT AVG(rating)
FROM ProductReviews
WHERE product_id = :product_id
''', product_id=product_id)
        return rows[0][0] if rows and rows[0][0] is not None else None