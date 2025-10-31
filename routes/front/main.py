from app import app, db
from flask import render_template, jsonify, request, redirect, url_for, session, flash
import requests
from datetime import datetime
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from models.order import Order, OrderItem
from models.product import Product
from product import products as API_PRODUCTS
import os
import threading
from threading import Thread
from werkzeug.utils import secure_filename


# Define Users model that maps to customer table
class Users(db.Model):
    __tablename__ = 'customer'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    email = db.Column(db.String(128))
    password = db.Column(db.String(128))
    gender = db.Column(db.String(128), default='male')
    profile = db.Column(db.String(128), nullable=True)


# Helper function to get current user
def get_user():
    if 'user_id' in session:
        return Users.query.get(session['user_id'])
    return None


# Login required decorator
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def get_user_by_id(user_id):
    return Users.query.get(user_id)


def fetch_products_from_database():
    """Fetch products from local database"""
    try:
        db_products = Product.query.all()
        product_list = []
        for product in db_products:
            product_data = {
                "id": product.id,
                "title": product.name,
                "price": float(product.price),
                "category": str(product.category_id),
                "image": f"/static/image/product/{product.image}" if product.image else "/static/image/No_Image_Available.jpg",
                "stock": product.stock if product.stock is not None else 0,
                "source": "database"
            }
            product_list.append(product_data)
        return product_list
    except Exception as e:
        print("Error fetching from database:", e)
        return []


def fetch_products_from_api():
    """Fetch products from LOCAL API data (no HTTP calls)"""
    try:
        product_list = []
        for product in API_PRODUCTS:
            product_data = {
                "id": product['id'] + 1000,
                "title": product['title'],
                "price": float(product['price']),
                "category": product['category'],
                "image": product['image'],
                "description": product.get('description', 'No description available'),
                "stock": 50,
                "source": "api"
            }
            product_list.append(product_data)
        return product_list
    except Exception as e:
        print("Error fetching from local API data:", e)
        return []


# Background email function
def send_email_async(app, msg):
    """Send email in background thread"""
    with app.app_context():
        try:
            mail.send(msg)
            print("✅ Email sent successfully in background")
        except Exception as e:
            print(f"⚠️ Background email failed: {e}")


# Background Telegram function
def send_telegram_async(message):
    """Send Telegram in background thread"""
    try:
        send_order_to_telegram(message)
        print("✅ Telegram sent successfully in background")
    except Exception as e:
        print(f"⚠️ Background Telegram failed: {e}")


@app.route("/")
def index():
    try:
        # Get products from both database and LOCAL API
        db_products = fetch_products_from_database()
        api_products_data = fetch_products_from_api()

        # Combine both product lists
        product_list = db_products + api_products_data

        print(
            f"Loaded {len(product_list)} products total (Database: {len(db_products)}, API: {len(api_products_data)})")

        user = get_user()
        return render_template("index.html", products=product_list, user=user)

    except Exception as e:
        print("Error in index route:", e)
        # Fallback to static products
        try:
            product_list = API_PRODUCTS
        except Exception as static_error:
            print("Static products also failed:", static_error)
            product_list = []

        user = get_user()
        return render_template("index.html", products=product_list, user=user)


@app.route("/contact")
def contact():
    user = get_user()
    return render_template("contact.html", user=user)


@app.route("/about")
def about():
    user = get_user()
    return render_template("about.html", user=user)


@app.route("/cart")
@login_required
def cart():
    user = get_user_by_id(session['user_id'])
    return render_template("cart.html", user=user)


@app.route("/checkout")
@login_required
def checkOut():
    user = get_user_by_id(session['user_id'])
    return render_template("checkout.html", user=user)


@app.route("/login", methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to home
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = Users.query.filter_by(email=email).first()

        # Check if user exists and password matches
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_email'] = user.email
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')


@app.route("/register", methods=['GET', 'POST'])
def register():
    # If user is already logged in, redirect to home
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        gender = request.form.get('gender', 'male')

        # Basic validation
        if not name or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'danger')
            return render_template('register.html')

        # Check if user already exists
        existing_user = Users.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'danger')
            return render_template('register.html')

        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = Users(
            name=name,
            email=email,
            password=hashed_password,
            gender=gender,
            profile=name
        )

        db.session.add(new_user)
        db.session.commit()

        # Auto login after registration
        session['user_id'] = new_user.id
        session['user_email'] = new_user.email
        flash('Registration successful! Welcome to DAMM SHOP!', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')


@app.route("/logout")
def logout():
    session.pop('user_id', None)
    session.pop('user_email', None)
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))


@app.route("/profile")
@login_required
def profile():
    user = get_user_by_id(session['user_id'])
    return render_template('profile.html', user=user)


# Email Config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'haktharoth18@gmail.com'
app.config['MAIL_PASSWORD'] = 'bjbu yxgl hixz wriu'
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

mail = Mail(app)


def send_order_to_telegram(message):
    token = "7938087424:AAESzgCJ5UjfYpQlRu15Xayy7OTuVUaFYmE"
    chat_id = "1239458595"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(url, data=payload)
        res.raise_for_status()
        return True
    except Exception as e:
        print("Telegram send error:", e)
        return False


@app.route("/placeOrder", methods=['POST'])
@login_required
def placeOrder():
    try:
        print("=== PLACE ORDER STARTED ===")
        data = request.get_json()
        print(f"✅ Received data")

        if not data:
            print("❌ No data received")
            return jsonify({"error": "No data received"}), 400

        cart_items = data.get("cart", [])
        print(f"✅ Cart items: {cart_items}")

        if not cart_items:
            print("❌ Cart is empty")
            return jsonify({"error": "Cart is empty"}), 400

        # Validate required fields
        required_fields = ['name', 'email', 'address', 'city', 'country', 'payment', 'total']
        for field in required_fields:
            if not data.get(field):
                print(f"❌ Missing required field: {field}")
                return jsonify({"error": f"Missing required field: {field}"}), 400

        print("✅ All validations passed")

        try:
            print("✅ Creating order record...")
            # Create order record
            order = Order(
                customer_id=session['user_id'],
                customer_name=data['name'],
                customer_email=data['email'],
                customer_phone=data.get('phone', ''),
                shipping_address=data['address'],
                city=data['city'],
                country=data['country'],
                payment_method=data['payment'],
                shipping_fee=float(data.get('shipping_fee', 0)),
                total_amount=float(data['total']),
                status='pending',
                order_date=datetime.now(),
                updated_at=datetime.now()
            )
            print(f"✅ Order object created")

            db.session.add(order)
            db.session.flush()
            print(f"✅ Order flushed with ID: {order.id}")

            # Create order items
            for item in cart_items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item['id'],
                    product_name=item['title'],
                    product_price=float(item['price']),
                    quantity=item['qty'],
                    subtotal=float(item['price']) * item['qty']
                )
                db.session.add(order_item)
                print(f"✅ Added order item: {item['title']}")

            # Commit both order and order items
            db.session.commit()
            print(f"✅ Order #{order.id} saved to database with {len(cart_items)} items")

        except Exception as db_error:
            print(f"❌ DATABASE ERROR: {db_error}")
            db.session.rollback()
            raise db_error

        # Send email and Telegram in background threads
        email_started = False
        telegram_started = False

        # Prepare and send email in background thread
        try:
            print("✅ Preparing email in background...")
            msg = Message(
                subject=f"Your Order Invoice #{order.id} - DAMM SHOP",
                sender=app.config['MAIL_USERNAME'],
                recipients=[data['email']]
            )
            msg.html = render_template(
                "invoice_email.html",
                name=data['name'],
                phone=data.get('phone'),
                address=data['address'],
                city=data['city'],
                country=data['country'],
                payment=data['payment'],
                shipping_fee=data.get('shipping_fee', 0),
                total=data['total'],
                cart=cart_items,
                date=datetime.now().strftime("%d-%m-%Y %H:%M"),
                order_id=order.id
            )
            # Send email in background thread
            email_thread = Thread(target=send_email_async, args=(app, msg))
            email_thread.daemon = True  # Daemon thread won't block shutdown
            email_thread.start()
            email_started = True
            print("✅ Email thread started")
        except Exception as e:
            print(f"⚠️ Email preparation failed: {e}")

        # Prepare and send Telegram in background thread
        try:
            print("✅ Preparing Telegram in background...")
            telegram_message = f"""
🛒 <b>New Order Received!</b>

👤 <b>Customer:</b> {data['name']}
📧 <b>Email:</b> {data['email']}
📞 <b>Phone:</b> {data.get('phone', 'N/A')}
🏠 <b>Address:</b> {data['address']}, {data['city']}, {data['country']}

🛍️ <b>Items:</b>
"""
            for item in cart_items:
                telegram_message += f"• {item['title']} x{item['qty']} - ${item['price']:.2f}\n"

            telegram_message += f"\n💰 <b>Total:</b> ${data['total']:.2f}"
            telegram_message += f"\n💳 <b>Payment Method:</b> {data['payment']}"
            telegram_message += f"\n🆔 <b>Order ID:</b> #{order.id}"
            telegram_message += f"\n🕒 <b>Time:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}"

            # Send Telegram in background thread
            telegram_thread = Thread(target=send_telegram_async, args=(telegram_message,))
            telegram_thread.daemon = True  # Daemon thread won't block shutdown
            telegram_thread.start()
            telegram_started = True
            print("✅ Telegram thread started")
        except Exception as e:
            print(f"⚠️ Telegram preparation failed: {e}")

        print("✅ Order processing completed successfully")
        return jsonify({
            "success": True,
            "message": "Order placed successfully! Invoice and notifications are being sent.",
            "order_id": order.id,
            "email_started": email_started,
            "telegram_started": telegram_started
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ CRITICAL ERROR in placeOrder: {str(e)}")
        return jsonify({"error": "Order processing failed"}), 500


@app.route("/product")
def product_detail():
    try:
        pro_id = request.args.get('pro_id', type=int)
        print(f"🔍 Looking for product ID: {pro_id}")

        if not pro_id:
            print("❌ No product ID provided")
            return render_template("detail.html", product=None, user=get_user())

        product_data = None

        # Database products (ID < 1000)
        if pro_id < 1000:
            print(f"🔍 Searching database for ID: {pro_id}")
            product = Product.query.get(pro_id)
            if product:
                product_data = {
                    "id": product.id,
                    "title": product.name,
                    "price": float(product.price),
                    "description": f"Stock: {product.stock}",
                    "category": str(product.category_id),
                    "image": f"/static/image/product/{product.image}" if product.image else "/static/image/No_Image_Available.jpg",
                    "stock": product.stock,
                    "source": "database"
                }
                print(f"✅ Found database product: {product_data['title']}")
            else:
                print(f"❌ Database product not found for ID: {pro_id}")
        else:
            # API products (ID >= 1000)
            api_id = pro_id - 1000
            print(f"🔍 Searching API products for ID: {api_id}")
            for product in API_PRODUCTS:
                if product['id'] == api_id:
                    product_data = {
                        "id": pro_id,
                        "title": product['title'],
                        "price": float(product['price']),
                        "description": product.get('description', 'No description available'),
                        "category": product['category'],
                        "image": product['image'],
                        "stock": 50,
                        "source": "api"
                    }
                    print(f"✅ Found API product: {product_data['title']}")
                    break
            if not product_data:
                print(f"❌ API product not found for ID: {api_id}")

        user = get_user()
        return render_template("detail.html", product=product_data, user=user)

    except Exception as e:
        print(f"❌ Error in product_detail: {e}")
        return render_template("detail.html", product=None, user=get_user())


# API endpoint to get products (optional - for frontend API calls)
@app.route("/api/products")
def api_products():
    try:
        db_products = fetch_products_from_database()
        api_products_data = fetch_products_from_api()

        all_products = db_products + api_products_data
        return jsonify(all_products)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== ADMIN ROUTES ====================

@app.route("/admin/product/list")
def admin_product_list():
    try:
        # Get products from both database and API
        db_products = fetch_products_from_database()
        api_products_data = fetch_products_from_api()
        all_products = db_products + api_products_data

        # Fix category format for admin display
        for product in all_products:
            # Add cost field if missing
            if 'cost' not in product:
                product['cost'] = round(float(product['price']) * 0.6, 2)

            # Fix category format for admin template
            category = product.get('category', '')

            # Convert category strings to IDs for the admin template
            if category == "men's clothing":
                product['category'] = 1
            elif category == "women's clothing":
                product['category'] = 2
            elif category == "jewelery":
                product['category'] = 3
            elif category == "electronics":
                product['category'] = 4
            else:
                # For database products or unknown categories, use default
                if isinstance(category, str) and category.isdigit():
                    product['category'] = int(category)
                else:
                    product['category'] = 1  # Default to men's clothing

        print(f"📦 Admin: Sending {len(all_products)} products")
        return jsonify(all_products)
    except Exception as e:
        print(f"❌ Error in admin_product_list: {e}")
        return jsonify([])


@app.route("/admin/category/list")
def admin_category_list():
    try:
        # Define categories
        categories = [
            {"id": 1, "name": "men's clothing"},
            {"id": 2, "name": "women's clothing"},
            {"id": 3, "name": "jewelery"},
            {"id": 4, "name": "electronics"},
            {"id": 5, "name": "sports"}
        ]
        return jsonify(categories)
    except Exception as e:
        print(f"❌ Error in admin_category_list: {e}")
        return jsonify([])


@app.route("/admin/product/create", methods=['POST'])
def admin_product_create():
    try:
        # Get form data
        title = request.form.get('title')
        price = request.form.get('price')
        stock = request.form.get('stock')
        category = request.form.get('category')

        # Validate required fields
        if not title or not price:
            return jsonify({"success": False, "error": "Title and price are required"}), 400

        # Handle image upload
        image_file = request.files.get('image')
        image_filename = None

        if image_file and image_file.filename:
            # Create uploads directory if it doesn't exist
            upload_dir = os.path.join(app.root_path, 'static', 'image', 'product')
            os.makedirs(upload_dir, exist_ok=True)

            # Generate secure filename
            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join(upload_dir, image_filename)
            image_file.save(image_path)
            print(f"✅ Image saved: {image_filename}")

        # Create new product in database
        new_product = Product(
            name=title,
            price=float(price),
            stock=int(stock) if stock else 0,
            category_id=int(category) if category else 1,
            image=image_filename
        )

        db.session.add(new_product)
        db.session.commit()

        print(f"✅ Product created: {title}")
        return jsonify({"success": True, "message": "Product created successfully"})

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating product: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/admin/product/update", methods=['POST'])
def admin_product_update():
    try:
        product_id = request.form.get('id')
        title = request.form.get('title')
        price = request.form.get('price')
        stock = request.form.get('stock')
        category = request.form.get('category')

        if not product_id:
            return jsonify({"success": False, "error": "Product ID is required"}), 400

        # Find the product
        product = Product.query.get(int(product_id))
        if not product:
            return jsonify({"success": False, "error": "Product not found"}), 404

        # Update product fields
        product.name = title
        product.price = float(price)
        product.stock = int(stock) if stock else product.stock
        product.category_id = int(category) if category else product.category_id

        # Handle image update
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            upload_dir = os.path.join(app.root_path, 'static', 'image', 'product')
            os.makedirs(upload_dir, exist_ok=True)

            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join(upload_dir, image_filename)
            image_file.save(image_path)
            product.image = image_filename
            print(f"✅ Image updated: {image_filename}")

        db.session.commit()

        print(f"✅ Product updated: {title}")
        return jsonify({"success": True, "message": "Product updated successfully"})

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error updating product: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/admin/product/delete", methods=['POST'])
def admin_product_delete():
    try:
        data = request.get_json()
        product_id = data.get('product_id')

        if not product_id:
            return jsonify({"success": False, "error": "Product ID is required"}), 400

        # Check if it's a database product (ID < 1000) or API product
        if int(product_id) < 1000:
            product = Product.query.get(int(product_id))
            if product:
                db.session.delete(product)
                db.session.commit()
                print(f"✅ Product deleted: ID {product_id}")
                return jsonify({"success": True, "message": "Product deleted successfully"})
            else:
                return jsonify({"success": False, "error": "Product not found"}), 404
        else:
            # API products cannot be deleted (they're read-only)
            return jsonify({"success": False, "error": "Cannot delete API products"}), 400

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error deleting product: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== DEBUG ROUTES ====================

@app.route("/debug-test")
def debug_test():
    return jsonify({"status": "debug route works"})


@app.route("/debug-products")
def debug_products():
    products = fetch_products_from_database() + fetch_products_from_api()
    return jsonify([{"id": p["id"], "title": p["title"]} for p in products])


@app.route("/debug-order-simple", methods=['POST'])
def debug_order_simple():
    try:
        data = request.get_json()
        return jsonify({
            "status": "success",
            "received": list(data.keys()) if data else "no data"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/debug-db")
def debug_db():
    try:
        order_count = Order.query.count()
        product_count = Product.query.count()
        return jsonify({
            "database": "connected",
            "orders_count": order_count,
            "products_count": product_count
        })
    except Exception as e:
        return jsonify({"database_error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)