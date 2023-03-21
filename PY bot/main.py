import tkinter as tk
from tkinter import ttk
import praw
import requests
from urllib.request import *
import json
from datetime import date
import webbrowser as fireFox
from ctypes import windll
from datetime import datetime
import itertools as IT
windll.shcore.SetProcessDpiAwareness(1) #Reduce text blur
import concurrent

class MainClass(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self)

        self.pane_1 = ttk.PanedWindow(self)
        self.pane_1.grid(row=0, column=1, pady=(25, 5), sticky="nsew", rowspan=3)

        self.frame_1 = ttk.Frame(self.pane_1, padding=5)
        self.pane_1.add(self.frame_1, weight=1)

        self.welcome_label = ttk.Label(
            self.frame_1,
            text="Welcome, Luke!",
            font="Arial 20 bold")
        self.welcome_label.pack(anchor="sw")

        self.reward_label = ttk.Label(
            self.frame_1,
            text="null Rewards!",
            font="Arial 10"
        )
        self.reward_label.pack(anchor='e')

        self.widgets_frame = ttk.Frame(self, padding=(0, 0, 0, 10))
        self.widgets_frame.grid(
            row=0, column=0, padx=10, pady=(30, 10), sticky="nsew", rowspan=3
        )
        self.widgets_frame.columnconfigure(index=0, weight=1)
        
        self.treeview_scrollbar = ttk.Scrollbar(self.frame_1)
        self.treeview_scrollbar.pack(side="right", fill="y")

        s = ttk.Style()
        s.configure('Treeview',rowheight=25)
        s.configure('Combobox.button',hightlightthickness=10,highlightcolor='white')

        self.treeview = ttk.Treeview(
            self.frame_1,
            selectmode="browse",
            yscrollcommand=self.treeview_scrollbar.set,
            columns=(0,1,2),
            height=10,
            show='headings'
        )

        self.treeview.pack(expand=True,fill="both")
        self.treeview_scrollbar.config(command=self.treeview.yview)

        self.treeview.heading(0, text="#", anchor="center")
        self.treeview.heading(1, text="Title", anchor="center")
        self.treeview.heading(2, text="Sub", anchor="center")

        self.treeview.column(0, anchor="w", width=25)
        self.treeview.column(1, anchor="w", width=400)
        self.treeview.column(2, anchor="w", width=100)

        self.timeFilter_options = ['day','week','month']
        self.timeFilter_currval = tk.StringVar(root)
        self.limit_options = [0,10,25,50]
        self.limit_currval = tk.StringVar(root)

        self.refresh_button = ttk.Button(
            self.widgets_frame, text="Refresh", style="Accent.TButton",command=self.mainfunc
        )
        self.refresh_button.grid(row=7, column=0, padx=5, pady=10, sticky="nsew")

        self.time_filter_menu = ttk.OptionMenu(
            self.widgets_frame, self.timeFilter_currval, "Time filter", *self.timeFilter_options
        )
        self.time_filter_menu.grid(row=5, column=0, padx=5, pady=10, sticky="nsew")

        self.limit_filter_menu = ttk.OptionMenu(self.widgets_frame, self.limit_currval, 'Limit', *self.limit_options)
        self.limit_filter_menu.grid(row=6, column=0, padx=5, pady=10, sticky="nsew")

    def login(self):
        reddit = praw.Reddit(
                client_id="bkOkm_ElnKpNGOS9-Fk1GQ",
                client_secret="pu8XcuEtOTRsyBVBgO5pJ6lRpi78dg",
                password="overluke123",
                user_agent="BullstrapTest",
                username="methwaves",
            )
        return reddit
    
    def api_access(self):
        start = datetime.now()
        url = "https://loyalty.yotpo.com/api/v1/customer_details?customer_email=lukee249%40outlook.com&customer_external_id=5755791442114&merchant_id=58315"
        s = requests.get(url)
        d1 = json.dumps(s.json())
        data = json.loads(d1)
        dollar_pointbal = float(data['points_balance'])/10
        referrals = int(data['vip_tier_stats']['referrals_completed'])+1
        self.reward_label.config(text=f"You have ${dollar_pointbal} in rewards! -- {referrals} referrals\n\t\t${referrals*15} lifetime")

        current_stats = {
            'Date':str(date.today()),
            'Referrals:':referrals,
            'Rewards:':dollar_pointbal   
        }
        json_log = 'PY bot/log.json'
        #Load last session JSON file 
        with open(json_log,'r') as log:
            last_session = json.load(log)

        if current_stats != last_session:
            if last_session.get('Rewards:'):
                reward_diff = current_stats['Rewards:']-last_session['Rewards:']
                referral_diff = current_stats['Referrals:']-int(last_session['Referrals:'])
                if reward_diff != 0:
                    print(f"\n${reward_diff} more in rewards and {referral_diff} more referrals!")

            else:
                log = open(json_log,'w').close() #Clears file

                with open(json_log,'a') as log:
                    log.write(json.dumps(current_stats,indent=4,sort_keys=True,default=str))
                with open(json_log,'r') as log: # Opening in read to reset last_session to proper val
                    last_session = json.load(log)       
                    
                print("\n\n--Last session JSON not valid, wrote new.--")
            
            with open('PY bot/ref.txt','a') as ref: #Adds outdated info to txt for reference
                ref.write(f"{str(last_session)},\n")
                print("\nRef updated")

            log = open(json_log,'w').close() 

            with open(json_log,'a') as log:
                log.write(json.dumps(current_stats,indent=4,sort_keys=True,default=str))
                print("Updated json\n")

        else:
            print("\nNo update on rewards yet!\n")
        print(f"API ACCESS: {datetime.now()-start}")

    def run_bot(self,r):
        start = datetime.now()
        if self.timeFilter_currval.get() in self.timeFilter_options and int(self.limit_currval.get()) in self.limit_options:
            self.treeview.delete(*self.treeview.get_children())
            self.info_list = []
            self.c_count = 0

            with open('PY bot/sublist.json','r') as srlist:
                js = json.load(srlist)
                for item in js:
                    self.searchfunc(js[item]['Search'],js[item]['Subreddit'])

            newlist = []
            for item in self.info_list:
                itemlist = list(item)  
                if itemlist[0] not in newlist:                
                    self.treeview.insert('',tk.END,values=(itemlist[0],itemlist[1],itemlist[2]),text=f"https://www.reddit.com{itemlist[3]}")
                    newlist.append(itemlist[0])

            #highlight first item
            if len(self.treeview.get_children()) > 0:
                print("List updated!")
                child_id = self.treeview.get_children()[0]
                self.treeview.selection_set(child_id)               
            else:
                self.treeview.insert('',tk.END,values=('-','0 posts found','-'))
            def selectItem(a):
                curitem = self.treeview.focus()
                fireFox.open(self.treeview.item(curitem)['text'])
            self.treeview.bind('<Double-1>',selectItem)
        else:
            print("Please choose a time filter and limit")
        print(f"RUNBOT: {datetime.now()-start}")

    def searchfunc(self, search_term,sub_name):
        r = self.login()
        sub = r.subreddit(sub_name)
        # Create a list of posts to process in parallel
        posts_to_process = [
            post
            for post in sub.search(search_term, sort="new", time_filter=self.timeFilter_currval.get(), limit=int(self.limit_currval.get()))
        ]
        # Create a pool of threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Start a thread for each post
            for post in posts_to_process:
                executor.submit(self.process_post, post)

    def process_post(self, post):
        post.comments.replace_more(limit=0)

        already = (self.c_count,f'*{post.title[:50]}',str(post.subreddit),post.permalink)
        notcom = (self.c_count,post.title[:50],str(post.subreddit),post.permalink)

        comment_author = [comment.author for comment in post.comments]
        if 'methwaves' in comment_author:
            self.info_list.append(already)
        self.info_list.append(notcom)
        self.c_count += 1

    def mainfunc(self):
            r = self.login()
            print('Logged in Reddit')
            self.api_access()
            self.run_bot(r)

if __name__ == "__main__":
    root = tk.Tk()

    root.title("BullstrapBot")
    root.tk.call("source", "Azure-ttk-theme/azure.tcl")
    root.tk.call("set_theme", "dark")

    app = MainClass(root)
    app.pack(fill="both", expand=True)

    root.resizable(0,0)
    root.eval('tk::PlaceWindow . center')
    root.mainloop()