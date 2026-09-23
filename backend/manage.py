from backend.app import create_app, db
from backend.app.seed import seed_demo_data

app = create_app()


@app.cli.command("seed")
def seed_command():
    """Load fictional demo data into an empty database."""
    with app.app_context():
        seed_demo_data()
        db.session.commit()
        print("Demo data loaded.")
