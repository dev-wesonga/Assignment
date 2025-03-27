from flask import Flask, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash ,check_password_hash
from flask_pymongo import PyMongo
from flask_wtf.csrf import CSRFProtect

from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
  

csrf = CSRFProtect(app)

# Flask-Mail Config
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
mail = Mail(app)

# MongoDB Config
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)

# Serializer for token-based operations (password reset, etc.)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])


@app.route('/', methods=['GET', 'POST'])
def home():
    if 'email' in session:
        user = mongo.db.users.find_one({"email": session['email']})

        if request.method == 'POST':
            phone_number = request.form.get("phone_number")
            email = request.form.get("email")
            address = request.form.get("address")
            registration_number = request.form.get("registration_number")

            # Ensure all fields are filled
            if not all([phone_number, email, address, registration_number]):
                flash("⚠️ All fields are required!", "danger")
                return redirect(url_for('home'))

            # Insert contact details into the database
            mongo.db.contacts.insert_one({
                "user_id": user["_id"],
                "name": user.get("name", "Guest"),
                "phone_number": phone_number,
                "email": email,
                "address": address,
                "registration_number": registration_number
            })

            flash("✅ Contact details submitted successfully!", "success")
            return redirect(url_for('home'))

        return render_template('Frontend/index.html', user=user)

    
    return redirect(url_for('login')) 

@app.route('/register', methods=['GET', 'POST'])
def register():
    if "email" in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        name = request.form['name'] 
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        # Hash the password
        hashed_password = generate_password_hash(password)
        
        # Check if user already exists
        existing_user = mongo.db.users.find_one({"email": email})
        if existing_user:
            flash('Email already registered', 'warning')
            return redirect(url_for('register'))
        
        # Create a new user instance
        new_user = {"name": name, "email": email, "password": hashed_password}
        mongo.db.users.insert_one(new_user)
        print("✅ User added!", new_user )
        
        flash('Registration successful! ', 'success')
        return redirect(url_for('login'))

    return render_template('Frontend/register.html')





@app.route('/login', methods=['GET', 'POST'])
def login():
    if "email" in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash("❌ Email and password are required.", "danger")
            return redirect(url_for('login'))        

        # 🔍 Find user by email
        user = mongo.db.users.find_one({"email": email})
        print(f"User found: {user}")  # Debugging

        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])  # Store user ID in session
            session['email'] = user['email']
            flash('✅ Login successful!', 'success')
            
           
            return redirect(url_for('home'))  # Redirect to home or dashboard
        else:
            flash('❌ Invalid email or password', 'danger')
           

    return render_template('Frontend/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('✅ You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/password_reset', methods=['GET', 'POST'])
def password_reset():
    if "email" in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form['email']
        user = mongo.db.users.find_one({"email": email})

        if not user:
            flash("❌ No account found with that email.", "danger")
            return redirect(url_for('password_reset'))

        # Generate a token that expires in 30 minutes
        token = serializer.dumps(email, salt="password-reset-salt")

        # Generate reset link
        reset_link = url_for('confirm_password', token=token, _external=True)

        # Send Email
        msg = Message("Password Reset Request", recipients=[email])
        msg.body = f"Click the link below to reset your password:\n{reset_link}\nThis link will expire in 30 minutes."
        mail.send(msg)

        flash("✅ Check your email for the password reset link.", "success")
        return render_template('Frontend/password_reset.html')

    return render_template('Frontend/password_reset.html')


@app.route('/confirm_password/<token>', methods=['GET', 'POST'])
def confirm_password(token):
    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=1800)  # 30 mins expiry
    except:
        flash("❌ The link is invalid or expired.", "danger")
        return redirect(url_for('password_reset'))  # Ensure this route exists!

    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash("❌ Passwords do not match.", "danger")
            return redirect(url_for('confirm_password', token=token))

        # Ensure password security
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')

        # Update password in the database
        mongo.db.users.update_one({"email": email}, {"$set": {"password": hashed_password}})

        flash("✅ Password reset successful! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('Frontend/confirm_password.html', token=token)

@app.route('/contacts', methods=['GET'])

def contacts():
     if 'email' in session:
        user = mongo.db.users.find_one({"email": session['email']})
    
        search_query = request.args.get('search', '').strip()
        
        if search_query:
            contacts = list(mongo.db.contacts.find({"registration_number": search_query}))
        else:
            contacts = list(mongo.db.contacts.find())

        return render_template('Frontend/contacts.html', contacts=contacts,user=user)
     return redirect(url_for('login'))




if __name__ == '__main__':
    app.run(debug=True)

