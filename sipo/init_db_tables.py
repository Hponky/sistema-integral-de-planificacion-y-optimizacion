from app import create_app, db
import os

# Ensure we use the correct config/env
os.environ['FLASK_ENV'] = 'development'

app = create_app('development')
with app.app_context():
    print("Creating all missing tables...")
    db.create_all()
    print("Done.")
