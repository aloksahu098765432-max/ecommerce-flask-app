from flask import Flask, render_template, redirect, url_for, request, session
import sqlite3

app = Flask(__name__)

app.secret_key = "mysecretkey"

cart = []


# =========================
# DATABASE SETUP
# =========================

def init_db():

    conn = sqlite3.connect('store.db')

    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            role TEXT
        )
    ''')

    # PRODUCTS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price INTEGER
        )
    ''')

    # ORDERS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            total INTEGER
        )
    ''')

    # DEFAULT PRODUCTS
    cursor.execute("SELECT * FROM products")

    existing_products = cursor.fetchall()

    if not existing_products:

        cursor.execute(
            "INSERT INTO products (name, price) VALUES (?, ?)",
            ("Laptop", 50000)
        )

        cursor.execute(
            "INSERT INTO products (name, price) VALUES (?, ?)",
            ("Phone", 20000)
        )

    # DEFAULT ADMIN
    cursor.execute(
        "SELECT * FROM users WHERE username=?",
        ("admin",)
    )

    admin_exists = cursor.fetchone()

    if not admin_exists:

        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", "admin123", "admin")
        )

    conn.commit()
    conn.close()


init_db()


# =========================
# HOME PAGE
# =========================

@app.route('/')
def home():

    conn = sqlite3.connect('store.db')

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")

    products = cursor.fetchall()

    conn.close()

    return render_template('index.html', products=products)


# =========================
# REGISTER
# =========================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('store.db')

        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password, "user")
        )

        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')


# =========================
# LOGIN
# =========================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('store.db')

        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:

            session['user'] = username
            session['role'] = user[3]

            return redirect(url_for('home'))

        return "Invalid Username or Password"

    return render_template('login.html')


# =========================
# LOGOUT
# =========================

@app.route('/logout')
def logout():

    session.pop('user', None)
    session.pop('role', None)

    return redirect(url_for('home'))


# =========================
# ADD PRODUCT (ADMIN ONLY)
# =========================

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():

    if 'role' not in session or session['role'] != 'admin':
        return "Access Denied"

    if request.method == 'POST':

        name = request.form['name']
        price = request.form['price']

        conn = sqlite3.connect('store.db')

        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO products (name, price) VALUES (?, ?)",
            (name, price)
        )

        conn.commit()
        conn.close()

        return redirect(url_for('home'))

    return render_template('add_product.html')


# =========================
# ADD TO CART
# =========================

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):

    conn = sqlite3.connect('store.db')

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM products WHERE id=?",
        (product_id,)
    )

    product = cursor.fetchone()

    conn.close()

    if product:

        cart.append({
            "id": product[0],
            "name": product[1],
            "price": product[2]
        })

    return redirect(url_for('home'))


# =========================
# VIEW CART
# =========================

@app.route('/cart')
def view_cart():

    total = 0

    for item in cart:
        total += item["price"]

    return render_template('cart.html', cart=cart, total=total)


# =========================
# REMOVE FROM CART
# =========================

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):

    for item in cart:

        if item["id"] == product_id:

            cart.remove(item)
            break

    return redirect(url_for('view_cart'))


# =========================
# CHECKOUT
# =========================

@app.route('/checkout')
def checkout():

    if 'user' not in session:
        return redirect(url_for('login'))

    total = 0

    for item in cart:
        total += item["price"]

    conn = sqlite3.connect('store.db')

    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO orders (username, total) VALUES (?, ?)",
        (session['user'], total)
    )

    conn.commit()
    conn.close()

    cart.clear()

    return render_template('checkout.html', total=total)


# =========================
# RUN APP
# =========================

if __name__ == '__main__':
    app.run(debug=True)