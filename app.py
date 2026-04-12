from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'slmr_secret_key_123'

db_config = {
    'host': 'localhost',
    'user': 'sek_admin',
    'password': 'sek_pass123',
    'database': 'second_life_mr'
}

def db_query(query, params=(), commit=False):
    conn = None
    try:
        conn = mysql.connector.connect(buffered=True, **db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        if commit:
            conn.commit()
            return f"Success. {cursor.rowcount} row(s) affected."
        return cursor.fetchall() if cursor.with_rows else None
    except Error as e:
        return f"Database Error: {e}"
    finally:
        if conn: conn.close()

def log_action(action, query):
    db_query("INSERT INTO audit_logs (user_id, action, executed_query) VALUES (%s, %s, %s)", 
             (session.get('user_id'), action, query), commit=True)

@app.context_processor
def inject_globals():
    logs = db_query("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 15")
    return dict(logs=logs if isinstance(logs, list) else [])

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/login/<role>', methods=['GET', 'POST'])
def login(role):
    if request.method == 'POST':
        q = "SELECT * FROM users WHERE username=%s AND password=%s AND role=%s"
        user = db_query(q, (request.form['username'], request.form['password'], role))
        if isinstance(user, list) and user:
            session.update({'user_id': user[0]['id'], 'role': user[0]['role'], 'full_name': user[0]['full_name']})
            log_action(f'{role.capitalize()} Login', q)
            return redirect(url_for(f'{role}_dashboard'))
        flash('Invalid credentials or role mismatch.')
    return render_template('login.html', role=role)

@app.route('/register', methods=['GET', 'POST'])
def register_patient():
    if request.method == 'POST':
        f = request.form
        q = "INSERT INTO users (username, password, role, full_name, dob, blood_group, sex, weight, height) VALUES (%s, %s, 'patient', %s, %s, %s, %s, %s, %s)"
        db_query(q, (f['username'], f['password'], f['full_name'], f['dob'], f['blood_group'], f['sex'], f['weight'], f['height']), commit=True)
        log_action('Patient Registration', f"New user: {f['username']}")
        flash('Registration successful! Please login.')
        return redirect(url_for('login', role='patient'))
    return render_template('register.html')

@app.route('/provider')
def provider_dashboard():
    if session.get('role') != 'provider': return redirect(url_for('landing'))
    patients = db_query("SELECT * FROM v_active_patients WHERE authorized_provider_id = %s", (session['user_id'],))
    return render_template('provider_dashboard.html', patients=patients)

@app.route('/add_record', methods=['POST'])
def add_record():
    if session.get('role') != 'provider': return redirect(url_for('landing'))
    f = request.form
    linked_id = f.get('linked_record_id') or None
    q = "INSERT INTO medical_records (patient_id, provider_id, linked_record_id, diagnosis, bp, pulse, temp, ecg, medicines, patient_status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    res = db_query(q, (f['patient_id'], session['user_id'], linked_id, f['diagnosis'], f['bp'], f['pulse'], f['temp'], f['ecg'], f['medicines'], f['status']), commit=True)
    if "Error" in res: flash(res)
    else: 
        log_action('Append Record', q)
        flash('Record appended to immutable history.')
    return redirect(url_for('provider_dashboard'))

@app.route('/patient')
def patient_dashboard():
    if session.get('role') != 'patient': return redirect(url_for('landing'))
    details = db_query("SELECT *, TIMESTAMPDIFF(YEAR, dob, CURDATE()) as calculated_age FROM users WHERE id = %s", (session['user_id'],))[0]
    records = db_query("SELECT mr.*, u.full_name as provider_name FROM medical_records mr JOIN users u ON mr.provider_id = u.id WHERE mr.patient_id = %s ORDER BY created_at DESC", (session['user_id'],))
    providers = db_query("SELECT id, full_name FROM users WHERE role = 'provider'")
    consents = db_query("SELECT c.*, u.full_name FROM consents c JOIN users u ON c.provider_id = u.id WHERE c.patient_id = %s AND c.expires_at >= CURDATE()", (session['user_id'],))
    return render_template('patient_dashboard.html', details=details, records=records, providers=providers, consents=consents)

@app.route('/grant_consent', methods=['POST'])
def grant_consent():
    if session.get('role') != 'patient': return redirect(url_for('landing'))
    f = request.form
    db_query("INSERT INTO consents (patient_id, provider_id, expires_at) VALUES (%s, %s, %s)", 
             (session['user_id'], f['provider_id'], f['expires_at']), commit=True)
    log_action('Grant Consent', f"Access granted to Provider ID: {f['provider_id']}")
    flash('Temporal access granted to provider.')
    return redirect(url_for('patient_dashboard'))

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin': return redirect(url_for('landing'))
    users = db_query("SELECT id, username, role, full_name FROM users")
    return render_template('admin_dashboard.html', users=users)

@app.route('/execute_sql', methods=['POST'])
def execute_sql():
    sql = request.form['sql']
    res = db_query(sql, commit=True if not sql.strip().upper().startswith('SELECT') else False)
    log_action('Direct SQL', sql)
    users = db_query("SELECT id, username, role, full_name FROM users")
    return render_template('admin_dashboard.html', users=users, sql_result=str(res))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
