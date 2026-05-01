from flask import session


WISHLIST_KEY = 'pokemart_wishlist'
RECENTLY_VIEWED_KEY = 'pokemart_recently_viewed'
SAVE_FOR_LATER_KEY = 'pokemart_save_for_later'
COUPON_KEY = 'pokemart_coupon'

COUPONS = {
    'POKE10': {
        'label': '10% off orders over P$40',
        'kind': 'percent',
        'value': 0.10,
        'min_subtotal': 40.0,
        'max_discount': 40.0,
    },
    'BALL5': {
        'label': 'P$5 off orders over P$25',
        'kind': 'fixed',
        'value': 5.0,
        'min_subtotal': 25.0,
    },
    'BERRY15': {
        'label': '15% off orders over P$75',
        'kind': 'percent',
        'value': 0.15,
        'min_subtotal': 75.0,
        'max_discount': 65.0,
    },
}


def _read_int_list(key):
    raw = session.get(key, [])
    if not isinstance(raw, list):
        return []

    values = []
    for item in raw:
        try:
            values.append(int(item))
        except (TypeError, ValueError):
            continue
    return values


def _write_int_list(key, values):
    deduped = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    session[key] = deduped
    session.modified = True


def get_wishlist_ids():
    return _read_int_list(WISHLIST_KEY)


def wishlist_contains(product_id):
    return int(product_id) in set(get_wishlist_ids())


def toggle_wishlist(product_id):
    product_id = int(product_id)
    current = get_wishlist_ids()
    if product_id in current:
        current = [value for value in current if value != product_id]
        _write_int_list(WISHLIST_KEY, current)
        return False

    current.insert(0, product_id)
    _write_int_list(WISHLIST_KEY, current[:48])
    return True


def record_recently_viewed(product_id):
    product_id = int(product_id)
    current = [value for value in get_recently_viewed_ids() if value != product_id]
    current.insert(0, product_id)
    _write_int_list(RECENTLY_VIEWED_KEY, current[:18])


def get_recently_viewed_ids():
    return _read_int_list(RECENTLY_VIEWED_KEY)


def _read_saved_items():
    raw = session.get(SAVE_FOR_LATER_KEY, [])
    if not isinstance(raw, list):
        return []

    items = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            items.append({
                'product_id': int(item['product_id']),
                'seller_id': int(item['seller_id']),
                'quantity': max(1, int(item.get('quantity', 1))),
            })
        except (KeyError, TypeError, ValueError):
            continue
    return items


def get_saved_for_later():
    return _read_saved_items()


def save_for_later(product_id, seller_id, quantity):
    saved = [
        item for item in _read_saved_items()
        if not (item['product_id'] == int(product_id) and item['seller_id'] == int(seller_id))
    ]
    saved.insert(0, {
        'product_id': int(product_id),
        'seller_id': int(seller_id),
        'quantity': max(1, int(quantity)),
    })
    session[SAVE_FOR_LATER_KEY] = saved[:24]
    session.modified = True


def pop_saved_for_later(product_id, seller_id):
    found = None
    kept = []
    for item in _read_saved_items():
        if item['product_id'] == int(product_id) and item['seller_id'] == int(seller_id) and found is None:
            found = item
            continue
        kept.append(item)
    session[SAVE_FOR_LATER_KEY] = kept
    session.modified = True
    return found


def remove_saved_for_later(product_id, seller_id):
    pop_saved_for_later(product_id, seller_id)


def get_active_coupon_code():
    raw = session.get(COUPON_KEY)
    if not raw:
        return None
    raw = str(raw).strip().upper()
    return raw if raw in COUPONS else None


def set_active_coupon_code(code):
    normalized = (code or '').strip().upper()
    if normalized in COUPONS:
        session[COUPON_KEY] = normalized
    else:
        session.pop(COUPON_KEY, None)
    session.modified = True


def clear_active_coupon():
    session.pop(COUPON_KEY, None)
    session.modified = True


def evaluate_coupon(subtotal, code=None):
    subtotal = float(subtotal or 0)
    code = (code or get_active_coupon_code() or '').upper()
    coupon = COUPONS.get(code)
    if not coupon:
        return {
            'code': None,
            'valid': False,
            'message': None,
            'discount': 0.0,
            'label': None,
        }

    min_subtotal = float(coupon.get('min_subtotal', 0))
    if subtotal < min_subtotal:
        return {
            'code': code,
            'valid': False,
            'message': f'{code} activates once your bag reaches P${min_subtotal:.2f}.',
            'discount': 0.0,
            'label': coupon['label'],
        }

    if coupon['kind'] == 'percent':
        discount = subtotal * float(coupon['value'])
    else:
        discount = float(coupon['value'])

    discount = min(discount, float(coupon.get('max_discount', discount)), subtotal)
    return {
        'code': code,
        'valid': discount > 0,
        'message': None,
        'discount': round(discount, 2),
        'label': coupon['label'],
    }


def variant_options_for_product(product):
    category = (getattr(product, 'category_name', '') or '').lower()
    name = (getattr(product, 'name', '') or '').lower()
    options = {}

    if 'book' in category:
        options['Format'] = ['Hardcover', 'Paperback', 'Collector Edition']
        options['Edition'] = ['Standard', 'Annotated', 'Anniversary']
    elif 'clothing' in category or 'apparel' in category:
        options['Size'] = ['XS', 'S', 'M', 'L', 'XL']
        options['Color'] = ['Red', 'Blue', 'Cream', 'Black']
    elif 'electronic' in category:
        options['Edition'] = ['Core', 'Plus', 'Pro']
        options['Color'] = ['Slate', 'Pearl', 'Sky']
    elif 'sport' in category:
        options['Size'] = ['Youth', 'Adult', 'Pro']
        options['Format'] = ['Single', '2-Pack', 'Team Bundle']
    elif 'home' in category:
        options['Format'] = ['Compact', 'Standard', 'Deluxe']
        options['Color'] = ['White', 'Natural', 'Ocean']
    else:
        options['Edition'] = ['Classic', 'Plus', 'Collector']
        options['Color'] = ['Blue', 'Yellow', 'Red']

    if 'plush' in name or 'figure' in name:
        options['Size'] = ['Mini', 'Standard', 'Mega']
    if 'card' in name:
        options['Format'] = ['Booster', 'Elite Box', 'Collector Tin']

    return options


def gallery_images_for_product(product, related_products=None):
    related_products = related_products or []
    gallery = []
    for image_url in [getattr(product, 'image_url', None)] + [item.image_url for item in related_products]:
        if image_url and image_url not in gallery:
            gallery.append(image_url)
        if len(gallery) == 4:
            break
    return gallery


def price_story_for_product(product, sellers=None):
    sellers = sellers or []
    if not sellers:
        return {'label': 'New Listing', 'detail': 'No live seller comparison yet.', 'drop_percent': 0}

    prices = [float(seller.price) for seller in sellers if getattr(seller, 'quantity', 0) > 0]
    if not prices:
        return {'label': 'Restock Watch', 'detail': 'Tracked sellers are currently restocking this item.', 'drop_percent': 0}

    low = min(prices)
    high = max(prices)
    if high > low:
        drop_percent = round((high - low) / high * 100)
        return {
            'label': f'Price Drop {drop_percent}% Off Peak',
            'detail': f'Best live offer is P${low:.2f} vs. a tracked high of P${high:.2f}.',
            'drop_percent': drop_percent,
        }

    return {'label': 'Steady Price', 'detail': f'All live sellers are clustered around P${low:.2f}.', 'drop_percent': 0}


def delivery_estimate_for_listing(quantity, seller_rating=None, price=None):
    quantity = int(quantity or 0)
    seller_rating = float(seller_rating or 0)
    price = float(price or 0)

    if quantity <= 0:
        return 'Restock soon'
    if quantity <= 2:
        return 'Arrives in 5-7 days'
    if seller_rating >= 4.5 or price >= 75:
        return 'Arrives in 1-2 days'
    if quantity >= 15:
        return 'Arrives in 2-3 days'
    return 'Arrives in 3-5 days'
