from flask import Flask, render_template,redirect,url_for
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('Frontend/index.html')

@app.route('/register')
def register():
    return render_template('Frontend/register.html')

@app.route('/login')
def login():
    return render_template('Frontend/login.html')

@app.route('/password_reset')
def password_reset():
    return render_template('Frontend/password_reset.html')

@app.route('/contacts')
def contacts():
    return render_template('Frontend/contacts.html')

@app.route('/confirm_password')
def confirm_password():
    return render_template('Frontend/confirm_password.html')


if __name__ == '__main__':
    app.run(debug=True)