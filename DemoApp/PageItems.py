from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

TRANSACTION_COLUMNS = ["status", "date", "description", "category", "amount"]

# LogIn Page
ICON_LOCATOR = (By.CLASS_NAME, "os-icon")
INPUT_LOCATOR = (By.CLASS_NAME, "form-control")
REMEMBER_CHECKBOX_LOCATOR = (By.CLASS_NAME, "form-check-label")
SOCIAL_ICON_LOCATOR = (By.CSS_SELECTOR, "a > img")
SUBMIT_LOGIN_LOCATOR = (By.CSS_SELECTOR, "button")

# Generic Locators
IMAGE_LOCATOR = (By.CSS_SELECTOR, "img")
LABEL_LOCATOR = (By.CSS_SELECTOR, "label")
TABLE_DATA_LOCATOR = (By.CSS_SELECTOR, "td")


class FormGroup(object):

    def __init__(self, scope):
        self.__scope = scope

    def _label_element(self):
        return self.__scope.find_element(*LABEL_LOCATOR)

    def _input_element(self):
        return self.__scope.find_element(*INPUT_LOCATOR)

    def _icon_element(self):
        return self.__scope.find_element(*ICON_LOCATOR)

    @property
    def label(self):
        return self._label_element().text

    @property
    def placeholder_text(self):
        return self._input_element().get_attribute("placeholder")

    @property
    def input_id(self):
        return self._input_element().get_attribute("id")

    @property
    def icon_class(self):
        return self._icon_element().get_attribute("class").split()[-1]

    def type(self, value):
        self._input_element().clear()
        self._input_element().send_keys(value)


class Buttons(object):

    def __init__(self, scope):
        self.__scope = scope

    def _submit_button(self):
        return self.__scope.find_element(*SUBMIT_LOGIN_LOCATOR)

    def _remember_checkbox(self):
        return self.__scope.find_element(*REMEMBER_CHECKBOX_LOCATOR)

    def _social_icons(self):
        for element in self.__scope.find_elements(*SOCIAL_ICON_LOCATOR):
            yield SocialIcon(element)

    @property
    def submit_button_text(self):
        return self._submit_button().text

    @property
    def checkbox_text(self):
        return self._remember_checkbox().text

    @property
    def social_icons(self):
        return list(self._social_icons())

    def press_submit_button(self):
        self._submit_button().click()


class SocialIcon(object):

    def __init__(self, element):
        self.__element = element

    @property
    def image_url(self):
        return self.__element.get_attribute("src")

    @property
    def accessibility_text(self):
        return self.__element.get_attribute("alt")


class TransactionRow(object):

    def __init__(self, scope):
        self.__scope = scope
        self.__data = {}

        values = iter(self._data_elements())
        for column_name in TRANSACTION_COLUMNS:
            self.__data[column_name] = next(values).text

    def _data_elements(self):
        return self.__scope.find_elements(*TABLE_DATA_LOCATOR)

    @property
    def data(self):
        return self.__data


class Balance(object):

    def __init__(self, driver, scope):
        self._scope = scope
        self._driver = driver

    def _image_element(self):
        try:
            return self._scope.find_element(*IMAGE_LOCATOR)
        except NoSuchElementException:
            return None

    @property
    def is_advert(self):
        return self._image_element() is not None

    def to_advert(self):
        return Advert(self._driver, self._scope)


class Advert(Balance):

    def __init__(self, driver, scope):
        super().__init__(driver, scope)

    @property
    def image_url(self):
        return self._image_element().get_attribute("src")

    @property
    def is_displayed(self):
        try:
            return self._image_element().is_displayed()
        except NoSuchElementException:
            return False
