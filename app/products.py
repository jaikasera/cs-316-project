from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import current_user, login_required

from .models.product import Product
from .models.inventory import InventoryItem
from .models.category import Category
from .models.feedback import Feedback

bp = Blueprint('products', __name__)


def _normalize_page_and_size(page_raw, per_page_raw, default_per_page=25):
    page = page_raw if isinstance(page_raw, int) and page_raw > 0 else 1
    allowed = [10, 25, 50, 100]
    per_page = per_page_raw if per_page_raw in allowed else default_per_page
    return page, per_page


@bp.route('/products')
def browse_products():
    category_id = request.args.get('category_id', type=int)
    keyword = request.args.get('keyword', default='', type=str)
    sort_by = request.args.get('sort_by', default='price_asc', type=str)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    min_rating = request.args.get('min_rating', type=float)

    products = Product.search(
        category_id=category_id,
        keyword=keyword,
        sort_by=sort_by,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating
    )
    categories = Category.get_all()

    return render_template(
        'products.html',
        products=products,
        categories=categories,
        selected_category=category_id,
        keyword=keyword,
        sort_by=sort_by,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating
    )


@bp.route('/products/<int:product_id>')
def product_detail(product_id):
    product = Product.get(product_id)
    if product is None:
        return redirect(url_for('products.browse_products'))

    sellers = InventoryItem.get_sellers_for_product(product_id)
    reviews = Feedback.get_product_reviews(product_id)
    avg_rating = Feedback.get_product_average_rating(product_id)

    return render_template(
        'product_detail.html',
        product=product,
        sellers=sellers,
        reviews=reviews,
        avg_rating=avg_rating
    )


@bp.route('/products/new', methods=['GET', 'POST'])
@login_required
def create_product():
    categories = Category.get_all()

    if request.method == 'POST':
        category_id = request.form.get('category_id', type=int)
        name = request.form.get('name')
        description = request.form.get('description')
        image_url = request.form.get('image_url')

        product_id = Product.create(
            current_user.id,
            category_id,
            name,
            description,
            image_url,
            True
        )
        return redirect(url_for('products.product_detail', product_id=product_id))

    return render_template('product_form.html', categories=categories, product=None)


@bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.get(product_id)
    if product is None or product.creator_id != current_user.id:
        return redirect(url_for('products.browse_products'))

    categories = Category.get_all()

    if request.method == 'POST':
        category_id = request.form.get('category_id', type=int)
        name = request.form.get('name')
        description = request.form.get('description')
        image_url = request.form.get('image_url')
        available = bool(request.form.get('available'))

        Product.update(
            product_id,
            current_user.id,
            category_id,
            name,
            description,
            image_url,
            available
        )
        return redirect(url_for('products.product_detail', product_id=product_id))

    return render_template('product_form.html', categories=categories, product=product)


@bp.route('/products/my')
@login_required
def my_products():
    products = Product.get_by_creator(current_user.id)
    return render_template('my_products.html', products=products)


@bp.route('/products/top/<int:k>')
def top_k_products_json(k):
    if k <= 0:
        return jsonify([])

    products = Product.get_top_k_expensive(k)
    return jsonify([
        {
            'id': row[0],
            'name': row[1],
            'top_price': str(row[2]),
            'min_price': str(row[3]),
            'available': row[4]
        }
        for row in products
    ])


@bp.route('/products/top')
def top_k_products_page():
    k = request.args.get('k', default=5, type=int)
    if k <= 0:
        k = 5

    products = Product.get_top_k_expensive(k)
    return render_template('top_products.html', products=products, k=k)


@bp.route('/sellers/<int:seller_id>/inventory')
def seller_inventory_json(seller_id: int):
    page_raw = request.args.get('page', default=1, type=int)
    per_page_raw = request.args.get('per_page', default=25, type=int)
    page, per_page = _normalize_page_and_size(page_raw, per_page_raw)

    products = InventoryItem.get_products_for_seller(seller_id, page=page, per_page=per_page)
    return jsonify([{
        'id': p.product_id,
        'name': p.name,
        'description': p.description,
        'image_url': p.image_url,
        'available': p.available,
        'quantity': p.quantity,
        'inventory_price': str(p.inventory_price)
    } for p in products])


@bp.route('/sellers/inventory')
def seller_inventory_page():
    seller_id = request.args.get('seller_id', type=int)
    if seller_id is None:
        seller_id = -1

    page_raw = request.args.get('page', default=1, type=int)
    per_page_raw = request.args.get('per_page', default=25, type=int)
    page, per_page = _normalize_page_and_size(page_raw, per_page_raw)

    total_count = InventoryItem.get_product_count_for_seller(seller_id)
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    if page > total_pages:
        page = total_pages

    products = InventoryItem.get_products_for_seller(seller_id, page=page, per_page=per_page)
    return render_template(
        'seller_inventory.html',
        products=products,
        seller_id=seller_id,
        page=page,
        per_page=per_page,
        total_count=total_count,
        total_pages=total_pages,
    )


@bp.route('/inventory/add', methods=['POST'])
@login_required
def add_inventory():
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', type=int)
    price_raw = request.form.get('price', type=str)
    if price_raw is not None and price_raw.strip() != '':
        try:
            price = float(price_raw)
        except ValueError:
            price = None
    else:
        price = None

    if product_id is None:
        flash('Product ID is required.')
        return redirect(url_for('index.index'))

    if Product.get(product_id) is None:
        flash('No product exists with that ID.')
        return redirect(url_for('index.index'))

    if quantity is None or quantity < 0:
        flash('Quantity must be a non-negative whole number.')
        return redirect(url_for('index.index'))

    if price is None or price < 0:
        flash('Price must be a non-negative number.')
        return redirect(url_for('index.index'))

    InventoryItem.add_item_to_inventory(
        seller_id=current_user.id,
        product_id=product_id,
        quantity=quantity,
        price=price,
    )
    flash('Product listing saved to your inventory.')
    return redirect(url_for('products.seller_inventory_page', seller_id=current_user.id))


@bp.route('/inventory/my', methods=['GET'])
@login_required
def my_inventory_lookup():
    product_id = request.args.get('product_id', type=int)
    if product_id is None:
        flash('Enter a product ID to open your listing.')
        return redirect(url_for('index.index'))
    return redirect(url_for('products.my_inventory_detail', product_id=product_id))


@bp.route('/inventory/my/<int:product_id>', methods=['GET'])
@login_required
def my_inventory_detail(product_id):
    page_raw = request.args.get('page', default=1, type=int)
    per_page_raw = request.args.get('per_page', default=25, type=int)
    page, per_page = _normalize_page_and_size(page_raw, per_page_raw)

    listing = InventoryItem.get_inventory_item_for_seller(current_user.id, product_id)
    if listing is None:
        flash('That product is not in your inventory (or the product no longer exists).')
        return redirect(
            url_for(
                'products.seller_inventory_page',
                seller_id=current_user.id,
                page=page,
                per_page=per_page,
            )
        )
    return render_template(
        'inventory_listing_detail.html',
        listing=listing,
        page=page,
        per_page=per_page,
    )


@bp.route('/inventory/my/<int:product_id>/quantity', methods=['POST'])
@login_required
def my_inventory_update_quantity(product_id):
    page_raw = request.form.get('page', type=int)
    per_page_raw = request.form.get('per_page', type=int)
    page, per_page = _normalize_page_and_size(page_raw, per_page_raw)

    quantity = request.form.get('quantity', type=int)
    if quantity is None or quantity < 0:
        flash('Quantity must be a non-negative whole number.')
        return redirect(
            url_for(
                'products.my_inventory_detail',
                product_id=product_id,
                page=page,
                per_page=per_page,
            )
        )

    rows = InventoryItem.update_inventory_item_quantity(
        current_user.id, product_id, quantity
    )
    if rows == 0:
        flash('Listing not found.')
        return redirect(
            url_for(
                'products.seller_inventory_page',
                seller_id=current_user.id,
                page=page,
                per_page=per_page,
            )
        )

    flash('Quantity updated.')
    return redirect(
        url_for(
            'products.my_inventory_detail',
            product_id=product_id,
            page=page,
            per_page=per_page,
        )
    )


@bp.route('/inventory/my/<int:product_id>/remove', methods=['POST'])
@login_required
def my_inventory_remove(product_id):
    page_raw = request.form.get('page', type=int)
    per_page_raw = request.form.get('per_page', type=int)
    page, per_page = _normalize_page_and_size(page_raw, per_page_raw)

    rows = InventoryItem.remove_inventory_item(current_user.id, product_id)
    if rows == 0:
        flash('Listing not found.')
    else:
        flash('Removed this product from your inventory.')
    return redirect(
        url_for(
            'products.seller_inventory_page',
            seller_id=current_user.id,
            page=page,
            per_page=per_page,
        )
    )