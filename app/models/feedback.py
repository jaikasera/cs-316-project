from flask import current_app as app


class Feedback:
    def __init__(self, feedback_type, target_id, rating, review, created_at):
        self.feedback_type = feedback_type
        self.target_id = target_id
        self.rating = rating
        self.review = review
        self.created_at = created_at

    @staticmethod
    def get_recent_by_uid(user_id):
        rows = app.db.execute('''
SELECT 'Product Review' AS feedback_type,
       product_id AS target_id,
       rating,
       review,
       created_at
FROM ProductReviews
WHERE user_id = :user_id

UNION ALL

SELECT 'Seller Review' AS feedback_type,
       seller_id AS target_id,
       rating,
       review,
       created_at
FROM SellerReviews
WHERE user_id = :user_id

ORDER BY created_at DESC
LIMIT 5
''',
                              user_id=user_id)
        return [Feedback(*row) for row in rows]

    @staticmethod
    def get_product_reviews(product_id):
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
    def get_product_average_rating(product_id):
        rows = app.db.execute('''
SELECT AVG(rating)
FROM ProductReviews
WHERE product_id = :product_id
''', product_id=product_id)
        return rows[0][0] if rows and rows[0][0] is not None else None

    @staticmethod
    def get_product_reviews(product_id):
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
    def get_product_average_rating(product_id):
        rows = app.db.execute('''
SELECT AVG(rating)
FROM ProductReviews
WHERE product_id = :product_id
''', product_id=product_id)
        return rows[0][0] if rows and rows[0][0] is not None else None