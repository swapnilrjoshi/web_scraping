from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import unicodedata
from DriverUtility import DriverUtility
import time
from tqdm import tqdm
import re
from fuzzywuzzy import process
from fuzzywuzzy import fuzz

class DrankPage(DriverUtility):
    
    def __init__(self, driver):
        self.driver = driver
        super(DrankPage, self).__init__(self.driver)
        self.ranking_table_css_selector = "tbody.table-body"
        
    def load_drank_page(self):
        super().get_locator(By.CSS_SELECTOR, self.ranking_table_css_selector)
        
#    def get_team_rank(self, table, team_name):
#        return unicodedata.normalize("NFKD", table.find('a', string=team_name).parent.get_text(strip=True)).strip().split('.')[0]
        

class RankingDetails:
    def __init__(self, driver):
        self.driver = driver
        self.home_rank = []
        self.visitor_rank = []
        self.rank_summary = []
        
    def get_team_rank(self, team_name):
        table_team_name = process.extractOne(team_name, self.team_rank_list, scorer=fuzz.token_sort_ratio, score_cutoff = 70)
        if not table_team_name:
            return 9999
        else:
            return self.team_rank_list.index(table_team_name[0])+1
    
    def get_team_ranks(self, match_info_dict):
        rank_detail = DrankPage(self.driver)
        rank_detail.load_drank_page()  
        time.sleep(5)
        drating_soup = BeautifulSoup(self.driver.page_source, "html.parser")
        ranking_table = drating_soup.find('tbody', class_='table-body')
        
        # Creating a list of all teams in ranking table in that order
        self.team_rank_list = []
        for r in ranking_table.findAll('a'):
            self.team_rank_list.append(r.string)
            
        home_teams = match_info_dict['Home Team']
        visitor_teams = match_info_dict['Visitor Team']

        for h_team, v_team in zip(home_teams, visitor_teams):
            if "(" in h_team:
                h_team = re.sub(' +', ' ', re.sub("\(.*?\)","", h_team)) # 1st sub removes extra space created by 2nd sub between words
            if "(" in v_team:
                v_team = re.sub(' +', ' ', re.sub("\(.*?\)","",v_team))
#            try:
#                h_rank = int(rank_detail.get_team_rank(ranking_table, h_team))
#            except:
#                #if rank is not found assign it with default big value
#                h_rank = 9999
#            try:
#                v_rank = int(rank_detail.get_team_rank(ranking_table, v_team))
#            except:
#                v_rank = 9999
            h_rank = int(self.get_team_rank(h_team))
            v_rank = int(self.get_team_rank(v_team))
            self.home_rank.append(h_rank)
            self.visitor_rank.append(v_rank)
            if h_rank > v_rank:
                low_rank_team = "V"
            else:
                low_rank_team = "H"
            team_rank_diff = abs(v_rank-h_rank)
            if team_rank_diff < 4:
                rank_diff_summary = ","+"T"*(4-team_rank_diff)
            elif (team_rank_diff >= 10) and (team_rank_diff < 15):
                rank_diff_summary = "+"
            elif (team_rank_diff >= 15) and (team_rank_diff < 20):
                rank_diff_summary = "++"
            elif (team_rank_diff >= 20):
                rank_diff_summary = "+++"
            else:
                rank_diff_summary = ""
            self.rank_summary.append(low_rank_team + rank_diff_summary)
        
        # close drank tab 
        self.driver.close()  
        rank_info_dict = {
                "V Rank": self.visitor_rank,
                "H Rank": self.home_rank,
                "Rank": self.rank_summary 
            }
        return rank_info_dict
