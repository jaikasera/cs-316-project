from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from types import SimpleNamespace
from flask_login import current_user, login_required

from .marketplace import (
    clear_active_coupon,
    evaluate_coupon,
    get_active_coupon_code,
    get_saved_for_later,
    pop_saved_for_later,
    save_for_later as save_session_for_later,
    set_active_coupon_code,
)
from .models.cart import CartItem
from .models.buyer_order import BuyerOrder
from .models.coupon import Coupon
from .models.analytics import OrderAnalytics
from .models.wishlist import Wishlist
from .models.user import User
from .models.product import Product

bp = Blueprint('carts', __name__)


def _safe_next_url(next_url, fallback_endpoint, **fallback_values):
    if next_url and next_url.startswith('/'):
        return next_url
    return url_for(fallback_endpoint, **fallback_values)


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
    saved_items = []
    total = 0.0
    user = None
    has_stock_issues = False
    guest_cart = []
    coupon_code = session.get('coupon_code', '')
    coupon_discount = 0.0
    coupon_error = None

    if user_id is not None:
        user = User.get(user_id)
        if user is None:
            flash('User not found', 'warning')
            return redirect(url_for('index.index'))
        items = CartItem.get_items_by_user(user_id, saved=False)
        saved_items = CartItem.get_items_by_user(user_id, saved=True)
        total = sum(item.line_total for item in items)
        has_stock_issues = any(item.insufficient_stock or item.out_of_stock for item in items)

    elif not current_user.is_authenticated:
        # Show guest cart from session
        guest_cart = session.get('guest_cart', [])

    coupon = {'code': None, 'valid': False, 'message': None, 'discount': 0.0, 'label': None}
    final_total = total
    if current_user.is_authenticated and current_user.id == user_id:
        for saved in get_saved_for_later():
            product = Product.get(saved['product_id'])
            snapshot = CartItem.get_inventory_snapshot(saved['product_id'], saved['seller_id'])
            if product is None or snapshot is None:
                continue
            available, product_name, stock_quantity, unit_price, seller_firstname, seller_lastname = snapshot
            saved_items.append(SimpleNamespace(
                product_id=saved['product_id'],
                seller_id=saved['seller_id'],
                quantity=saved['quantity'],
                product_name=product_name,
                product_image_url=product.image_url,
                seller_name=f'{seller_firstname} {seller_lastname}',
                unit_price=float(unit_price),
                stock_quantity=stock_quantity,
                available=available,
            ))

        coupon = evaluate_coupon(total, get_active_coupon_code())
        final_total = round(max(0.0, total - coupon['discount']), 2)

    return render_template(
        'cart.html',
        items=items,
        user=user,
        user_id=user_id,
        total=total,
        saved_items=saved_items,
        has_stock_issues=has_stock_issues,
        guest_cart=guest_cart,
        coupon=coupon,
        final_total=final_total,
    )


@bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    product_id = request.form.get('product_id', type=int)
    seller_id = request.form.get('seller_id', type=int)
    quantity = request.form.get('quantity', type=int)
    next_url = request.form.get('next')

    if product_id is None or seller_id is None:
        flash('Missing product or seller.', 'danger')
        return redirect(url_for('index.index'))

    if quantity is None or quantity <= 0:
        quantity = 1

    # Guest cart: store in session
    if not current_user.is_authenticated:
        inventory_snapshot = CartItem.get_inventory_snapshot(product_id, seller_id)
        if inventory_snapshot is None:
            flash('That seller listing could not be found.', 'warning')
            return redirect(_safe_next_url(next_url, 'products.product_detail', product_id=product_id))

        available, product_name, stock_quantity, price, seller_firstname, seller_lastname = inventory_snapshot
        if not available or stock_quantity <= 0:
            flash('This product is not available.', 'warning')
            return redirect(_safe_next_url(next_url, 'products.product_detail', product_id=product_id))

        guest_cart = session.get('guest_cart', [])
        # Check if already in guest cart
        found = False
        for item in guest_cart:
            if item['product_id'] == product_id and item['seller_id'] == seller_id:
                item['quantity'] = min(item['quantity'] + quantity, stock_quantity)
                item['product_name'] = product_name
                item['unit_price'] = float(price)
                item['seller_name'] = f'{seller_firstname} {seller_lastname}'
                found = True
                break
        if not found:
            guest_cart.append({
                'product_id': product_id,
                'seller_id': seller_id,
                'quantity': min(quantity, stock_quantity),
                'product_name': product_name,
                'unit_price': float(price),
                'seller_name': f'{seller_firstname} {seller_lastname}',
            })
        session['guest_cart'] = guest_cart
        flash(f'Added {quantity} x {product_name} to your cart. Log in to checkout.', 'success')
        return redirect(_safe_next_url(next_url, 'products.product_detail', product_id=product_id))

    # Authenticated user: normal flow
    inventory_snapshot = CartItem.get_inventory_snapshot(product_id, seller_id)
    if inventory_snapshot is None:
        flash('That seller listing could not be found.', 'warning')
        return redirect(_safe_next_url(next_url, 'products.product_detail', product_id=product_id))

    available, product_name, stock_quantity, _, seller_firstname, seller_lastname = inventory_snapshot
    if not available:
        flash('This product is inactive and cannot be added to the cart.', 'warning')
        return redirect(_safe_next_url(next_url, 'products.product_detail', product_id=product_id))

    if stock_quantity <= 0:
        flash('That seller is currently out of stock.', 'warning')
        return redirect(_safe_next_url(next_url, 'products.product_detail', product_id=product_id))

    existing_quantity = CartItem.get_item_quantity(current_user.id, product_id, seller_id)
    desired_quantity = existing_quantity + quantity
    if desired_quantity > stock_quantity:
        flash(f'Only {stock_quantity} unit(s) are available from this seller right now.', 'warning')
        return redirect(_safe_next_url(next_url, 'products.product_detail', product_id=product_id))

    CartItem.add_item(
        user_id=current_user.id,
        product_id=product_id,
        seller_id=seller_id,
        quantity=quantity
    )

    seller_name = f'{seller_firstname} {seller_lastname}'
    flash(f'Added {quantity} x {product_name} from {seller_name} to your cart.', 'success')
    return redirect(_safe_next_url(next_url, 'products.product_detail', product_id=product_id))


@bp.route('/cart/update', methods=['POST'])
@login_required
def update_cart_item():
    product_id = request.form.get('product_id', type=int)
    seller_id = request.form.get('seller_id', type=int)
    quantity = request.form.get('quantity', type=int)

    if product_id is None or seller_id is None or quantity is None or quantity < 1:
        flash('Invalid quantity.', 'danger')
        return redirect(url_for('carts.cart_page'))

    CartItem.update_quantity(current_user.id, product_id, seller_id, quantity)
    flash('Quantity updated.', 'success')
    return redirect(url_for('carts.cart_page'))


@bp.route('/cart/remove', methods=['POST'])
@login_required
def remove_cart_item():
    product_id = request.form.get('product_id', type=int)
    seller_id = request.form.get('seller_id', type=int)

    if product_id is None or seller_id is None:
        flash('Invalid item.', 'danger')
        return redirect(url_for('carts.cart_page'))

    CartItem.remove_item(current_user.id, product_id, seller_id)
    flash('Item removed from cart.', 'info')
    return redirect(url_for('carts.cart_page'))


@bp.route('/cart/save-for-later', methods=['POST'])
@login_required
def save_cart_item_for_later():
    product_id = request.form.get('product_id', type=int)
    seller_id = request.form.get('seller_id', type=int)

    if product_id is None or seller_id is None:
        flash('Invalid item.', 'danger')
        return redirect(url_for('carts.cart_page'))

    quantity = CartItem.get_item_quantity(current_user.id, product_id, seller_id)
    if quantity <= 0:
        flash('That item is no longer in your bag.', 'warning')
        return redirect(url_for('carts.cart_page'))

    save_session_for_later(product_id, seller_id, quantity)
    CartItem.remove_item(current_user.id, product_id, seller_id)
    flash('Item moved to Save for later.', 'success')
    return redirect(url_for('carts.cart_page'))


@bp.route('/cart/save-for-later/restore', methods=['POST'])
@login_required
def restore_saved_item():
    product_id = request.form.get('product_id', type=int)
    seller_id = request.form.get('seller_id', type=int)

    if product_id is None or seller_id is None:
        flash('Invalid saved item.', 'danger')
        return redirect(url_for('carts.cart_page'))

    saved = pop_saved_for_later(product_id, seller_id)
    if saved is None:
        flash('That saved item could not be found.', 'warning')
        return redirect(url_for('carts.cart_page'))

    snapshot = CartItem.get_inventory_snapshot(product_id, seller_id)
    if snapshot is None:
        flash('That seller listing is no longer available.', 'warning')
        return redirect(url_for('carts.cart_page'))

    available, _, stock_quantity, _, _, _ = snapshot
    if not available or stock_quantity <= 0:
        flash('That saved item is currently unavailable.', 'warning')
        return redirect(url_for('carts.cart_page'))

    CartItem.add_item(current_user.id, product_id, seller_id, min(saved['quantity'], stock_quantity))
    flash('Saved item moved back into your bag.', 'success')
    return redirect(url_for('carts.cart_page'))


@bp.route('/cart/save-for-later/remove', methods=['POST'])
@login_required
def remove_saved_item():
    product_id = request.form.get('product_id', type=int)
    seller_id = request.form.get('seller_id', type=int)
    if product_id is None or seller_id is None:
        flash('Invalid saved item.', 'danger')
        return redirect(url_for('carts.cart_page'))

    pop_saved_for_later(product_id, seller_id)
    flash('Saved item removed.', 'info')
    return redirect(url_for('carts.cart_page'))


@bp.route('/cart/coupon', methods=['POST'])
@login_required
def apply_coupon():
    code = request.form.get('coupon_code', type=str) or ''
    subtotal = sum(item.line_total for item in CartItem.get_items_by_user(current_user.id))
    result = evaluate_coupon(subtotal, code)
    if not result['code']:
        clear_active_coupon()
        flash('Coupon code not recognized.', 'warning')
    elif not result['valid']:
        set_active_coupon_code(result['code'])
        flash(result['message'], 'warning')
    else:
        set_active_coupon_code(result['code'])
        flash(f'{result["code"]} applied for P${result["discount"]:.2f} off.', 'success')
    return redirect(url_for('carts.cart_page'))


@bp.route('/cart/coupon/remove', methods=['POST'])
@login_required
def remove_coupon():
    clear_active_coupon()
    flash('Coupon removed.', 'info')
    return redirect(url_for('carts.cart_page'))


@bp.route('/cart/checkout', methods=['POST'])
@login_required
def checkout():
    subtotal = sum(item.line_total for item in CartItem.get_items_by_user(current_user.id))
    coupon = evaluate_coupon(subtotal, get_active_coupon_code())
    order_id, error = CartItem.checkout(current_user.id, discount_amount=coupon['discount'])
    if error:
        flash(error, 'danger')
        return redirect(url_for('carts.cart_page'))

    if coupon['discount'] > 0:
        clear_active_coupon()
    flash(f'Order #{order_id} placed successfully!', 'success')
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

    keyword = (request.args.get('q') or '').strip()
    status = request.args.get('status', 'all')
    if status not in ('all', 'fulfilled', 'pending', 'cancelled'):
        status = 'all'
    date_from = request.args.get('date_from') or None
    date_to = request.args.get('date_to') or None
    sort_by = request.args.get('sort_by', 'date_desc')
    if sort_by not in ('date_desc', 'date_asc', 'amount_desc', 'amount_asc', 'items_desc'):
        sort_by = 'date_desc'

    orders, total_count = BuyerOrder.get_orders_by_user(
        current_user.id, page, per_page,
        keyword=keyword, status=status,
        date_from=date_from, date_to=date_to,
        sort_by=sort_by
    )
    total_pages = max(1, (total_count + per_page - 1) // per_page)

    if page > total_pages:
        page = total_pages
        orders, total_count = BuyerOrder.get_orders_by_user(
            current_user.id, page, per_page,
            keyword=keyword, status=status,
            date_from=date_from, date_to=date_to,
            sort_by=sort_by
        )

    return render_template('order_history.html',
                           orders=orders, page=page, per_page=per_page,
                           total_count=total_count, total_pages=total_pages,
                           search_q=keyword, search_status=status,
                           date_from=date_from or '', date_to=date_to or '',
                           sort_by=sort_by)


@bp.route('/orders/analytics')
@login_required
def order_analytics():
    summary = OrderAnalytics.get_spending_summary(current_user.id)
    monthly = OrderAnalytics.get_monthly_spending(current_user.id)
    top_products = OrderAnalytics.get_top_products(current_user.id)
    top_sellers = OrderAnalytics.get_top_sellers(current_user.id)
    categories = OrderAnalytics.get_category_breakdown(current_user.id)
    return render_template('order_analytics.html',
                           summary=summary, monthly=monthly,
                           top_products=top_products, top_sellers=top_sellers,
                           categories=categories)


@bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order, line_items = BuyerOrder.get_order_detail(order_id, current_user.id)
    if order is None:
        flash('Order not found.', 'warning')
        return redirect(url_for('carts.order_history'))

    return render_template('order_detail.html', order=order, line_items=line_items)


@bp.route('/orders/<int:order_id>/receipt')
@login_required
def order_receipt(order_id):
    order, line_items = BuyerOrder.get_order_detail(order_id, current_user.id)
    if order is None:
        flash('Order not found.', 'warning')
        return redirect(url_for('carts.order_history'))

    user = User.get(current_user.id)
    return render_template('order_receipt.html', order=order, line_items=line_items, user=user)


@bp.route('/orders/<int:order_id>/reorder', methods=['POST'])
@login_required
def reorder(order_id):
    added, skipped = CartItem.reorder(current_user.id, order_id)
    if added > 0:
        flash(f'{added} item(s) added to your cart.', 'success')
    if skipped:
        flash(f'Could not re-add: {", ".join(skipped)} (out of stock or unavailable).', 'warning')
    if added == 0 and not skipped:
        flash('No items could be added.', 'warning')
    return redirect(url_for('carts.cart_page'))


@bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    success, error = BuyerOrder.cancel_order(order_id, current_user.id)
    if success:
        flash(f'Order #{order_id} has been cancelled and refunded.', 'success')
    else:
        flash(error, 'danger')
    return redirect(url_for('carts.order_detail', order_id=order_id))


# ── Wishlist ──

@bp.route('/wishlist')
@login_required
def wishlist_page():
    items = Wishlist.get_items(current_user.id)
    return render_template('wishlist.html', items=items)


@bp.route('/wishlist/add', methods=['POST'])
@login_required
def wishlist_add():
    product_id = request.form.get('product_id', type=int)
    next_url = request.form.get('next')
    if product_id is None:
        flash('Invalid product.', 'danger')
        return redirect(url_for('index.index'))
    Wishlist.add(current_user.id, product_id)
    flash('Added to wishlist.', 'success')
    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect(url_for('products.product_detail', product_id=product_id))


@bp.route('/wishlist/remove', methods=['POST'])
@login_required
def wishlist_remove():
    product_id = request.form.get('product_id', type=int)
    if product_id is None:
        flash('Invalid product.', 'danger')
        return redirect(url_for('carts.wishlist_page'))
    Wishlist.remove(current_user.id, product_id)
    flash('Removed from wishlist.', 'info')
    return redirect(url_for('carts.wishlist_page'))
