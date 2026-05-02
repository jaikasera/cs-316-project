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
    * Designed product_reviews and seller_reviews tables in BCNF with primary keys, foreign keys, uniqueness constraints, and rating checks
    * Defined eligibility and summary ratings (average and count) for products and sellers using joins
    * Planned “My Reviews” with reverse chronological sorting and edit/delete support



MILESTONE 3 

Link to demo: https://drive.google.com/file/d/1XSaOzB5qoASo1ZXaf36c-HJ-JXw0l6B3/view?usp=sharing 

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
   * Implemented backend API endpoint GET /cart/items/<user_id> that returns all cart items for a given user as JSON, with product name, seller name, quantity, unit price, and line total
   * Added the CartItem model in app/models/cart.py with get_items_by_user() and add_item() methods using parameterized SQL queries with ON CONFLICT upsert logic
   * Created the cart page at GET /cart with a user ID lookup form and a table displaying all cart items, unit prices, line totals, and an overall cart total
   * Added POST /cart/add endpoint for adding items to the cart from the product detail page, integrated with the existing products blueprint
Social Guru: Blake Passe
   * Added ProductReviews and SellerReviews to db/create.sql with seed CSVs and \COPY in db/load.sql
   * Implemented Feedback.get_recent_by_uid(user_id) in app/models/feedback.py (UNION ALL across both tables, newest first, LIMIT 5)
   * Added GET /social/feedback?user_id=<id>, social_feedback.html (form + table), and registered the social blueprint in app/__init__.py

LLMs were used to assist with this assignment

TODO LIST (Users Guru) 

*public view for user (show account number and name, if seller also show email, address, and reviews)
*make subpages to align more closely with design

MILESTONE 4
Link to demo video: https://drive.google.com/file/d/1ZL7iXbDUhyM7SIDq71ptRFl3HRxBIF8X/view?usp=sharing

Users Guru — Darren Li
    * added address and balance columns to users relation and added balance display to main bar
    * modified registration screen and load.sql to support new address field
    * add page to withdraw/add to balance (implemented associated endpoints, html, etc)
    * investigated potential SQL injection vulnerabilities from UI (want to investigate more into direct queries on API endpoints)
    * created additional sample user data entries to start out with (passwords are all "test123")

Products Guru: responsible for Products — Shambhavi Sinha
    * Refactored the Product schema and model to support richer metadata (category, description, image) and moved pricing logic to Inventory.
    * Built and connected product browsing + detail pages, including seller inventory and review display.
    * Unified review handling by extending the Feedback model to support product reviews (instead of a separate ProductReview model).
    * Improved the homepage UI/UX, organizing it into a dashboard with cards, cleaner tables, and consistent labeling.
    * Added cart implementation in conjuction with Carts Guru

Carts Guru: responsible for Cart / Order — Jai Kasera
    * Implemented full checkout flow with transactional order submission that validates inventory availability and buyer balance before processing
    * Added cart management functionality including quantity updates and item removal with interactive controls on the cart page
    * Built buyer-facing order history page with pagination and order detail page showing per-line-item fulfillment status and timestamps
    * Updated seller fulfillment logic to automatically mark the entire order as fulfilled once all line items are fulfilled
    * Added navigation links for My Cart and My Orders and integrated cart/order pages with product detail and seller inventory views

Social Guru: responsible for Feedback / Messaging — Blake Passe
    * Added product detail review pagination with sort (newest, oldest, highest, lowest) and per-page controls
    * Added GET /social/feedback/all?user_id=<id>&page=<n>&per_page=<m> for paginated user-authored feedback
    * Added indexes on ProductReviews and SellerReviews for query patterns at scale (product/seller/user with created_at)
    * Increased generated seed scale in db/generated/gen.py (e.g. 300 users, 2000 products, 12k product reviews, 6k seller reviews)

Sellers Guru: responsible for Inventory / Order Fulfillment - Evan Bulan
    * Added the ability to add products to inventory for seller accounts
    * Added a seller inventory page to allow for full viewing of seller inventory
    * Added ability to view current products in inventory and edit quantities/remove products
    * Implemented order history page to allow for sellers to see all information regarding their order history
    * Added ability to mark pending orders as fulfilled on order history


FINAL SUBMISSION

Products Guru: responsible for Products — Shambhavi Sinha
    * db/generated/gen.py now builds a larger marketplace-style seed dataset with hundreds of users, thousands of category-aware products, multi-seller inventory, popularity-weighted reviews, realistic price spreads, mixed stock levels, and repeat cart/order patterns.
    * The generator is intentionally category-driven so products in Books, Electronics, Home, Clothing, Sports, Beauty, Grocery, Pet Supplies, and Office read like real listings instead of generic Faker text.
    * Added browse-page pagination, an only-in-stock filter, and cheapest-seller highlighting.
    * Added homepage support for top-rated products.
    * Added product review submission and update support from the product detail page.
    * Added creator-only product deactivation controls and status handling.
    * Improved add-to-cart validation and flash-message UX across product/cart flows.
    * Upgraded the create/edit product form with stronger validation and a more guided setup experience.
    * Reworked the generated marketplace dataset to be larger, category-aware, and more realistic.
    * Restyled the customer-facing storefront into a Pokemon-inspired PokeMart theme with a custom banner/header, rotating hero banners, responsive product shelves, and updated customer pages.
    * Added wish list support, recently viewed tracking, and personalized homepage recommendations.
    * Added related products and frequently-bought-together suggestions on the product detail page.
    * Added product variants, image gallery support, price-watch messaging, and low-stock/restock alerts.
    * Added richer seller comparison details including seller ratings, stock visibility, cheapest-seller emphasis, and delivery estimate messaging.
    * Added review filters (stars, recent, with text, verified purchase only) plus verified-purchase badges.
    * Added popularity-based browse sorting in addition to price/rating sorting.
    * Added coupon support and save-for-later functionality in the cart flow.
    * Polished seller storefront pages with merchant stats, featured items, and improved inventory presentation.
    * Replaced the flat category-only setup with a label taxonomy that supports hierarchical categories plus reusable product tags.
    * Added a Labels page for creating and reviewing category/tag labels, with product forms updated to choose a leaf category and attach comma-separated tags.
    * Updated browse and product-detail flows to show taxonomy labels directly: products can now be filtered by category descendants or tag labels, and tags appear on browse cards and detail pages.
    * Updated the schema/load files to support Categories with parent-child structure plus Tags and ProductTags join data.
    * Added starter taxonomy seed data in both db/data and db/generated so the new hierarchy/tag workflow is represented in the dataset as well.
    * Revamped the /products/top?k= page into a more polished “top finds” showcase with styled cards, ranking badges, and a friendlier k-selector flow.

Social Guru: responsible for Feedback / Messaging — Blake Passe
    * Built out the full review lifecycle on top of the existing ProductReviews and SellerReviews schema so that buyers can now create, update, and delete their own reviews, not just submit them once.
    * Added Feedback.delete_product_review, Feedback.upsert_seller_review, Feedback.delete_seller_review, and Feedback.get_seller_review_by_user in app/models/feedback.py, each parameterized and scoped to the (user_id, product_id) or (user_id, seller_id) unique key so a buyer can only modify their own row.
    * Wrote Feedback.user_can_review_seller, an eligibility helper that joins orders and order_items so a buyer can only leave a seller review if they actually have an order containing an item fulfilled by that seller, replacing the older Inventory-based heuristic now that the orders schema exists.
    * Added Feedback.get_my_reviews, a single SQL query that UNIONs ProductReviews and SellerReviews with their target product name or seller display name and returns one combined, reverse-chronological list — used to power the new My Reviews page without needing two round trips.
    * Added POST /products/<id>/review/delete in app/products.py with login_required, existence checks, and consistent flash-category messaging so buyers can remove their own product review from the product detail page.
    * Added POST /sellers/<id>/review and POST /sellers/<id>/review/delete in app/users.py, including server-side input validation (1–5 rating, optional text), self-review prevention, eligibility enforcement, upsert vs first-time messaging, and flash feedback for every outcome.
    * Updated /users/public to pre-compute the visiting buyer’s own seller review and eligibility status, so the seller profile page can render the right form state (submit vs update vs ineligible vs not-logged-in) without doing extra requests in the template.
    * Added GET /social/my-reviews in app/social.py, a login-required page that consolidates every review the current user has written across both products and sellers into one timeline.
    * Created app/templates/my_reviews.html, a polished table that lists Type, Target (linked to the product or seller), star rating with N/5 score, review text (or a “(no review text)” placeholder), date, and per-row Edit + Delete actions — with deep links that jump straight into the corresponding review form via the new #review-form / #seller-review-form anchors.
    * Updated app/templates/user_public.html to render a buyer-facing seller review card right above the existing reviews list: a star-rating dropdown, optional review text area, a Submit/Update button, and (when applicable) a separate non-nested Delete Review form, all gated on eligibility and on the visitor not being the seller themselves.
    * Updated app/templates/product_detail.html with an explicit Delete My Note button under the existing TRAINER NOTES form, plus an id=“review-form” anchor so review-related deep links scroll directly to the form instead of dumping the user at the top of the page.
    * Updated app/templates/order_detail.html so that every line item in a buyer’s order now exposes Review product and Review seller links pointing at the right product or seller review form, dramatically shortening the path from “I just bought this” to “here is my review”.
    * Updated app/templates/account.html with a new My Reviews card containing a one-click Open My Reviews button, so buyers can find their own review history straight from the account dashboard.
    * Updated app/templates/base.html to add a 📒 My Reviews link in the global category nav strip for authenticated users, so the page is reachable from anywhere in the storefront.
    * Wired confirmation prompts (window.confirm) onto every destructive delete form across the new templates so a misclick can not silently wipe out a review.
    * Made sure delete buttons that appear inside review cards are placed in their own <form> blocks rather than nested inside the submit form, fixing a quietly invalid-HTML pattern that older versions of the page would have hit if they had supported delete.
    * Aligned all new flash-message categories (success, warning, danger) with the Bootstrap classes the rest of the app uses, so the new endpoints render with the same color treatment as other team members’ pages.
    * Reused the existing UNION ALL pattern from Feedback.get_recent_by_uid for the new combined My Reviews query, so the codebase keeps a single, consistent way of mixing product and seller feedback.
    * Kept verified-purchase and per-product review summary logic compatible with the larger Final Submission seed dataset so star averages and review counts continue to render correctly under heavier load.
    * Made the visitor experience work cleanly for both signed-in and anonymous users on every social page: anonymous viewers can still read product and seller reviews and see ratings, but every write/edit/delete entry point only appears to authenticated buyers.
    * Verified the new endpoints against the existing seller storefront and order history pages so review entry points appear in every place a buyer naturally lands after a purchase, not just on the product detail page.
    * Updated this README with a Social Guru section describing every shipping change above, and added an explicit acknowledgement that LLM tools were used for assistance during this assignment.

LLMs were used to assist with this assignment.
