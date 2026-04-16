from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import current_user, login_required

from .models.cart import CartItem
from .models.buyer_order import BuyerOrder
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
    if user_id is None and current_user.is_authenticated:
        user_id = current_user.id

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


@bp.route('/cart/update', methods=['POST'])
@login_required
def update_cart_item():
    product_id = request.form.get('product_id', type=int)
    seller_id = request.form.get('seller_id', type=int)
    quantity = request.form.get('quantity', type=int)

    if not all([product_id, seller_id]) or quantity is None or quantity < 1:
        flash('Invalid quantity.')
        return redirect(url_for('carts.cart_page'))

    CartItem.update_quantity(current_user.id, product_id, seller_id, quantity)
    flash('Quantity updated.')
    return redirect(url_for('carts.cart_page'))


@bp.route('/cart/remove', methods=['POST'])
@login_required
def remove_cart_item():
    product_id = request.form.get('product_id', type=int)
    seller_id = request.form.get('seller_id', type=int)

    if not all([product_id, seller_id]):
        flash('Invalid item.')
        return redirect(url_for('carts.cart_page'))

    CartItem.remove_item(current_user.id, product_id, seller_id)
    flash('Item removed from cart.')
    return redirect(url_for('carts.cart_page'))


@bp.route('/cart/checkout', methods=['POST'])
@login_required
def checkout():
    order_id, error = CartItem.checkout(current_user.id)
    if error:
        flash(error)
        return redirect(url_for('carts.cart_page'))

    flash(f'Order #{order_id} placed successfully!')
    return redirect(url_for('carts.order_detail', order_id=order_id))


@bp.route('/orders')
@login_required
def order_history():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    if per_page not in (10, 20, 50):
        per_page = 20
    if page < 1:
        page = 1

    orders, total_count = BuyerOrder.get_orders_by_user(current_user.id, page, per_page)
    total_pages = max(1, (total_count + per_page - 1) // per_page)

    if page > total_pages:
        page = total_pages
        orders, total_count = BuyerOrder.get_orders_by_user(current_user.id, page, per_page)

    return render_template('order_history.html',
                           orders=orders, page=page, per_page=per_page,
                           total_count=total_count, total_pages=total_pages)


@bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order, line_items = BuyerOrder.get_order_detail(order_id, current_user.id)
    if order is None:
        flash('Order not found.')
        return redirect(url_for('carts.order_history'))

    return render_template('order_detail.html', order=order, line_items=line_items)
