#!/usr/bin/env bash
# Exit on error
set -o errexit

# Modify this line as needed for your package manager (pip, poetry, etc.)
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply any outstanding database migrations
python manage.py migrate

# Add super_user
if [[ "$CREATE_SUPERUSER" == "true" ]]; then
    python manage.py createsuperuser --no-input
fi

gunicorn m_journal.wsgi
