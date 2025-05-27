from flask import Flask, render_template, request, redirect, url_for    
app = Flask(__name__)
from models import *
from flask import session
import re

app.secret_key = 'a12sadsdsahasaafsdaqwegasd'

@app.route('/')
def root():
    return render_template('/pages/index.html')

@app.route('/login')
def login():
    return render_template('/pages/login.html')

@app.route('/register')
def register():
    return render_template('/pages/register.html')

@app.route('/scan')
def scan():
    if 'user_id' not in session or session.get('user_type') != 'users':
        return redirect(url_for('login'))
    return render_template('/pages/scan.html')

@app.route('/settings')
def settings():
    if 'user_id' not in session or session.get('user_type') != 'users':
        return redirect(url_for('login'))
    id  = session.get('user_id')
    result = Users.getUserById(id)
    return render_template('/pages/settings.html', data=result)

@app.route('/tips')
def tips():
    if 'user_id' not in session or session.get('user_type') != 'users':
        return redirect(url_for('login'))
    return render_template('/pages/tips.html')

@app.route('/view_tips')
def view_tips():
    if 'user_id' not in session or session.get('user_type') != 'users':
        return redirect(url_for('login'))
    return render_template('/pages/view_tips.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/register_users', methods=['POST'])
def register_users():
    fullname = request.form.get('fullname')
    email = request.form.get('email')
    password = request.form.get('password')
    Users.insertUser(fullname, email, password)
    return redirect(url_for('login'))

@app.route('/login_action', methods=['POST'])
def login_action():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return render_template('/pages/login.html', error="Email and password are required.")

    user = Users.login(email, password)
    if user:
        print(user)
        session['user_id'] = user['id']
        session['user_type'] = 'users'  # Assuming 'type' is a field in the user data
        return redirect(url_for('scan'))
    else:
        return render_template('/pages/login.html', error=1)

@app.route('/update_personal', methods=['POST'])
def update_personal():
    fullname = request.form.get('fullname')
    email = request.form.get('email')
    id = session.get('user_id')

    if not fullname or not email:
        return render_template('/pages/settings.html', error="All fields are required.")

    Users.updateUser(id, fullname, email)
    result = Users.getUserById(id)
    return render_template('/pages/settings.html', message=1, data=result)

@app.route('/update_password', methods=['POST'])
def update_password():
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    user_id = session.get('user_id')

    if not new_password or not confirm_password:
        result = Users.getUserById(user_id)
        return render_template('/pages/settings.html', message=5, data=result)

    if new_password != confirm_password:
        result = Users.getUserById(user_id)
        return render_template('/pages/settings.html', message=3, data=result)

    # if len(new_password) < 8 or not re.search(r'[A-Z]', new_password) or not re.search(r'[a-z]', new_password) or not re.search(r'[0-9]', new_password) or not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
    #     result = Users.getUserById(user_id)
    #     return render_template('/pages/settings.html', message=4, data=result)

    Users.updatePassword(user_id, new_password)
    result = Users.getUserById(user_id)
    return render_template('/pages/settings.html', message=2, data=result)

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)