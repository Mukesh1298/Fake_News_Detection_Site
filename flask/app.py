from flask import Flask, render_template, request, redirect, flash, session,jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pickle


app = Flask(__name__)

# Secret key for session management and flashing messages
app.secret_key = "your_secret_key"

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Fake2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
#load model
with open("C:/CollegeProjectP/fake_news_model.pkl", "rb") as LR_file:
    model = pickle.load(LR_file)
#load vectorizer
with open("C:/CollegeProjectP/vectorizer.pkl", 'rb') as f:
    vectorizer = pickle.load(f)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Primary key
    username = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"

# Create database tables (run this only once or after changes to models)
with app.app_context():
    db.create_all()

@app.route("/", methods=['GET', 'POST'])
def home():
    # Check if the user is logged in
    if 'user_id' in session:
        return render_template('front2.html', logged_in=True)  # Pass logged_in status to the template
    return render_template('front2.html', logged_in=False)  # Pass logged_in status to the template
@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "error")
            return redirect('/signup')

        # Check if the email is already registered
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email is already registered. Please log in.", "error")
            return redirect('/signup')

        # Save new user to the database
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash("Signup successful! You can now log in.", "success")
        # Redirect to detection page after successful signup
        # return redirect('/detection')  # Change this line

    return render_template('signup.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate user credentials
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            # Store user info in session
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f"Welcome, {user.username}!", "success")
            # Redirect to detection page after successful login
            return redirect('/detection')
        else:
            flash("Invalid email or password. Please try again.", "error")
            return redirect('/login')

    return render_template('login.html')
@app.route("/detection")
def detection():
    # Ensure the user is logged in
    if 'user_id' not in session:
        flash("Please log in to access the detection page.", "error")
        return redirect('/login')
    
    return render_template('detection.html')

### **👉 Fake News Detection API Endpoint (Where "text" is used)**
@app.route("/predict", methods=['GET','POST'])
def predict():
    if 'user_id' not in session:  # Ensure only logged-in users can access
        flash("Please log in to access the detection API.", "error")
        return redirect('/login')

    try:
        # Step 1: Get JSON data from request
        data = request.get_json()
        
        # Step 2: Extract text from JSON
        text = data['text']  # 🔹 This is where "text" is used

        # Step 3: Transform text using the vectorizer
        text_vectorized = vectorizer.transform([text])

        # Step 4: Predict using the trained model
        prediction = model.predict(text_vectorized)

        # Step 5: Convert result (0 = FAKE, 1 = REAL)
        result = "FAKE" if prediction[0] == 0 else "REAL"

        # Step 6: Return the prediction as JSON
        return jsonify({"prediction": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/forgot_password", methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Check if passwords match
        if new_password != confirm_password:
            flash("Passwords do not match. Please try again.", "error")
            return redirect('/forgot_password')

        # Find the user by email
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Email not found. Please check and try again.", "error")
            return redirect('/forgot_password')
        # Update the password
        user.password = new_password
        db.session.commit()

        flash("Password reset successful! Please log in.", "success")
        return redirect('/login')

    return render_template('forgot_password.html')

@app.route("/")
def dashboard():
    if 'user_id' not in session:
        flash("Please log in to access the dashboard.", "error")
        return redirect('/login')

    return render_template('front2.html', username=session['username'])



@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
