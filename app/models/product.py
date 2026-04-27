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
        cheapest_seller_name=None,
        review_count=None,
        order_count=None,
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
        self.review_count = review_count if review_count is not None else 0
        self.order_count = order_count if order_count is not None else 0

    @property
    def in_stock(self):
        return self.total_stock > 0

    @property
    def popularity_score(self):
        rating_points = float(self.avg_rating or 0) * 20
        return int(rating_points + (self.review_count * 3) + (self.order_count * 5) + (self.seller_count or 0))

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
    COALESCE(parent.name || ' > ' || c.name, c.name) AS category_name,
    inv.seller_count,
    inv.total_stock,
    cheapest.seller_name AS cheapest_seller_name,
    rev.review_count,
    ord.order_count
FROM Products p
LEFT JOIN Categories c ON c.id = p.category_id
LEFT JOIN Categories parent ON parent.id = c.parent_id
LEFT JOIN LATERAL (
    SELECT
        MIN(i.price) FILTER (WHERE i.quantity > 0) AS min_price,
        COUNT(*) FILTER (WHERE i.quantity > 0) AS seller_count,
        COALESCE(SUM(CASE WHEN i.quantity > 0 THEN i.quantity ELSE 0 END), 0) AS total_stock
    FROM Inventory i
    WHERE i.product_id = p.id
) inv ON TRUE
LEFT JOIN LATERAL (
    SELECT
        AVG(pr.rating) AS avg_rating,
        COUNT(*) AS review_count
    FROM ProductReviews pr
    WHERE pr.product_id = p.id
) rev ON TRUE
LEFT JOIN LATERAL (
    SELECT COUNT(*) AS order_count
    FROM order_items oi
    JOIN orders o ON o.id = oi.order_id
    WHERE oi.product_id = p.id
) ord ON TRUE
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
        rows = app.db.execute(
            Product._query_base(['p.id = :id']) + '\nLIMIT 1',
            id=id,
        )
        return Product(*rows[0]) if rows else None

    @staticmethod
    def get_many(ids, available_only=False):
        if not ids:
            return []

        values = [int(value) for value in ids]
        where_clauses = ['p.id = ANY(:ids)']
        if available_only:
            where_clauses.append('p.available = TRUE')

        rows = app.db.execute(
            Product._query_base(where_clauses),
            ids=values,
        )
        products = Product._rows_to_products(rows)
        by_id = {product.id: product for product in products}
        return [by_id[product_id] for product_id in values if product_id in by_id]

    @staticmethod
    def get_all(available=True):
        rows = app.db.execute(
            Product._query_base(['p.available = :available']) + '\nORDER BY p.id ASC',
            available=available,
        )
        return Product._rows_to_products(rows)

    @staticmethod
    def _order_by_for_sort(sort_by):
        if sort_by == 'price_desc':
            return 'inv.min_price DESC NULLS LAST, p.id ASC'
        if sort_by == 'rating_desc':
            return 'rev.avg_rating DESC NULLS LAST, rev.review_count DESC, p.id ASC'
        if sort_by == 'rating_asc':
            return 'rev.avg_rating ASC NULLS LAST, p.id ASC'
        if sort_by == 'popularity_desc':
            return '((COALESCE(rev.avg_rating, 0) * 20) + (COALESCE(rev.review_count, 0) * 3) + (COALESCE(ord.order_count, 0) * 5) + COALESCE(inv.seller_count, 0)) DESC, p.id ASC'
        return 'inv.min_price ASC NULLS LAST, p.id ASC'

    @staticmethod
    def search(
        category_id=None,
        category_ids=None,
        tag_slug=None,
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
            where_clauses.append('p.category_id = ANY(:category_ids)')
            params['category_id'] = category_id
            params['category_ids'] = category_ids or [category_id]

        if tag_slug:
            where_clauses.append('EXISTS (SELECT 1 FROM ProductTags pt JOIN Tags t ON t.id = pt.tag_id WHERE pt.product_id = p.id AND t.slug = :tag_slug AND t.is_active = TRUE)')
            params['tag_slug'] = tag_slug

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
        order_by = Product._order_by_for_sort(sort_by)

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
ORDER BY rev.avg_rating DESC, rev.review_count DESC, inv.total_stock DESC, p.id ASC
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

    @staticmethod
    def get_related(product_id, category_id, limit=4):
        rows = app.db.execute(
            Product._query_base([
                'p.available = TRUE',
                'p.category_id = :category_id',
                'p.id != :product_id',
            ]) + '''
ORDER BY ((COALESCE(rev.avg_rating, 0) * 20) + (COALESCE(rev.review_count, 0) * 3) + (COALESCE(ord.order_count, 0) * 5)) DESC,
         inv.total_stock DESC,
         p.id ASC
LIMIT :limit
''',
            product_id=product_id,
            category_id=category_id,
            limit=limit,
        )
        return Product._rows_to_products(rows)

    @staticmethod
    def get_bundle_suggestions(product_id, limit=4):
        rows = app.db.execute(
            Product._query_base([
                'p.available = TRUE',
                'p.id IN ('
                'SELECT oi2.product_id '
                'FROM order_items oi '
                'JOIN order_items oi2 ON oi.order_id = oi2.order_id '
                'WHERE oi.product_id = :product_id AND oi2.product_id != :product_id '
                'GROUP BY oi2.product_id '
                'ORDER BY COUNT(*) DESC '
                'LIMIT :limit'
                ')',
            ]) + '''
ORDER BY ord.order_count DESC, rev.review_count DESC, p.id ASC
''',
            product_id=product_id,
            limit=limit,
        )
        return Product._rows_to_products(rows)

    @staticmethod
    def get_personalized(user_id=None, recent_ids=None, wishlist_ids=None, cart_product_ids=None, limit=8):
        recent_ids = [int(value) for value in (recent_ids or [])]
        wishlist_ids = [int(value) for value in (wishlist_ids or [])]
        cart_product_ids = [int(value) for value in (cart_product_ids or [])]

        seed_ids = []
        seen = set()
        for group in (wishlist_ids, recent_ids, cart_product_ids):
            for value in group:
                if value not in seen:
                    seen.add(value)
                    seed_ids.append(value)

        seed_categories = []
        if seed_ids:
            rows = app.db.execute('''
SELECT DISTINCT category_id
FROM Products
WHERE id = ANY(:seed_ids)
''', seed_ids=seed_ids)
            seed_categories = [row[0] for row in rows]

        if user_id is not None:
            rows = app.db.execute('''
SELECT DISTINCT p.category_id
FROM order_items oi
JOIN Products p ON p.id = oi.product_id
JOIN orders o ON o.id = oi.order_id
WHERE o.user_id = :user_id
ORDER BY p.category_id
LIMIT 6
''', user_id=user_id)
            for row in rows:
                if row[0] not in seed_categories:
                    seed_categories.append(row[0])

        if not seed_categories:
            return Product.get_top_rated(limit)

        rows = app.db.execute(
            Product._query_base([
                'p.available = TRUE',
                'p.category_id = ANY(:category_ids)',
                '(NOT (:exclude_enabled) OR p.id != ALL(:exclude_ids))',
            ]) + '''
ORDER BY (
            CASE WHEN p.id = ANY(:wishlist_ids) THEN 18 ELSE 0 END +
            CASE WHEN p.id = ANY(:recent_ids) THEN 12 ELSE 0 END +
            CASE WHEN p.id = ANY(:cart_ids) THEN 9 ELSE 0 END +
            (COALESCE(rev.avg_rating, 0) * 20) +
            (COALESCE(rev.review_count, 0) * 3) +
            (COALESCE(ord.order_count, 0) * 5)
         ) DESC,
         inv.total_stock DESC,
         p.id ASC
LIMIT :limit
''',
            category_ids=seed_categories,
            exclude_enabled=bool(seed_ids),
            exclude_ids=seed_ids or [0],
            wishlist_ids=wishlist_ids or [0],
            recent_ids=recent_ids or [0],
            cart_ids=cart_product_ids or [0],
            limit=limit,
        )
        products = Product._rows_to_products(rows)
        if products:
            return products
        return Product.get_top_rated(limit)
