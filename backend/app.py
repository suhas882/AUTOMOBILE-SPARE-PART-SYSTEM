import os
from flask import Flask, send_from_directory, abort, request, redirect, url_for, flash, jsonify, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong, random key

# MySQL Configuration
app.config['MYSQL_HOST'] = '@your_sql_host'
app.config['MYSQL_USER'] = '@your_sql_user'
app.config['MYSQL_PASSWORD'] = '@your_mysql_pass'
app.config['MYSQL_DB'] = '@your_sql_db'

# Initialize MySQL
mysql = MySQL(app)

# Define path to your frontend directory
STATIC_DIR = r'C:\Users\majet\.vscode\project\sample\frontend'

# === ROUTES FOR HTML PAGES ===

@app.route('/')
@app.route('/home')
@app.route('/index')
@app.route('/index.html')
def serve_index():
    return send_from_directory(STATIC_DIR, 'index.html')

@app.route('/team')
@app.route('/team.html')
def serve_team():
    return send_from_directory(STATIC_DIR, 'team.html')

@app.route('/contact')
@app.route('/contact.html')
def serve_contact():
    return send_from_directory(STATIC_DIR, 'contact.html')

@app.route('/distributors')
@app.route('/distributors.html')
def serve_distributors():
    return send_from_directory(STATIC_DIR, 'distributors.html')

@app.route('/login')

def serve_login():
    return send_from_directory(STATIC_DIR, 'login.html')

# === STATIC FILES (CSS, JS, Images) ===

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(STATIC_DIR, 'static'), filename)

# === DATABASE ROUTES ===

@app.route('/fetch_parts')
def fetch_parts():
    cur = mysql.connection.cursor()
    cur.execute("SELECT part_id, name, brand, price, stock FROM spare_parts")
    data = cur.fetchall()
    cur.close()
    return jsonify(data)

@app.route('/fetch_orders')
def fetch_orders():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT o.order_id, c.name AS customer, s.name AS part, o.quantity, o.order_date 
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN spare_parts s ON o.part_id = s.part_id
    """)
    orders = cur.fetchall()
    cur.close()
    return jsonify(orders)

@app.route('/add_order', methods=['POST'])
def add_order():
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        part_id = request.form.get('part_id')
        quantity = request.form.get('quantity')
        order_date = request.form.get('order_date')

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO orders (customer_id, part_id, quantity, order_date)
            VALUES (%s, %s, %s, %s)
        """, (customer_id, part_id, quantity, order_date))
        mysql.connection.commit()
        cur.close()
        flash('Order placed successfully!', 'success')
        return redirect(url_for('serve_index'))

@app.route('/add_user', methods=['POST'])
def add_user():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    is_admin = request.form.get('isAdmin', '0')  # Optional checkbox

    # Hash the password
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            INSERT INTO users (username, email, password, isAdmin)
            VALUES (%s, %s, %s, %s)
        """, (username, email, hashed_password, is_admin))
        mysql.connection.commit()
        flash('User registered successfully! Please log in.', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error: {str(e)}', 'danger')
    finally:
        cur.close()
    
    return redirect(url_for('serve_login'))

# === LOGIN ROUTE ===

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()

    if user and check_password_hash(user[3], password):  # Assuming password is 4th column (index 3)
        session['user_id'] = user[0]  # Store user ID in session
        session['username'] = user[1]  # Store username
        session['is_admin'] = user[4]  # Store admin status
        flash('Login successful!', 'success')
        return redirect(url_for('serve_index'))
    else:
        flash('Invalid email or password.', 'danger')
        return redirect(url_for('serve_login'))

# === LOGOUT ROUTE ===

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('serve_login'))

# === APP RUN ===

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
