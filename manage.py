from app import app, db
from flask_migrate import Migrate
from flask.cli import with_appcontext
import click

# Initialize Migrate
migrate = Migrate(app, db)

# Register migrations CLI commands
@app.cli.command('db_init')
@with_appcontext
def db_init():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)  # Keep this here only for manual running, not for CLI migrations
