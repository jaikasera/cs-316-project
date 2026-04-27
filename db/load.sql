-- USERS
\COPY Users FROM 'Users.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.users_id_seq',
                         (SELECT MAX(id)+1 FROM Users),
                         false);

-- CATEGORIES
\COPY Categories(id, name, parent_id, slug, is_active) FROM 'Categories.csv' WITH (FORMAT csv, DELIMITER ',', NULL '', FORCE_NULL(parent_id));
SELECT pg_catalog.setval('public.categories_id_seq',
                         (SELECT MAX(id)+1 FROM Categories),
                         false);

-- TAGS
\COPY Tags(id, display_name, slug, created_by, is_active) FROM 'Tags.csv' WITH (FORMAT csv, DELIMITER ',', NULL '', FORCE_NULL(created_by));
SELECT pg_catalog.setval('public.tags_id_seq',
                         (SELECT COALESCE(MAX(id), 0)+1 FROM Tags),
                         false);

-- PRODUCTS
\COPY Products(id, creator_id, category_id, name, description, image_url, available) FROM 'Products.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.products_id_seq',
                         (SELECT MAX(id)+1 FROM Products),
                         false);

-- INVENTORY
\COPY Inventory(seller_id, product_id, quantity, price, updated_at) FROM 'Inventory.csv' WITH DELIMITER ',' NULL '' CSV;

-- PRODUCT TAGS
\COPY ProductTags(product_id, tag_id) FROM 'ProductTags.csv' WITH DELIMITER ',' NULL '' CSV;

-- PURCHASES
\COPY Purchases(id, uid, pid, time_purchased) FROM 'Purchases.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.purchases_id_seq',
                         (SELECT MAX(id)+1 FROM Purchases),
                         false);

-- PRODUCT REVIEWS
\COPY ProductReviews(id, user_id, product_id, rating, review, created_at) FROM 'ProductReviews.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.productreviews_id_seq',
                         (SELECT MAX(id)+1 FROM ProductReviews),
                         false);

-- SELLER REVIEWS
\COPY SellerReviews(id, user_id, seller_id, rating, review, created_at) FROM 'SellerReviews.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.sellerreviews_id_seq',
                         (SELECT MAX(id)+1 FROM SellerReviews),
                         false);

-- CART ITEMS
\COPY cart_items(user_id, product_id, seller_id, quantity, unit_price) FROM 'CartItems.csv' WITH DELIMITER ',' NULL '' CSV;

-- ORDERS
\COPY orders(id, user_id, total_amount, num_items, created_at, fulfilled) FROM 'Orders.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.orders_id_seq',
                         (SELECT MAX(id)+1 FROM orders),
                         false);

-- ORDER ITEMS
\COPY order_items(id, order_id, product_id, seller_id, quantity, unit_price, fulfilled, fulfilled_at) FROM 'OrderItems.csv' WITH DELIMITER ',' NULL '' CSV;
SELECT pg_catalog.setval('public.order_items_id_seq',
                         (SELECT MAX(id)+1 FROM order_items),
                         false);
