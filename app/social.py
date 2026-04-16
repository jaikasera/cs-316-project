from flask import render_template, request, flash, redirect, url_for
from flask import Blueprint

from .models.feedback import Feedback
from .models.user import User

bp = Blueprint('social', __name__)


def _normalize_page_and_size(page_raw, per_page_raw, default_per_page=25):
    page = page_raw if isinstance(page_raw, int) and page_raw > 0 else 1
    allowed = [10, 25, 50, 100]
    per_page = per_page_raw if per_page_raw in allowed else default_per_page
    return page, per_page


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


@bp.route('/social/feedback/all')
def user_feedback_all():
    user_id = request.args.get('user_id', type=int)
    if user_id is None:
        return render_template('social_feedback_all.html', feedback=None, user=None)

    user = User.get(user_id)
    if user is None:
        flash(f'No user found with ID {user_id}.')
        return render_template('social_feedback_all.html', feedback=None, user=None)

    page_raw = request.args.get('page', default=1, type=int)
    per_page_raw = request.args.get('per_page', default=25, type=int)
    page, per_page = _normalize_page_and_size(page_raw, per_page_raw)

    total_count = Feedback.get_feedback_count_by_uid(user_id)
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    if page > total_pages:
        page = total_pages

    feedback = Feedback.get_feedback_by_uid(user_id, page=page, per_page=per_page)
    return render_template(
        'social_feedback_all.html',
        feedback=feedback,
        user=user,
        page=page,
        per_page=per_page,
        total_count=total_count,
        total_pages=total_pages,
    )
