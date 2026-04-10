\COPY Users FROM 'Users.csv' WITH DELIMITER ',' NULL '' CSV
\COPY Categories(name) FROM 'Categories.csv' WITH DELIMITER ',' NULL '' CSV

SELECT pg_catalog.setval('public.categories_id_seq',
                         (SELECT MAX(id)+1 FROM Categories),
                         false);

SELECT pg_catalog.setval('public.users_id_seq',
                         (SELECT MAX(id)+1 FROM Users),
                         false);

\COPY Products(id, creator_id, category_id, name, description, image_url, available) FROM 'Products.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.products_id_seq',
                         (SELECT MAX(id)+1 FROM Products),
                         false);

\COPY Purchases FROM 'Purchases.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.purchases_id_seq',
                         (SELECT MAX(id)+1 FROM Purchases),
                         false);

\COPY Inventory FROM 'Inventory.csv' WITH DELIMITER ',' NULL '' CSV

\COPY ProductReviews FROM 'ProductReviews.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.productreviews_id_seq',
                         (SELECT MAX(id)+1 FROM ProductReviews),
                         false);

\COPY SellerReviews FROM 'SellerReviews.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.sellerreviews_id_seq',
                         (SELECT MAX(id)+1 FROM SellerReviews),
                         false);

\COPY cart_items(user_id, product_id, seller_id, quantity, unit_price) FROM 'CartItems.csv' WITH DELIMITER ',' NULL '' CSV
