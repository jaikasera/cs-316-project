from flask import render_template, request, flash, redirect, url_for
from flask import Blueprint

from .models.feedback import Feedback
from .models.user import User

bp = Blueprint('social', __name__)


@bp.route('/social/feedback')
def user_feedback():
    user_id = request.args.get('user_id', type=int)

    if user_id is None:
        return render_template('social_feedback.html', feedback=None, user=None)

    user = User.get(user_id)
    if user is None:
        flash(f'No user found with ID {user_id}.')
        return render_template('social_feedback.html', feedback=None, user=None)

    feedback = Feedback.get_recent_by_uid(user_id)
    return render_template('social_feedback.html', feedback=feedback, user=user)
