from flask import current_app as app


class Category:
    def __init__(self, id, name, parent_id=None, slug=None, is_active=True):
        self.id = id
        self.name = name
        self.parent_id = parent_id
        self.slug = slug
        self.is_active = is_active
        self.children = []
        self.parent_name = None

    @property
    def is_top_level(self):
        return self.parent_id is None

    @property
    def path_label(self):
        if self.parent_name:
            return f'{self.parent_name} > {self.name}'
        return self.name

    @staticmethod
    def _rows_to_categories(rows):
        return [Category(*row) for row in rows]

    @staticmethod
    def get_all(include_inactive=False):
        where_sql = '' if include_inactive else 'WHERE is_active = TRUE'
        rows = app.db.execute('''
SELECT id, name, parent_id, slug, is_active
FROM Categories
''' + where_sql + '''
ORDER BY COALESCE(parent_id, id), parent_id NULLS FIRST, name
''')
        return Category._rows_to_categories(rows)

    @staticmethod
    def get_top_level(include_inactive=False):
        where_clauses = ['parent_id IS NULL']
        if not include_inactive:
            where_clauses.append('is_active = TRUE')
        rows = app.db.execute(f'''
SELECT id, name, parent_id, slug, is_active
FROM Categories
WHERE {' AND '.join(where_clauses)}
ORDER BY name
''')
        return Category._rows_to_categories(rows)

    @staticmethod
    def get_leaf_categories(include_inactive=False):
        where_clauses = ['NOT EXISTS (SELECT 1 FROM Categories c2 WHERE c2.parent_id = c.id AND c2.is_active = TRUE)']
        if not include_inactive:
            where_clauses.append('c.is_active = TRUE')

        rows = app.db.execute(f'''
SELECT
    c.id,
    c.name,
    c.parent_id,
    c.slug,
    c.is_active
FROM Categories c
WHERE {' AND '.join(where_clauses)}
ORDER BY c.name
''')
        categories = Category._rows_to_categories(rows)
        parent_lookup = {category.id: category.name for category in Category.get_all(include_inactive=True)}
        for category in categories:
            category.parent_name = parent_lookup.get(category.parent_id)
        return categories

    @staticmethod
    def get_tree(include_inactive=False):
        categories = Category.get_all(include_inactive=include_inactive)
        by_id = {category.id: category for category in categories}
        roots = []
        for category in categories:
            category.children = []
        for category in categories:
            if category.parent_id and category.parent_id in by_id:
                parent = by_id[category.parent_id]
                parent.children.append(category)
                category.parent_name = parent.name
            else:
                roots.append(category)
        roots.sort(key=lambda category: category.name)
        for category in categories:
            category.children.sort(key=lambda child: child.name)
        return roots

    @staticmethod
    def get_descendant_ids(category_id):
        rows = app.db.execute('''
WITH RECURSIVE descendants AS (
    SELECT id
    FROM Categories
    WHERE id = :category_id
  UNION ALL
    SELECT c.id
    FROM Categories c
    JOIN descendants d ON c.parent_id = d.id
    WHERE c.is_active = TRUE
)
SELECT id FROM descendants
''', category_id=category_id)
        return [row[0] for row in rows]

    @staticmethod
    def create(name, parent_id=None):
        slug = Category.slugify(name)
        rows = app.db.execute('''
INSERT INTO Categories(name, parent_id, slug, is_active)
VALUES (:name, :parent_id, :slug, TRUE)
RETURNING id, name, parent_id, slug, is_active
''', name=name, parent_id=parent_id, slug=slug)
        return Category(*rows[0]) if rows else None

    @staticmethod
    def slugify(value):
        import re
        return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')
