from selenium import webdriver
import datetime
import pandas as pd
from RankingDetails import RankingDetails
from Email import Email
from MatchDetails import MatchDetails
import time
from pytz import timezone
tz = timezone('Canada/Eastern')
# print(pytz.all_timezones)
# import sys
# sys.path.insert(0, r'C:\Users\swapn\proline\chromedriver.exe')
import chromedriver_autoinstaller as chromedriver

         
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--start-maximized')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--window-size=1920,1080")

PROLINE_URL = "https://proline.olg.ca/en-ca/"
DRATING_URL = "https://www.dratings.com/sports/mlb-baseball-ratings/"

def final_table(match_info_dict, rank_info_dict):
    home_teams = match_info_dict['Home Team']
    visitor_teams = match_info_dict['Visitor Team']
    home_team_runline = match_info_dict.pop("home_team_runline")
    visitor_team_runline = match_info_dict.pop("visitor_team_runline")
    runline_3_way = match_info_dict.pop("runline_3_way") 
    home_runline_odds = match_info_dict.pop("home_runline_odds")
    visitor_runline_odds = match_info_dict.pop("visitor_runline_odds")
    runline_3_way_odds = match_info_dict.pop("runline_3_way_odds")
    
    pl = []
    diff = []
    po = []
    for i in range(len(visitor_teams)):
        # favourite team:  team having - sign in runline is favourite 
        # team
        if '-' in home_team_runline[i]:
            pl.append('H '+ home_team_runline[i])
            po.append(home_runline_odds[i])
        else:
            pl.append('V '+ visitor_team_runline[i])
            po.append(visitor_runline_odds[i])
        if visitor_teams[i] in runline_3_way[i]:
            diff.append('V '+ runline_3_way[i].strip(visitor_teams[i]))
        elif home_teams[i] in runline_3_way[i]:
            diff.append('H '+ runline_3_way[i].strip(home_teams[i]))
    
    pl_info = {
            "PL":pl,
            "PO": po,
            "Diff":diff,
            "Diff_PO":runline_3_way_odds
        }
    match_info_dict.update(pl_info)
    match_info_dict.update(rank_info_dict)
    return match_info_dict


def utcnow():
    return datetime.datetime.now(tz=tz)

start_time = time.time()
utc = utcnow()

driver = webdriver.Chrome(chromedriver.install(), options=chrome_options)
driver.implicitly_wait(20)
driver.get(PROLINE_URL)

print("Getting Match Details")
match_detail = MatchDetails(driver)
match_info_dict = match_detail.get_match_details()
print("Getting Match Details Complete")
 
# open new tab
driver.execute_script("window.open('');")
# switch to new tab and open match link
driver.switch_to.window(driver.window_handles[-1])
driver.get(DRATING_URL)

print("Getting Rank Details")
rank_detail = RankingDetails(driver)
rank_info_dict = rank_detail.get_team_ranks(match_info_dict)
driver.quit()
print("Getting Rank Details Complete")

info_dict = final_table(match_info_dict, rank_info_dict)
df = pd.DataFrame(info_dict)

# Save file with datetime stamp
dt =  utc.strftime("%Y_%m_%d_%H_%M_%S")
filename = "mlb_matches_"+ dt +".xlsx"
df.to_excel(filename, index=False, sheet_name='MLB')

print("Sending an Email:")
email = Email()
with open('PASSWD.txt','r') as f:
    PASSWD = f.read() 
    
with open('EMAILTO.txt','r') as f:
    TO = f.read() 

dt =  utc.strftime("%d %b %Y, %H:%M")
subject = "List for " + dt
user_name = "swapnilrajjoshi@gmail.com"
to = TO

password = PASSWD
file_path = filename
email.send_email(subject, user_name, to, password, file_path)

time_taken = time.time() - start_time
print("Time: {}".format(time_taken/60))