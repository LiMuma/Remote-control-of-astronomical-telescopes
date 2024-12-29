from flask import Flask, render_template, request, jsonify, session
import datetime
import threading
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 设置用于加密 session 的密钥

# Shared data
access_dict = {}
lock = threading.Lock()

# Function to manage user access and time
def manage_access():
    global access_dict
    while True:
        if access_dict:
            first_user = next(iter(access_dict))
            start_time = access_dict[first_user]['timestamp']
            while (datetime.datetime.now() - start_time).seconds < 40:  # 30 minutes
                time.sleep(1)
            with lock:
                if first_user in access_dict:
                    access_dict.pop(first_user)

threading.Thread(target=manage_access, daemon=True).start()

@app.route('/')
def index():
    if 'user' in session:
        user = session['user']
        if user in access_dict:
            time_left = 40 - (datetime.datetime.now() - access_dict[user]['timestamp']).seconds
            return render_template('inuse.html', user=user, time_left=time_left)
        else:
            session.pop('user')  # 清除无效的 session
    return render_template('available.html')

@app.route('/request_access', methods=['POST'])
def request_access():
    user_name = request.form['name']
    with lock:
        if 'user' in session or access_dict:
            return jsonify({'status': 'queued'})
        else:
            access_dict[user_name] = {'timestamp': datetime.datetime.now()}
            session['user'] = user_name
            return jsonify({'status': 'granted', 'time_left': 40})

@app.route('/current_status')
def current_status():
    if 'user' in session:
        user = session['user']
        if user in access_dict:
            time_left = 40 - (datetime.datetime.now() - access_dict[user]['timestamp']).seconds
            return jsonify({'current_user': user, 'time_left': time_left})
        else:
            session.pop('user')  # 清除无效的 session
    return jsonify({'current_user': None})

if __name__ == '__main__':
    app.run(debug=True,port=10022)
