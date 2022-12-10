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
        self.matches_menu_id = "middle-col"
        self.team_name_class = "fdjgs-event-details"
        self.match_link_class = "fdjgs-market-counter"
        self.match_date_class = "fdjgs-event-time"

        
    def load_matches_page(self, sport, country, league):
        main_menu_css_selector = "div.fdjgs-sport[data-sport='"+sport+"']"
      # submenu_css_selector = "li.fdjgs-item[aria-label*='"+country+"']"
        submenu_css_selector = "li.fdjgs-item[aria-label*='"+country+"'][aria-label$='"+sport+".']"
        submenu2_link_text = "div.fdjgs-item-description>a[aria-label*='"+ league +".']"
        main_menu = super().get_locator(By.CSS_SELECTOR, main_menu_css_selector)
        super().perform_actions(main_menu)
        submenu = super().get_locator(By.CSS_SELECTOR, submenu_css_selector)
        super().perform_actions(submenu)
#        time.sleep(2)
        submenu2 = super().get_locator(By.CSS_SELECTOR, submenu2_link_text)
        super().perform_actions(submenu2)
        time.sleep(4)
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
      # self.match_stats_section_css_selector = "ul.fdjgs-markets"
        self.stats_section_xpath = '//*[@id="fdjgs-widget-market-display"]/div/section'
        
    def load_match_stats_page(self):
#         super().get_locator(By.CSS_SELECTOR, self.match_stats_section_css_selector)
      super().get_locator(By.XPATH, self.stats_section_xpath)

    def get_runline_info(self, all_stats, v_team, h_team):
        runline_stats = all_stats.find("span", class_= "fdjgs-market-description", string="Runline").parent.parent
        teams_runline = runline_stats.find_all("span", class_= "fdjgs-description")
        visitor_team_runline = teams_runline[0].string.strip().strip(v_team)
        home_team_runline = teams_runline[1].string.strip().strip(h_team)
        # Getting payout(odds)
        odds_runline = runline_stats.find_all("span", class_="fdjgs-price")
        visitor_runline_odds = odds_runline[0].string.strip()
        home_runline_odds = odds_runline[1].string.strip()
        runline_dict = {
          "v_runline":visitor_team_runline,
          "h_runline":home_team_runline,
          "v_runline_po":visitor_runline_odds,
          "h_runline_po":home_runline_odds
          }
        return runline_dict
        
    def get_moneyline_info(self, all_stats):
        moneyline_stats = all_stats.find("span", class_="fdjgs-market-description", string="Moneyline").parent.parent
        teams_moneyline = moneyline_stats.find_all("li", class_="fdjgs-outcome")
        moneyline_info = []
        for team in teams_moneyline:
            if team['data-hidden'] == 'true':
                moneyline_info.append('NA')
            else:
                wrapper = team.find("span", class_="fdjgs-outcome-wrapper")
                if 'suspended' in wrapper['aria-label']:
                    moneyline_info.append('suspended')
                else:
                    moneyline_info.append(wrapper.find("span", class_="fdjgs-price").string.strip())
        moneyline_dict = {
                  "v_moneyline":moneyline_info[0],
                  "h_moneyline":moneyline_info[1]
              }
        return moneyline_dict

    def get_ps_info(self, all_stats, v_team, h_team, search_str="Point Spread"):
        ps_stats = all_stats.find("span", class_="fdjgs-market-description", string=search_str).parent.parent
        teams_ps = ps_stats.find_all("li", class_="fdjgs-outcome")
        ps_info = []
        for team in teams_ps:
            if team['data-hidden'] == 'true':
                ps_info.append(tuple(('NA','NA')))
            else:
                wrapper = team.find("span", class_="fdjgs-outcome-wrapper")
                if 'suspended' in wrapper['aria-label']:
                    ps_info.append(tuple(('suspended','suspended')))
                else:
                    ps = wrapper.find("span", class_="fdjgs-description").string.strip()
                    po = wrapper.find("span", class_="fdjgs-price").string.strip()
                    ps_info.append(tuple((ps, po)))
        ps_dict = {
          "v_ps":ps_info[0][0].replace(v_team,''),
          "h_ps":ps_info[1][0].replace(h_team,''),
          "v_ps_po":ps_info[0][1],
          "h_ps_po":ps_info[1][1]
          }
        return ps_dict

    def get_3way_info(self, all_stats, v_team, h_team, search_str):
        ps_3way_stats = all_stats.find("span", class_="fdjgs-market-description", string=search_str).parent.parent
        ps_3way_draw = ps_3way_stats.find("span", class_="fdjgs-description", string=lambda text: "Draw" in text)
        draw_str = ps_3way_draw.string
        if ps_3way_stats['data-hidden'] == 'true':
            ps_3way_dict = {
              "spread": 'NA',
              "spread_po": 'NA'
            }
        elif 'suspended' in ps_3way_draw.parent['aria-label']:
            ps_3way_dict = {
              "spread": 'suspended',
              "spread_po": 'suspended'
            }
        else:
            ps_3way_str = re.findall('\((.*?)\)', draw_str)[0].strip()
        if v_team in ps_3way_str:
            ps_3way  = 'V ' + ps_3way_str.strip(v_team)
        else:
            ps_3way  = 'H ' + ps_3way_str.strip(h_team)
        ps_3way_dict = {
            "spread": ps_3way,
            "spread_po": ps_3way_draw.next_sibling.string.strip()
        }
        return ps_3way_dict

class MatchDetails:  
    def __init__(self, driver, sport, country, league):
        self.driver = driver
        self.sport = sport
        self.country = country
        self.league = league
        self.visitor_teams = []
        self.home_teams = []
        self.match_date = []
        self.match_time = []
        self.main_url = "https://proline.olg.ca"
        self.h_moneyline = []
        self.v_moneyline = []
        self.h_ps = []
        self.v_ps = []
        self.h_ps_po = []
        self.v_ps_po = []
        self.ps_3way = []
        self.ps_3way_po = []
        self.h_runline = []
        self.v_runline = []
        self.runline_3way = []
        self.h_runline_po = []
        self.v_runline_po = []
        self.runline_3way_po = []

    def get_details(self, match_page, match_link, _sleep=False):
        # Open each match link to collect runline info and in the end
        # close the match link tab
        # open new tab
        self.driver.execute_script("window.open('');")
        # switch to new tab and open match link
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get(match_link)
        match_page.load_match_stats_page()
        # get the html using BeautifulSoup
        if _sleep:
            time.sleep(15)
        match_page_source = self.driver.page_source
        match_soup = BeautifulSoup(match_page_source, "html.parser")
        all_stats = match_soup.find('ul', class_="fdjgs-markets")
        v_team = self.visitor_teams[-1]
        h_team = self.home_teams[-1]
        if self.sport in ["Football", "Basketball"]:
            # get point spread info
            ps_dict = match_page.get_ps_info(all_stats, v_team, h_team)
            self.h_ps.append(ps_dict["h_ps"])
            self.h_ps_po.append(ps_dict["h_ps_po"])
            self.v_ps.append(ps_dict["v_ps"])
            self.v_ps_po.append(ps_dict["v_ps_po"])
            # get moneyline runline info
            moneyline_dict = match_page.get_moneyline_info(all_stats)
            self.h_moneyline.append(moneyline_dict["h_moneyline"])
            self.v_moneyline.append(moneyline_dict["v_moneyline"])
        if self.league in ["NFL", "NCAA Basketball", "NBA"]:
            # get 3 way point spread info
            try:
                ps_3way_dict = match_page.get_3way_info(all_stats, v_team, h_team, search_str="Point Spread 3-Way")
                self.ps_3way.append(ps_3way_dict['spread'])
                self.ps_3way_po.append(ps_3way_dict['spread_po'])
            except:
                self.ps_3way.append("NA")
                self.ps_3way_po.append("NA")
        elif self.sport == "Baseball":
            try:
              # get runline info
              # TODO: Handle condition if event does not have odds info added
                runline_dict = match_page.get_runline_info(all_stats, v_team, h_team)
                self.v_runline.append(runline_dict["v_runline"])
                self.h_runline.append(runline_dict["h_runline"])
                self.v_runline_po.append(runline_dict["v_runline_po"])
                self.h_runline_po.append(runline_dict["h_runline_po"])
            except:
                self.v_runline.append("NA")
                self.h_runline.append("NA")
                self.v_runline_po.append("NA")
                self.h_runline_po.append("NA")
            try:
                # get 3 way runline info
                runline_3_way_dict = match_page.get_3way_info(all_stats, v_team, h_team, search_str="Runline 3-Way")
                self.runline_3way.append(runline_3_way_dict["spread"])
                self.runline_3way_po.append(runline_3_way_dict["spread_po"])
            except:
                self.runline_3way.append("NA")
                self.runline_3way_po.append("NA")
        elif self.sport == "Hockey":
            # get point spread info
            ps_dict = match_page.get_ps_info(all_stats, v_team, h_team, search_str="Puckline")
            self.h_ps.append(ps_dict["h_ps"])
            self.h_ps_po.append(ps_dict["h_ps_po"])
            self.v_ps.append(ps_dict["v_ps"])
            self.v_ps_po.append(ps_dict["v_ps_po"])
            # get moneyline runline info
            moneyline_dict = match_page.get_moneyline_info(all_stats)
            self.h_moneyline.append(moneyline_dict["h_moneyline"])
            self.v_moneyline.append(moneyline_dict["v_moneyline"])
            # get 3 way point spread info
            try:
                ps_3way_dict = match_page.get_3way_info(all_stats, v_team, h_team, search_str="Puckline 3-Way")
                self.ps_3way.append(ps_3way_dict['spread'])
                self.ps_3way_po.append(ps_3way_dict['spread_po'])
            except:
                self.ps_3way.append("NA")
                self.ps_3way_po.append("NA")
                
        # close current match tab and return to home league page
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

    def spread_summary(self):
        spread = []
        spread_po = []
        for i in range(len(self.visitor_teams)):
            # favourite team:  team having - sign in runline is favourite team
            if self.sport in ["Football", "Basketball", "Hockey"]:
                tmp_h_spread = self.h_ps[i]
                tmp_h_spread_po = self.h_ps_po[i]
                tmp_v_spread = self.v_ps[i]
                tmp_v_spread_po = self.v_ps_po[i]
            elif self.sport == "Baseball":
                tmp_h_spread = self.h_runline[i]
                tmp_h_spread_po = self.h_runline_po[i]
                tmp_v_spread = self.v_runline[i]
                tmp_v_spread_po = self.v_runline_po[i]

            if '-' in tmp_h_spread:
                spread.append('H '+tmp_h_spread)
                spread_po.append(tmp_h_spread_po)
            elif tmp_h_spread in ['NA', 'suspended']:
                spread.append(tmp_h_spread)
                spread_po.append(tmp_h_spread_po)
            else:
                spread.append('V '+tmp_v_spread)
                spread_po.append(tmp_v_spread_po)
        spread_info = {
              "spread": spread,
              "spread_po": spread_po
          }
        return spread_info

    def get_match_details(self):
        # load and locate individual matches locator
        home_page = HomePage(self.driver)
        home_page.load_matches_page(self.sport, self.country, self.league)
        time.sleep(5)
        # get the html using BeautifulSoup
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        results = soup.find(id=home_page.matches_menu_id)
        section = results.section
        # list of all matches to iterate over
        matches = section.find_all('article')
        # iterate over each match to read team names, match timing and 
        # individual match link for runline info collection
        match_page = MatchPage(self.driver)
        for match in matches:
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
            # Adding try catch as a precaution in case page is not 
            # loaded properly without sleep and through element not fount error
            try:
                self.get_details(match_page, match_link, _sleep=False)
            except:
                self.get_details(match_page, match_link, _sleep=True)

        spread_info = self.spread_summary()
        
        match_info_dict = {
                "Match Date": self.match_date,
                "Match Time": self.match_time,
                "Visitor Team": self.visitor_teams,
                "Home Team": self.home_teams
          }   
        if self.league in ["NFL", "NCAA Basketball", "NBA", "NHL"]:
            tmp_match_info_dict = {
                    "V ML": self.v_moneyline,
                    "H ML": self.h_moneyline,
                    "PS": spread_info['spread'],
                    "PS PO": spread_info['spread_po'],
                    "PS 3W": self.ps_3way,
                    "PS 3W PO": self.ps_3way_po
                }
            match_info_dict.update(tmp_match_info_dict)
        elif self.league == 'NCAA Football':
            tmp_match_info_dict = {
                    "V ML": self.v_moneyline,
                    "H ML": self.h_moneyline,
                    "PS": spread_info['spread'],
                    "PS PO": spread_info['spread_po']
                }
            match_info_dict.update(tmp_match_info_dict)
        elif self.league == 'MLB':
            tmp_match_info_dict = {
                    "RL": spread_info['spread'],
                    "RL PO": spread_info['spread_po'],
                    "RL 3W": self.runline_3way,
                    "RL 3W PO": self.runline_3way_po,
                }
            match_info_dict.update(tmp_match_info_dict)
        if self.league in ["NHL"]:
            tmp_match_info_dict = {
                    "V ML": self.v_moneyline,
                    "H ML": self.h_moneyline,
                    "PL": spread_info['spread'],
                    "PL PO": spread_info['spread_po'],
                    "PL 3W": self.ps_3way,
                    "PL 3W PO": self.ps_3way_po
                }
            match_info_dict.update(tmp_match_info_dict)
            
        return match_info_dict
