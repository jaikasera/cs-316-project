from collections import defaultdict

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from .models.seller_order import SellerOrder

bp = Blueprint('seller_orders', __name__)


@bp.route('/seller/orders')
@login_required
def seller_orders_page():
    keyword = (request.args.get('q') or '').strip()
    status = request.args.get('status', default='all', type=str)
    if status not in ('all', 'pending', 'complete'):
        status = 'all'

    summaries = SellerOrder.list_orders_for_seller(
        current_user.id, keyword=keyword, status=status
    )
    order_ids = [s.order_id for s in summaries]
    lines = SellerOrder.lines_for_orders(current_user.id, order_ids)
    lines_by_order = defaultdict(list)
    for line in lines:
        lines_by_order[line.order_id].append(line)

    return render_template(
        'seller_orders.html',
        summaries=summaries,
        lines_by_order=lines_by_order,
        search_q=keyword,
        search_status=status,
    )


@bp.route('/seller/orders/fulfill', methods=['POST'])
@login_required
def seller_fulfill_line():
    line_id = request.form.get('line_id', type=int)
    q = (request.form.get('q') or '').strip()
    status = request.form.get('status', default='all', type=str)
    if status not in ('all', 'pending', 'complete'):
        status = 'all'

    redirect_args = {}
    if q:
        redirect_args['q'] = q
    if status != 'all':
        redirect_args['status'] = status

    if line_id is None:
        flash('Invalid line item.')
        return redirect(url_for('seller_orders.seller_orders_page', **redirect_args))

    rows = SellerOrder.fulfill_line_item(line_id, current_user.id)
    if rows == 0:
        flash('Could not mark that line fulfilled (not found, not yours, or already fulfilled).')
    else:
        flash('Line item marked fulfilled.')

    return redirect(url_for('seller_orders.seller_orders_page', **redirect_args))
