from app import app, db

def upgrade():
    with app.app_context():
        # Use connection to execute SQL
        with db.engine.connect() as connection:
            connection.execute(db.text('ALTER TABLE customer ADD COLUMN is_admin BOOLEAN DEFAULT FALSE'))
            connection.commit()
        print("✅ is_admin column added to customer table")

if __name__ == "__main__":
    upgrade()