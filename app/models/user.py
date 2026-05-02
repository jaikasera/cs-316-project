from flask_login import UserMixin
from flask import current_app as app
from werkzeug.security import generate_password_hash, check_password_hash
from decimal import Decimal, InvalidOperation
import re

from .. import login


class User(UserMixin):
    MAX_BALANCE = Decimal('999999999999.99')
    _AMOUNT_PATTERN = re.compile(r'^\d+(?:\.\d{1,2})?$')

    def __init__(self, id, email, firstname, lastname, balance, address=None):
        self.id = id
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.balance = balance
        self.address = address

    @staticmethod
    def get_by_auth(email, password):
        rows = app.db.execute("""
SELECT password, id, email, firstname, lastname, balance
FROM Users
WHERE email = :email
""",
                              email=email)
        if not rows:  # email not found
            return None
        elif not check_password_hash(rows[0][0], password):
            # incorrect password
            return None
        else:
            return User(*(rows[0][1:]))

    @staticmethod
    def email_exists(email):
        rows = app.db.execute("""
SELECT email
FROM Users
WHERE email = :email
""",
                              email=email)
        return len(rows) > 0

    @staticmethod
    def register(email, password, firstname, lastname, address):
        try:
            rows = app.db.execute("""
INSERT INTO Users(email, password, firstname, lastname, address, balance)
VALUES(:email, :password, :firstname, :lastname, :address, :balance)
RETURNING id
""",
                                  email=email,
                                  password=generate_password_hash(password),
                                  firstname=firstname,
                                  lastname=lastname,
                                  address=address,
                                  balance=0.00)
            id = rows[0][0]
            return User.get(id)
        except Exception as e:
            # likely email already in use; better error checking and reporting needed;
            # the following simply prints the error to the console:
            print(str(e))
            return None

    @staticmethod
    @login.user_loader
    def get(id):
        rows = app.db.execute("""
SELECT id, email, firstname, lastname, balance, address
FROM Users
WHERE id = :id
""",
                              id=id)
        return User(*(rows[0])) if rows else None

    @staticmethod
    def _parse_balance_amount(raw_amount):
        amount_str = (raw_amount or '').strip()
        if not User._AMOUNT_PATTERN.fullmatch(amount_str):
            return None

        try:
            amount = Decimal(amount_str).quantize(Decimal('0.01'))
        except InvalidOperation:
            return None

        if amount <= 0:
            return None
        return amount

    @staticmethod
    def update_balance(uid, raw_amount, operation):
        amount = User._parse_balance_amount(raw_amount)
        if amount is None:
            return None, 'Enter a valid amount (integer or up to 2 decimal places).'

        if operation not in {'add', 'withdraw'}:
            return None, 'Invalid balance operation.'

        delta = amount if operation == 'add' else -amount

        try:
            rows = app.db.execute("""
UPDATE Users
SET balance = balance + :delta
WHERE id = :uid
  AND balance + :delta >= 0
  AND balance + :delta <= :max_balance
RETURNING id, email, firstname, lastname, balance
""",
                                  uid=uid,
                                  delta=delta,
                                  max_balance=User.MAX_BALANCE)
        except Exception:
            return None, 'Unable to update balance with that amount.'

        if not rows:
            return None, 'Balance must stay between $0.00 and $999,999,999,999.99.'

        return User(*(rows[0])), None
