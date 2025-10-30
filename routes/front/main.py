from app import app, db
from flask import render_template, jsonify, request, redirect, url_for, session, flash
import requests
from datetime import datetime
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash

# Import your Product model
from models.product import Product


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
                "stock": product.stock if product.stock is not None else 0,  # Ensure stock is never None
                "source": "database"
            }
            product_list.append(product_data)
        return product_list
    except Exception as e:
        print("Error fetching from database:", e)
        return []

def fetch_products_from_api():
    """Fetch products from external API (FakeStore API)"""
    try:
        response = requests.get('https://fakestoreapi.com/products', timeout=10)
        if response.status_code == 200:
            api_products = response.json()
            product_list = []
            for product in api_products:
                product_data = {
                    "id": product['id'] + 1000,  # Offset to avoid ID conflicts with database
                    "title": product['title'],
                    "price": float(product['price']),
                    "category": product['category'],
                    "image": product['image'],
                    "description": product.get('description', ''),
                    "stock": 10,  # Default stock for API products
                    "source": "api"
                }
                product_list.append(product_data)
            return product_list
        else:
            print(f"API returned status code: {response.status_code}")
            return []
    except Exception as e:
        print("Error fetching from API:", e)
        return []


@app.route("/")
def index():
    try:
        # Get products from both database and API
        db_products = fetch_products_from_database()
        api_products = fetch_products_from_api()

        # Combine both product lists
        product_list = db_products + api_products

        print(f"Loaded {len(product_list)} products total (Database: {len(db_products)}, API: {len(api_products)})")

        user = None
        if 'user_id' in session:
            user = get_user_by_id(session['user_id'])

        return render_template("index.html", products=product_list, user=user)

    except Exception as e:
        print("Error in index route:", e)
        # Final fallback to static products
        try:
            from product import products as static_products
            product_list = static_products
        except Exception as static_error:
            print("Static products also failed:", static_error)
            product_list = []

        user = None
        if 'user_id' in session:
            user = get_user_by_id(session['user_id'])

        return render_template("index.html", products=product_list, user=user)


@app.route("/contact")
def contact():
    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
    return render_template("contact.html", user=user)


@app.route("/about")
def about():
    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
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
        return
    except Exception as e:
        print("Telegram send error:", e)


from models.order import Order, OrderItem


@app.route("/placeOrder", methods=['POST'])
@login_required
def placeOrder():
    data = request.get_json()
    cart_items = data.get("cart", [])

    try:
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
            shipping_fee=float(data['shipping_fee']),
            total_amount=float(data['total']),
            status='pending'
        )
        db.session.add(order)
        db.session.flush()  # Get the order ID without committing

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

        # Commit both order and order items
        db.session.commit()

        print(f"✅ Order #{order.id} saved to database with {len(cart_items)} items")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error saving order to database: {e}")
        return jsonify({"error": "Failed to save order"}), 500

    # Rest of your email and telegram code...
    try:
        msg = Message(
            subject="Your Order Invoice",
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
            shipping_fee=data['shipping_fee'],
            total=data['total'],
            cart=cart_items,
            date=datetime.now().strftime("%d-%m-%Y %H:%M")
        )
        mail.send(msg)
        print("✅ Email sent successfully")
    except Exception as e:
        print(f"❌ Error sending email: {e}")

    # Send Message To Telegram
    try:
        message = f"""
        🛒 <b>New Order Received!</b>

        👤 <b>Customer:</b> {data['name']}
        📧 <b>Email:</b> {data['email']}
        📞 <b>Phone:</b> {data.get('phone')}
        🏠 <b>Address:</b> {data['address']} {data['city']} {data['country']}

        🛍️ <b>Items:</b>
        """
        for item in cart_items:
            message += f"• {item['title']}\n"
            message += f"  Quantity: {item['qty']}\n"
            message += f"  Price: ${item['price']:.2f}\n\n"

        message += f"\n💰 <b>Total:</b> ${data['total']:.2f}"
        message += f"\n💳 <b>Payment Method:</b> {data['payment']}"
        message += f"\n🕒 <b>Time:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}"

        send_order_to_telegram(message)
        print("✅ Telegram message sent")
    except Exception as e:
        print(f"❌ Error sending telegram: {e}")

    return "Order placed successfully! Invoice sent to your email."


@app.route("/product")
def product_detail():
    try:
        pro_id = request.args.get('pro_id', type=int)

        if pro_id:
            # Check if it's a database product (ID < 1000) or API product (ID >= 1000)
            if pro_id < 1000:
                # Database product
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
                else:
                    product_data = None
            else:
                # API product - fetch from API
                api_id = pro_id - 1000  # Convert back to original API ID
                try:
                    response = requests.get(f'https://fakestoreapi.com/products/{api_id}', timeout=10)
                    if response.status_code == 200:
                        api_product = response.json()
                        product_data = {
                            "id": pro_id,
                            "title": api_product['title'],
                            "price": float(api_product['price']),
                            "description": api_product['description'],
                            "category": api_product['category'],
                            "image": api_product['image'],
                            "stock": 10,
                            "source": "api"
                        }
                    else:
                        product_data = None
                except:
                    product_data = None
        else:
            product_data = None

    except Exception as e:
        print("Error fetching product detail:", e)
        product_data = None

    if not product_data:
        # Fallback to static product data
        try:
            from product import get_product_by_id
            pro_id = request.args.get('pro_id', type=int)
            product_data = get_product_by_id(pro_id)
        except:
            product_data = None

    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])

    return render_template("detail.html", product=product_data, user=user)


# API endpoint to get products (optional - for frontend API calls)
@app.route("/api/products")
def api_products():
    try:
        db_products = fetch_products_from_database()
        api_products = fetch_products_from_api()
        all_products = db_products + api_products
        return jsonify(all_products)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)