from flask import current_app as app


class Product:
    def __init__(
        self,
        id,
        creator_id,
        category_id,
        name,
        description,
        image_url,
        available,
        min_price=None,
        avg_rating=None
    ):
        self.id = id
        self.creator_id = creator_id
        self.category_id = category_id
        self.name = name
        self.description = description
        self.image_url = image_url
        self.available = available
        self.min_price = min_price
        self.avg_rating = avg_rating

    @staticmethod
    def get(id):
        rows = app.db.execute('''
SELECT id, creator_id, category_id, name, description, image_url, available
FROM Products
WHERE id = :id
''', id=id)

        return Product(*(rows[0])) if rows else None

    @staticmethod
    def get_all(available=True):
        rows = app.db.execute('''
SELECT
    p.id,
    p.creator_id,
    p.category_id,
    p.name,
    p.description,
    p.image_url,
    p.available,
    MIN(i.price) AS min_price
FROM Products p
LEFT JOIN Inventory i ON p.id = i.product_id
WHERE p.available = :available
GROUP BY p.id, p.creator_id, p.category_id, p.name, p.description, p.image_url, p.available
ORDER BY p.id ASC
''', available=available)

        return [Product(*row) for row in rows]

    @staticmethod
    def search(category_id=None, keyword=None, sort_by='price_asc'):
        query = '''
SELECT
    p.id,
    p.creator_id,
    p.category_id,
    p.name,
    p.description,
    p.image_url,
    p.available,
    MIN(i.price) AS min_price,
    AVG(pr.rating) AS avg_rating
FROM Products p
LEFT JOIN Inventory i ON p.id = i.product_id
LEFT JOIN ProductReviews pr ON p.id = pr.product_id
WHERE p.available = TRUE
'''
        params = {}

        if category_id:
            query += '\nAND p.category_id = :category_id'
            params['category_id'] = category_id

        if keyword:
            query += '\nAND (LOWER(p.name) LIKE LOWER(:kw) OR LOWER(p.description) LIKE LOWER(:kw))'
            params['kw'] = f'%{keyword}%'

        query += '''
GROUP BY p.id, p.creator_id, p.category_id, p.name, p.description, p.image_url, p.available
'''

        if sort_by == 'price_desc':
            query += '\nORDER BY min_price DESC NULLS LAST, p.id ASC'
        else:
            query += '\nORDER BY min_price ASC NULLS LAST, p.id ASC'

        rows = app.db.execute(query, **params)
        return [Product(*row) for row in rows]

    @staticmethod
    def create(creator_id, category_id, name, description, image_url, available=True):
        rows = app.db.execute('''
INSERT INTO Products(creator_id, category_id, name, description, image_url, available)
VALUES (:creator_id, :category_id, :name, :description, :image_url, :available)
RETURNING id
''',
                              creator_id=creator_id,
                              category_id=category_id,
                              name=name,
                              description=description,
                              image_url=image_url,
                              available=available)
        return rows[0][0]

    @staticmethod
    def update(product_id, creator_id, category_id, name, description, image_url, available):
        app.db.execute('''
UPDATE Products
SET category_id = :category_id,
    name = :name,
    description = :description,
    image_url = :image_url,
    available = :available
WHERE id = :product_id AND creator_id = :creator_id
''',
                       product_id=product_id,
                       creator_id=creator_id,
                       category_id=category_id,
                       name=name,
                       description=description,
                       image_url=image_url,
                       available=available)

    @staticmethod
    def get_top_k_expensive(k):
        return app.db.execute('''
SELECT
    p.id,
    p.name,
    MAX(i.price) AS top_price,
    MIN(i.price) AS min_price,
    p.available
FROM Products p
JOIN Inventory i ON p.id = i.product_id
WHERE p.available = TRUE
GROUP BY p.id, p.name, p.available
ORDER BY top_price DESC, p.id ASC
LIMIT :k
''', k=k)