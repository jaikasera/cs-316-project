from flask import render_template
from flask_login import current_user
import datetime

from .marketplace import get_recently_viewed_ids, get_wishlist_ids
from .models.cart import CartItem
from .models.product import Product
from .models.purchase import Purchase

from flask import Blueprint
bp = Blueprint('index', __name__)


@bp.route('/')
def index():
    # all available products
    products = Product.get_all(True)

    # recently added products for homepage cards
    recent_products = Product.get_recent(4)

    # top rated products for homepage cards
    top_rated_products = Product.get_top_rated(4)

    wishlist_ids = get_wishlist_ids()
    recently_viewed_ids = get_recently_viewed_ids()
    cart_product_ids = []
    if current_user.is_authenticated:
        cart_product_ids = [item.product_id for item in CartItem.get_items_by_user(current_user.id)]

    personalized_products = Product.get_personalized(
        user_id=current_user.id if current_user.is_authenticated else None,
        recent_ids=recently_viewed_ids,
        wishlist_ids=wishlist_ids,
        cart_product_ids=cart_product_ids,
        limit=10,
    )
    recently_viewed_products = Product.get_many(recently_viewed_ids[:10], available_only=False)
    wishlist_products = Product.get_many(wishlist_ids[:10], available_only=False)

    # purchases for logged-in user
    if current_user.is_authenticated:
        purchases = Purchase.get_all_by_uid_since(
            current_user.id,
            datetime.datetime(1980, 9, 14, 0, 0, 0)
        )
    else:
        purchases = None

    return render_template(
        'index.html',
        avail_products=products,
        purchase_history=purchases,
        recent_products=recent_products,
        top_rated_products=top_rated_products,
        personalized_products=personalized_products,
        recently_viewed_products=recently_viewed_products,
        wishlist_products=wishlist_products,
        wishlist_ids=set(wishlist_ids),
    )
