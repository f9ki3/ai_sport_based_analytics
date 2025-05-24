from flask import Flask, render_template, request, redirect, url_for    
app = Flask(__name__)

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
    return render_template('/pages/scan.html')

@app.route('/settings')
def settings():
    return render_template('/pages/settings.html')

@app.route('/tips')
def tips():
    return render_template('/pages/tips.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)