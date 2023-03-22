import SMS
import requests
import json
import time
from datetime import date
import os
import threading
from flask import Flask, render_template, url_for, jsonify


app = Flask(__name__)

current_stats = None

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route("/")
def home():
    if current_stats is None:
        message = "Please wait for the script to run at least once"
        print("Idk why this isnt working",flush=True)
    else:
        print("For some reason this wont update!",flush=True)
        message = f"Date: {current_stats['Date']}, Referrals: {current_stats['Referrals:']}, Rewards: {current_stats['Rewards:']}"

    return render_template("index.html", message=message, css=url_for("static", filename="styles.css"), time=time, current_stats=current_stats)

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
        
        with open('log.json', 'r') as log:
            last_session = json.load(log)

        if current_stats != last_session:
            if last_session.get('Rewards:'):
                reward_diff = dollarPtBal - last_session['Rewards:']
                referral_diff = referrals - int(last_session['Referrals:'])
                if int(reward_diff) != 0:
                    print("Text sent!")
                    print(reward_diff, dollarPtBal)
                    SMS.send(message=f'\n{"%.2f" % round(reward_diff, 2)} more in rewards, total ${"%.2f" % round(dollarPtBal, 2)}')

            else:
                log = open('log.json', 'w').close()  # Clears file

                with open('log.json', 'a') as log:
                    log.write(json.dumps(current_stats, indent=4, sort_keys=True, default=str))
                    log.flush()
                with open('log.json', 'r') as log:  # Opening in read to reset last_session to proper val
                    last_session = json.load(log)

                print("\n\n--Last session JSON not valid, wrote new.--")

            with open('ref.txt', 'a') as ref:  # Adds outdated info to txt for reference
                ref.write(f"{str(last_session)},\n")
                ref.flush()
                ref.close()
                print("\nRef updated")

            log = open('log.json', 'w').close()

            current_stats = {
                'Date':todaydate,
                'Referrals:':referrals,
                'Rewards:':dollarPtBal   
            }

            with open('log.json', 'a') as log:
                log.write(json.dumps(current_stats, indent=4, sort_keys=True, default=str))
                log.flush()
                log.close()
                print("Updated json\n")

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
