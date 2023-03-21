import SMS
import requests
import json
import time
from datetime import date
import os

recipient = '6154892677'  # Update with your recipient's phone number
sms_api_key = os.environ['SMS_API_KEY']  # Get the SMS API key from environment variables

url = "https://loyalty.yotpo.com/api/v1/customer_details?customer_email=lukee249%40outlook.com&customer_external_id=5755791442114&merchant_id=58315"
s = requests.get(url)
d1 = json.dumps(s.json())
data = json.loads(d1)
dollarPtBal = float(data['points_balance'])/10
referrals = int(data['vip_tier_stats']['referrals_completed'])+1
todaydate = str(date.today()) 
current_stats = {
    'Date':todaydate,
    'Referrals:':referrals,
    'Rewards:':dollarPtBal   
}

while True:

    with open('log.json','r') as log:
        last_session = json.load(log)

    if current_stats != last_session:
        if last_session.get('Rewards:'):
            reward_diff = current_stats['Rewards:']-last_session['Rewards:']
            referral_diff = current_stats['Referrals:']-int(last_session['Referrals:'])
            if int(reward_diff) != 0:
                print("Text sent!")
                print(reward_diff,dollarPtBal)
                SMS.send(api_key=sms_api_key, message=f'\n{"%.2f" % round(reward_diff, 2)} more in rewards, total ${"%.2f" % round(dollarPtBal, 2)}', recipients=[recipient])

        else:
            log = open('log.json','w').close() #Clears file

            with open('log.json','a') as log:
                log.write(json.dumps(current_stats,indent=4,sort_keys=True,default=str))
            with open('log.json','r') as log: # Opening in read to reset last_session to proper val
                last_session = json.load(log)       
                
            print("\n\n--Last session JSON not valid, wrote new.--")
        
        with open('ref.txt','a') as ref: #Adds outdated info to txt for reference
            ref.write(f"{str(last_session)},\n")
            print("\nRef updated")

        log = open('log.json','w').close() 

        with open('log.json','a') as log:
            log.write(json.dumps(current_stats,indent=4,sort_keys=True,default=str))
            print("Updated json\n")
            
    else:
        print('\n\nno update\n')
        
    time.sleep(300)
   