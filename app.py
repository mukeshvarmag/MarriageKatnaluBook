from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask import make_response
from xhtml2pdf import pisa
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session handling

# SQLite DB config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gifts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Fake login credentials (for now)
USERNAME = 'admin'
PASSWORD = 'pass123'

# Models
class Gift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    place = db.Column(db.String(100), nullable=False)
    amount_or_gift = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

# ------------------ LOGIN REQUIRED DECORATOR ------------------
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ------------------ ROUTES ------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            error = 'Invalid Credentials'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    return render_template('form.html')

@app.route('/submit_gift', methods=['POST'])
@login_required
def submit_gift():
    name = request.form['name']
    place = request.form['place']
    amount_or_gift = request.form['amount_or_gift']
    new_gift = Gift(name=name, place=place, amount_or_gift=amount_or_gift)
    db.session.add(new_gift)
    db.session.commit()
    return redirect(url_for('view_gifts'))

@app.route('/gifts')
@login_required
def view_gifts():
    gifts = Gift.query.all()
    return render_template('gifts.html', gifts=gifts)

@app.route('/edit/<int:gift_id>', methods=['GET', 'POST'])
@login_required
def edit_gift(gift_id):
    gift = Gift.query.get_or_404(gift_id)
    if request.method == 'POST':
        gift.name = request.form['name']
        gift.place = request.form['place']
        gift.amount_or_gift = request.form['amount_or_gift']
        db.session.commit()
        return redirect(url_for('view_gifts'))
    return render_template('edit.html', gift=gift)

@app.route('/delete/<int:gift_id>', methods=['POST'])
@login_required
def delete_gift(gift_id):
    gift = Gift.query.get_or_404(gift_id)
    db.session.delete(gift)
    db.session.commit()
    return redirect(url_for('view_gifts'))


@app.route('/download_pdf')
@login_required
def download_pdf():
    gifts = Gift.query.all()
    rendered = render_template('gifts_pdf.html', gifts=gifts)
    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(rendered, dest=pdf)

    if pisa_status.err:
        return "Error generating PDF", 500

    pdf.seek(0)
    return make_response(pdf.read(), {
        "Content-Type": "application/pdf",
        "Content-Disposition": "attachment; filename=marriage_gifts.pdf"
    })


if __name__ == '__main__':
    app.run(debug=True)
