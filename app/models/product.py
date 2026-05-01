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
        avg_rating=None,
        category_name=None,
        seller_count=None,
        total_stock=None,
        cheapest_seller_name=None
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
        self.category_name = category_name
        self.seller_count = seller_count
        self.total_stock = total_stock if total_stock is not None else 0
        self.cheapest_seller_name = cheapest_seller_name

    @property
    def in_stock(self):
        return self.total_stock > 0

    @staticmethod
    def _query_base(where_clauses=None):
        where_sql = ''
        if where_clauses:
            where_sql = '\nWHERE ' + '\n  AND '.join(where_clauses)

        return f'''
SELECT
    p.id,
    p.creator_id,
    p.category_id,
    p.name,
    p.description,
    p.image_url,
    p.available,
    inv.min_price,
    rev.avg_rating,
    c.name AS category_name,
    inv.seller_count,
    inv.total_stock,
    cheapest.seller_name AS cheapest_seller_name
FROM Products p
LEFT JOIN Categories c ON c.id = p.category_id
LEFT JOIN LATERAL (
    SELECT
        MIN(i.price) FILTER (WHERE i.quantity > 0) AS min_price,
        COUNT(*) FILTER (WHERE i.quantity > 0) AS seller_count,
        COALESCE(SUM(CASE WHEN i.quantity > 0 THEN i.quantity ELSE 0 END), 0) AS total_stock
    FROM Inventory i
    WHERE i.product_id = p.id
) inv ON TRUE
LEFT JOIN LATERAL (
    SELECT AVG(pr.rating) AS avg_rating
    FROM ProductReviews pr
    WHERE pr.product_id = p.id
) rev ON TRUE
LEFT JOIN LATERAL (
    SELECT CONCAT(u.firstname, ' ', u.lastname) AS seller_name
    FROM Inventory i2
    JOIN Users u ON u.id = i2.seller_id
    WHERE i2.product_id = p.id AND i2.quantity > 0
    ORDER BY i2.price ASC, i2.quantity DESC, i2.seller_id ASC
    LIMIT 1
) cheapest ON TRUE
{where_sql}
'''

    @staticmethod
    def _rows_to_products(rows):
        return [Product(*row) for row in rows]

    @staticmethod
    def get(id):
        rows = app.db.execute('''
SELECT
    p.id,
    p.creator_id,
    p.category_id,
    p.name,
    p.description,
    p.image_url,
    p.available
FROM Products p
WHERE p.id = :id
''', id=id)

        return Product(*rows[0]) if rows else None

    @staticmethod
    def get_all(available=True):
        rows = app.db.execute(
            Product._query_base(['p.available = :available']) + '\nORDER BY p.id ASC',
            available=available,
        )
        return Product._rows_to_products(rows)

    @staticmethod
    def search(
        category_id=None,
        keyword=None,
        sort_by='price_asc',
        min_price=None,
        max_price=None,
        min_rating=None,
        only_in_stock=False,
        page=1,
        per_page=25,
    ):
        page = page if page and page > 0 else 1
        per_page = per_page if per_page and per_page > 0 else 25
        offset = (page - 1) * per_page

        params = {}
        where_clauses = ['p.available = TRUE']

        if category_id:
            where_clauses.append('p.category_id = :category_id')
            params['category_id'] = category_id

        if keyword:
            where_clauses.append('(LOWER(p.name) LIKE LOWER(:kw) OR LOWER(p.description) LIKE LOWER(:kw))')
            params['kw'] = f'%{keyword}%'

        if min_price is not None:
            where_clauses.append('inv.min_price >= :min_price')
            params['min_price'] = min_price

        if max_price is not None:
            where_clauses.append('inv.min_price <= :max_price')
            params['max_price'] = max_price

        if min_rating is not None:
            where_clauses.append('rev.avg_rating >= :min_rating')
            params['min_rating'] = min_rating

        if only_in_stock:
            where_clauses.append('inv.total_stock > 0')

        base_query = Product._query_base(where_clauses)

        if sort_by == 'price_desc':
            order_by = 'inv.min_price DESC NULLS LAST, p.id ASC'
        elif sort_by == 'rating_desc':
            order_by = 'rev.avg_rating DESC NULLS LAST, p.id ASC'
        elif sort_by == 'rating_asc':
            order_by = 'rev.avg_rating ASC NULLS LAST, p.id ASC'
        else:
            order_by = 'inv.min_price ASC NULLS LAST, p.id ASC'

        count_rows = app.db.execute(
            f'''SELECT COUNT(*) FROM ({base_query}) filtered_products''',
            **params,
        )
        total_count = count_rows[0][0] if count_rows else 0

        rows = app.db.execute(
            base_query + f'\nORDER BY {order_by}\nLIMIT :per_page\nOFFSET :offset',
            per_page=per_page,
            offset=offset,
            **params,
        )
        return Product._rows_to_products(rows), total_count

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
    def deactivate(product_id, creator_id):
        return app.db.execute('''
UPDATE Products
SET available = FALSE
WHERE id = :product_id AND creator_id = :creator_id AND available = TRUE
''', product_id=product_id, creator_id=creator_id)

    @staticmethod
    def get_top_k_expensive(k):
        return app.db.execute('''
SELECT
    p.id,
    p.name,
    MAX(i.price) AS top_price,
    MIN(i.price) FILTER (WHERE i.quantity > 0) AS min_price,
    p.available
FROM Products p
JOIN Inventory i ON p.id = i.product_id
WHERE p.available = TRUE
GROUP BY p.id, p.name, p.available
ORDER BY top_price DESC, p.id ASC
LIMIT :k
''', k=k)

    @staticmethod
    def get_top_rated(limit=4):
        rows = app.db.execute(
            Product._query_base(['p.available = TRUE', 'rev.avg_rating IS NOT NULL', 'inv.total_stock > 0']) + '''
ORDER BY rev.avg_rating DESC, inv.total_stock DESC, p.id ASC
LIMIT :limit
''',
            limit=limit,
        )
        return Product._rows_to_products(rows)

    @staticmethod
    def get_by_creator(creator_id):
        rows = app.db.execute(
            Product._query_base(['p.creator_id = :creator_id']) + '\nORDER BY p.id DESC',
            creator_id=creator_id,
        )
        return Product._rows_to_products(rows)

    @staticmethod
    def get_recent(limit=5):
        rows = app.db.execute(
            Product._query_base(['p.available = TRUE']) + '''
ORDER BY p.id DESC
LIMIT :limit
''',
            limit=limit,
        )
        return Product._rows_to_products(rows)
