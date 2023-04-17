import SMS
import requests
import json
import time
from datetime import datetime, date, timedelta
import os
import urllib.parse
import threading
import psycopg2
from flask import Flask, render_template, url_for, jsonify, request


app = Flask(__name__)

elephantsql_url = os.environ["DATABASE_URL"]
url = urllib.parse.urlparse(elephantsql_url)
db_url = f"dbname={url.path[1:]} user={url.username} password={url.password} host={url.hostname} port={url.port}"
conn = psycopg2.connect(db_url)

current_stats = None

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route("/")
def home():
    if current_stats is not None:
        message = f"Date: {current_stats['Date']}, Referrals: {current_stats['Referrals:']}, Rewards: {current_stats['Rewards:']}"
    return render_template("index.html", message=message, css=url_for("static", filename="styles.css"), time=time, current_stats=current_stats)

@app.route("/all_data")
def all_data():
    with conn.cursor() as cur:
        cur.execute("SELECT data FROM stats;")
        fetched_data = cur.fetchall()

    all_stats = [row[0] for row in fetched_data]
    return jsonify(all_stats)

@app.route("/logs", methods=["POST"])
def receive_logs():
    data = request.data
    try:
        with conn.cursor() as cur:
            # Delete logs that are older than 24 hours
            yesterday = datetime.now() - timedelta(hours=24)
            cur.execute("DELETE FROM logs WHERE created_at < %s", (yesterday,))
            # Insert the new log into the database
            cur.execute("INSERT INTO logs (data) VALUES (%s) LIMIT 1", (data,))
            conn.commit()
    except Exception as e:
        # Roll back the transaction in case of an error
        conn.rollback()
        print(f"Error: {e}")
        return "Error", 500
    return 'OK', 200


@app.route('/logs')
def get_logs():
    # Query the logs table in the database
    with conn.cursor() as cur:
        cur.execute("SELECT data FROM logs LIMIT 1")
        rows = cur.fetchall()
    # Combine all the log data into a single string
    data = '\n'.join([row[0] for row in rows])
    return render_template("logs.html", data=data)


def update_stats():
    url = "https://loyalty.yotpo.com/api/v1/customer_details?customer_email=lukee249%40outlook.com&customer_external_id=5755791442114&merchant_id=58315"
    s = requests.get(url)
    d1 = json.dumps(s.json())
    data = json.loads(d1)
    dollarPtBal = float(data['points_balance'])/10
    referrals = int(data['vip_tier_stats']['referrals_completed'])+1
    todaydate = str(date.today()) 
    return dollarPtBal, referrals, todaydate

def run_script():
    global current_stats

    while True:
        dollarPtBal, referrals, todaydate = update_stats()
        current_stats = {
                'Date':todaydate,
                'Referrals:':referrals,
                'Rewards:':dollarPtBal   
            }

        with conn.cursor() as cur:
            cur.execute("SELECT data FROM stats ORDER BY id DESC LIMIT 1;")
            fetched_result = cur.fetchone()
            if fetched_result is None:
                last_session = None
            else:
                last_session = fetched_result[0]
            print(last_session, "Last session")
        
        if last_session is None or current_stats != last_session:
            if last_session and last_session.get('Rewards:'):
                reward_diff = dollarPtBal - last_session['Rewards:']
                if int(reward_diff) != 0:
                    print("Text sent!")
                    print(reward_diff, dollarPtBal)
                    SMS.send(message=f'\n{"%.2f" % round(reward_diff, 2)} more in rewards, total ${"%.2f" % round(dollarPtBal, 2)}')

            with conn.cursor() as cur:
                cur.execute("INSERT INTO stats (data) VALUES (%s);", (json.dumps(current_stats),))
                conn.commit()
                print("Updated stats\n")

        else:
            print('\n\nno update\n')

        time.sleep(1800)

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    script_thread = threading.Thread(target=run_script)
    script_thread.start()
    run_flask()