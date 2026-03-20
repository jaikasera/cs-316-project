from flask import Blueprint, render_template, request, jsonify
from .models.product import Product
from .models.inventory import InventoryItem

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


@bp.route('/sellers/<int:seller_id>/inventory')
def seller_inventory_json(seller_id: int):
    products = InventoryItem.get_products_for_seller(seller_id)
    return jsonify([{'id': p.product_id, 'name': p.name} for p in products])


@bp.route('/sellers/inventory')
def seller_inventory_page():
    seller_id = request.args.get('seller_id', type=int)
    if seller_id is None:
        seller_id = -1

    products = InventoryItem.get_products_for_seller(seller_id)
    return render_template('seller_inventory.html', products=products, seller_id=seller_id)