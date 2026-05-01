from flask import render_template
from flask_login import current_user
import datetime

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
    )
