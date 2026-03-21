Final Project (Standard Project/Mini-Amazon) for CS 316

Team: Jai Kasera, Blake Passe, Darren Li, Evan Bulan, Shambhavi Sinha

Team Name: Project Jeff

MILESTONE 2

Users Guru: responsible for Account / Purchases — Darren Li
    * Created table designs for account (users table) and purchases (purchases table) in BCNF, decided on reasonable column values for each table (notes included in table descriptions)
    * Wrote constraints for each table 
    * Wrote a view that retrieves seller/user info based on whether they are a seller or not (subject to change) 
    * Set up GitHub repo with template files
Products Guru: responsible for Products — Shambhavi Sinha
    * Created tables designs for products, defined schema with categories, products, seller specific inventory and pricing, with constraints, relationships and update triggers
    * Browsing by category, keywords, price sorting, creator based edit control and multiseller listings per product possible
Carts Guru: responsible for Cart / Order — Jai Kasera
    * Designed cart and order tables in BCNF, including cart_items and order_items with appropriate primary keys and foreign key relationships
    * Defined logic for adding/removing items from cart and updating item quantities
    * Created order placement workflow that converts cart entries into finalized orders
Sellers Guru: responsible for Inventory / Order Fulfillment — Evan Bulan
    * Designed inventory management schema to track seller-specific stock levels per product
    * Defined order fulfillment workflow including shipment status updates and tracking metadata
Social Guru: responsible for Feedback / Messaging — Blake Passe
    * Designed product_reviews and seller_reviews tables in BCNF with appropriate primary keys, foreign keys, uniqueness constraints, and rating checks
    * Defined eligibility logic with joins and specified summary rating computation (average and count) for products and sellers
    * Worked on  “My Reviews” functionality integration with reverse chronological sorting and edit/delete support



MILESTONE 3 

Products Guru: responsible for Products — Shambhavi Sinha
    * Implemented a backend API endpoint that returns the top k most expensive available products using a SQL query with ORDER BY price DESC and LIMIT k.
    * Added the method Product.get_top_k_expensive(k) in app/models/product.py and the corresponding routes in app/products.py (/products/top/<int:k> for JSON and /products/top?k= for the HTML page).
    * Created app/templates/top_products.html, which allows the user to input a value of k and displays the resulting products in a table.
    * Registered the products blueprint in app/__init__.py and added a form on the homepage (index.html) to interact with the feature and demonstrate it during the project demo
Users Guru: Darren Li
    * added search box for looking up purchases given a user_id (index.html) + corresponding endpoint (users.py, purchase.py) and result display screen (purchases.html)
    * implemented error popup if user_id is not registered yet (see changes in base.html)
        * in future, can consider implementing new feature for looking up users by firstname OR lastname OR email (or listing out all users)
Sellers Guru: Evan Bulan
   * Added Inventory table (as created originally by Products Guru), added necessary copy to load.sh, and added dummy data to allow for interaction with the Inventory table in testing/demo
   * Implemented backend API endpoint that will return a list of all products of a given seller ID, only retrieving product ID and name for now (though selecting all columns in the SQL query that will be useful for seller dashboard later on)
   * Modeled execution and displayed results of this endpoint on te Flask frontend in similar style to previously created displays, where a user ID can be input and then the product IDs and names are returned
Carts Guru: Jai Kasera
   * Added CartItems table to db/create.sql with columns (user_id, product_id, seller_id, quantity, unit_price, added_at) and foreign key constraints to Users, Products, and Users (seller)
   * Added seed data CSV (db/data/CartItems.csv) and corresponding \COPY statement in db/load.sql
   * Implemented CartItem.get_items_by_user(user_id) in app/models/cart.py using a parameterized SQL query that joins cart_items with Products and Users to retrieve product names and seller names, ordered by added_at DESC
   * Created backend routes GET /cart (HTML page with user ID input and cart table display) and GET /cart/items/<user_id> (JSON API) in app/carts.py, with validation that redirects and flashes an error if the user ID is not found
   * Created app/templates/cart.html with a User ID input form and results table showing product ID, product name, seller, quantity, unit price, line total, and date added, with a computed grand total

   Implementation file locations:
     app/carts.py                         (backend routes)
     app/models/cart.py                   (SQL query / model)
     app/templates/cart.html              (frontend template)
     db/create.sql                        (CartItems table definition)
     db/load.sql                          (seed data loading)
     db/data/CartItems.csv                (cart item seed data)

Social Guru: Blake Passe
   * Added ProductReviews and SellerReviews tables to db/create.sql with appropriate columns (user_id, product_id/seller_id, rating 1-5, review text, created_at timestamp) and uniqueness constraints
   * Added seed data CSVs (db/data/ProductReviews.csv, db/data/SellerReviews.csv) and corresponding \COPY statements in db/load.sql
   * Implemented Feedback.get_recent_by_uid(user_id) in app/models/feedback.py using a parameterized UNION ALL SQL query across both feedback tables, ordered by created_at DESC with LIMIT 5
   * Created backend route GET /social/feedback?user_id=<id> in app/social.py that validates the user exists and returns the 5 most recent feedback posts
   * Created app/templates/social_feedback.html with a User ID input form and results table showing feedback type, target ID, star rating, review text, and date
   * Registered the social blueprint in app/__init__.py

   Implementation file locations:
     app/social.py                        (backend route)
     app/models/feedback.py              (SQL query / model)
     app/templates/social_feedback.html  (frontend template)
     db/create.sql                        (ProductReviews + SellerReviews table definitions)
     db/load.sql                          (seed data loading)
     db/data/ProductReviews.csv           (product review seed data)
     db/data/SellerReviews.csv            (seller review seed data)

LLMs were used to assist with this assignment
