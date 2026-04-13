from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import current_user, login_required

from .models.cart import CartItem
from .models.user import User

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
    user = None
    if user_id is not None:
        user = User.get(user_id)
        if user is None:
            flash('User not found')
            return redirect(url_for('index.index'))
        items = CartItem.get_items_by_user(user_id)
        total = sum(item.line_total for item in items)
    return render_template('cart.html', items=items, user=user, user_id=user_id, total=total)


@bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    product_id = request.form.get('product_id', type=int)
    seller_id = request.form.get('seller_id', type=int)
    quantity = request.form.get('quantity', type=int)

    if product_id is None or seller_id is None:
        flash('Missing product or seller.')
        return redirect(url_for('index.index'))

    if quantity is None or quantity <= 0:
        quantity = 1

    CartItem.add_item(
        user_id=current_user.id,
        product_id=product_id,
        seller_id=seller_id,
        quantity=quantity
    )

    flash('Item added to cart.')
    return redirect(url_for('products.product_detail', product_id=product_id))