from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
import csv
import random
import re

from faker import Faker
from werkzeug.security import generate_password_hash

BASE = Path(__file__).resolve().parent

NUM_USERS = 450
NUM_PRODUCTS = 3500
NUM_PURCHASES = 12000
NUM_PRODUCT_REVIEWS = 18000
NUM_SELLER_REVIEWS = 7000
NUM_CART_ITEMS = 2600
NUM_ORDERS = 3200

Faker.seed(7)
random.seed(7)
fake = Faker()

CATEGORY_CATALOG = [
    {
        'name': 'Books',
        'weight': 18,
        'subcategories': ['Cookbooks', 'Reference', 'Hobbies & Skills'],
        'price_range': (8.99, 34.99),
        'premium_multiplier': (1.4, 2.2),
        'premium_rate': 0.10,
        'brands': ['North Street Press', 'Juniper House', 'Blue Lantern', 'Cedar Ink', 'Summit Editions'],
        'modifiers': ['Practical', 'Essential', 'Modern', 'Complete', 'Illustrated', 'Everyday', 'Field'],
        'nouns': ['Guide', 'Cookbook', 'Atlas', 'Workbook', 'Handbook', 'Companion', 'Playbook'],
        'topics': ['Home Baking', 'Trail Running', 'Personal Finance', 'Digital Photography', 'Indoor Gardening', 'Strength Training', 'Minimalist Living', 'Creative Writing'],
        'features': ['clear chapter summaries', 'easy reference tables', 'step-by-step examples', 'photography throughout', 'practical checklists'],
        'use_cases': ['weeknight learning', 'gift giving', 'reference on the shelf', 'learning a new hobby', 'building better routines'],
        'tag_pool': ['giftable', 'illustrated', 'beginner-friendly', 'reference', 'paperback', 'hardcover'],
    },
    {
        'name': 'Electronics',
        'weight': 16,
        'subcategories': ['Audio', 'Computing', 'Cameras & Wearables'],
        'price_range': (24.99, 699.99),
        'premium_multiplier': (1.5, 3.4),
        'premium_rate': 0.22,
        'brands': ['Voltix', 'Aether', 'NovaCore', 'NorthPeak', 'SignalLab', 'Orbiton'],
        'modifiers': ['Wireless', 'Smart', 'Portable', 'Compact', 'Ultra', 'Pro', 'Noise-Canceling'],
        'nouns': ['Headphones', 'Tablet', 'Speaker', 'Monitor', 'Keyboard', 'Action Camera', 'Smartwatch', 'Webcam'],
        'features': ['long battery life', 'USB-C charging', 'fast pairing', 'crisp display quality', 'stable Bluetooth performance'],
        'use_cases': ['remote work setups', 'travel days', 'gaming desks', 'daily commuting', 'video calls'],
        'tag_pool': ['wireless', 'portable', 'usb-c', 'bluetooth', 'premium', 'desk setup'],
    },
    {
        'name': 'Home',
        'weight': 14,
        'subcategories': ['Decor & Storage', 'Kitchen', 'Bedding & Bath'],
        'price_range': (14.99, 249.99),
        'premium_multiplier': (1.4, 2.8),
        'premium_rate': 0.16,
        'brands': ['Harbor & Oak', 'Mason Row', 'Bright Nest', 'Elm Grove', 'Stonefield'],
        'modifiers': ['Stackable', 'Soft', 'Ceramic', 'Woven', 'Glass', 'Everyday', 'Premium'],
        'nouns': ['Storage Bins', 'Sheet Set', 'Throw Blanket', 'Knife Set', 'Floor Lamp', 'Bath Towels', 'Bakeware Set'],
        'features': ['easy-clean surfaces', 'durable construction', 'space-saving design', 'soft-touch materials', 'neutral finishes'],
        'use_cases': ['small apartments', 'guest rooms', 'kitchen refreshes', 'weekly meal prep', 'everyday home organization'],
        'tag_pool': ['space-saving', 'soft-touch', 'giftable', 'kitchen', 'home refresh', 'neutral finish'],
    },
    {
        'name': 'Clothing',
        'weight': 12,
        'subcategories': ['Tops & Layers', 'Bottoms', 'Activewear'],
        'price_range': (12.99, 119.99),
        'premium_multiplier': (1.3, 2.6),
        'premium_rate': 0.18,
        'brands': ['Threadwell', 'Peak Line', 'Harbor Knit', 'Ridge Supply', 'Juniper Lane'],
        'modifiers': ['Relaxed', 'Slim', 'Performance', 'Classic', 'Lightweight', 'Everyday', 'Premium'],
        'nouns': ['Hoodie', 'Joggers', 'Oxford Shirt', 'Puffer Vest', 'Training Tee', 'Denim Jacket', 'Crew Socks'],
        'features': ['soft fabric blends', 'clean stitching', 'easy layering', 'breathable materials', 'comfortable stretch'],
        'use_cases': ['daily wear', 'travel outfits', 'gym sessions', 'weekend errands', 'cool-weather layering'],
        'tag_pool': ['lightweight', 'layering', 'everyday', 'stretch', 'travel-ready', 'giftable'],
    },
    {
        'name': 'Sports',
        'weight': 10,
        'subcategories': ['Fitness', 'Outdoor Gear', 'Recovery'],
        'price_range': (15.99, 289.99),
        'premium_multiplier': (1.4, 3.0),
        'premium_rate': 0.20,
        'brands': ['TrailForge', 'Summit Pace', 'Core Motion', 'PeakTrail', 'North Ridge'],
        'modifiers': ['Adjustable', 'All-Weather', 'Compact', 'Training', 'Pro', 'Recovery', 'Lightweight'],
        'nouns': ['Yoga Mat', 'Camping Stove', 'Dumbbell Set', 'Running Vest', 'Hydration Pack', 'Trekking Poles', 'Resistance Bands'],
        'features': ['grippy surfaces', 'solid balance', 'packable designs', 'weather-ready materials', 'stable performance'],
        'use_cases': ['garage workouts', 'weekend hikes', 'race prep', 'outdoor training', 'recovery days'],
        'tag_pool': ['training', 'recovery', 'weather-ready', 'packable', 'lightweight', 'outdoor'],
    },
    {
        'name': 'Beauty',
        'weight': 8,
        'subcategories': ['Skincare', 'Haircare', 'Body Care'],
        'price_range': (9.99, 89.99),
        'premium_multiplier': (1.4, 2.5),
        'premium_rate': 0.15,
        'brands': ['Veloura', 'Pure Bloom', 'Lumen Skin', 'Clover & Coast', 'Aster Labs'],
        'modifiers': ['Hydrating', 'Daily', 'Gentle', 'Balancing', 'Brightening', 'Nourishing', 'Fragrance-Free'],
        'nouns': ['Face Serum', 'Shampoo', 'Body Lotion', 'Cleanser', 'Hair Mask', 'Lip Balm Set', 'Sunscreen'],
        'features': ['lightweight textures', 'clean finishes', 'easy daily use', 'skin-friendly formulas', 'fresh scents'],
        'use_cases': ['morning routines', 'travel kits', 'dry-weather care', 'everyday maintenance', 'gift baskets'],
        'tag_pool': ['hydrating', 'daily routine', 'gentle', 'travel size', 'fragrance-free', 'giftable'],
    },
    {
        'name': 'Grocery',
        'weight': 9,
        'subcategories': ['Pantry Staples', 'Snacks', 'Coffee & Breakfast'],
        'price_range': (4.49, 39.99),
        'premium_multiplier': (1.2, 1.9),
        'premium_rate': 0.08,
        'brands': ['Pantry North', 'Harvest Table', 'Open Field', 'Golden Acre', 'Daily Mill'],
        'modifiers': ['Organic', 'Roasted', 'Classic', 'Family Size', 'Single-Origin', 'Protein', 'Whole Grain'],
        'nouns': ['Coffee Beans', 'Granola', 'Pasta Pack', 'Olive Oil', 'Trail Mix', 'Oatmeal Cups', 'Snack Variety Box'],
        'features': ['reliable pantry value', 'balanced flavor', 'fresh packaging', 'easy portioning', 'simple ingredients'],
        'use_cases': ['busy mornings', 'office snacks', 'quick dinners', 'road trips', 'stocking the pantry'],
        'tag_pool': ['organic', 'family size', 'quick meal', 'snackable', 'single-origin', 'pantry staple'],
    },
    {
        'name': 'Pet Supplies',
        'weight': 7,
        'subcategories': ['Beds & Furniture', 'Walk & Travel', 'Feeding & Toys'],
        'price_range': (7.99, 149.99),
        'premium_multiplier': (1.3, 2.4),
        'premium_rate': 0.14,
        'brands': ['Happy Tails', 'Pawfield', 'Cozy Critter', 'Fetch & Co.', 'Willow Pet'],
        'modifiers': ['Durable', 'Soft', 'Interactive', 'Travel', 'Orthopedic', 'Indoor', 'Outdoor'],
        'nouns': ['Dog Bed', 'Cat Tree', 'Treat Pouch', 'Leash Set', 'Automatic Feeder', 'Chew Toy Pack', 'Litter Mat'],
        'features': ['pet-safe materials', 'easy cleanup', 'thoughtful sizing', 'durable hardware', 'cozy finishes'],
        'use_cases': ['daily walks', 'apartment pets', 'crate training', 'older dogs', 'active cats'],
        'tag_pool': ['durable', 'travel-friendly', 'pet-safe', 'easy-clean', 'cozy', 'interactive'],
    },
    {
        'name': 'Office',
        'weight': 6,
        'subcategories': ['Desk Setup', 'Planning & Paper', 'Organization'],
        'price_range': (6.99, 219.99),
        'premium_multiplier': (1.3, 2.6),
        'premium_rate': 0.12,
        'brands': ['Deskline', 'North Ledger', 'Paper Harbor', 'Slate Works', 'Taskwell'],
        'modifiers': ['Ergonomic', 'Adjustable', 'Minimal', 'Heavy-Duty', 'Weekly', 'Compact', 'Professional'],
        'nouns': ['Desk Pad', 'Planner', 'Monitor Stand', 'Filing Set', 'Notebook Pack', 'Task Chair Cushion', 'Cable Organizer'],
        'features': ['clean desk organization', 'professional finish', 'sturdy build quality', 'useful daily layout', 'workspace-friendly sizing'],
        'use_cases': ['hybrid work', 'student desks', 'paper planning', 'small offices', 'daily admin tasks'],
        'tag_pool': ['ergonomic', 'compact', 'desk setup', 'planner', 'organization', 'professional'],
    },
]

ROOT_CATEGORIES = {index + 1: dict(category, id=index + 1) for index, category in enumerate(CATEGORY_CATALOG)}
ROOT_CATEGORY_IDS = list(ROOT_CATEGORIES.keys())
ROOT_CATEGORY_WEIGHTS = [ROOT_CATEGORIES[category_id]['weight'] for category_id in ROOT_CATEGORY_IDS]


def build_category_rows():
    slugify_local = lambda value: re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')
    rows = []
    leaf_ids_by_root = defaultdict(list)

    for root_id, category in ROOT_CATEGORIES.items():
        rows.append({
            'id': root_id,
            'name': category['name'],
            'parent_id': '',
            'slug': slugify_local(category['name']),
            'is_active': 'true',
            'root_id': root_id,
            'is_leaf': False,
        })

    next_id = len(ROOT_CATEGORIES) + 1
    for root_id, category in ROOT_CATEGORIES.items():
        for subcategory_name in category['subcategories']:
            rows.append({
                'id': next_id,
                'name': subcategory_name,
                'parent_id': root_id,
                'slug': slugify_local(subcategory_name),
                'is_active': 'true',
                'root_id': root_id,
                'is_leaf': True,
            })
            leaf_ids_by_root[root_id].append(next_id)
            next_id += 1

    return rows, dict(leaf_ids_by_root)


CATEGORY_ROWS, LEAF_CATEGORY_IDS_BY_ROOT = build_category_rows()

POSITIVE_REVIEW_OPENERS = [
    'Really happy with this purchase.',
    'This ended up being a great value.',
    'Exactly what I hoped it would be.',
    'It has held up well so far.',
    'The quality feels better than expected.',
]
MID_REVIEW_OPENERS = [
    'Overall this is pretty solid.',
    'A decent option for the price.',
    'It does the job without much fuss.',
    'There are a few tradeoffs, but it works.',
    'Mostly satisfied after a few uses.',
]
LOW_REVIEW_OPENERS = [
    'I wanted to like this more than I did.',
    'Not as polished as the listing suggested.',
    'This was fine at first, but a few issues showed up.',
    'There are some frustrating compromises here.',
    'It works, but I would not buy it again.',
]
LOW_REVIEW_ISSUES = [
    'the finish arrived a little rough',
    'the sizing felt inconsistent',
    'battery life was shorter than I expected',
    'the packaging could have been better',
    'the materials felt cheaper than expected',
    'setup took more effort than it should have',
]
SELLER_REVIEW_POSITIVE = [
    'Fast shipping and the item matched the listing well.',
    'Arrived on time and was packaged carefully.',
    'Would happily order from this seller again.',
    'Good communication and the product condition was exactly as described.',
]
SELLER_REVIEW_NEUTRAL = [
    'No major problems, just a pretty standard transaction.',
    'Shipping took a bit, but the item itself was fine.',
    'The order was okay overall and arrived as expected.',
]
SELLER_REVIEW_NEGATIVE = [
    'Packaging could have been better and delivery felt slow.',
    'The listing details were a little optimistic.',
    'Customer service was polite, but the experience was not smooth.',
]


def get_csv_writer(f):
    return csv.writer(f, dialect='unix')


def money(value):
    return f'{value:.2f}'


def slugify(value):
    return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')


def clamp(value, low, high):
    return max(low, min(high, value))


def weighted_choice(values, weights):
    return random.choices(values, weights=weights, k=1)[0]


def weighted_sample_without_replacement(items, weights, count):
    """
    Draw `count` items from `items` without replacement, using `weights` as
    selection probabilities.  Works by maintaining a shrinking pool: each
    iteration picks a random point in [0, total_weight) and walks the pool
    until the cumulative weight crosses that point, then removes the chosen
    item so it cannot be selected again.  Returns up to min(count, len(items))
    items.
    """
    pool = list(zip(items, weights))
    chosen = []
    count = min(count, len(pool))
    for _ in range(count):
        total = sum(weight for _, weight in pool)
        pick = random.random() * total
        upto = 0.0
        for index, (item, weight) in enumerate(pool):
            upto += weight
            if upto >= pick:
                chosen.append(item)
                pool.pop(index)
                break
    return chosen


def random_timestamp(days_back=900):
    return fake.date_time_between(start_date=f'-{days_back}d', end_date='now')


def choose_interest_ids():
    interest_count = weighted_choice([2, 3, 4], [56, 31, 13])
    chosen = []
    while len(chosen) < interest_count:
        category_id = weighted_choice(ROOT_CATEGORY_IDS, ROOT_CATEGORY_WEIGHTS)
        if category_id not in chosen:
            chosen.append(category_id)
    return chosen


def choose_user_for_category(user_profiles, category_id, prefer_seller=False, exclude_ids=None):
    exclude_ids = exclude_ids or set()
    candidates = []
    weights = []
    for profile in user_profiles:
        if profile['id'] in exclude_ids:
            continue
        if category_id not in profile['interests']:
            continue
        base_weight = 1.0 + profile['interest_rank'][category_id] * 1.5
        if prefer_seller:
            base_weight *= profile['seller_affinity']
        candidates.append(profile)
        weights.append(base_weight)
    if not candidates:
        fallback = [profile for profile in user_profiles if profile['id'] not in exclude_ids]
        return random.choice(fallback)
    return weighted_choice(candidates, weights)


def choose_leaf_category_id(root_category_id):
    leaf_ids = LEAF_CATEGORY_IDS_BY_ROOT[root_category_id]
    return random.choice(leaf_ids)


def generate_book_name(category):
    topic = random.choice(category['topics'])
    modifier = random.choice(category['modifiers'])
    noun = random.choice(category['nouns'])
    style = weighted_choice([
        f'{topic} {noun}',
        f'The {modifier} {topic} {noun}',
        f'{modifier} {noun} to {topic}',
    ], [4, 3, 2])
    return style


def generate_general_name(category, premium=False):
    brand = random.choice(category['brands'])
    modifier = random.choice(category['modifiers'])
    noun = random.choice(category['nouns'])
    if premium:
        tier = weighted_choice(['Signature', 'Studio', 'Elite', 'Reserve'], [4, 3, 2, 1])
        return f'{brand} {modifier} {noun} {tier}'
    variant = weighted_choice(['Mk II', 'Plus', 'Set', 'Edition', ''], [1, 2, 3, 2, 6]).strip()
    return f'{brand} {modifier} {noun} {variant}'.strip()


def ensure_unique_name(base_name, seen_names):
    if base_name not in seen_names:
        seen_names[base_name] = 1
        return base_name
    seen_names[base_name] += 1
    return f'{base_name} {seen_names[base_name]}'


def generate_product_description(category, premium=False):
    feature_a, feature_b = random.sample(category['features'], 2)
    use_case = random.choice(category['use_cases'])
    lead = 'Premium pick built for' if premium else 'Well-suited for'
    return (
        f'{lead} {use_case}, with {feature_a} and {feature_b}. '
        f'Designed to feel dependable for everyday use without sounding overbuilt.'
    )


def generate_product_tags(category, product_name, premium=False, popularity=0.0):
    tags = set(random.sample(category['tag_pool'], k=min(2, len(category['tag_pool']))))
    lowered_name = product_name.lower()

    keyword_tags = {
        'wireless': 'wireless',
        'portable': 'portable',
        'compact': 'compact',
        'smart': 'smart',
        'noise-canceling': 'noise-canceling',
        'organic': 'organic',
        'protein': 'protein',
        'ergonomic': 'ergonomic',
        'adjustable': 'adjustable',
        'lightweight': 'lightweight',
        'hydrating': 'hydrating',
        'fragrance-free': 'fragrance-free',
        'interactive': 'interactive',
        'orthopedic': 'orthopedic',
    }
    for keyword, tag in keyword_tags.items():
        if keyword in lowered_name:
            tags.add(tag)

    if premium:
        tags.add('premium')
        tags.add('giftable')
    if popularity > 0.72:
        tags.add('best-seller')
    if category['name'] == 'Books':
        tags.add(weighted_choice(['reference', 'illustrated', 'beginner-friendly'], [3, 2, 2]))
    elif category['name'] == 'Electronics':
        tags.add(weighted_choice(['desk setup', 'travel-ready', 'bluetooth'], [2, 2, 3]))
    elif category['name'] == 'Home':
        tags.add(weighted_choice(['space-saving', 'home refresh', 'giftable'], [3, 2, 2]))
    elif category['name'] == 'Clothing':
        tags.add(weighted_choice(['everyday', 'layering', 'travel-ready'], [3, 3, 2]))
    elif category['name'] == 'Sports':
        tags.add(weighted_choice(['training', 'outdoor', 'recovery'], [3, 2, 2]))
    elif category['name'] == 'Beauty':
        tags.add(weighted_choice(['daily routine', 'gentle', 'travel size'], [3, 2, 2]))
    elif category['name'] == 'Grocery':
        tags.add(weighted_choice(['pantry staple', 'quick meal', 'snackable'], [3, 2, 2]))
    elif category['name'] == 'Pet Supplies':
        tags.add(weighted_choice(['pet-safe', 'easy-clean', 'durable'], [3, 2, 2]))
    elif category['name'] == 'Office':
        tags.add(weighted_choice(['desk setup', 'organization', 'professional'], [3, 2, 2]))

    return sorted(tags)[:6]


def product_quality_score(popularity, premium=False):
    quality = 0.48 + popularity * 0.32 + random.uniform(-0.18, 0.18)
    if premium:
        quality += 0.05
    return clamp(quality, 0.08, 0.96)


def review_rating_from_quality(quality):
    rating_weights = {
        1: clamp(0.04 + (0.35 - quality) * 0.20, 0.02, 0.18),
        2: clamp(0.06 + (0.45 - quality) * 0.22, 0.03, 0.22),
        3: clamp(0.20 + (0.55 - abs(quality - 0.55)) * 0.25, 0.12, 0.32),
        4: clamp(0.32 + quality * 0.22, 0.20, 0.42),
        5: clamp(0.22 + quality * 0.34, 0.12, 0.50),
    }
    ratings = list(rating_weights.keys())
    weights = list(rating_weights.values())
    return weighted_choice(ratings, weights)


def product_review_text(product, rating):
    category = ROOT_CATEGORIES[product['root_category_id']]
    feature = random.choice(category['features'])
    use_case = random.choice(category['use_cases'])
    if rating >= 5:
        return f"{random.choice(POSITIVE_REVIEW_OPENERS)} The {feature} stood out right away, and it fits nicely into {use_case}."
    if rating == 4:
        return f"{random.choice(POSITIVE_REVIEW_OPENERS)} It feels reliable, and the {feature} makes it easy to keep using for {use_case}."
    if rating == 3:
        return f"{random.choice(MID_REVIEW_OPENERS)} The {feature} is helpful, though it still feels like a middle-of-the-road option for {use_case}."
    return f"{random.choice(LOW_REVIEW_OPENERS)} For me, {random.choice(LOW_REVIEW_ISSUES)}, which made it harder to enjoy for {use_case}."


def seller_review_text(rating):
    if rating >= 5:
        return random.choice(SELLER_REVIEW_POSITIVE)
    if rating == 4 or rating == 3:
        return random.choice(SELLER_REVIEW_NEUTRAL)
    return random.choice(SELLER_REVIEW_NEGATIVE)


def select_product_for_user(user_profile, products_by_category, available_product_ids, product_popularity_weights, require_stock=False, stocked_products=None):
    if random.random() < 0.82:
        category_id = weighted_choice(user_profile['interests'], [user_profile['interest_rank'][cid] + 1 for cid in user_profile['interests']])
        category_pool = products_by_category[category_id]
        if require_stock and stocked_products is not None:
            category_pool = [product_id for product_id in category_pool if product_id in stocked_products]
        if category_pool:
            weights = [product_popularity_weights[product_id] for product_id in category_pool]
            return weighted_choice(category_pool, weights)

    pool = stocked_products if require_stock and stocked_products is not None else available_product_ids
    weights = [product_popularity_weights[product_id] for product_id in pool]
    return weighted_choice(pool, weights)


def choose_listing_for_product(listings, buyer_id=None, prefer_cheapest=True, require_stock=False):
    candidate_listings = [listing for listing in listings if (not require_stock or listing['quantity'] > 0)]
    if buyer_id is not None:
        filtered = [listing for listing in candidate_listings if listing['seller_id'] != buyer_id]
        if filtered:
            candidate_listings = filtered
    if not candidate_listings:
        return None
    sorted_candidates = sorted(candidate_listings, key=lambda listing: (listing['price'], -listing['quantity']))
    if prefer_cheapest and random.random() < 0.62:
        shortlist = sorted_candidates[: min(3, len(sorted_candidates))]
        weights = [1 / (index + 1) for index in range(len(shortlist))]
        return weighted_choice(shortlist, weights)
    return random.choice(candidate_listings)


def seller_review_rating(seller_quality):
    weights = {
        1: clamp(0.03 + (0.35 - seller_quality) * 0.20, 0.02, 0.16),
        2: clamp(0.06 + (0.42 - seller_quality) * 0.22, 0.03, 0.20),
        3: clamp(0.20 + (0.55 - abs(seller_quality - 0.55)) * 0.20, 0.12, 0.30),
        4: clamp(0.36 + seller_quality * 0.18, 0.24, 0.42),
        5: clamp(0.24 + seller_quality * 0.30, 0.14, 0.46),
    }
    return weighted_choice(list(weights.keys()), list(weights.values()))


def gen_users(num_users):
    user_profiles = []
    with open(BASE / 'Users.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Users...', end=' ', flush=True)
        for uid in range(num_users):
            if uid % 25 == 0:
                print(f'{uid}', end=' ', flush=True)
            firstname = fake.first_name()
            lastname = fake.last_name()
            email = f"{slugify(firstname)}.{slugify(lastname)}.{uid}@marketplace.local"
            password = generate_password_hash('test123')
            balance_value = clamp(random.lognormvariate(4.4, 0.65), 20, 4500)
            address = fake.address().replace('\n', ', ')
            interests = choose_interest_ids()
            primary_interest = interests[0]
            interest_rank = {category_id: max(1, len(interests) - index) for index, category_id in enumerate(interests)}
            seller_affinity = random.uniform(0.8, 2.3) if random.random() < 0.62 else random.uniform(0.3, 1.2)
            cart_affinity = random.uniform(0.8, 2.2)
            order_affinity = random.uniform(0.8, 2.4)
            writer.writerow([uid, email, password, firstname, lastname, money(balance_value), address])
            user_profiles.append({
                'id': uid,
                'firstname': firstname,
                'lastname': lastname,
                'interests': interests,
                'primary_interest': primary_interest,
                'interest_rank': interest_rank,
                'seller_affinity': seller_affinity,
                'cart_affinity': cart_affinity,
                'order_affinity': order_affinity,
            })
        print(f'{num_users} generated')
    return user_profiles


def gen_categories():
    with open(BASE / 'Categories.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Categories...', end=' ', flush=True)
        for row in CATEGORY_ROWS:
            writer.writerow([row['id'], row['name'], row['parent_id'], row['slug'], row['is_active']])
        print(f'{len(CATEGORY_ROWS)} generated')


def gen_products(num_products, user_profiles):
    """
    Generate `num_products` products and write them to Products.csv.

    Each product is assigned to a weighted-random root category (high-weight
    categories like Books and Electronics appear more often).  A `popularity`
    score is drawn from a right-skewed beta(1.2, 4.5) distribution so most
    products are niche, with rare spikes of high popularity.  A `quality_score`
    is then derived from popularity plus a small random offset — this score
    is used downstream by review generators to bias ratings (high-quality
    products receive more 4- and 5-star reviews).  Premium products exist in
    each category at category-specific rates and receive a price multiplier.

    Returns: (products list, available_product_ids, products_by_category, popularity_weights)
    """
    products = []
    available_product_ids = []
    products_by_category = defaultdict(list)
    popularity_weights = {}
    seen_names = {}

    with open(BASE / 'Products.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Products...', end=' ', flush=True)
        for pid in range(1, num_products + 1):
            if pid % 100 == 0:
                print(f'{pid}', end=' ', flush=True)

            root_category_id = weighted_choice(ROOT_CATEGORY_IDS, ROOT_CATEGORY_WEIGHTS)
            leaf_category_id = choose_leaf_category_id(root_category_id)
            category = ROOT_CATEGORIES[root_category_id]
            creator = choose_user_for_category(user_profiles, root_category_id, prefer_seller=True)
            premium = random.random() < category['premium_rate']
            raw_name = generate_book_name(category) if category['name'] == 'Books' else generate_general_name(category, premium=premium)
            name = ensure_unique_name(raw_name, seen_names)
            description = generate_product_description(category, premium=premium)
            base_price = random.uniform(*category['price_range'])
            if premium:
                base_price *= random.uniform(*category['premium_multiplier'])
            base_price = round(base_price, 2)
            popularity = clamp(random.betavariate(1.2, 4.5) + (0.42 if random.random() < 0.08 else 0.0), 0.03, 0.98)
            quality = product_quality_score(popularity, premium=premium)
            available = 'true' if random.random() < 0.93 else 'false'
            image_url = f'https://picsum.photos/seed/{slugify(name)}/600/400'

            product = {
                'id': pid,
                'creator_id': creator['id'],
                'category_id': leaf_category_id,
                'root_category_id': root_category_id,
                'name': name,
                'description': description,
                'image_url': image_url,
                'available': available == 'true',
                'base_price': base_price,
                'popularity': popularity,
                'quality': quality,
                'premium': premium,
                'tags': generate_product_tags(category, name, premium=premium, popularity=popularity),
            }
            products.append(product)
            products_by_category[root_category_id].append(pid)
            popularity_weights[pid] = 0.2 + popularity * 3.6
            if product['available']:
                available_product_ids.append(pid)

            writer.writerow([
                pid,
                creator['id'],
                leaf_category_id,
                name,
                description,
                image_url,
                available,
            ])
        print(f'{num_products} generated; {len(available_product_ids)} available')

    return products, available_product_ids, products_by_category, popularity_weights


def gen_inventory(products, user_profiles):
    product_lookup = {product['id']: product for product in products}
    product_listings = defaultdict(list)
    seller_product_pairs = []
    seller_listing_count = Counter()
    seller_quality = {}

    with open(BASE / 'Inventory.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Inventory...', end=' ', flush=True)
        count = 0

        for product in products:
            if not product['available']:
                continue

            category_id = product['root_category_id']
            popularity = product['popularity']
            premium = product['premium']
            if premium:
                seller_count = weighted_choice([1, 2, 3, 4], [26, 38, 26, 10])
            elif popularity > 0.75:
                seller_count = weighted_choice([3, 4, 5, 6, 7], [16, 25, 26, 21, 12])
            elif popularity > 0.40:
                seller_count = weighted_choice([2, 3, 4, 5], [26, 34, 25, 15])
            else:
                seller_count = weighted_choice([1, 2, 3, 4], [28, 37, 24, 11])

            candidates = []
            weights = []
            for profile in user_profiles:
                if profile['id'] == product['creator_id']:
                    continue
                if category_id not in profile['interests']:
                    continue
                candidates.append(profile)
                weights.append(profile['seller_affinity'] * (1 + profile['interest_rank'][category_id] * 0.7))
            if len(candidates) < seller_count:
                candidates = [profile for profile in user_profiles if profile['id'] != product['creator_id']]
                weights = [profile['seller_affinity'] for profile in candidates]

            sellers = weighted_sample_without_replacement(candidates, weights, seller_count)
            base_price = product['base_price']

            for index, seller in enumerate(sellers):
                if premium:
                    quantity = weighted_choice([0, 1, 2, 3, 4, 5, 6], [10, 18, 22, 20, 14, 10, 6])
                elif ROOT_CATEGORIES[category_id]['name'] in {'Books', 'Home', 'Grocery', 'Office'} and random.random() < 0.28:
                    quantity = random.randint(25, 140)
                elif random.random() < 0.12:
                    quantity = 0
                else:
                    quantity = random.randint(1, 18) if popularity < 0.35 else random.randint(2, 40)

                if premium and random.random() < 0.22:
                    quantity = random.randint(0, 3)

                price_delta = random.uniform(-0.07, 0.11) + index * random.uniform(0.0, 0.018)
                price = round(base_price * (1 + price_delta), 2)
                if price <= 0:
                    price = round(base_price, 2)
                updated_at = random_timestamp(days_back=160)
                listing = {
                    'seller_id': seller['id'],
                    'product_id': product['id'],
                    'quantity': quantity,
                    'price': price,
                    'updated_at': updated_at,
                }
                product_listings[product['id']].append(listing)
                seller_product_pairs.append((seller['id'], product['id']))
                seller_listing_count[seller['id']] += 1
                seller_quality.setdefault(seller['id'], clamp(random.uniform(0.48, 0.92), 0.1, 0.98))
                writer.writerow([seller['id'], product['id'], quantity, money(price), updated_at])
                count += 1
                if count % 500 == 0:
                    print(f'{count}', end=' ', flush=True)

        print(f'{count} generated')

    stocked_product_ids = {product_id for product_id, listings in product_listings.items() if any(listing['quantity'] > 0 for listing in listings)}
    return product_lookup, product_listings, seller_product_pairs, seller_listing_count, seller_quality, stocked_product_ids


def gen_purchases(num_purchases, user_profiles, available_product_ids, products_by_category, popularity_weights):
    with open(BASE / 'Purchases.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Purchases...', end=' ', flush=True)
        for purchase_id in range(1, num_purchases + 1):
            if purchase_id % 250 == 0:
                print(f'{purchase_id}', end=' ', flush=True)
            user = weighted_choice(user_profiles, [profile['order_affinity'] for profile in user_profiles])
            product_id = select_product_for_user(user, products_by_category, available_product_ids, popularity_weights)
            time_purchased = random_timestamp(days_back=1100)
            writer.writerow([purchase_id, user['id'], product_id, time_purchased])
        print(f'{num_purchases} generated')


def gen_product_reviews(num_reviews, user_profiles, available_product_ids, products_by_category, popularity_weights, product_lookup):
    used_pairs = set()
    with open(BASE / 'ProductReviews.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('ProductReviews...', end=' ', flush=True)
        review_id = 1
        attempts = 0
        while review_id <= num_reviews and attempts < num_reviews * 40:
            attempts += 1
            user = weighted_choice(user_profiles, [profile['cart_affinity'] for profile in user_profiles])
            product_id = select_product_for_user(user, products_by_category, available_product_ids, popularity_weights)
            pair = (user['id'], product_id)
            if pair in used_pairs:
                continue
            used_pairs.add(pair)
            product = product_lookup[product_id]
            rating = review_rating_from_quality(product['quality'])
            review = product_review_text(product, rating)
            created_at = random_timestamp(days_back=1000)
            writer.writerow([review_id, user['id'], product_id, rating, review, created_at])
            if review_id % 300 == 0:
                print(f'{review_id}', end=' ', flush=True)
            review_id += 1
        print(f'{review_id - 1} generated')


def gen_order_items(num_orders, user_profiles, product_listings, stocked_product_ids, products_by_category, popularity_weights, product_lookup, seller_quality):
    order_summaries = []
    seller_sales = Counter()
    item_id = 1

    with open(BASE / 'OrderItems.csv', 'w') as f:
        writer = csv.writer(f, dialect='excel', lineterminator='\n')
        print('OrderItems...', end=' ', flush=True)

        for order_id in range(1, num_orders + 1):
            if order_id % 100 == 0:
                print(f'o{order_id}', end=' ', flush=True)

            user = weighted_choice(user_profiles, [profile['order_affinity'] for profile in user_profiles])
            created_at = random_timestamp(days_back=750)
            line_count = weighted_choice([1, 2, 3, 4, 5], [44, 30, 16, 7, 3])
            chosen_listing_keys = set()
            line_items = []

            attempts = 0
            while len(line_items) < line_count and attempts < 50:
                attempts += 1
                product_id = select_product_for_user(
                    user,
                    products_by_category,
                    list(stocked_product_ids),
                    popularity_weights,
                    require_stock=True,
                    stocked_products=list(stocked_product_ids),
                )
                listing = choose_listing_for_product(product_listings[product_id], buyer_id=user['id'], require_stock=True)
                if listing is None:
                    continue
                key = (listing['seller_id'], listing['product_id'])
                if key in chosen_listing_keys:
                    continue
                chosen_listing_keys.add(key)
                quantity = weighted_choice([1, 2, 3], [76, 20, 4])
                quantity = min(quantity, max(1, listing['quantity']))
                unit_price = round(listing['price'] * random.uniform(0.96, 1.04), 2)
                age_days = max(0, (datetime.now() - created_at).days)
                base_fulfilled = 0.92 if age_days > 90 else 0.68 if age_days > 30 else 0.34
                seller_factor = seller_quality.get(listing['seller_id'], 0.7) - 0.65
                fulfilled = random.random() < clamp(base_fulfilled + seller_factor * 0.18, 0.1, 0.98)
                fulfilled_at = ''
                if fulfilled:
                    fulfilled_at = created_at + timedelta(hours=random.randint(6, 168), minutes=random.randint(0, 59))
                line_items.append({
                    'seller_id': listing['seller_id'],
                    'product_id': listing['product_id'],
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'fulfilled': fulfilled,
                    'fulfilled_at': fulfilled_at,
                })

            if not line_items:
                fallback_product_id = random.choice(list(stocked_product_ids))
                fallback_listing = choose_listing_for_product(product_listings[fallback_product_id], buyer_id=user['id'], require_stock=True)
                line_items.append({
                    'seller_id': fallback_listing['seller_id'],
                    'product_id': fallback_listing['product_id'],
                    'quantity': 1,
                    'unit_price': fallback_listing['price'],
                    'fulfilled': False,
                    'fulfilled_at': '',
                })

            total_amount = 0.0
            total_quantity = 0
            all_fulfilled = True
            for line in line_items:
                total_amount += line['quantity'] * line['unit_price']
                total_quantity += line['quantity']
                all_fulfilled = all_fulfilled and line['fulfilled']
                seller_sales[line['seller_id']] += line['quantity']
                writer.writerow([
                    item_id,
                    order_id,
                    line['product_id'],
                    line['seller_id'],
                    line['quantity'],
                    money(line['unit_price']),
                    str(line['fulfilled']).lower(),
                    line['fulfilled_at'],
                ])
                item_id += 1

            order_summaries.append((
                order_id,
                user['id'],
                money(total_amount),
                total_quantity,
                created_at,
                str(all_fulfilled).lower(),
                'false',
            ))

        print(f'{item_id - 1} generated')

    return order_summaries, seller_sales


def gen_orders(order_summaries):
    """
    Write pre-built order summary rows to Orders.csv.

    order_summaries is produced by the order-building loop upstream, which
    assigns each order a fulfillment probability based on age:
      - >90 days old: 92% chance fulfilled (most old orders are complete)
      - >30 days old: 68% chance fulfilled
      - recent:       34% chance fulfilled (many new orders still pending)
    A seller quality factor (±0.65) further adjusts each order's fulfillment
    probability to simulate sellers with varying reliability.
    """
    with open(BASE / 'Orders.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Orders...', end=' ', flush=True)
        for index, summary in enumerate(order_summaries, start=1):
            if index % 100 == 0:
                print(f'{index}', end=' ', flush=True)
            writer.writerow(summary)
        print(f'{len(order_summaries)} generated')


def gen_seller_reviews(num_reviews, user_profiles, seller_listing_count, seller_quality, seller_sales):
    used_pairs = set()
    seller_ids = sorted(seller_listing_count.keys())
    seller_weights = [max(1, seller_listing_count[seller_id] + seller_sales.get(seller_id, 0) * 0.8) for seller_id in seller_ids]
    with open(BASE / 'SellerReviews.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('SellerReviews...', end=' ', flush=True)
        review_id = 1
        attempts = 0
        while review_id <= num_reviews and attempts < num_reviews * 40:
            attempts += 1
            seller_id = weighted_choice(seller_ids, seller_weights)
            user = weighted_choice(user_profiles, [profile['order_affinity'] for profile in user_profiles])
            if user['id'] == seller_id:
                continue
            pair = (user['id'], seller_id)
            if pair in used_pairs:
                continue
            used_pairs.add(pair)
            rating = seller_review_rating(seller_quality.get(seller_id, 0.72))
            review = seller_review_text(rating)
            created_at = random_timestamp(days_back=1000)
            writer.writerow([review_id, user['id'], seller_id, rating, review, created_at])
            if review_id % 300 == 0:
                print(f'{review_id}', end=' ', flush=True)
            review_id += 1
        print(f'{review_id - 1} generated')


def gen_cart_items(num_cart_items, user_profiles, product_listings, stocked_product_ids, products_by_category, popularity_weights):
    used_triples = set()
    stocked_products = list(stocked_product_ids)
    cart_users = weighted_sample_without_replacement(
        user_profiles,
        [profile['cart_affinity'] for profile in user_profiles],
        min(len(user_profiles), 220),
    )
    with open(BASE / 'CartItems.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('CartItems...', end=' ', flush=True)
        item_count = 0
        attempts = 0
        while item_count < num_cart_items and attempts < num_cart_items * 50:
            attempts += 1
            user = weighted_choice(cart_users, [profile['cart_affinity'] for profile in cart_users])
            product_id = select_product_for_user(
                user,
                products_by_category,
                stocked_products,
                popularity_weights,
                require_stock=True,
                stocked_products=stocked_products,
            )
            listing = choose_listing_for_product(product_listings[product_id], buyer_id=user['id'], require_stock=True)
            if listing is None:
                continue
            triple = (user['id'], product_id, listing['seller_id'])
            if triple in used_triples:
                continue
            used_triples.add(triple)
            quantity = weighted_choice([1, 2, 3, 4], [72, 21, 5, 2])
            quantity = min(quantity, listing['quantity'])
            saved = 'true' if random.random() < 0.15 else 'false'
            writer.writerow([user['id'], product_id, listing['seller_id'], quantity, money(listing['price']), saved])
            item_count += 1
            if item_count % 250 == 0:
                print(f'{item_count}', end=' ', flush=True)
        print(f'{item_count} generated')


def gen_wishlist(user_profiles, available_product_ids, products_by_category, popularity_weights, num_items=800):
    used_pairs = set()
    with open(BASE / 'Wishlist.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Wishlist...', end=' ', flush=True)
        count = 0
        attempts = 0
        while count < num_items and attempts < num_items * 20:
            attempts += 1
            user = weighted_choice(user_profiles, [p['cart_affinity'] for p in user_profiles])
            product_id = select_product_for_user(user, products_by_category, available_product_ids, popularity_weights)
            pair = (user['id'], product_id)
            if pair in used_pairs:
                continue
            used_pairs.add(pair)
            added_at = random_timestamp(days_back=200)
            writer.writerow([user['id'], product_id, added_at])
            count += 1
        print(f'{count} generated')


def gen_coupons():
    coupons = [
        (1, 'WELCOME10', 'percentage', '10.00', '0.00', 500, '', ''),
        (2, 'FLAT5OFF', 'flat', '5.00', '25.00', 200, '', ''),
        (3, 'SAVE20', 'percentage', '20.00', '50.00', 100, '', ''),
        (4, 'FREESHIP', 'flat', '3.99', '0.00', 1000, '', ''),
        (5, 'BIGORDER15', 'percentage', '15.00', '100.00', 50, '', ''),
        (6, 'SUMMER25', 'percentage', '25.00', '75.00', 150, '', ''),
        (7, 'FLAT10', 'flat', '10.00', '40.00', 300, '', ''),
        (8, 'VIP30', 'percentage', '30.00', '200.00', 20, '', ''),
    ]
    with open(BASE / 'Coupons.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Coupons...', end=' ', flush=True)
        for coupon in coupons:
            writer.writerow(coupon)
        print(f'{len(coupons)} generated')


def gen_tags_and_product_tags(products):
    tag_to_id = {}
    product_tag_rows = []

    for product in products:
        for tag_name in product.get('tags', []):
            slug = slugify(tag_name)
            if slug not in tag_to_id:
                tag_to_id[slug] = {
                    'id': len(tag_to_id) + 1,
                    'display_name': tag_name.title() if '-' not in tag_name else tag_name.replace('-', ' ').title(),
                    'slug': slug,
                    'created_by': '',
                    'is_active': 'true',
                }
            product_tag_rows.append((product['id'], tag_to_id[slug]['id']))

    with open(BASE / 'Tags.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Tags...', end=' ', flush=True)
        for tag in sorted(tag_to_id.values(), key=lambda value: value['display_name']):
            writer.writerow([tag['id'], tag['display_name'], tag['slug'], tag['created_by'], tag['is_active']])
        print(f'{len(tag_to_id)} generated')

    with open(BASE / 'ProductTags.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('ProductTags...', end=' ', flush=True)
        for product_id, tag_id in product_tag_rows:
            writer.writerow([product_id, tag_id])
        print(f'{len(product_tag_rows)} generated')


def main():
    user_profiles = gen_users(NUM_USERS)
    gen_categories()
    products, available_product_ids, products_by_category, popularity_weights = gen_products(NUM_PRODUCTS, user_profiles)
    gen_tags_and_product_tags(products)
    product_lookup, product_listings, seller_product_pairs, seller_listing_count, seller_quality, stocked_product_ids = gen_inventory(products, user_profiles)
    gen_purchases(NUM_PURCHASES, user_profiles, available_product_ids, products_by_category, popularity_weights)
    gen_product_reviews(NUM_PRODUCT_REVIEWS, user_profiles, available_product_ids, products_by_category, popularity_weights, product_lookup)
    order_summaries, seller_sales = gen_order_items(
        NUM_ORDERS,
        user_profiles,
        product_listings,
        stocked_product_ids,
        products_by_category,
        popularity_weights,
        product_lookup,
        seller_quality,
    )
    gen_orders(order_summaries)
    gen_seller_reviews(NUM_SELLER_REVIEWS, user_profiles, seller_listing_count, seller_quality, seller_sales)
    gen_cart_items(NUM_CART_ITEMS, user_profiles, product_listings, stocked_product_ids, products_by_category, popularity_weights)
    gen_wishlist(user_profiles, available_product_ids, products_by_category, popularity_weights)
    gen_coupons()


if __name__ == '__main__':
    main()
