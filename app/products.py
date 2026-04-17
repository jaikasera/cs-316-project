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


def _safe_next_url(next_url, fallback_endpoint, **fallback_values):
    if next_url and next_url.startswith('/'):
        return next_url
    return url_for(fallback_endpoint, **fallback_values)


def _build_product_form_data(product=None):
    if request.method == 'POST':
        return {
            'category_id': request.form.get('category_id', type=int),
            'name': (request.form.get('name') or '').strip(),
            'description': (request.form.get('description') or '').strip(),
            'image_url': (request.form.get('image_url') or '').strip(),
            'available': bool(request.form.get('available')) if product else True,
        }

    return {
        'category_id': product.category_id if product else None,
        'name': product.name if product else '',
        'description': product.description if product else '',
        'image_url': product.image_url if product and product.image_url else '',
        'available': product.available if product else True,
    }


def _validate_product_form(form_data, categories):
    category_ids = {category.id for category in categories}

    if form_data['category_id'] not in category_ids:
        return 'Choose a valid category.'

    if len(form_data['name']) < 3:
        return 'Product name should be at least 3 characters long.'

    if len(form_data['name']) > 120:
        return 'Product name should stay under 120 characters.'

    if len(form_data['description']) < 20:
        return 'Add a more descriptive product summary of at least 20 characters.'

    if form_data['image_url'] and not (
        form_data['image_url'].startswith('http://') or form_data['image_url'].startswith('https://')
    ):
        return 'Image URL must start with http:// or https://.'

    return None


@bp.route('/products')
def browse_products():
    category_id = request.args.get('category_id', type=int)
    keyword = request.args.get('keyword', default='', type=str)
    sort_by = request.args.get('sort_by', default='price_asc', type=str)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    min_rating = request.args.get('min_rating', type=float)
    only_in_stock = request.args.get('only_in_stock') == '1'
    page_raw = request.args.get('page', default=1, type=int)
    per_page_raw = request.args.get('per_page', default=25, type=int)
    page, per_page = _normalize_page_and_size(page_raw, per_page_raw)

    products, total_count = Product.search(
        category_id=category_id,
        keyword=keyword,
        sort_by=sort_by,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        only_in_stock=only_in_stock,
        page=page,
        per_page=per_page,
    )
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    if page > total_pages:
        page = total_pages
        products, total_count = Product.search(
            category_id=category_id,
            keyword=keyword,
            sort_by=sort_by,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
            only_in_stock=only_in_stock,
            page=page,
            per_page=per_page,
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
        min_rating=min_rating,
        only_in_stock=only_in_stock,
        page=page,
        per_page=per_page,
        total_count=total_count,
        total_pages=total_pages,
    )


@bp.route('/products/<int:product_id>')
def product_detail(product_id):
    product = Product.get(product_id)
    if product is None:
        return redirect(url_for('products.browse_products'))

    review_page_raw = request.args.get('review_page', default=1, type=int)
    review_per_page_raw = request.args.get('review_per_page', default=10, type=int)
    review_sort = request.args.get('review_sort', default='date_desc', type=str)
    review_page, review_per_page = _normalize_page_and_size(
        review_page_raw, review_per_page_raw, default_per_page=10
    )
    allowed_review_sort = {'date_desc', 'date_asc', 'rating_desc', 'rating_asc'}
    if review_sort not in allowed_review_sort:
        review_sort = 'date_desc'

    sellers = InventoryItem.get_sellers_for_product(product_id)
    total_reviews = Feedback.get_product_review_count(product_id)
    review_total_pages = max(1, (total_reviews + review_per_page - 1) // review_per_page)
    if review_page > review_total_pages:
        review_page = review_total_pages

    reviews = Feedback.get_product_reviews(
        product_id,
        page=review_page,
        per_page=review_per_page,
        sort_by=review_sort,
    )
    avg_rating = Feedback.get_product_average_rating(product_id)
    user_review = None
    if current_user.is_authenticated:
        user_review = Feedback.get_product_review_by_user(product_id, current_user.id)

    return render_template(
        'product_detail.html',
        product=product,
        sellers=sellers,
        reviews=reviews,
        avg_rating=avg_rating,
        review_page=review_page,
        review_per_page=review_per_page,
        review_total_pages=review_total_pages,
        total_reviews=total_reviews,
        review_sort=review_sort,
        user_review=user_review,
    )


@bp.route('/products/<int:product_id>/review', methods=['POST'])
@login_required
def submit_product_review(product_id):
    product = Product.get(product_id)
    if product is None or not product.available:
        flash('That product is not available for review.', 'warning')
        return redirect(url_for('products.browse_products'))

    rating = request.form.get('rating', type=int)
    review = (request.form.get('review') or '').strip()

    if rating is None or rating < 1 or rating > 5:
        flash('Choose a rating from 1 to 5 stars.', 'danger')
        return redirect(url_for('products.product_detail', product_id=product_id))

    is_update = Feedback.get_product_review_by_user(product_id, current_user.id) is not None
    Feedback.upsert_product_review(product_id, current_user.id, rating, review or None)

    if is_update:
        flash('Your product review was updated.', 'success')
    else:
        flash('Thanks for reviewing this product.', 'success')
    return redirect(url_for('products.product_detail', product_id=product_id))


@bp.route('/products/new', methods=['GET', 'POST'])
@login_required
def create_product():
    categories = Category.get_all()
    form_data = _build_product_form_data()

    if request.method == 'POST':
        error = _validate_product_form(form_data, categories)
        if error:
            flash(error, 'danger')
            return render_template(
                'product_form.html',
                categories=categories,
                product=None,
                form_data=form_data,
            )

        product_id = Product.create(
            current_user.id,
            form_data['category_id'],
            form_data['name'],
            form_data['description'],
            form_data['image_url'] or None,
            True
        )
        flash('Product created successfully.', 'success')
        return redirect(url_for('products.product_detail', product_id=product_id))

    return render_template(
        'product_form.html',
        categories=categories,
        product=None,
        form_data=form_data,
    )


@bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.get(product_id)
    if product is None or product.creator_id != current_user.id:
        flash('You can only edit products that you created.', 'warning')
        return redirect(url_for('products.browse_products'))

    categories = Category.get_all()
    form_data = _build_product_form_data(product=product)

    if request.method == 'POST':
        error = _validate_product_form(form_data, categories)
        if error:
            flash(error, 'danger')
            return render_template(
                'product_form.html',
                categories=categories,
                product=product,
                form_data=form_data,
            )

        Product.update(
            product_id,
            current_user.id,
            form_data['category_id'],
            form_data['name'],
            form_data['description'],
            form_data['image_url'] or None,
            form_data['available']
        )
        flash('Product updated.', 'success')
        return redirect(url_for('products.product_detail', product_id=product_id))

    return render_template(
        'product_form.html',
        categories=categories,
        product=product,
        form_data=form_data,
    )


@bp.route('/products/<int:product_id>/deactivate', methods=['POST'])
@login_required
def deactivate_product(product_id):
    product = Product.get(product_id)
    if product is None:
        flash('Product not found.', 'warning')
        return redirect(url_for('products.my_products'))

    if product.creator_id != current_user.id:
        flash('Only the product creator can deactivate this product.', 'danger')
        return redirect(url_for('products.product_detail', product_id=product_id))

    updated_rows = Product.deactivate(product_id, current_user.id)
    if updated_rows:
        flash('Product deactivated. It will no longer appear in public browsing.', 'success')
    else:
        flash('This product is already inactive.', 'info')

    next_url = request.form.get('next')
    return redirect(_safe_next_url(next_url, 'products.my_products'))


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
        flash('Product ID is required.', 'danger')
        return redirect(url_for('index.index'))

    if Product.get(product_id) is None:
        flash('No product exists with that ID.', 'warning')
        return redirect(url_for('index.index'))

    if quantity is None or quantity < 0:
        flash('Quantity must be a non-negative whole number.', 'danger')
        return redirect(url_for('index.index'))

    if price is None or price < 0:
        flash('Price must be a non-negative number.', 'danger')
        return redirect(url_for('index.index'))

    InventoryItem.add_item_to_inventory(
        seller_id=current_user.id,
        product_id=product_id,
        quantity=quantity,
        price=price,
    )
    flash('Product listing saved to your inventory.', 'success')
    return redirect(url_for('products.seller_inventory_page', seller_id=current_user.id))


@bp.route('/inventory/my', methods=['GET'])
@login_required
def my_inventory_lookup():
    product_id = request.args.get('product_id', type=int)
    if product_id is None:
        flash('Enter a product ID to open your listing.', 'warning')
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
        flash('That product is not in your inventory (or the product no longer exists).', 'warning')
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
        flash('Quantity must be a non-negative whole number.', 'danger')
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
        flash('Listing not found.', 'warning')
        return redirect(
            url_for(
                'products.seller_inventory_page',
                seller_id=current_user.id,
                page=page,
                per_page=per_page,
            )
        )

    flash('Quantity updated.', 'success')
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
        flash('Listing not found.', 'warning')
    else:
        flash('Removed this product from your inventory.', 'success')
    return redirect(
        url_for(
            'products.seller_inventory_page',
            seller_id=current_user.id,
            page=page,
            per_page=per_page,
        )
    )
