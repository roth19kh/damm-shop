from flask import Flask, render_template,jsonify,abort,request
import requests
from datetime import datetime
from flask_mail import Mail,Message

app = Flask(__name__)

#Email Config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'haktharoth18@gmail.com'
app.config['MAIL_PASSWORD'] = 'bjbu yxgl hixz wriu'

mail = Mail(app)

def send_order_to_telegram(message):

    token = "7938087424:AAESzgCJ5UjfYpQlRu15Xayy7OTuVUaFYmE"
    chat_id = "1239458595"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"  # optional for formatting
    }
    try:
        res = requests.post(url, data=payload)
        res.raise_for_status()
        return
    except Exception as e:
        print("Telegram send error:", e)
    
@app.route("/")
def index():
    try:
    #Request From API
        # res = requests.get("https://fakestoreapi.com/products")
        # if(res.status_code==200):
        #     product = res.json()
        #     return render_template("index.html",products=product)
        # else:
        #     print("Error: ",res.status_code)
    
    #Static
        from product import products
        product_list = products
        return render_template("index.html", products = product_list )
            
    except Exception as e:
        print(e)
    return render_template("index.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/cart")
def cart():
    return render_template("cart.html")

@app.route("/checkout")
def checkOut():
    return render_template("checkout.html")

@app.route("/placeOrder", methods=['POST'])
def placeOrder():
    data = request.get_json()
    cart_items = data.get("cart", [])
    name = data['name']
    email = data['email']
    address = data['address']
    city = data['city']
    country = data['country']
    phone = data['phone']
    payment = data['payment']
    shipping_fee = data['shipping_fee']
    total = data['total']
    
    msg = Message(
        subject="Your Order Invoice",
        sender = app.config['MAIL_USERNAME'],
        recipients=[email]
    )
    msg.html = render_template(
        "invoice_email.html",
        name = name,
        phone = phone,
        address = address,
        city = city,
        country = country,
        payment = payment,
        shipping_fee = shipping_fee,
        total = total,
        cart = cart_items,
        date=datetime.now().strftime("%d-%m-%Y %H:%M")
    )

    mail.send(msg)
    
    #Send Message To Telegram
    message = f"""
    🛒 <b>New Order Received!</b>

    👤 <b>Customer:</b> {name}
    📧 <b>Email:</b> {email}
    📞 <b>Phone:</b> {data.get('phone')}
    🏠 <b>Address:</b> {data.get('address')} {data.get('city')} {data.get('country')}

    🛍️ <b>Items:</b>
    """
    for item in cart_items:
        message += f"• *{item['title']}*\n"
        message += f"  Quantity: {item['qty']}\n"
        message += f"  Price: ${item['price']:.2f}\n\n"

    message += f"\n💰 <b>Total:</b> ${total:.2f}"
    message += f"\n💳 <b>Payment Method:</b> {data.get('payment')}"
    message += f"\n🕒 <b>Time:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}"
    
    send_order_to_telegram(message)
        
    return "Invoice Sent!\n Thank you for your order."

@app.route("/product")
def product_detail():
    #Request From API
    # product = []
    # res = requests.get(f"https://fakestoreapi.com/products/{product_id}", timeout=5)
    # if res.status_code==200:
    #     product = res.json()
    
    #Static
    from product import products, get_product_by_id
    pro_id = request.args.get('pro_id',type=int)
    product = get_product_by_id(pro_id)
    return render_template("detail.html",product=product)


if __name__ == "__main__":
    app.run(debug=True)