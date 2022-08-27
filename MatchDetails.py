from selenium.webdriver.common.by import By
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import unicodedata
import re
from DriverUtility import DriverUtility
import time
from tqdm import tqdm

class HomePage(DriverUtility):
    
    def __init__(self, driver):
        self.driver = driver
        super(HomePage, self).__init__(self.driver)
        self.baseball_menu_css_selector = "div.fdjgs-sport[data-sport='Baseball']"
        self.baseball_submenu_css_selector = "li.fdjgs-item[aria-label*='USA']"
        self.baseball_submenu2_link_text = "MLB"
        self.matches_menu_id = "middle-col"
        self.team_name_class = "fdjgs-event-details"
        self.match_link_class = "fdjgs-market-counter"
        self.match_date_class = "fdjgs-event-time"
#         self.maches_section_xpath = '//*[@id="fdjgs-widget-competition"]/div/div/div[2]/div[2]/section'
        
    def load_matches_page(self):
        baseball_menu = super().get_locator(By.CSS_SELECTOR, self.baseball_menu_css_selector)
        super().perform_actions(baseball_menu)
        baseball_submenu = super().get_locator(By.CSS_SELECTOR, self.baseball_submenu_css_selector)
        super().perform_actions(baseball_submenu)
        baseball_submenu2 = super().get_locator(By.LINK_TEXT, self.baseball_submenu2_link_text)
        super().perform_actions(baseball_submenu2)
        super().get_locator(By.ID, self.matches_menu_id)
        
    def get_team_names(self, match_info):
        return match_info.find('div', class_=self.team_name_class).a.get_text(strip=True).split('@')
    
    def get_match_link(self, match_info):
        return match_info.find('div', class_=self.match_link_class).a['href']
        
    def get_match_date_time(self, match_info):
        return unicodedata.normalize("NFKD", match_info.find('span', class_=self.match_date_class).get_text(strip=True)).split('|')
        
        
class MatchPage(DriverUtility):
    
    def __init__(self, driver):
        self.driver = driver
        super(MatchPage, self).__init__(self.driver)
        self.match_stats_section_css_selector = "ul.fdjgs-markets"
        self.runline_class = "fdjgs-market-description"
        self.runline_subclass = "fdjgs-description"
        self.stats_section_xpath = '//*[@id="fdjgs-widget-market-display"]/div/section'
        
    def load_match_stats_page(self):
#         super().get_locator(By.CSS_SELECTOR, self.match_stats_section_css_selector)
        super().get_locator(By.XPATH, self.stats_section_xpath)
        
    def get_runline_info(self, all_stats, v_team, h_team):
        runline_stats = all_stats.find("span", class_= self.runline_class, string="Runline").parent.parent
        teams_runline = runline_stats.find_all("span", class_= self.runline_subclass)
        visitor_team_runline = teams_runline[0].string.strip().strip(v_team)
        home_team_runline = teams_runline[1].string.strip().strip(h_team)
        # Getting odds
        odds_runline = runline_stats.find_all("span", class_="fdjgs-price")
        visitor_runline_odds = odds_runline[0].string.strip()
        home_runline_odds = odds_runline[1].string.strip()
        runline_dict = {
            "visitor_runline":visitor_team_runline,
            "home_runline":home_team_runline,
            "visitor_odds":visitor_runline_odds,
            "home_odds":home_runline_odds
        }
        return runline_dict
    
    def get_runline_3way_info(self, all_stats):
        runline_3way_stats = all_stats.find("span", class_=self.runline_class, string="Runline 3-Way").parent.parent
        runline_3way_draw = runline_3way_stats.find("span", class_="fdjgs-description", string=lambda text: "Draw" in text)
        draw_str = runline_3way_draw.string
        runline_3_way_dict = {
            "runline_3_way": re.findall('\((.*?)\)', draw_str)[0].strip(),
            "odds": runline_3way_draw.next_sibling.string.strip()
        }
        return runline_3_way_dict

    
class MatchDetails:
   
    def __init__(self, driver):
        self.driver = driver
        self.visitor_teams = []
        self.home_teams = []
        self.match_date = []
        self.match_time = []
        self.main_url = "https://proline.olg.ca"
        self.home_team_runline = []
        self.visitor_team_runline = []
        self.runline_3_way = []
        self.home_runline_odds = []
        self.visitor_runline_odds = []
        self.runline_3_way_odds = []

    def get_match_details(self):
        # load and locate individual matches locator
        home_page = HomePage(self.driver)
        home_page.load_matches_page()
        time.sleep(5)
        # get the html using BeautifulSoup
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        results = soup.find(id=home_page.matches_menu_id)
#         print(results)
#         exit()
        section = results.section
#         print(section)
        # list of all matches to iterate over
        matches = section.find_all('article')
        # iterate over each match to read team names, match timing and 
        # individual match link for runline info collection
        match_page = MatchPage(self.driver)
        for match in tqdm(matches):
            match_date_time = home_page.get_match_date_time(match)
            teams = home_page.get_team_names(match)
            match_link = home_page.get_match_link(match)
            v_team = teams[0].strip()
            h_team = teams[1].strip()
            self.match_date.append(match_date_time[0].strip())
            self.match_time.append(match_date_time[1].strip())
            self.visitor_teams.append(v_team)
            self.home_teams.append(h_team)
            match_link = self.main_url + match_link
            # Open each match link to collect runline info and in the end
            # close the match link tab
            # open new tab
            self.driver.execute_script("window.open('');")
            # switch to new tab and open match link
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.get(match_link)
            match_page.load_match_stats_page()
            # get the html using BeautifulSoup
#             time.sleep(5)
            match_page_source = self.driver.page_source
            match_soup = BeautifulSoup(match_page_source, "html.parser")
            all_stats = match_soup.find('ul', class_="fdjgs-markets")
            try:
              # get runline info
              # TODO: Handle condition if event does not have odds info added
              runline_dict = match_page.get_runline_info(all_stats, v_team, h_team)
              self.visitor_team_runline.append(runline_dict["visitor_runline"])
              self.home_team_runline.append(runline_dict["home_runline"])
              self.visitor_runline_odds.append(runline_dict["visitor_odds"])
              self.home_runline_odds.append(runline_dict["home_odds"])
              # get 3 way runline info
              runline_3_way_dict = match_page.get_runline_3way_info(all_stats)
              self.runline_3_way.append(runline_3_way_dict["runline_3_way"])
              self.runline_3_way_odds.append(runline_3_way_dict["odds"])
              self.driver.close()
              self.driver.switch_to.window(self.driver.window_handles[0])
            except:
              self.match_date.pop(-1)
              self.match_time.pop(-1)
              self.visitor_teams.pop(-1)
              self.home_teams.pop(-1)
        
        match_info_dict = {
                "Match Date": self.match_date,
                "Match Time": self.match_time,
                "Visitor Team": self.visitor_teams,
                "Home Team": self.home_teams,
                "home_team_runline": self.home_team_runline,
                "visitor_team_runline": self.visitor_team_runline,
                "runline_3_way": self.runline_3_way,
                "home_runline_odds": self.home_runline_odds,
                "visitor_runline_odds": self.visitor_runline_odds,
                "runline_3_way_odds": self.runline_3_way_odds
            }
        return match_info_dict