from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import current_user, login_required

from .models.product import Product
from .models.inventory import InventoryItem
from .models.category import Category
from .models.feedback import Feedback

bp = Blueprint('products', __name__)


@bp.route('/products')
def browse_products():
    category_id = request.args.get('category_id', type=int)
    keyword = request.args.get('keyword', default='', type=str)
    sort_by = request.args.get('sort_by', default='price_asc', type=str)

    products = Product.search(category_id=category_id, keyword=keyword, sort_by=sort_by)
    categories = Category.get_all()

    return render_template(
        'products.html',
        products=products,
        categories=categories,
        selected_category=category_id,
        keyword=keyword,
        sort_by=sort_by
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
    products = InventoryItem.get_products_for_seller(seller_id)
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

    products = InventoryItem.get_products_for_seller(seller_id)
    return render_template('seller_inventory.html', products=products, seller_id=seller_id)