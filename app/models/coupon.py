from flask import current_app as app


class Coupon:
    def __init__(self, coupon_id, code, discount_type, discount_value,
                 min_order_amount, max_uses, expiry_date, applicable_product_id):
        self.id = coupon_id
        self.code = code
        self.discount_type = discount_type
        self.discount_value = discount_value
        self.min_order_amount = min_order_amount
        self.max_uses = max_uses
        self.expiry_date = expiry_date
        self.applicable_product_id = applicable_product_id

    @staticmethod
    def get_by_code(code):
        rows = app.db.execute('''
SELECT id, code, discount_type, discount_value, min_order_amount,
       max_uses, expiry_date, applicable_product_id
FROM coupons WHERE code = :code
''', code=code.strip().upper())
        return Coupon(*rows[0]) if rows else None

    @staticmethod
    def validate(code, cart_total):
        """Quick validation for display purposes. Returns (coupon, discount, error)."""
        import datetime
        coupon = Coupon.get_by_code(code)
        if coupon is None:
            return None, 0, 'Invalid coupon code.'

        if coupon.expiry_date and coupon.expiry_date < datetime.datetime.now():
            return None, 0, 'This coupon has expired.'

        if cart_total < float(coupon.min_order_amount):
            return None, 0, f'Order must be at least ${float(coupon.min_order_amount):.2f} to use this coupon.'

        if coupon.max_uses is not None:
            use_count_rows = app.db.execute('''
SELECT COUNT(*) FROM coupon_uses WHERE coupon_id = :cid
''', cid=coupon.id)
            if use_count_rows[0][0] >= coupon.max_uses:
                return None, 0, 'This coupon has reached its maximum number of uses.'

        if coupon.discount_type == 'percentage':
            discount = round(cart_total * float(coupon.discount_value) / 100, 2)
        else:
            discount = min(float(coupon.discount_value), cart_total)

        return coupon, discount, None
