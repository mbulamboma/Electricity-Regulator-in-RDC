# Régulation Électricité RDC - AI Development Guide

## Architecture Overview

This is a modular Flask application for managing electricity operators in the Democratic Republic of Congo. The app follows Flask best practices with blueprint organization, factory pattern, and domain-driven design.

### Core Components
- **Factory Pattern**: `app/__init__.py` creates the Flask app using `create_app()` function
- **Extensions**: Centralized in `app/extensions.py` (SQLAlchemy, Flask-Login, Migrate, Bcrypt, CSRF)
- **Domain Modules**: Production (hydro/thermal/solar), transport, distribution, workflow, notifications, contacts, admin
- **Base Model**: `app/models/base.py` provides common functionality (timestamps, soft delete, CRUD methods)

## Key Patterns & Conventions

### Model Architecture
- All models inherit from `BaseModel` which provides: `id`, `date_creation`, `date_modification`, `actif`
- Use `save()`, `delete()`, `update()`, `soft_delete()` methods instead of raw SQLAlchemy calls
- Models have `to_dict()` for JSON serialization
- Enum classes for typed fields: `TypeRapport`, `StatutWorkflow`, `TypeNotification`

### Authentication & Authorization
- Dual authentication: `User` model + `Contact` model (company representatives)
- User loader checks for `contact_` prefix to distinguish contact vs user authentication
- Role hierarchy: `super_admin`, `admin_operateur`, `operateur`, `contact`
- Custom decorators in `app/utils/decorators.py`: `@role_required('super_admin')`, `@admin_required`
- **Permissions System**: `app/utils/permissions.py` provides operator-scoped access control
- French language interface throughout ("Nom d'utilisateur", "Se connecter")

### Service Layer Pattern
- Service classes in modules like `app/notifications/services.py` for business logic
- `NotificationService.creer_notification()` - centralized notification creation
- Services handle complex operations and cross-domain logic
- Import services at the top of routes that need them

### Template Component System
- Reusable Jinja2 macros in `templates/components/` (notifications, graphs, tables)
- Usage: `{% from 'components/notifications.html' import dropdown_notifications %}`
- Real-time UI updates via JavaScript for notifications and dynamic content
- Bootstrap 5 with custom CSS in `static/css/style.css`

### Domain Modules (Blueprints)
Each domain has consistent structure:
- `__init__.py` - Blueprint registration  
- `forms.py` - WTForms with French validators
- `routes.py` - View functions
- `models/` - Domain-specific SQLAlchemy models
- `templates/` - Domain templates

Current domains: `auth`, `operateurs`, `production_hydro`, `production_thermique`, `production_solaire`, `transport`, `distribution`, `workflow`, `notifications`, `contacts`, `admin`, `are`

### ARE Dashboard Module (NEW)
- **Strategic Dashboard**: `app/are/dashboard/` provides executive-level KPIs and analytics
- **Key Models**: `KPIStrategic`, `IndicateurSectoriel`, `AlerteRegulateur`, `DonneesProvince`, `RapportAnnuel`
- **Auto-calculation**: Services in `app/are/services.py` compute national indicators from operational data
- **Interactive Features**: Real-time charts, province map, automated alerts, multi-format exports
- **Access Control**: Admin-only access with `@admin_required` decorator

### Form Patterns & Common Issues
- **SelectField Coercion**: Use `coerce=lambda x: int(x) if x else None` for optional SelectFields to avoid ValueError
- **Permissions in Forms**: Add `__init__` methods to filter choices based on user permissions
- **Hierarchical Relations**: Distribution models don't have direct `operateur_id` - access via parent relationships
- Example: `PosteDistribution` → `ReseauDistribution.operateur_id` for permission filtering

## Critical Workflows

### Database Management
```powershell
# Initialize database and migrations
flask --app run init-db

# Create admin user (interactive prompts)  
flask --app run create-admin

# Add sample data
flask --app run seed-data

# Complete reset (with confirmation)
flask --app run reset-db
```

### Development Setup
```powershell
# Windows PowerShell environment activation
.\venv\Scripts\Activate.ps1

# Run with debug mode
flask --app run run --debug

# Interactive shell (auto-imports db, User, Operateur)
flask --app run shell

# Initialize ARE dashboard data (after basic setup)
python init_are_dashboard.py
```

### Permission System Usage
```python
# In routes: check operator access
from app.utils.permissions import can_access_operateur, get_accessible_operateurs

# Filter queries by user permissions
accessible_operateurs = get_accessible_operateurs()
query = filter_query_by_operateur(base_query, 'operateur_id')

# Check specific operator access
if not can_access_operateur(operateur_id):
    abort(403)
```

## Electricity Domain Context

### Production Types & Models
- **Hydro**: `CentraleHydro` with technical specs (`puissance_installee`, `hauteur_chute`, `debit_equipement`)
- **Thermal**: Coal, gas, diesel plants with fuel consumption tracking
- **Solar**: Photovoltaic installations with irradiance and efficiency data
- Geographic data: coordinates, provinces, coverage areas

### Workflow System
- Report validation pipeline: `BROUILLON → SOUMIS → EN_VALIDATION → VALIDE/REJETE`
- `TypeRapport` enum: production, transport, distribution, maintenance, incident
- Automatic deadline tracking and notification triggers
- Historical audit trail in `HistoriqueWorkflow`

### Notification System  
- Real-time notifications with priority levels (1=normal, 2=urgent, 3=critical)
- Template-based notifications with variable substitution
- User preferences for notification types
- Internal messaging between users and contacts

## Configuration System
- Environment-based configs in `app/config.py`: `DevelopmentConfig`, `ProductionConfig`, `TestingConfig`  
- Database: SQLite in `instance/` directory (development and production)
- Session settings: 24-hour lifetime, secure cookies in production
- Upload limits: 16MB max, files in `static/uploads/`
- Pagination: 20 items per page default

## Business Rules & Constraints
- License status tracking: `active`, `suspendue`, `expirée`
- Soft deletion preferred over hard deletion (`actif` flag)
- French language throughout (forms, flash messages, UI text)
- Default admin credentials: admin/admin123 (change in production)
- All dates use datetime objects, display with custom Jinja2 filters (`|time_ago`, `|month_name`)

## File Organization Patterns

### Template Structure
- Base template: `templates/base.html` with Bootstrap 5
- Domain templates in respective folders: `templates/production_hydro/`, etc.
- Reusable components: `templates/components/` for macros
- Three base template variants: `base.html`, `base_clean.html`, `base_backup.html`

### Static Assets
- CSS: `static/css/style.css` with custom Bootstrap overrides
- JavaScript: `static/js/main.js` for notifications and dynamic features  
- Uploads: `static/uploads/` with 16MB limit
- Images: `static/images/` for logos and assets

### Custom Jinja2 Filters
- `|time_ago`: Convert datetime to French relative time ("Il y a 2 heures")  
- `|month_name`: Convert month number to French name ("Janvier", "Février")
- `|nl2br`: Convert newlines to HTML line breaks
- Available in all templates via `app/__init__.py` registration

## Integration Points

- **Flask-Migrate**: Database versioning in `migrations/` directory
- **Flask-WTF**: CSRF protection on all forms with `{{ csrf_token() }}`
- **Instance Folder**: Runtime data storage (`instance/database.db`, config overrides)
- **CLI Commands**: Custom Flask commands in `run.py` for database operations
- **SQLAlchemy**: Relationship patterns with backref, foreign keys across domains

## Development Notes

- Use `flask --app run shell` for interactive development (auto-imports `db`, `User`, `Operateur`)
- Database changes require migrations, not direct schema edits  
- French UI/UX throughout - maintain language consistency
- Bootstrap 5 for responsive design
- Role checks: use `@login_required` + custom decorators (`@role_required`, `@admin_required`)
- Service layer for complex business logic - import services in routes as needed
- Main entry point: `run.py` with CLI commands and shell context
- Configuration via environment variables (`.env` file support)

## Recent Fixes & Known Issues

### SelectField Coercion Pattern
- **Problem**: `ValueError: invalid literal for int() with base 10: ''` in forms with empty SelectField choices
- **Solution**: Use `coerce=lambda x: int(x) if x else None` instead of `coerce=int`
- **Files affected**: All forms with optional SelectField (production_hydro, distribution, etc.)

### Permission Architecture for Hierarchical Models
- **Distribution models**: No direct `operateur_id` - access via parent relationships
- **Pattern**: `PosteDistribution` → `ReseauDistribution.operateur_id` for filtering
- **Utility functions**: Use `app/utils/permissions.py` for consistent permission checking
- **Form initialization**: Add `__init__` methods to filter choices based on user permissions