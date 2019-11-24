from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

import DemoApp.PageItems as PageItems

EMPTY_ALERT_ID = "alertEmpty"
STYLE_HIDDEN = "display: none"

# LogIn Page
ALERT_LOCATOR = (By.CLASS_NAME, "alert")
BUTTONS_SECTION_LOCATOR = (By.CLASS_NAME, "buttons-w")
FORM_GROUP_LOCATOR = (By.CLASS_NAME, "form-group")
HEADER_TEXT_LOCATOR = (By.CSS_SELECTOR, "h4")
IMAGE_LOCATOR = (By.CSS_SELECTOR, "img")
LOGIN_FORM_LOCATOR = (By.CSS_SELECTOR, "form")
LOGO_LOCATOR = (By.CLASS_NAME, "logo-w")

# Dashboard Page
AMOUNTS_HEADER_LOCATOR = (By.ID, "amount")
BALANCE_LOCATOR = (By.CSS_SELECTOR, ".element-balances > .balance")
COMPARE_EXPENSES_LOCATOR = (By.ID, "showExpensesChart")
TABLE_ROW_LOCATOR = (By.CSS_SELECTOR, "tbody > tr")
TRANSACTIONS_LOCATOR = (By.ID, "transactionsTable")

# Expenses Section
CANVAS_LOCATOR = (By.ID, "canvas")
SHOW_NEXT_YEAR_LOCATOR = (By.ID, "addDataset")


class PageWithHeader(object):
    def __init__(self, driver):
        self._driver = driver

    def _logo_element(self):
        return self._driver.find_element(*LOGO_LOCATOR)

    def _header_element(self):
        return self._driver.find_element(*HEADER_TEXT_LOCATOR)

    @property
    def logo_image(self):
        return self._logo_element().find_element(*IMAGE_LOCATOR).get_attribute("src")

    @property
    def logo_accessibility_text(self):
        return self._logo_element().find_element(*IMAGE_LOCATOR).get_attribute("alt")

    @property
    def header_text(self):
        return self._header_element().text


class Login(PageWithHeader):

    def __init__(self, driver, base_url, query_string=""):
        super().__init__(driver)
        driver.get(base_url + query_string)

    def _alert_elements(self):
        return self._driver.find_elements(*ALERT_LOCATOR)

    def _login_form_element(self):
        return self._driver.find_element(*LOGIN_FORM_LOCATOR)

    def _buttons_section(self):
        return self._driver.find_element(*BUTTONS_SECTION_LOCATOR)

    def _alerts(self):
        for element in self._alert_elements():
            if element.get_attribute("id") != EMPTY_ALERT_ID and STYLE_HIDDEN not in element.get_attribute("style"):
                yield element.text

    def _form_fields(self):
        form_group_elements = self._login_form_element().find_elements(*FORM_GROUP_LOCATOR)

        for element in form_group_elements:
            yield PageItems.FormGroup(element)

    def _form_field(self, id):
        return next(field for field in self._form_fields() if field.input_id == id)

    @property
    def alerts(self):
        try:
            return list(self._alerts())
        except TypeError:
            return None

    @property
    def form_fields(self):
        return list(self._form_fields())

    @property
    def buttons(self):
        return PageItems.Buttons(self._buttons_section())

    def type_user_name(self, value):
        self._form_field("username").type(value)

    def type_password(self, value):
        self._form_field("password").type(value)

    def submit(self):
        self.buttons.press_submit_button()


class CustomerDashboard(object):

    def __init__(self, driver):
        self._driver = driver

    def _transactions_table(self):
        return self._driver.find_element(*TRANSACTIONS_LOCATOR)

    def _amounts_header_element(self):
        return self._transactions_table().find_element(*AMOUNTS_HEADER_LOCATOR)

    def _transaction_elements(self):
        return self._transactions_table().find_elements(*TABLE_ROW_LOCATOR)

    def _compare_expenses_element(self):
        return self._driver.find_element(*COMPARE_EXPENSES_LOCATOR)

    def _show_next_year_element(self):
        return self._driver.find_element(*SHOW_NEXT_YEAR_LOCATOR)

    def _canvas_element(self):
        return self._driver.find_element(*CANVAS_LOCATOR)

    def _balance_elements(self):
        return self._driver.find_elements(*BALANCE_LOCATOR)

    def _transactions(self):
        for element in self._transaction_elements():
            yield PageItems.TransactionRow(element).data

    def _adverts(self):
        for element in self._balance_elements():
            balance = PageItems.Balance(self._driver, element)
            if balance.is_advert:
                yield balance.to_advert()

    def transactions(self):
        return list(self._transactions())

    def adverts(self):
        return list(self._adverts())

    def order_by_amount(self):
        self._amounts_header_element().click()

    def view_expense_chart(self):
        self._compare_expenses_element().click()

    def include_another_year(self):
        self._show_next_year_element().click()

    def download_canvas(self):
        return self._driver.execute_script("return arguments[0].toDataURL('image/png')", self._canvas_element())

    def is_loaded(self):
        try:
            # NOTE: amounts column header is clearly not optimal candidate for checking if page has been loaded fully
            return self._amounts_header_element().is_displayed()
        except NoSuchElementException:
            return False
