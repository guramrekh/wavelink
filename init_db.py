from myapp import create_app
from myapp.db import db
from myapp import models

app = create_app()
with app.app_context():
    db.create_all()
    print("Database initialized")
