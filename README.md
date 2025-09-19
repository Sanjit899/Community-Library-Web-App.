Community Library Web App

Community Library is a modern, production-ready web application that allows students and community members to access, borrow, and reserve books online. This project demonstrates a full-featured library management system with a clean, responsive interface, user authentication, dashboards, reservations, and more.


🌟 Features
1. User Authentication & Management

Secure registration and login with password hashing.

Dashboard for users to manage borrowed books and reservations.

Admin role for library management (optional for extensions).

2. Book Borrowing

Users can borrow books and see due dates.

Borrowed books display status: Borrowed / Returned.

Option to return books directly from the dashboard.

3. Reservations

Users can reserve books that are currently borrowed by others.

Manage all reservations from the dashboard.

Notifications (demo via dashboard flash messages).

4. Responsive & Modern UI

Built using Bootstrap 5 for mobile-first, responsive design.

Professional layout for Home, About, Catalog, E-books, Events, and Contact pages.

Clean typography and card-based design for mission, vision, and team sections.

5. Dark/Light Mode

Toggle between dark and light themes for better accessibility.

Saved preference for logged-in users (frontend demo).

6. Admin Features

Admin dashboard to manage books, users, and reservations (extendable).

Book addition, editing, and deletion (optional for future updates).

7. Community Engagement

Forum and events pages to interact with other members (placeholders in demo).

Option to donate books to the library.

8. Production Ready

Uses Flask with MongoDB backend (NoSQL).

User-friendly interface with real-time updates via page reloads.

Structured project folder for easy maintenance and deployment.

🛠️ Tech Stack
Layer	Technology
Backend	Python, Flask
Frontend	HTML, CSS, Bootstrap 5, JS
Database	MongoDB
Authentication	Flask-Login
Forms & Security	Werkzeug Security
Deployment	GitHub Pages (frontend demo) / Heroku / Render (full app)

📁 Project Structure
community-library/
├─ app.py                 # Main Flask application
├─ requirements.txt       # Python dependencies
├─ templates/             # HTML templates
│   ├─ base.html
│   ├─ index.html
│   ├─ about.html
│   ├─ contact.html
│   ├─ dashboard.html
│   ├─ catalog.html
│   ├─ ebooks.html
│   └─ ...other pages
├─ static/
│   ├─ css/
│   │   └─ style.css
│   ├─ js/
│   │   └─ main.js
│   └─ images/
│       ├─ mission.jpg
│       ├─ vision.jpg
│       ├─ team1.jpg
│       ├─ team2.jpg
│       └─ ...other images
├─ .env                   # Environment variables (e.g., MongoDB URI, secret key)
└─ README.md


Create a virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

Install dependencies
pip install -r requirements.txt


Dependencies :-  requirements.txt
Flask==3.0.3
Flask-Login==0.6.3
Flask-WTF==1.2.1
Flask-Bcrypt==1.0.1
pymongo==4.9.2
dnspython==2.7.0
email-validator==2.2.0
python-dotenv==1.0.1
gunicorn==23.0.0

📌 Why these packages?

Flask → Core web framework.

Flask-Login → User authentication/session management.

Flask-WTF → Form handling + CSRF protection.

Flask-Bcrypt → Password hashing.

pymongo → MongoDB driver.

dnspython → Needed for MongoDB Atlas SRV connection strings.

email-validator → To validate email inputs.

python-dotenv → Load .env configs (secret key, DB URI).

gunicorn → For production deployment (Render/Heroku/etc.).


Set up environment variables
Create a .env file in the root directory with the following:
SECRET_KEY=your_secret_key
MONGO_URI=your_mongodb_connection_string

Run the app locally
python app.py
Open your browser at http://127.0.0.1:5000

Register a new user and explore the dashboard, borrow books, and manage reservations.

🔧 Usage Instructions
User Dashboard

View all borrowed books with due dates and return options.

See all reservations and reserve available books.

Toggle between dark and light mode.

Catalog & E-books

Browse the book catalog and E-books section.

Reserve books directly from the catalog page.

Admin Panel (Optional)

Manage users, books, and reservations.

Add or remove books (requires admin account setup in app.py).


🤝 Contribution

Fork the repository.

Create a new branch (git checkout -b feature-name).

Commit your changes (git commit -am 'Add new feature').

Push to the branch (git push origin feature-name).

Open a Pull Request.


✅ License

This project is open-source and free to use under the MIT License.

