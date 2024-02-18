from selenium import webdriver
import datetime
import pandas as pd
from RankingDetails import RankingDetails
from Email import Email
from MatchDetails import MatchDetails
import time
from pytz import timezone
tz = timezone('Canada/Eastern')
import chromedriver_autoinstaller as chromedriver
import pandas as pd
from openpyxl import load_workbook
import numpy as np
import os
        
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--start-maximized')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--window-size=1920,1080")

PROLINE_URL = "https://proline.olg.ca/en-ca/"
DRATING_MLB_URL = "https://www.dratings.com/sports/mlb-baseball-ratings/"
DRATING_NFL_URL = "https://www.dratings.com/sports/nfl-football-ratings/"
DRATING_NCAA_URL = "https://www.dratings.com/sports/ncaa-fbs-football-ratings/"
DRATING_NCAA_B_URL = "https://www.dratings.com/sports/ncaa-college-basketball-ratings/"
DRATING_NBA_URL = "https://www.dratings.com/sports/nba-basketball-ratings/"
DRATING_NHL_URL = "https://www.dratings.com/sports/nhl-hockey-ratings/"

def utcnow():
    return datetime.datetime.now(tz=tz)


start_time = time.time()
utc = utcnow()
# Save file with datetime stamp
dt =  utc.strftime("%Y_%m_%d_%H_%M_%S")
dt_list = dt.split("_")
print("\nRun for :", dt)
#filename = "/home/ec2-user/olg/output_files/list_for_"+ dt +".xlsx"
filename = os.path.join("/home/ec2-user/olg/output_files/",dt_list[0],dt_list[1],"list_for_"+ dt +".xlsx")
os.makedirs(os.path.dirname(filename), exist_ok=True)
#sports = [("Baseball", "MLB", DRATING_MLB_URL), ("Football", "NFL", DRATING_NFL_URL), ("Football","NCAA Football", DRATING_NCAA_URL)]
sports = [("Football", "NFL", DRATING_NFL_URL), ("Football","NCAA Football", DRATING_NCAA_URL), 
          ("Basketball","NCAA Basketball", DRATING_NCAA_B_URL), 
          ("Basketball","NBA", DRATING_NBA_URL), ("Hockey", "NHL", DRATING_NHL_URL),("Baseball", "MLB", DRATING_MLB_URL)]
df_dict = {}
#sports = [("Football", "NFL", DRATING_NFL_URL)]
for i, league in enumerate(sports):
    try:
        driver = webdriver.Chrome(chromedriver.install(), options=chrome_options)
        driver.implicitly_wait(20)
        driver.get(PROLINE_URL)
        time.sleep(10)
        # Hockey is at the end of the page. Need scrolling
        driver.execute_script("window.scrollTo(0,300)")
        print("Getting Match Details of {}".format(league[1]))
        match_detail = MatchDetails(driver,league[0], "USA", league[1])
        match_info_dict = match_detail.get_match_details()
        print("Getting Match Details Complete")
        print("Getting Rank Details of {}".format(league[1]))
        # open new tab
        driver.execute_script("window.open('');")
        # switch to new tab and open match link
        driver.switch_to.window(driver.window_handles[-1])
        driver.get(league[2])
        rank_detail = RankingDetails(driver)
        rank_info_dict = rank_detail.get_team_ranks(match_info_dict)  
        print("Getting Rank Details Complete")
        match_info_dict.update(rank_info_dict)
        df_dict[league[1]] = match_info_dict
    except Exception as e:
        print(e)
    driver.quit()

for i,(league, info) in enumerate(df_dict.items()):
    df = pd.DataFrame(info)
    if i==0:
        df = pd.DataFrame(info)
        df.to_excel(filename, index=False, sheet_name=league)
    else:
        ExcelWorkbook = load_workbook(filename)
        # Generating the writer engine
        writer = pd.ExcelWriter(filename, engine = 'openpyxl')
        # Assigning the workbook to the writer engine
        writer.book = ExcelWorkbook
        df = pd.DataFrame(info)
        df.to_excel(writer, index=False, sheet_name=league)
        writer.save()
        writer.close()

print("Sending an Email")
email = Email()
with open('/home/ec2-user/olg/web_scraping/PASSWD.txt','r') as f:
    PASSWD = (f.read()).rstrip()
    
with open('/home/ec2-user/olg/web_scraping/EMAILTO.txt','r') as f:
    TO = (f.read()).rstrip()

dt =  utc.strftime("%d %b %Y, %H:%M")
subject = "List for " + dt
user_name = "swapnilrajjoshi@gmail.com"
#TO = "swapnilrajjoshi@gmail.com"

file_path = filename
email.send_email(subject, user_name, TO, PASSWD, file_path)

time_taken = time.time() - start_time
print("Time: {}".format(time_taken/60))
