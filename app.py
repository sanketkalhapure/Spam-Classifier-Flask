from flask import Flask, render_template, request, redirect, url_for, session, flash
import pickle
import string
import nltk
from nltk.stem import PorterStemmer
import mysql.connector
import os # <-- ADDED for environment variables
# For password security (assuming you installed it)
from werkzeug.security import generate_password_hash, check_password_hash 

app = Flask(__name__)
# 1. SECRET KEY: Load from environment or use a fallback (for local testing)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', '1c8073775dbc85a92ce20ebd44fd6a4fd832078f59ef16ec')

ps = PorterStemmer()
tfidf = pickle.load(open('vectorizer.pkl', 'rb'))
model = pickle.load(open('model.pkl', 'rb'))

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def transform_text(text):
    text = text.lower()
    text = nltk.word_tokenize(text)

    y = []
    for i in text:
        if i.isalnum():
            y.append(i)

    text = y[:]
    y.clear()

    for i in text:
        if i not in string.punctuation:
            y.append(i)

    text = y[:]
    y.clear()

    for i in text:
        y.append(ps.stem(i))

    return " ".join(y)

# 2. DATABASE CONNECTION: Load credentials from environment
try:
    db = mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', 'sanket'),
        database=os.environ.get('DB_DATABASE', 'smc')
    )
except mysql.connector.Error as err:
    print(f"Error connecting to MySQL: {err}")
    db = None 

# --- Routes (No changes to /home, /about, /index, /predict, /signin, /signup, /logout) ---

@app.route('/index')
def index():
    if 'user' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('signin'))

@app.route('/predict', methods=['POST'])
def predict():
    # ... (prediction logic remains the same)
    input_sms = request.form.get('message')
    transformed_sms = transform_text(input_sms)
    vector_input = tfidf.transform([transformed_sms])
    result = model.predict(vector_input)[0]
    prediction = "Spam" if result == 1 else "Not Spam"
    return render_template('result.html', prediction=prediction)

# 3. REGISTER ROUTE: Implements Password Hashing
@app.route('/register', methods=['POST'])
def register():
    full_name = request.form['full_name']
    username = request.form['username']
    email = request.form['email']
    phone = request.form['phone']
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    if password != confirm_password:
        flash('Password and Confirm Password do not match.', 'danger')
        return redirect(url_for('signup'))

    # Hash the password before insertion
    hashed_password = generate_password_hash(password)

    if db is None:
         flash('Database connection failed.', 'danger')
         return redirect(url_for('signup'))

    try:
        cur = db.cursor()
        # Insert the HASHED password
        cur.execute("INSERT INTO users (full_name, username, email, phone, password) VALUES (%s, %s, %s, %s, %s)",
                    (full_name, username, email, phone, hashed_password))
        db.commit()
        cur.close()
    except Exception as e:
        flash(f'Registration failed: {e}', 'danger')
        return redirect(url_for('signup'))

    flash('Registration successful', 'success')
    return redirect(url_for('signin'))

# 4. LOGIN ROUTE: Implements Password Verification
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    remember_me = request.form.get('remember_me')

    if db is None:
         flash('Database connection failed.', 'danger')
         return redirect(url_for('signin'))

    cur = db.cursor()
    # Fetch the user's data (including the HASHED password) based on email
    # Ensure your password column can store a long hash string!
    cur.execute("SELECT full_name, username, email, phone, password FROM users WHERE email = %s", (email,))
    user_record = cur.fetchone()
    cur.close()

    if user_record and check_password_hash(user_record[4], password): # user_record[4] is the hashed password
        session['user'] = user_record # User is logged in
        if remember_me:
            session.permanent = True
        return redirect(url_for('index'))
    else:
        flash('Login failed. Check your email and password.', 'danger')
        return redirect(url_for('signin'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
