from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class DriverUtility:

    def __init__(self, driver):
        self.driver = driver
        self.actions = ActionChains(self.driver)
        
    def perform_actions(self, menu):
        self.actions.move_to_element(menu)
        self.actions.click(menu)
        self.actions.perform()
        
    def get_locator(self, locator_type, locator):
#         return WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((locator_type, locator)))
        return self.driver.find_element(locator_type, locator)