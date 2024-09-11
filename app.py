from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import json
import os
import random
import string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

# Paths for JSON files
points_path = 'points.json'
rankings_path = 'rankings.json'
registrations_path = 'registrations.json'

# Initialize files if they don't exist
def init_json_file(path, default_data):
    if not os.path.exists(path):
        with open(path, 'w') as f:
            json.dump(default_data, f)

init_json_file(points_path, {})
init_json_file(rankings_path, [])
init_json_file(registrations_path, [])

def update_team_points(team_name, points):
    try:
        with open(points_path, 'r') as f:
            data = json.load(f)
        
        data[team_name] = data.get(team_name, 0) + points

        with open(points_path, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error updating points: {e}")

def update_team_ranking(team_name, rank):
    try:
        with open(rankings_path, 'r') as f:
            ranking_data = json.load(f)
        
        ranking_data = [team for team in ranking_data if team['name'] != team_name]
        ranking_data.append({'name': team_name, 'rank': rank})
        ranking_data.sort(key=lambda x: x['rank'])
        
        with open(rankings_path, 'w') as f:
            json.dump(ranking_data, f)
    except Exception as e:
        print(f"Error updating ranking: {e}")

@app.route('/')
def index():
    return render_template('admin.html')

@app.route('/record_attendance', methods=['POST'])
def record_attendance():
    qr_code = request.json.get('qrCode')
    try:
        with open(points_path, 'r') as f:
            data = json.load(f)
        
        if qr_code not in data:
            update_team_points(qr_code, 10)
            return jsonify({'status': 'success', 'message': 'تم تسجيل الحضور ومنح 10 نقاط!'})
        else:
            return jsonify({'status': 'error', 'message': 'تم مسح هذا الكود مسبقاً.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/add_points', methods=['POST'])
def add_points():
    if 'team_name' not in request.form or 'points' not in request.form:
        return jsonify({'status': 'error', 'message': 'Missing required fields'})
    
    team_name = request.form['team_name']
    points = int(request.form['points'])
    try:
        update_team_points(team_name, points)
        # Update ranking after adding points (if needed)
        # update_team_ranking(team_name, calculate_rank())
        return 'Points added successfully'
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/add_rank', methods=['POST'])
def add_rank():
    data = request.get_json()
    team_name = data.get('team_name')
    rank = data.get('rank')
    try:
        if team_name is None or rank is None:
            return jsonify({'error': 'Missing data'}), 400
        update_team_ranking(team_name, rank)
        return jsonify({'message': 'تم إضافة المركز بنجاح!'}), 200
    except Exception as e:
        return jsonify({'error': f'حدث خطأ أثناء إضافة المركز: {str(e)}'}), 500

@app.route('/get_ranking', methods=['GET'])
def get_ranking():
    try:
        with open(rankings_path, 'r') as f:
            ranking_data = json.load(f)
        return jsonify(ranking_data)
    except Exception as e:
        return jsonify({'error': f'حدث خطأ أثناء استرجاع البيانات: {str(e)}'}), 500

@app.route('/success')
def success():
    qr_code_filename = request.args.get('qr_code_filename')
    username = request.args.get('username')
    password = request.args.get('password')
    return render_template('success.html', qr_code_filename=qr_code_filename, username=username, password=password)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Example admin credentials, use environment variables or a secure store in production
        if username == 'admin' and password == 'admin':
            session['admin_logged_in'] = True
            return redirect(url_for('index'))
        else:
            return "Invalid login", 401
    return render_template('admin_login.html')

@app.route('/admin')
def admin():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    try:
        with open(points_path, 'r') as f:
            points_data = json.load(f)
        
        with open(rankings_path, 'r') as f:
            ranking_data = json.load(f)
        
        if not isinstance(points_data, dict):
            points_data = {}
        
        if not isinstance(ranking_data, list):
            ranking_data = []
        
        return render_template('admin.html', points=points_data, rankings=ranking_data)
    
    except Exception as e:
        return str(e), 500

@app.route('/team_login', methods=['GET', 'POST'])
def team_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            with open(registrations_path, 'r') as f:
                registrations = json.load(f)
            
            if any(registration['team_name'] == username and check_password_hash(registration.get('password', ''), password) for registration in registrations):
                session['team_logged_in'] = True
                session['team_name'] = username
                return redirect(url_for('profile', team_name=username))
            else:
                return "Invalid login", 401
        except Exception as e:
            return f"Error during login: {e}", 500

    return render_template('team_login.html')

@app.route('/profile/<team_name>')
def profile(team_name):
    if 'team_logged_in' not in session or session.get('team_name') != team_name:
        return redirect(url_for('team_login'))

    try:
        with open(points_path, 'r') as f:
            data = json.load(f)
        
        points = data.get(team_name, 0)
        
        with open(rankings_path, 'r') as f:
            ranking_data = json.load(f)
        
        sorted_teams = sorted(ranking_data, key=lambda x: x['rank'])
        rank = next((team['rank'] for team in sorted_teams if team['name'] == team_name), 'Not Ranked')

        return render_template('profile.html', team_name=team_name, points=points, rank=rank)
    except Exception as e:
        return f"Error loading profile: {e}", 500

@app.route('/logout')
def logout():
    session.pop('team_logged_in', None)
    session.pop('team_name', None)
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
