from werkzeug.security import generate_password_hash
import csv
import random
from datetime import timedelta
from pathlib import Path
from faker import Faker

BASE = Path(__file__).resolve().parent

num_users = 300
num_categories = 8
num_products = 2000
num_purchases = 2500
num_product_reviews = 12000
num_seller_reviews = 6000
num_cart_items = 1200
num_orders = 1800

Faker.seed(0)
random.seed(0)
fake = Faker()

CATEGORY_NAMES = [
    "Food",
    "Art",
    "Luxury",
    "Books",
    "Electronics",
    "Home",
    "Clothing",
    "Sports",
]


def get_csv_writer(f):
    return csv.writer(f, dialect='unix')


def gen_users(num_users):
    with open(BASE / 'Users.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Users...', end=' ', flush=True)
        for uid in range(num_users):
            if uid % 10 == 0:
                print(f'{uid}', end=' ', flush=True)
            profile = fake.profile()
            email = profile['mail']
            plain_password = f'pass{uid}'
            password = generate_password_hash(plain_password)
            name_components = profile['name'].split(' ')
            firstname = name_components[0]
            lastname = name_components[-1]
            balance = f"{random.randint(0, 50000) / 100:.2f}"
            # Keep addresses single-line for predictable CSV ingestion.
            address = fake.address().replace('\n', ', ')
            writer.writerow([uid, email, password, firstname, lastname, balance, address])
        print(f'{num_users} generated')


def gen_categories():
    with open(BASE / 'Categories.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Categories...', end=' ', flush=True)
        for cname in CATEGORY_NAMES:
            writer.writerow([cname])
        print(f'{len(CATEGORY_NAMES)} generated')


def gen_products(num_products, num_users, num_categories):
    available_pids = []
    with open(BASE / 'Products.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Products...', end=' ', flush=True)
        for pid in range(1, num_products + 1):
            if pid % 100 == 0:
                print(f'{pid}', end=' ', flush=True)

            creator_id = random.randint(0, num_users - 1)
            category_id = random.randint(1, num_categories)
            name = fake.sentence(nb_words=4).rstrip('.')
            description = fake.paragraph(nb_sentences=3)
            image_url = f"https://picsum.photos/seed/product{pid}/300/200"
            available = random.choice(['true', 'false'])

            if available == 'true':
                available_pids.append(pid)

            writer.writerow([
                pid,
                creator_id,
                category_id,
                name,
                description,
                image_url,
                available
            ])

        print(f'{num_products} generated; {len(available_pids)} available')
    return available_pids


def gen_inventory(available_pids, num_users):
    seller_product_pairs = set()

    with open(BASE / 'Inventory.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Inventory...', end=' ', flush=True)

        count = 0
        for pid in available_pids:
            num_sellers_for_product = random.randint(1, 5)
            sellers = random.sample(range(num_users), k=min(num_sellers_for_product, num_users))

            for seller_id in sellers:
                pair = (seller_id, pid)
                if pair in seller_product_pairs:
                    continue
                seller_product_pairs.add(pair)

                quantity = random.randint(0, 50)
                price = f"{random.randint(2, 1000)}.{random.randint(0, 99):02}"
                updated_at = fake.date_time_this_year()

                writer.writerow([seller_id, pid, quantity, price, updated_at])
                count += 1

                if count % 500 == 0:
                    print(f'{count}', end=' ', flush=True)

        print(f'{count} generated')

    return list(seller_product_pairs)


def gen_purchases(num_purchases, available_pids, num_users):
    with open(BASE / 'Purchases.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Purchases...', end=' ', flush=True)
        for purchase_id in range(num_purchases):
            if purchase_id % 100 == 0:
                print(f'{purchase_id}', end=' ', flush=True)

            uid = random.randint(0, num_users - 1)
            pid = random.choice(available_pids)
            time_purchased = fake.date_time_this_decade()

            writer.writerow([purchase_id, uid, pid, time_purchased])

        print(f'{num_purchases} generated')


def gen_product_reviews(num_reviews, available_pids, num_users):
    used_pairs = set()

    with open(BASE / 'ProductReviews.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('ProductReviews...', end=' ', flush=True)

        review_id = 0
        attempts = 0
        while review_id < num_reviews and attempts < num_reviews * 10:
            attempts += 1

            user_id = random.randint(0, num_users - 1)
            product_id = random.choice(available_pids)
            pair = (user_id, product_id)

            if pair in used_pairs:
                continue
            used_pairs.add(pair)

            rating = random.randint(1, 5)
            review = fake.sentence(nb_words=12)
            created_at = fake.date_time_this_decade()

            writer.writerow([review_id, user_id, product_id, rating, review, created_at])
            review_id += 1

            if review_id % 200 == 0:
                print(f'{review_id}', end=' ', flush=True)

        print(f'{review_id} generated')


def gen_seller_reviews(num_reviews, seller_product_pairs, num_users):
    used_pairs = set()
    seller_ids = sorted({seller_id for seller_id, _ in seller_product_pairs})

    with open(BASE / 'SellerReviews.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('SellerReviews...', end=' ', flush=True)

        review_id = 0
        attempts = 0
        while review_id < num_reviews and attempts < num_reviews * 10:
            attempts += 1

            user_id = random.randint(0, num_users - 1)
            seller_id = random.choice(seller_ids)

            if user_id == seller_id:
                continue

            pair = (user_id, seller_id)
            if pair in used_pairs:
                continue
            used_pairs.add(pair)

            rating = random.randint(1, 5)
            review = fake.sentence(nb_words=10)
            created_at = fake.date_time_this_decade()

            writer.writerow([review_id, user_id, seller_id, rating, review, created_at])
            review_id += 1

            if review_id % 200 == 0:
                print(f'{review_id}', end=' ', flush=True)

        print(f'{review_id} generated')


def gen_cart_items(num_cart_items, seller_product_pairs, num_users):
    used_triples = set()

    with open(BASE / 'CartItems.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('CartItems...', end=' ', flush=True)

        item_count = 0
        attempts = 0
        while item_count < num_cart_items and attempts < num_cart_items * 10:
            attempts += 1

            user_id = random.randint(0, num_users - 1)
            seller_id, product_id = random.choice(seller_product_pairs)

            triple = (user_id, product_id, seller_id)
            if triple in used_triples:
                continue
            used_triples.add(triple)

            quantity = random.randint(1, 5)
            unit_price = f"{random.randint(2, 1000)}.{random.randint(0, 99):02}"

            writer.writerow([user_id, product_id, seller_id, quantity, unit_price])
            item_count += 1

            if item_count % 200 == 0:
                print(f'{item_count}', end=' ', flush=True)

        print(f'{item_count} generated')


def gen_order_items(num_orders, seller_product_pairs, num_users):
    """
    Generate order_items rows and return computed order summaries for gen_orders.
    Each summary tuple is:
      (order_id, user_id, total_amount, num_items, created_at, fulfilled)
    """
    order_summaries = []
    item_id = 1

    with open(BASE / 'OrderItems.csv', 'w') as f:
        # Use non-quoting-for-empty behavior so blank fulfilled_at loads as SQL NULL
        # under \COPY ... NULL '' CSV.
        writer = csv.writer(f, dialect='excel', lineterminator='\n')
        print('OrderItems...', end=' ', flush=True)

        for order_id in range(1, num_orders + 1):
            if order_id % 100 == 0:
                print(f'o{order_id}', end=' ', flush=True)

            user_id = random.randint(0, num_users - 1)
            created_at = fake.date_time_this_decade()

            max_unique_items = min(6, len(seller_product_pairs))
            line_count = random.randint(1, max_unique_items)
            chosen_pairs = random.sample(seller_product_pairs, k=line_count)

            total_amount = 0.0
            total_quantity = 0
            all_fulfilled = True

            for seller_id, product_id in chosen_pairs:
                quantity = random.randint(1, 5)
                unit_price = random.randint(200, 100000) / 100

                # Older orders are more likely to be fulfilled.
                age_days = (fake.date_time_this_year() - created_at).days
                fulfilled_prob = 0.85 if age_days > 30 else 0.35
                fulfilled = random.random() < fulfilled_prob

                if fulfilled:
                    fulfillment_delay = timedelta(
                        hours=random.randint(1, 96),
                        minutes=random.randint(0, 59),
                        seconds=random.randint(0, 59),
                    )
                    fulfilled_at = created_at + fulfillment_delay
                    fulfilled_at_value = fulfilled_at
                else:
                    fulfilled_at_value = ''
                    all_fulfilled = False

                total_amount += quantity * unit_price
                total_quantity += quantity

                writer.writerow([
                    item_id,
                    order_id,
                    product_id,
                    seller_id,
                    quantity,
                    f'{unit_price:.2f}',
                    str(fulfilled).lower(),
                    fulfilled_at_value,
                ])
                item_id += 1

            order_summaries.append((
                order_id,
                user_id,
                f'{total_amount:.2f}',
                total_quantity,
                created_at,
                str(all_fulfilled).lower(),
            ))

        print(f'{item_id - 1} generated')

    return order_summaries


def gen_orders(order_summaries):
    with open(BASE / 'Orders.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Orders...', end=' ', flush=True)

        for i, summary in enumerate(order_summaries, start=1):
            if i % 100 == 0:
                print(f'{i}', end=' ', flush=True)
            writer.writerow(summary)

        print(f'{len(order_summaries)} generated')


if __name__ == '__main__':
    gen_users(num_users)
    gen_categories()
    available_pids = gen_products(num_products, num_users, num_categories)
    seller_product_pairs = gen_inventory(available_pids, num_users)
    gen_purchases(num_purchases, available_pids, num_users)
    gen_product_reviews(num_product_reviews, available_pids, num_users)
    gen_seller_reviews(num_seller_reviews, seller_product_pairs, num_users)
    gen_cart_items(num_cart_items, seller_product_pairs, num_users)
    order_summaries = gen_order_items(num_orders, seller_product_pairs, num_users)
    gen_orders(order_summaries)