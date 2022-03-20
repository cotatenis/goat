from typing import Optional
import scrapy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from urllib.parse import urljoin
from time import sleep
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from scrapy import signals
from scrapy.utils.project import get_project_settings
from goat.items import GoatItem
from datetime import datetime
import re


class AdidasSpider(scrapy.Spider):
    settings = get_project_settings()
    name = "goat-adidas"
    version = settings.get("VERSION")
    allowed_domains = ["www.goat.com"]
    start_urls = ["https://quotes.toscrape.com/"]
    MAIN_URL = "https://www.goat.com/"
    slice_by_months = [
        "&sortBy=POPULAR&t=jan-feb",
        "&sortBy=POPULAR&t=feb-mar",
        "&sortBy=POPULAR&t=mar-apr",
        "&sortBy=POPULAR&t=apr-may",
        "&sortBy=POPULAR&t=may-jun",
        "&sortBy=POPULAR&t=jun-jul",
        "&sortBy=POPULAR&t=jul-aug",
        "&sortBy=POPULAR&t=aug-sep",
        "&sortBy=POPULAR&t=sep-oct",
        "&sortBy=POPULAR&t=oct-nov",
        "&sortBy=POPULAR&t=nov-dec",
    ]
    visited_urls = []

    def __init__(self, years=None, *args, **kwargs):
        super(AdidasSpider, self).__init__(*args, **kwargs)
        if not years:
            years = [datetime.now().year]
        self.urls = []
        for year in years:
            self.urls.append(f"https://www.goat.com/timeline/{year}?brand_name=adidas")

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(AdidasSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        display = Display(visible=True, size=(800, 600), backend="xvfb")
        display.start()
        options = Options()
        options.add_extension("./plugin.zip")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--dns-prefetch-disable")
        self.browser = webdriver.Chrome(options=options)
        self.browser.set_page_load_timeout(30)
        self.wdw = WebDriverWait(self.browser, 5)
        self.wdw_captcha_solver = WebDriverWait(self.browser, 240)

    def spider_closed(self, spider):
        self.browser.close()

    def parse(self, response):
        for url in self.urls:
            year = url.split("/")[-1].split("?")[0]
            try:
                self.browser.get(url)
            except TimeoutException as ex:
                self.logger.warning(ex)
                self.browser.refresh()
            self.logger.info(f"Visitando: {url}")
            sleep(0.5)
            self.popup_checker()
            # CHECK FOR CATPCHA PAGE
            has_captcha = self.evaluate_captcha_presence()
            if has_captcha:
                try:
                    self.resolve_captcha()
                except TimeoutException:
                    continue
                else:
                    self.logger.info("CAPTCHA SOLVED.")
            self.popup_checker()
            # VEFICIAR SE EXISTEM MAIS DE 1000 RESULTADOS NA PÁGINA
            try:
                num_results_element = self.browser.find_element_by_xpath(
                    "//h1[@data-qa='search-result-num']"
                )
            except (NoSuchElementException, TimeoutException):
                has_more_than_1k = False
            else:
                num_results = num_results_element.text
                num_results = re.search(r"\d+", num_results)
                if num_results:
                    has_more_than_1k = int(num_results.group(0)) > 1000
                else:
                    has_more_than_1k = False
            if has_more_than_1k:
                for partial in self.slice_by_months:
                    month_year_url = (
                        f"https://www.goat.com/timeline/{year}?brand_name=adidas"
                        + partial
                    )
                    self.logger.debug(f"[{year}] Visitando: {month_year_url}")
                    try:
                        self.browser.get(month_year_url)
                    except TimeoutException as ex:
                        self.logger.warning(ex)
                        self.browser.refresh()
                    self.popup_checker()
                    # CHECK FOR CATPCHA PAGE
                    has_captcha = self.evaluate_captcha_presence()
                    if has_captcha:
                        try:
                            self.resolve_captcha()
                        except TimeoutException:
                            continue
                        else:
                            self.logger.info("CAPTCHA SOLVED.")
                    self.popup_checker()
                    # self.parse_results(url=month_year_url, year=year)
                    num_products = self.count_num_products()
                    if num_products:
                        self.logger.debug(f"{num_products} produtos listados.")
                        scroll_pause_time = 1
                        self.scroll_results(scroll_pause_time)
                        products = self.browser.find_elements(
                            By.XPATH,
                            "//div[@data-qa='grid']//a[@data-qa='search_grid_cell']",
                        )
                        product_urls = [
                            urljoin(self.MAIN_URL, product.get_attribute("href"))
                            for product in products
                        ]
                        for url in product_urls:
                            if url in self.visited_urls:
                                self.logger.debug(
                                    f"[{year}] Página {url} já foi visitada."
                                )
                                continue
                            try:
                                self.browser.get(url)
                            except TimeoutException as ex:
                                self.logger.warning(ex)
                                self.browser.refresh()
                            self.visited_urls.append(url)
                            self.logger.debug(f"[{year}] Visitando: {url}")
                            self.popup_checker()
                            # CHECK FOR CATPCHA PAGE
                            has_captcha = self.evaluate_captcha_presence()
                            if has_captcha:
                                try:
                                    self.resolve_captcha()
                                except TimeoutException:
                                    continue
                                else:
                                    self.logger.info("CAPTCHA SOLVED.")
                            self.popup_checker()
                            is_this_page_valid = self.validate_product_page()
                            if not is_this_page_valid:
                                try:
                                    self.browser.get(url)
                                except TimeoutException as ex:
                                    self.logger.warning(ex)
                                    self.browser.refresh()
                                self.logger.debug(f"RELOAD: {url}")
                                self.popup_checker()
                                # CHECK FOR CATPCHA PAGE
                                has_captcha = self.evaluate_captcha_presence()
                                if has_captcha:
                                    try:
                                        self.resolve_captcha()
                                    except TimeoutException:
                                        continue
                                    else:
                                        self.logger.info("CAPTCHA SOLVED.")
                                self.popup_checker()
                            try:
                                item = self.parse_product_info(url=url)
                            except TimeoutException:
                                continue
                            else:
                                yield item
                    else:
                        self.logger.debug(
                            f"Não foram encontrados produtos a serem coletados na página: {month_year_url}."
                        )
            else:
                # self.parse_results(url=url, year=year)
                num_products = self.count_num_products()
                if num_products:
                    self.logger.debug(f"{num_products} produtos listados.")
                    scroll_pause_time = 1
                    self.scroll_results(scroll_pause_time)
                    products = self.browser.find_elements(
                        By.XPATH,
                        "//div[@data-qa='grid']//a[@data-qa='search_grid_cell']",
                    )
                    product_urls = [
                        urljoin(self.MAIN_URL, product.get_attribute("href"))
                        for product in products
                    ]
                    for url in product_urls:
                        if url in self.visited_urls:
                            self.logger.debug(f"[{year}] Página {url} já foi visitada.")
                            continue
                        try:
                            self.browser.get(url)
                        except TimeoutException as ex:
                            self.logger.warning(ex)
                            self.browser.refresh()
                        self.visited_urls.append(url)
                        self.logger.debug(f"[{year}] Visitando: {url}")
                        self.popup_checker()
                        # CHECK FOR CATPCHA PAGE
                        has_captcha = self.evaluate_captcha_presence()
                        if has_captcha:
                            try:
                                self.resolve_captcha()
                            except TimeoutException:
                                continue
                            else:
                                self.logger.info("CAPTCHA SOLVED.")
                        self.popup_checker()
                        is_this_page_valid = self.validate_product_page()
                        if not is_this_page_valid:
                            try:
                                self.browser.get(url)
                            except TimeoutException as ex:
                                self.logger.warning(ex)
                                self.browser.refresh()
                            self.logger.debug(f"RELOAD: {url}")
                            self.popup_checker()
                            # CHECK FOR CATPCHA PAGE
                            has_captcha = self.evaluate_captcha_presence()
                            if has_captcha:
                                try:
                                    self.resolve_captcha()
                                except TimeoutException:
                                    continue
                                else:
                                    self.logger.info("CAPTCHA SOLVED.")
                            self.popup_checker()
                        try:
                            item = self.parse_product_info(url=url)
                        except TimeoutException:
                            continue
                        else:
                            yield item
                else:
                    self.logger.debug(
                        f"Não foram encontrados produtos a serem coletados na página: {url}."
                    )

    def parse_product_info(self, url):
        # breadcrumbs
        try:
            breadcrumbs = self.browser.find_element(
                By.XPATH, "//nav[@data-qa='pdp_breadcrumb']"
            )
        except (NoSuchElementException, StaleElementReferenceException):
            breadcrumbs = ""
        else:
            breadcrumbs = breadcrumbs.text.split("/")
            breadcrumbs = [v.strip() for v in breadcrumbs]
        # model
        try:
            model = self.browser.find_element(
                By.XPATH, "//h1[@data-qa='product_display_name_text']"
            )
        except (NoSuchElementException, StaleElementReferenceException):
            model = ""
        else:
            model = model.text
        try:
            price_new = self.browser.find_element(
                By.XPATH, "//button[@data-qa='btn-pdp-buy-new']"
            )
        except (NoSuchElementException, StaleElementReferenceException):
            price_new = ""
        else:
            price_new = price_new.text.split("\n")[-1]
        # price used
        try:
            price_used = self.browser.find_element(
                By.XPATH, "//button[@data-qa='btn-pdp-view-shoes-used']"
            )
        except (NoSuchElementException, StaleElementReferenceException):
            price_used = ""
        else:
            price_used = price_used.text.split("\n")[-1]
        # description
        try:
            description = self.browser.find_element(
                By.XPATH, "//div[@data-qa='product_display_story_module']"
            )
        except (NoSuchElementException, StaleElementReferenceException):
            description = ""
        else:
            description = description.text
        # brand
        try:
            brand = self.browser.find_element(
                By.XPATH,
                "//span[contains(@class, 'Fact__') and contains(text(), 'Brand')]/../span[2]",
            )
        except (NoSuchElementException, StaleElementReferenceException):
            brand = ""
        else:
            brand = brand.text
        # release date
        try:
            release = self.browser.find_element(
                By.XPATH,
                "//span[contains(@class, 'Fact__') and contains(text(), 'Release')]/../span[2]",
            )
        except (NoSuchElementException, StaleElementReferenceException):
            release = ""
        else:
            release = release.text
        # SKU
        try:
            sku = self.browser.find_element(
                By.XPATH,
                "//span[contains(@class, 'Fact__') and contains(text(), 'SKU')]/../span[2]",
            )
        except (NoSuchElementException, StaleElementReferenceException):
            sku = ""
        else:
            sku = sku.text
        # material
        try:
            material = self.browser.find_element(
                By.XPATH,
                "//span[contains(@class, 'Fact__') and contains(text(), 'Material')]/../span[2]",
            )
        except (NoSuchElementException, StaleElementReferenceException):
            material = ""
        else:
            material = material.text
        # color
        try:
            main_color = self.browser.find_element(
                By.XPATH,
                "//span[contains(@class, 'Fact__') and contains(text(), 'Color')]/../span[2]",
            )
        except (NoSuchElementException, StaleElementReferenceException):
            main_color = ""
        else:
            main_color = main_color.text
        # colorway
        try:
            colorway = self.browser.find_element(
                By.XPATH,
                "//span[contains(@class, 'Fact__') and contains(text(), 'Colorway')]/../span[2]",
            )
        except (NoSuchElementException, StaleElementReferenceException):
            colorway = ""
        else:
            colorway = colorway.text
            if colorway:
                colorway = colorway.split("/")
                colorway = [c.strip() for c in colorway]
            else:
                colorway = []
        # designer
        try:
            designer = self.browser.find_element(
                By.XPATH,
                "//span[contains(@class, 'Fact__') and contains(text(), 'Designer')]/../span[2]",
            )
        except (NoSuchElementException, StaleElementReferenceException):
            designer = ""
        else:
            designer = designer.text
        # collection
        try:
            collection = self.browser.find_element(
                By.XPATH,
                "//span[contains(@class, 'Fact__') and contains(text(), 'Silho')]/../span[2]",
            )
        except (NoSuchElementException, StaleElementReferenceException):
            collection = ""
        else:
            collection = collection.text
        # technology
        try:
            technology = self.browser.find_element(
                By.XPATH,
                "//span[contains(@class, 'Fact__') and contains(text(), 'Tech')]/../span[2]",
            )
        except (NoSuchElementException, StaleElementReferenceException):
            technology = ""
        else:
            technology = technology.text
        # nickname
        try:
            nickname = self.browser.find_element(
                By.XPATH,
                "//span[contains(@class, 'Fact__') and contains(text(), 'Nickname')]/../span[2]",
            )
        except (NoSuchElementException, StaleElementReferenceException):
            nickname = ""
        else:
            nickname = nickname.text
        # category
        try:
            category = self.browser.find_element(
                By.XPATH,
                "//span[contains(@class, 'Fact__') and contains(text(), 'Category')]/../span[2]",
            )
        except (NoSuchElementException, StaleElementReferenceException):
            category = ""
        else:
            category = category.text
        try:
            image_urls = []
            imgs_elements = self.browser.find_elements_by_xpath(
                "//div[contains(@class, 'ProductImageCarousel')]//img"
            )
        except (NoSuchElementException, StaleElementReferenceException):
            image_urls = []
        else:
            for element in imgs_elements:
                product_imgs = element.get_attribute("srcset").split(",")
                product_imgs = [url.split(" ")[-2] for url in product_imgs]
                product_img = product_imgs[-1]
                image_urls.append(product_img)
        image_uris = []
        if len(image_urls) > 0:
            image_uris = [
                f"{self.settings.get('IMAGES_STORE')}{sku}_{filename.split('/')[-1].split('?')[0]}"
                for filename in image_urls
            ]
        payload = {
            "url": url,
            "breadcrumbs": breadcrumbs,
            "model": model,
            "price_new": price_new,
            "price_used": price_used,
            "description": description,
            "brand": brand,
            "release": release,
            "sku": sku,
            "material": material,
            "main_color": main_color,
            "colorway": colorway,
            "designer": designer,
            "collection": collection,
            "technology": technology,
            "nickname": nickname,
            "category": category,
            "image_urls": image_urls,
            "image_uris": image_uris,
            "spider": self.name,
            "spider_version": self.version,
        }
        item = GoatItem(**payload)
        return item

    def popup_checker(self):
        popup_locator = By.XPATH, "//button[@data-qa='button-cancel']"
        try:
            popup = self.wdw.until(EC.presence_of_element_located(popup_locator))
        except (NoSuchElementException, TimeoutException):
            pass
        else:
            popup.click()

    def evaluate_captcha_presence(self):
        header_captcha_locator = By.XPATH, "//div[@class='page-title']/h1"
        try:
            element_header_captcha = self.wdw.until(
                EC.presence_of_element_located(header_captcha_locator)
            )
        except (NoSuchElementException, TimeoutException):
            return False
        else:
            if element_header_captcha.text == "Please verify you are a human":
                self.logger.warning("Foi encontrado CAPTCHA.")
                return True
            else:
                return False

    def resolve_captcha(self):
        self.wdw_captcha_solver.until(
            lambda x: x.find_element_by_css_selector(".antigate_solver.solved")
        )

    def scroll_results(self, scroll_pause_time):
        screen_height = self.browser.execute_script(
            "return window.screen.height;"
        )  # get the screen height of the web
        screen_height -= 50
        i = 1
        while True:
            num_products = self.count_num_products()
            self.logger.debug(f"{num_products} produtos listados.")
            # scroll one screen height each time
            self.browser.execute_script(
                "window.scrollTo(0, {screen_height}*{i});".format(
                    screen_height=screen_height, i=i
                )
            )
            i += 1
            sleep(scroll_pause_time)
            # update scroll height each time after scrolled, as the scroll height can change after we scrolled the page
            scroll_height = self.browser.execute_script(
                "return document.body.scrollHeight;"
            )
            # Break the loop when the height we need to scroll to is larger than the total scroll height
            if (screen_height) * i > scroll_height:
                break

    def count_num_products(self):
        products = self.browser.find_elements(
            By.XPATH, "//div[@data-qa='grid']//a[@data-qa='search_grid_cell']"
        )
        return len(products)

    def validate_product_page(self) -> Optional[str]:
        # SKU
        try:
            sku = self.browser.find_element(
                By.XPATH,
                "//span[contains(@class, 'Fact__') and contains(text(), 'SKU')]/../span[2]",
            )
        except NoSuchElementException:
            sku = None
        else:
            sku = sku.text
        return sku

    def parse_results(self, url, year):
        num_products = self.count_num_products()
        if num_products:
            self.logger.debug(f"{num_products} produtos listados.")
            scroll_pause_time = 1
            self.scroll_results(scroll_pause_time)
            products = self.browser.find_elements(
                By.XPATH, "//div[@data-qa='grid']//a[@data-qa='search_grid_cell']"
            )
            product_urls = [
                urljoin(self.MAIN_URL, product.get_attribute("href"))
                for product in products
            ]
            for url in product_urls:
                if url in self.visited_urls:
                    self.logger.debug(f"{[year]} Página {url} já foi visitada.")
                    continue
                try:
                    self.browser.get(url)
                except TimeoutException as ex:
                    self.logger.warning(ex)
                    self.browser.refresh()
                self.visited_urls.append(url)
                self.logger.debug(f"[{year}] Visitando: {url}")
                self.popup_checker()
                # CHECK FOR CATPCHA PAGE
                has_captcha = self.evaluate_captcha_presence()
                if has_captcha:
                    try:
                        self.resolve_captcha()
                    except TimeoutException:
                        continue
                    else:
                        self.logger.info("CAPTCHA SOLVED.")
                self.popup_checker()
                is_this_page_valid = self.validate_product_page()
                if not is_this_page_valid:
                    try:
                        self.browser.get(url)
                    except TimeoutException as ex:
                        self.logger.warning(ex)
                        self.browser.refresh()
                    self.logger.debug(f"RELOAD: {url}")
                    self.popup_checker()
                    # CHECK FOR CATPCHA PAGE
                    has_captcha = self.evaluate_captcha_presence()
                    if has_captcha:
                        try:
                            self.resolve_captcha()
                        except TimeoutException:
                            continue
                        else:
                            self.logger.info("CAPTCHA SOLVED.")
                    self.popup_checker()
                item = self.parse_product_info(url=url)
                yield item
        else:
            self.logger.debug(
                f"Não foram encontrados produtos a serem coletados na página: {url}."
            )
