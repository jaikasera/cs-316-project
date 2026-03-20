from flask import Blueprint, render_template, request, jsonify
from .models.cart import CartItem

bp = Blueprint('carts', __name__)


@bp.route('/cart/items/<int:user_id>')
def cart_items_json(user_id):
    items = CartItem.get_items_by_user(user_id)
    return jsonify([{
        'product_id': item.product_id,
        'product_name': item.product_name,
        'seller_id': item.seller_id,
        'seller_name': item.seller_name,
        'quantity': item.quantity,
        'unit_price': float(item.unit_price),
        'line_total': item.line_total,
        'added_at': item.added_at.isoformat() if item.added_at else None
    } for item in items])


@bp.route('/cart')
def cart_page():
    user_id = request.args.get('user_id', type=int)
    items = []
    total = 0.0
    if user_id is not None:
        items = CartItem.get_items_by_user(user_id)
        total = sum(item.line_total for item in items)
    return render_template('cart.html', items=items, user_id=user_id, total=total)
