import configparser
import hashlib
import time
import urllib.request
from decimal import Decimal

import pytest
import pytest_check as check
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

import DemoApp.Pages as Pages

DEFAULT_TIMEOUT_SEC = 10

CANVAS_ANIMATION_SEC = 1
CANVAS_DEFAULT_YEARS = 2
REFERENCE_CANVAS_2YRS_MD5 = "b65234091b35b4521b4a5d33e6034985"
REFERENCE_CANVAS_3YRS_MD5 = "062ed6be5f785811721544ef76e582bc"

DEFAULT_CREDENTIALS = {"user": "user",
                       "password": "password"}


class TestLoginPageAppearance(object):
    """
    Although the actual rendered appearance of a website is not feasible to test with selenium, there's a bunch
    of things that are closely related with it and can be easily checked in an automated manner.

    Tests in this class are not changing the status of the application, therefore it is enough to load the page once
    and execute all these tests in the same session.

    Instead of separation of each assert into a new test case, appearance is checked via pytest-check plugin that allows
    non-blocking assertions.
    """

    def setup_class(self):
        self.__config = configparser.ConfigParser()
        self.__config.read("config.ini")
        self.__driver = webdriver.Chrome()
        self.__page = Pages.Login(self.__driver, self.__config["environment"]["base_url"])

    def teardown_class(self):
        self.__driver.quit()

    def test_login_page_basics(self):
        assert self.__driver.title == "ACME demo app"
        assert self.__page.header_text == "Login Form"

    def test_no_alerts(self):
        assert not self.__page.alerts

    def test_form_contents(self):
        form_fields = self.__page.form_fields
        check.equal(len(form_fields), 2)

        check.equal(form_fields[0].label, "Username")
        check.equal(form_fields[0].placeholder_text, "Enter your username")
        check.equal(form_fields[0].icon_class, "os-icon-user-male-circle")

        check.equal(form_fields[1].label, "Password")
        check.equal(form_fields[1].placeholder_text, "Enter your password")
        check.equal(form_fields[1].icon_class, "os-icon-fingerprint")

        check.equal(self.__page.buttons.submit_button_text, "Log In")
        check.equal(self.__page.buttons.checkbox_text, "Remember Me")

    def test_images(self):
        check.equal(self.__page.logo_image, "https://demo.applitools.com/img/logo-big.png")

        social_icons = self.__page.buttons.social_icons

        # normal pytest assert on purpose: if the number of icons differs order in the following checks is not relevant
        assert len(social_icons) == 3

        check.equal(social_icons[0].image_url, "https://demo.applitools.com/img/social-icons/twitter.png")
        check.equal(social_icons[1].image_url, "https://demo.applitools.com/img/social-icons/facebook.png")
        check.equal(social_icons[2].image_url, "https://demo.applitools.com/img/social-icons/linkedin.png")

    # known defect: non-complient with WCAG standards
    def test_accessibility(self):
        check.is_not_in(self.__page.logo_accessibility_text, [None, ""],
                        "Product logo (containing an anchor) should have alternative text.")

        for icon in self.__page.buttons.social_icons:
            check.is_not_in(icon.accessibility_text, [None, ""],
                            "Functional elements without text should have alternative text.")


class TestLoginFunctionality(object):
    """
    In this class a set of simple functional data-driven test cases are implemented to check whether or not the login
    is successful with the credentials being completely or partly missing, or all credentials are correct.
    According to specification, any non-empty value is considered correct, therefore there's no reason to use test
    design techniques for various string values, a single space character or any default string will do.
    """

    def setup_method(self):
        self.__config = configparser.ConfigParser()
        self.__config.read("config.ini")
        self.__driver = webdriver.Chrome()
        self.__page = Pages.Login(self.__driver, self.__config["environment"]["base_url"])
        self.__wait = WebDriverWait(self.__driver, DEFAULT_TIMEOUT_SEC)

    def teardown_method(self):
        self.__driver.quit()

    @pytest.mark.parametrize("user, password,expected",
                             [("", "", "Both Username and Password must be present"),
                              (" ", "", "Password must be present"),
                              ("", " ", "Username must be present")])
    def test_credentials_missing(self, user, password, expected):
        self.__page.type_user_name(user)
        self.__page.type_password(password)
        self.__page.submit()

        self.__wait.until(lambda _: len(self.__page.alerts) == 1)

        assert self.__page.alerts[0] == expected

    @pytest.mark.parametrize("missing, expected",
                             [("user", "Username must be present"),
                              ("password", "Password must be present"),
                              ("both", "Both Username and Password must be present")])
    def test_credentials_removed(self, missing, expected):
        self.__page.type_user_name(DEFAULT_CREDENTIALS["user"])
        self.__page.type_password(DEFAULT_CREDENTIALS["password"])

        self.__remove_credential(missing)
        self.__page.submit()

        self.__wait.until(lambda _: len(self.__page.alerts) == 1)

        assert self.__page.alerts[0] == expected

    def test_successful_login(self):
        self.__page.type_user_name(DEFAULT_CREDENTIALS["user"])
        self.__page.type_password(DEFAULT_CREDENTIALS["password"])
        self.__page.submit()

        self.__wait.until(lambda _: Pages.CustomerDashboard(self.__driver).is_loaded())
        assert "hackathonApp" in self.__driver.current_url

    def __remove_credential(self, missing):
        if missing not in ["user", "password", "both"]:
            raise AttributeError

        if missing in ["user", "both"]:
            self.__page.type_user_name("")

        if missing in ["password", "both"]:
            self.__page.type_password("")


class TestTableSorting(object):
    """
    Tests in this class are meant to verify the ordering of records in transactions table by the column headers. The class
    contains some static methods that are good candidates for a utilities module, although for simplicity they are
    kept here within the class. Tests are using the built-in sorting of Python to determine the expected results.
    """

    def setup_method(self):
        self.__config = configparser.ConfigParser()
        self.__config.read("config.ini")
        self.__driver = webdriver.Chrome()
        self.__wait = WebDriverWait(self.__driver, DEFAULT_TIMEOUT_SEC)
        self.__page = self.__open_customer_dashboard(DEFAULT_CREDENTIALS)

    def teardown_method(self):
        self.__driver.quit()

    def test_ascending_by_amount(self):
        table_data_before = self.__amounts_to_decimal(self.__page.transactions())
        sorted_by_amount = sorted(table_data_before, key=lambda _: _["amount"])

        self.__page.order_by_amount()

        table_data_after = self.__amounts_to_decimal(self.__page.transactions())
        assert table_data_after == sorted_by_amount

    def __open_customer_dashboard(self, credentials):
        login_page = Pages.Login(self.__driver, self.__config["environment"]["base_url"])
        login_page.type_user_name(credentials["user"])
        login_page.type_password(credentials["password"])
        login_page.submit()

        dashboard_page = Pages.CustomerDashboard(self.__driver)
        self.__wait.until(lambda _: dashboard_page.is_loaded())

        return dashboard_page

    @staticmethod
    def __amounts_to_decimal(transactions):
        return list(map(TestTableSorting.__amount_to_decimal, transactions))

    @staticmethod
    def __amount_to_decimal(transaction_data):
        amount_with_currency = transaction_data["amount"]
        stripped_amount = amount_with_currency[:-4].replace(',', '').replace(' ', '')
        new_instance = transaction_data.copy()
        new_instance["amount"] = Decimal(stripped_amount)
        return new_instance


class TestCanvas(object):
    """
    Inner contents of the canvas cannot be processed via Selenium, therefore this kind of tests are good candidate for
    OpenCV based technologies e.g. Applitools products. The best effort in the traditional way is to download
    and binary compare the rendered canvas to a reference (approval testing).
    NOTE that this is very brittle and therefore inadvisable for automation.

    Trying to avoid environment-specific behaviour, headless browser with explicitly set resolution is used.
    """

    def setup_method(self):
        self.__config = configparser.ConfigParser()
        self.__config.read("config.ini")

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")

        self.__driver = webdriver.Chrome(options=chrome_options)
        self.__wait = WebDriverWait(self.__driver, DEFAULT_TIMEOUT_SEC)

    def teardown_method(self):
        self.__driver.quit()

    @pytest.mark.parametrize("number_of_years, expected_md5",
                             [(2, REFERENCE_CANVAS_2YRS_MD5),
                              (3, REFERENCE_CANVAS_3YRS_MD5)])
    def test_canvas_chart(self, number_of_years, expected_md5):
        page_with_canvas = self.__open_customer_dashboard_with_canvas(DEFAULT_CREDENTIALS)

        for _ in range(number_of_years - CANVAS_DEFAULT_YEARS):
            page_with_canvas.include_another_year()

        self.__wait_for_canvas_animation()
        md5_of_canvas = hashlib.md5(page_with_canvas.download_canvas().encode('utf-8'))

        assert md5_of_canvas.hexdigest() == expected_md5,\
            "Contents of the canvas is binary different from the reference, please check manually."

    def __open_customer_dashboard_with_canvas(self, credentials):
        login_page = Pages.Login(self.__driver, self.__config["environment"]["base_url"])
        login_page.type_user_name(credentials["user"])
        login_page.type_password(credentials["password"])
        login_page.submit()

        dashboard_page = Pages.CustomerDashboard(self.__driver)
        self.__wait.until(lambda _: dashboard_page.is_loaded())

        dashboard_page.view_expense_chart()

        return dashboard_page

    @staticmethod
    def __wait_for_canvas_animation():
        """
        time.sleep is a very bad practice in test automation in general, however in this case the animation duration of
        JavaScript drawing on canvas is explicitly known, it is expected to remain the same unless requirements change.
        :return:s
        """
        time.sleep(CANVAS_ANIMATION_SEC)


class TestAdverts(object):
    """
    These test cases are meant to verify that the adverts on a page are displayed. With the traditional way a feasible
    strategy is checking the existence of the images in DOM, and verification of the referred image files are present
    on the server.
    """

    def setup_method(self):
        self.__config = configparser.ConfigParser()
        self.__config.read("config.ini")
        self.__driver = webdriver.Chrome()
        self.__page = Pages.Login(self.__driver, self.__config["environment"]["base_url"], query_string="?showAd=true")
        self.__wait = WebDriverWait(self.__driver, DEFAULT_TIMEOUT_SEC)

    def teardown_method(self):
        self.__driver.quit()

    def test_two_adverts_on_dashboard(self):
        self.__go_to_dashboard()
        adverts = self.__page.adverts()

        assert len(adverts) == 2

        for advert in adverts:
            assert advert.is_displayed
            assert self.__is_file_present(advert.image_url)

        assert adverts[0].image_url == "https://demo.applitools.com/img/flashSale.gif"
        assert adverts[1].image_url == "https://demo.applitools.com/img/flashSale2.gif"

    def __go_to_dashboard(self):
        self.__page.type_user_name(DEFAULT_CREDENTIALS["user"])
        self.__page.type_password(DEFAULT_CREDENTIALS["password"])
        self.__page.submit()

        self.__page = Pages.CustomerDashboard(self.__driver)
        self.__wait.until(lambda _: self.__page.is_loaded())

    @staticmethod
    def __is_file_present(url):
        return urllib.request.urlopen(url).getcode() == 200
