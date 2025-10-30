import sqlite3
from app import app, db
from models.users import Users
from werkzeug.security import generate_password_hash


def setup_admin():
    print("🚀 Starting admin setup...")

    with app.app_context():
        # Step 1: Add is_admin column to customer table if it doesn't exist
        print("📋 Step 1: Checking database structure...")
        try:
            conn = sqlite3.connect('instance/flask.db')  # Updated path
            cursor = conn.cursor()

            # Check if is_admin column exists
            cursor.execute("PRAGMA table_info(customer)")
            columns = [column[1] for column in cursor.fetchall()]

            if 'is_admin' not in columns:
                print("➕ Adding is_admin column to customer table...")
                cursor.execute('ALTER TABLE customer ADD COLUMN is_admin BOOLEAN DEFAULT FALSE')
                conn.commit()
                print("✅ is_admin column added successfully!")
            else:
                print("✅ is_admin column already exists")

            conn.close()
        except Exception as e:
            print(f"❌ Database error: {e}")
            return

        # Step 2: Create or update admin user
        print("\n👤 Step 2: Setting up admin user...")
        try:
            # Check if admin user already exists
            admin_user = Users.query.filter_by(email='admin@damm.com').first()

            if not admin_user:
                # Create new admin user
                admin_user = Users(
                    name="DAMM Admin",
                    email="admin@damm.com",
                    password=generate_password_hash("admin123"),
                    gender="male",
                    profile="Administrator",
                    is_admin=True
                )
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Admin user created successfully!")
                print("   📧 Email: admin@damm.com")
                print("   🔑 Password: admin123")
            else:
                # Update existing user to be admin
                admin_user.is_admin = True
                admin_user.name = "DAMM Admin"
                admin_user.password = generate_password_hash("admin123")
                db.session.commit()
                print("✅ Existing user updated to admin!")
                print("   📧 Email: admin@damm.com")
                print("   🔑 Password: admin123")

            # Verify the admin user
            print("\n🔍 Step 3: Verifying admin user...")
            verified_admin = Users.query.filter_by(email='admin@damm.com').first()
            if verified_admin and verified_admin.is_admin:
                print("✅ Admin user verified successfully!")
                print(f"   Name: {verified_admin.name}")
                print(f"   Email: {verified_admin.email}")
                print(f"   Is Admin: {verified_admin.is_admin}")

                # Test password verification
                from werkzeug.security import check_password_hash
                password_correct = check_password_hash(verified_admin.password, "admin123")
                print(f"   Password verification: {password_correct}")
            else:
                print("❌ Admin verification failed!")

        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            db.session.rollback()

    print("\n🎉 Admin setup completed!")


if __name__ == "__main__":
    setup_admin()