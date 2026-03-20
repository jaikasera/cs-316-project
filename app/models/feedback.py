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
        """Return the 5 most recent feedback entries posted by a given user,
        combining product reviews and seller reviews via UNION ALL."""
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
