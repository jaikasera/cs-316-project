import re

from flask import current_app as app


class Tag:
    def __init__(self, id, display_name, slug, created_by=None, is_active=True, usage_count=None):
        self.id = id
        self.display_name = display_name
        self.slug = slug
        self.created_by = created_by
        self.is_active = is_active
        self.usage_count = usage_count if usage_count is not None else 0

    @staticmethod
    def normalize_name(value):
        return re.sub(r'\s+', ' ', (value or '').strip())

    @staticmethod
    def slugify(value):
        return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')

    @staticmethod
    def parse_input(raw_value):
        tags = []
        seen = set()
        for piece in (raw_value or '').split(','):
            normalized = Tag.normalize_name(piece)
            if not normalized:
                continue
            slug = Tag.slugify(normalized)
            if not slug or slug in seen:
                continue
            seen.add(slug)
            tags.append(normalized[:40])
        return tags[:10]

    @staticmethod
    def get_all(include_inactive=False):
        where_sql = '' if include_inactive else 'WHERE is_active = TRUE'
        rows = app.db.execute('''
SELECT id, display_name, slug, created_by, is_active
FROM Tags
''' + where_sql + '''
ORDER BY display_name
''')
        return [Tag(*row) for row in rows]

    @staticmethod
    def get_all_with_usage(include_inactive=False):
        where_sql = '' if include_inactive else 'WHERE t.is_active = TRUE'
        rows = app.db.execute('''
SELECT
    t.id,
    t.display_name,
    t.slug,
    t.created_by,
    t.is_active,
    COUNT(pt.product_id) AS usage_count
FROM Tags t
LEFT JOIN ProductTags pt ON pt.tag_id = t.id
''' + where_sql + '''
GROUP BY t.id, t.display_name, t.slug, t.created_by, t.is_active
ORDER BY usage_count DESC, t.display_name ASC
''')
        return [Tag(*row) for row in rows]

    @staticmethod
    def get_for_product(product_id):
        rows = app.db.execute('''
SELECT t.id, t.display_name, t.slug, t.created_by, t.is_active
FROM Tags t
JOIN ProductTags pt ON pt.tag_id = t.id
WHERE pt.product_id = :product_id AND t.is_active = TRUE
ORDER BY t.display_name
''', product_id=product_id)
        return [Tag(*row) for row in rows]

    @staticmethod
    def get_names_for_product(product_id):
        return [tag.display_name for tag in Tag.get_for_product(product_id)]

    @staticmethod
    def get_for_products(product_ids):
        if not product_ids:
            return {}
        rows = app.db.execute('''
SELECT pt.product_id, t.id, t.display_name, t.slug, t.created_by, t.is_active
FROM ProductTags pt
JOIN Tags t ON t.id = pt.tag_id
WHERE pt.product_id = ANY(:product_ids) AND t.is_active = TRUE
ORDER BY t.display_name
''', product_ids=[int(value) for value in product_ids])
        grouped = {}
        for row in rows:
            grouped.setdefault(row[0], []).append(Tag(*row[1:]))
        return grouped

    @staticmethod
    def create(display_name, created_by=None):
        normalized = Tag.normalize_name(display_name)
        slug = Tag.slugify(normalized)
        rows = app.db.execute('''
INSERT INTO Tags(display_name, slug, created_by, is_active)
VALUES (:display_name, :slug, :created_by, TRUE)
ON CONFLICT (slug)
DO UPDATE SET display_name = EXCLUDED.display_name
RETURNING id, display_name, slug, created_by, is_active
''', display_name=normalized, slug=slug, created_by=created_by)
        return Tag(*rows[0]) if rows else None

    @staticmethod
    def ensure_many(tag_names, created_by=None):
        ensured = []
        for name in tag_names:
            tag = Tag.create(name, created_by=created_by)
            if tag:
                ensured.append(tag)
        return ensured

    @staticmethod
    def sync_product_tags(product_id, tag_names, created_by=None):
        tag_names = Tag.parse_input(','.join(tag_names) if isinstance(tag_names, list) else tag_names)
        tags = Tag.ensure_many(tag_names, created_by=created_by)
        tag_ids = [tag.id for tag in tags]

        app.db.execute('''
DELETE FROM ProductTags
WHERE product_id = :product_id
''', product_id=product_id)

        for tag_id in tag_ids:
            app.db.execute('''
INSERT INTO ProductTags(product_id, tag_id)
VALUES (:product_id, :tag_id)
ON CONFLICT (product_id, tag_id) DO NOTHING
''', product_id=product_id, tag_id=tag_id)

        return tags
