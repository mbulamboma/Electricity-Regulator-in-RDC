"""
Routes principales du module ARE
"""
from flask import render_template, redirect, url_for
from flask_login import login_required

from app.are import bp
from app.utils.decorators import admin_required


@bp.route('/')
@login_required
@admin_required
def index():
    """Page d'accueil du module ARE"""
    return redirect(url_for('are_dashboard.index'))


@bp.route('/aide')
@login_required
@admin_required
def aide():
    """Page d'aide du module ARE"""
    return render_template('are/aide.html')