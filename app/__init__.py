from flask import Flask
from flask_login import LoginManager, current_user
from .config import Config
from .db import DB


login = LoginManager()
login.login_view = 'users.login'
_CACHED_TOP_LEVEL_CATEGORIES = None


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.db = DB(app)
    login.init_app(app)

    @app.context_processor
    def inject_hud_stats():
        from .models.category import Category
        from .marketplace import get_recently_viewed_ids, get_wishlist_ids

        global _CACHED_TOP_LEVEL_CATEGORIES
        if _CACHED_TOP_LEVEL_CATEGORIES is None:
            _CACHED_TOP_LEVEL_CATEGORIES = Category.get_top_level()
        categories = _CACHED_TOP_LEVEL_CATEGORIES
        wishlist_count = len(get_wishlist_ids())
        recent_count = len(get_recently_viewed_ids())
        if not current_user.is_authenticated:
            return {
                'hud_player': 'Guest Trainer',
                'hud_items': 0,
                'hud_gold': 0.0,
                'site_categories': categories,
                'wishlist_count': wishlist_count,
                'recent_count': recent_count,
            }

        from .models.cart import CartItem

        hud_items, hud_gold = CartItem.get_hud_totals(current_user.id)
        return {
            'hud_player': f'{current_user.firstname} {current_user.lastname}',
            'hud_items': hud_items,
            'hud_gold': hud_gold,
            'site_categories': categories,
            'wishlist_count': wishlist_count,
            'recent_count': recent_count,
        }

    from .index import bp as index_bp
    app.register_blueprint(index_bp)

    from .users import bp as user_bp
    app.register_blueprint(user_bp)

    from .products import bp as products_bp
    app.register_blueprint(products_bp)

    from .social import bp as social_bp
    app.register_blueprint(social_bp)

    from .carts import bp as carts_bp
    app.register_blueprint(carts_bp)

    from .seller_orders import bp as seller_orders_bp
    app.register_blueprint(seller_orders_bp)

    return app
