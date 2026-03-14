from flask import Blueprint, render_template, request, jsonify
from .models.product import Product

bp = Blueprint('products', __name__)

@bp.route('/products/top/<int:k>')
def top_k_products_json(k):
    if k <= 0:
        return jsonify([])

    products = Product.get_top_k_expensive(k)
    return jsonify([product.__dict__ for product in products])


@bp.route('/products/top')
def top_k_products_page():
    k = request.args.get('k', default=5, type=int)
    if k <= 0:
        k = 5

    products = Product.get_top_k_expensive(k)
    return render_template('top_products.html', products=products, k=k)