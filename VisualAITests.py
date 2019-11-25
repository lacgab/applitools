import configparser
import time

import pytest
from applitools.selenium import Eyes
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

import DemoApp.Pages as Pages

CANVAS_ANIMATION_SEC = 1
DEFAULT_TIMEOUT_SEC = 10
DEFAULT_VIEWPORT = {'width': 1024, 'height': 768}
DEFAULT_CREDENTIALS = {"user": "user",
                       "password": "password"}


class TestDemoApp(object):
    """
    This class contains all the test cases for Visual AI based testing of the application, because the number of test
    cases are expected to be sinificantly less than in the Traditional way.

    Eyes is initialized only once for possible efficiency increase.

    Setting explicit batch id seems to have a bug in the current version of selenium-based python implementation:
    sessions/running API keeps returning 400 response code when eyes.batch is set.
    """

    def setup_class(self):
        self.__config = configparser.ConfigParser()
        self.__config.read("config.ini")

        self.__driver = webdriver.Chrome()
        self.__wait = WebDriverWait(self.__driver, DEFAULT_TIMEOUT_SEC)

        self.__eyes = Eyes()
        self.__eyes.api_key = self.__config["applitools"]["api_key"]

    def teardown_class(self):
        self.__driver.quit()
        self.__eyes.abort()

    def test_login_page_appearance(self):
        self.__driver.get(self.__config["environment"]["base_url"])
        self.__eyes.open(self.__driver, "DemoApp", "Login Page Appearance", DEFAULT_VIEWPORT)
        self.__eyes.check_window("Login Page Default")
        self.__eyes.close()

    @pytest.mark.parametrize("user, password, test_name",
                             [("", "", "Both Empty"),
                              (" ", "", "Password Empty"),
                              ("", " ", "User Empty")])
    def test_credentials_missing(self, user, password, test_name):
        page = Pages.Login(self.__driver, self.__config["environment"]["base_url"])
        page.type_user_name(user)
        page.type_password(password)
        page.submit()

        self.__wait.until(lambda _: len(page.alerts) == 1)
        self.__eyes.open(self.__driver, "DemoApp", f"Credentials Missing - {test_name}", DEFAULT_VIEWPORT)
        self.__eyes.check_window("Login Page With Alert")
        self.__eyes.close()

    @pytest.mark.parametrize("missing", ["User", "Password", "Both"])
    def test_credentials_removed(self, missing):
        page = Pages.Login(self.__driver, self.__config["environment"]["base_url"])
        page.type_user_name(DEFAULT_CREDENTIALS["user"])
        page.type_password(DEFAULT_CREDENTIALS["password"])

        self.__remove_credential(page, missing)
        page.submit()

        self.__wait.until(lambda _: len(page.alerts) == 1)

        self.__eyes.open(self.__driver, "DemoApp", f"Credentials Removed - {missing} Empty", DEFAULT_VIEWPORT)
        self.__eyes.check_window("Login Page With Alert")
        self.__eyes.close()

    def test_successful_login(self):
        page = Pages.Login(self.__driver, self.__config["environment"]["base_url"])
        page.type_user_name(DEFAULT_CREDENTIALS["user"])
        page.type_password(DEFAULT_CREDENTIALS["password"])
        page.submit()

        self.__wait.until(lambda _: Pages.CustomerDashboard(self.__driver).is_loaded())

        self.__eyes.open(self.__driver, "DemoApp", "Successful Login", DEFAULT_VIEWPORT)
        self.__eyes.check_window("Customer Dashboard")
        self.__eyes.close()

    def test_table_sorting(self):
        self.__do_login()
        page = Pages.CustomerDashboard(self.__driver)

        self.__eyes.open(self.__driver, "DemoApp", "Table Sorting", DEFAULT_VIEWPORT)
        self.__eyes.check_window("Customer Dashboard - Default")

        page.order_by_amount()

        self.__eyes.check_window("Customer Dashboard - Sorted by Amount")
        self.__eyes.close()

    def test_canvas_chart(self):
        self.__do_login()
        page = Pages.CustomerDashboard(self.__driver)

        page.view_expense_chart()
        self.__wait_for_canvas_animation()

        self.__eyes.open(self.__driver, "DemoApp", "Expenses Chart", DEFAULT_VIEWPORT)
        self.__eyes.check_window("Chart Two Years")

        page.include_another_year()
        self.__wait_for_canvas_animation()

        self.__eyes.check_window("Chart Three Years")
        self.__eyes.close()

    def test_two_adverts_on_dashboard(self):
        self.__do_login(query_string="?showAd=true")

        self.__eyes.open(self.__driver, "DemoApp", "Adverts On Dashboard", DEFAULT_VIEWPORT)
        self.__eyes.check_window("Dashboard With Adverts")
        self.__eyes.close()

    def __do_login(self, credentials=DEFAULT_CREDENTIALS, query_string=""):
        page = Pages.Login(self.__driver, self.__config["environment"]["base_url"], query_string)
        page.type_user_name(credentials["user"])
        page.type_password(credentials["password"])
        page.submit()

        self.__wait.until(lambda _: Pages.CustomerDashboard(self.__driver).is_loaded())

    @staticmethod
    def __remove_credential(page, missing):
        if missing not in ["User", "Password", "Both"]:
            raise AttributeError

        if missing in ["User", "Both"]:
            page.type_user_name("")

        if missing in ["Password", "Both"]:
            page.type_password("")

    @staticmethod
    def __wait_for_canvas_animation():
        """
        time.sleep is a very bad practice in test automation in general, however in this case the animation duration of
        JavaScript drawing on canvas is explicitly known, it is expected to remain the same unless requirements change.
        :return:s
        """
        time.sleep(CANVAS_ANIMATION_SEC)
