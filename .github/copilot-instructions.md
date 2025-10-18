---
# DRC Electricity Regulator - AI Coding Agent Guide

## Architecture Overview

This is a modular Flask application for regulatory oversight of electricity operators in the DRC. It uses blueprints, a factory pattern (`app/__init__.py`), and domain-driven design. Major modules: production (hydro/thermal/solar), transport, distribution, workflow, notifications, contacts, admin, ARE dashboard, and **collecte** (real data collection). Data flows through service layers, with business logic separated from routes. All persistent data is managed via SQLAlchemy models, with soft delete (`actif`) and timestamp conventions.


## Essential Patterns & Conventions

- **Models**: All SQLAlchemy models inherit from `BaseModel` (`app/models/base.py`) with `id`, timestamps, `actif` (soft delete), and CRUD helpers (`save()`, `delete()`, etc.). Use `to_dict()` for serialization. Enums are used for typed fields (see `app/models/`).
- **Authentication**: Dual system (`User` and `Contact` models). Role hierarchy: `super_admin`, `admin_operateur`, `operateur`, `contact`. Use decorators from `app/utils/decorators.py` and permission helpers in `app/utils/permissions.py`.
- **Service Layer**: Business logic is in service classes (e.g., `app/notifications/services.py`, `app/are/services_reel.py`). Always import services at the top of routes.
- **Templates**: Jinja2 macros/components in `templates/components/`. Use `{% from 'components/notifications.html' import dropdown_notifications %}`. Real-time UI via JS in `static/js/main.js`. French language throughout.
- **Forms**: WTForms in each domain. For optional `SelectField`, use `coerce=lambda x: int(x) if x else None` to avoid ValueError. Filter choices by user permissions in form `__init__`.
- **Distribution Models**: No direct `operateur_id`; access via parent (e.g., `PosteDistribution` → `ReseauDistribution.operateur_id`).
- **Soft Delete**: Prefer `actif` flag over hard deletion.
- **Custom Jinja2 Filters**: Registered in `app/__init__.py` (`|time_ago`, `|month_name`, `|nl2br`).
- **Testing**: Scripts in `tests/` simulate real user flows, including route, form, and DB integrity checks. See `tests/README.md` for advanced usage and troubleshooting.


## Critical Workflows

- **Database**: Use CLI commands in `run.py`:
    - `flask --app run init-db` (init)
    - `flask --app run create-admin` (admin user)
    - `flask --app run seed-data` (sample data)
    - `flask --app run init-are-data` (ARE dashboard)
    - `flask --app run reset-db` (full reset)
- **Testing**: Run `python tests/run_all_tests.py --full-report` for full coverage, or use `run_tests.ps1` for PowerShell-based tests. Manual and quick scripts in `tests/` allow targeted route and form validation. Reports are saved in `tests/rapport_complet_YYYYMMDD_HHMMSS.txt`.
- **Development**: Activate venv (`.\venv\Scripts\Activate.ps1`), run with debug (`flask --app run run --debug`), or open shell (`flask --app run shell`).
- **Migrations**: Use Flask-Migrate (`migrations/`). Never edit schema directly.
- **Environment**: Use `.env` for secrets and DB config. Example:
    ```env
    FLASK_ENV=development
    SECRET_KEY=...
    DATABASE_URL=sqlite:///instance/database.db
    ```


## Integration Points

- **Flask Extensions**: Centralized in `app/extensions.py` (SQLAlchemy, Flask-Login, Migrate, Bcrypt, CSRF).
- **Instance Folder**: Runtime data (`instance/database.db`, config overrides).
- **ARE Dashboard**: KPIs, analytics, and real data in `app/are/dashboard/` and `app/are/services_reel.py`.
- **Collecte Module**: Real data collection in `app/models/collecte_donnees.py` and `app/collecte/`.
- **Testing**: Uses `requests`, `beautifulsoup4`, `lxml` for HTTP and HTML validation. Install with `python tests/setup_test_env.py`.


## File Organization

- **Blueprints**: Each domain has `__init__.py`, `forms.py`, `routes.py`, models, and templates.
- **Templates**: Base (`base.html`), domain folders, and reusable components.
- **Static**: Custom CSS (`static/css/style.css`), JS (`static/js/main.js`), uploads, images.
- **Tests**: Automated scripts in `tests/` for routes, forms, and DB checks. See `tests/README.md` for details.


## Project-Specific Examples

- **Permission Check**:
    ```python
    from app.utils.permissions import can_access_operateur
    if not can_access_operateur(operateur_id):
        abort(403)
    ```
- **SelectField Coercion**:
    ```python
    field = SelectField(coerce=lambda x: int(x) if x else None)
    ```
- **Service Usage**:
    ```python
    from app.notifications.services import NotificationService
    NotificationService.creer_notification(...)
    ```
- **Test Execution**:
    ```powershell
    python tests/run_all_tests.py --full-report
    python tests/manual_test_routes.py --auth-user admin --auth-pass admin123
    ```

## Known Issues & Fixes

- Use `coerce=lambda x: int(x) if x else None` for SelectFields to avoid ValueError.
- Distribution models: always filter by parent relationship for permissions.

---

For unclear or missing sections, please provide feedback to improve these instructions for future AI agents.