from flask import Flask, render_template, request, redirect, url_for, session
import time
from datetime import datetime

app = Flask(__name__)
app.secret_key = "ib_cs_ia_final_ultimate"

users = {} 

@app.route('/')
def start():
    return render_template('index.html', page='start')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        if user in users:
            error = "Account already exists!"
        elif user and pw:
            users[user] = pw
            return redirect(url_for('login'))
    return render_template('index.html', page='signup', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'attempts' not in session: session['attempts'] = 0
    error = None
    current_time = time.time()
    
    if session['attempts'] >= 3:
        time_passed = current_time - session.get('lockout_time', 0)
        remaining = 300 - time_passed
        if remaining > 0:
            return render_template('index.html', page='login', locked=True, end_time=session['lockout_time'] + 300)
        else:
            session['attempts'] = 0 

    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        if user in users and users[user] == pw:
            session.clear() 
            session['user'] = user
            session['attempts'] = 0
            session['history'] = [] 
            return redirect(url_for('homepage'))
        else:
            session['attempts'] += 1
            if session['attempts'] >= 3:
                session['lockout_time'] = time.time()
            error = f"Invalid login. {session['attempts']}/3 trials used."
            
    return render_template('index.html', page='login', error=error, locked=False)

@app.route('/homepage')
def homepage():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('index.html', page='homepage', 
                           gpa=session.get('last_gpa'), 
                           progress=session.get('progress', 0), 
                           status=session.get('status', ""),
                           history=session.get('history', []),
                           current_courses=session.get('current_courses', []))

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        names = request.form.getlist('c_name')
        grades = request.form.getlist('grade')
        credits = request.form.getlist('credit')
        
        course_data = []
        valid_pairs = []
        
        for n, g, c in zip(names, grades, credits):
            if g and c:
                g_val, c_val = float(g), float(c)
                course_data.append({'name': n, 'grade': g_val, 'credit': c_val})
                if 0 <= g_val <= 4.0:
                    valid_pairs.append((g_val, c_val))
        
        session['current_courses'] = course_data
        
        if valid_pairs:
            total_points = sum(g * c for g, c in valid_pairs)
            total_credits = sum(c for g, c in valid_pairs)
            res = round(total_points / total_credits, 2)
            
            session['last_gpa'] = res
            session['progress'] = int((res / 4.0) * 100)
            session['status'] = "AT RISK" if res < 2.0 else "SAFE"
            
            dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            session['history'].append({'gpa': res, 'datetime': dt_string})
            session.modified = True
    except:
        pass
    return redirect(url_for('homepage'))

@app.route('/clear')
def clear_calc():
    session.pop('last_gpa', None)
    session.pop('progress', None)
    session.pop('status', None)
    session.pop('current_courses', None)
    return redirect(url_for('homepage'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('start'))

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)