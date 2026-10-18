# THE EYE — Q&A (Created by ~ Mridul)

A dark, red-accented multi-user Q&A starter built with Flask and SQLAlchemy. Users must provide a display name to post questions or answers. The admin dashboard shows submissions, display names, and UTC timestamps.

## Run locally

1. Install Python 3.11+.
2. Open a terminal in this folder.
3. Create and activate a virtual environment (optional but recommended):
   - Windows: `py -m venv .venv` then `.venv\Scripts\activate`
   - macOS/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set environment variables before starting:
   - Windows PowerShell:
     ```
     $env:SECRET_KEY = "replace-with-a-long-random-secret"
     $env:ADMIN_USERNAME = "mridul"
     $env:ADMIN_PASSWORD_HASH = (python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('Choose-A-Strong-Unique-Password'))")
     ```
     Replace the example password with your own strong password before running the command. Do not publish it.
   - macOS/Linux:
     ```
     export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
     export ADMIN_USERNAME="mridul"
     export ADMIN_PASSWORD_HASH="$(python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('Choose-A-Strong-Unique-Password'))")"
     ```
6. Start: `python app.py`
7. Open `http://127.0.0.1:5000`

The default local database is `illuminati_qa.db`. Keep secrets out of source control.

## Deploy online with Render + PostgreSQL

1. Create a GitHub repository and upload these project files (never upload passwords or secret values).
2. In Render, create a new Blueprint from the repository and use `render.yaml`, or create a Python web service and PostgreSQL database manually.
3. Set `SECRET_KEY` to a long random secret; set `COOKIE_SECURE=1`; set `ADMIN_USERNAME` to your preferred admin username.
4. Generate a password hash locally and paste only the hash into `ADMIN_PASSWORD_HASH`:
   ```
   python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('YOUR-UNIQUE-PASSWORD'))"
   ```
   Run this locally using your own chosen password, then put the output hash in Render's environment settings. Never put your actual password in `render.yaml` or code.
5. Set `DATABASE_URL` to the PostgreSQL internal connection string from your database. Deploy.
6. Visit `/admin/login` on your deployed domain to sign in.

## Security and privacy notes

- CSRF protection, password hashing, secure cookie options, and request rate limits are enabled.
- Set `COOKIE_SECURE=1` only when using HTTPS (as on Render).
- Admin login uses environment variables; there is no public admin registration.
- Public question/answer names are display names, not verified real identities. Do not claim that a display name proves who a person is.
- This starter does not collect IP addresses or hidden identity data. It stores the display name, question/answer text, relationship to the question, and UTC timestamp.
- Public submissions are visible to all visitors. Tell users what is public before they submit and do not collect sensitive information.
- For a real public launch, add backups, monitoring, a privacy notice, moderation/reporting, and review rate limits and hosting costs.
- SQLite is fine for local testing; use persistent PostgreSQL for an online deployment.
