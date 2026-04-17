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
    def get_feedback_by_uid(user_id, page=1, per_page=25):
        offset = (page - 1) * per_page
        rows = app.db.execute('''
SELECT feedback_type, target_id, rating, review, created_at
FROM (
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
) f
ORDER BY created_at DESC
LIMIT :per_page
OFFSET :offset
''',
                              user_id=user_id,
                              per_page=per_page,
                              offset=offset)
        return [Feedback(*row) for row in rows]

    @staticmethod
    def get_feedback_count_by_uid(user_id):
        rows = app.db.execute('''
SELECT (
    (SELECT COUNT(*) FROM ProductReviews WHERE user_id = :user_id)
    +
    (SELECT COUNT(*) FROM SellerReviews WHERE user_id = :user_id)
) AS total_feedback
''', user_id=user_id)
        return rows[0][0] if rows else 0

    @staticmethod
    def get_product_reviews(product_id, page=1, per_page=10, sort_by='date_desc'):
        offset = (page - 1) * per_page
        order_by = 'pr.created_at DESC'
        if sort_by == 'date_asc':
            order_by = 'pr.created_at ASC'
        elif sort_by == 'rating_desc':
            order_by = 'pr.rating DESC, pr.created_at DESC'
        elif sort_by == 'rating_asc':
            order_by = 'pr.rating ASC, pr.created_at DESC'

        return app.db.execute(f'''
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
ORDER BY {order_by}
LIMIT :per_page
OFFSET :offset
''', product_id=product_id, per_page=per_page, offset=offset)

    @staticmethod
    def get_product_review_count(product_id):
        rows = app.db.execute('''
SELECT COUNT(*)
FROM ProductReviews
WHERE product_id = :product_id
''', product_id=product_id)
        return rows[0][0] if rows else 0

    @staticmethod
    def get_product_average_rating(product_id):
        rows = app.db.execute('''
SELECT AVG(rating)
FROM ProductReviews
WHERE product_id = :product_id
''', product_id=product_id)
        return rows[0][0] if rows and rows[0][0] is not None else None

    @staticmethod
    def get_product_review_by_user(product_id, user_id):
        rows = app.db.execute('''
SELECT id, user_id, product_id, rating, review, created_at
FROM ProductReviews
WHERE product_id = :product_id AND user_id = :user_id
''', product_id=product_id, user_id=user_id)
        return rows[0] if rows else None

    @staticmethod
    def upsert_product_review(product_id, user_id, rating, review):
        rows = app.db.execute('''
INSERT INTO ProductReviews (user_id, product_id, rating, review)
VALUES (:user_id, :product_id, :rating, :review)
ON CONFLICT (user_id, product_id)
DO UPDATE SET
    rating = EXCLUDED.rating,
    review = EXCLUDED.review,
    created_at = CURRENT_TIMESTAMP
RETURNING id
''', product_id=product_id, user_id=user_id, rating=rating, review=review)
        return rows[0][0] if rows else None

    @staticmethod
    def get_seller_reviews(seller_id, page=1, per_page=10, sort_by='date_desc'):
        offset = (page - 1) * per_page
        order_by = 'sr.created_at DESC'
        if sort_by == 'date_asc':
            order_by = 'sr.created_at ASC'
        elif sort_by == 'rating_desc':
            order_by = 'sr.rating DESC, sr.created_at DESC'
        elif sort_by == 'rating_asc':
            order_by = 'sr.rating ASC, sr.created_at DESC'

        return app.db.execute(f'''
SELECT
    sr.id,
    sr.user_id,
    sr.seller_id,
    sr.rating,
    sr.review,
    sr.created_at,
    u.firstname,
    u.lastname
FROM SellerReviews sr
JOIN Users u ON u.id = sr.user_id
WHERE sr.seller_id = :seller_id
ORDER BY {order_by}
LIMIT :per_page
OFFSET :offset
''', seller_id=seller_id, per_page=per_page, offset=offset)

    @staticmethod
    def get_seller_review_count(seller_id):
        rows = app.db.execute('''
SELECT COUNT(*)
FROM SellerReviews
WHERE seller_id = :seller_id
''', seller_id=seller_id)
        return rows[0][0] if rows else 0

    @staticmethod
    def get_seller_average_rating(seller_id):
        rows = app.db.execute('''
SELECT AVG(rating)
FROM SellerReviews
WHERE seller_id = :seller_id
''', seller_id=seller_id)
        return rows[0][0] if rows and rows[0][0] is not None else None