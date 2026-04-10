from flask import current_app as app


class Category:
    def __init__(self, id, name):
        self.id = id
        self.name = name

    @staticmethod
    def get_all():
        rows = app.db.execute('''
SELECT id, name
FROM Categories
ORDER BY name
''')
        return [Category(*row) for row in rows]