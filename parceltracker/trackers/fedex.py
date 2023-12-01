from datetime import datetime
import dateparser
import re as regex
from selenium.webdriver.common.by import By
from selenium import webdriver
import undetected_chromedriver as uc

from .. import base


class FedEx(base.ParcelTracker):
    company_name: str = "FedEx"
    provider_domain: str = "speedy.bg"
    tracking_number_regex: str = r'^\d{12,15}$|^\d{20,22}$'

    def get_parcel_info(self, tracking_number: str) -> base.ParcelInfo:
        tracking_number = tracking_number.strip().upper()
        if regex.match(self.tracking_number_regex, tracking_number) is None:
            return base.ParcelInfo()

        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--window-size=1920,1080')
        driver = uc.Chrome()
        driver.get(f"https://www.fedex.com/fedextrack/?action=track&tracknumbers={tracking_number}&locale=en_RO&cntry_code=us")

        # Wait for the page to load
        driver.implicitly_wait(8)

        categories_xpath = '.travel-history-table__row'
        categories = driver.find_elements(By.CSS_SELECTOR, categories_xpath)

        parcel_info = base.ParcelInfo()

        for category in categories:
            date = category.find_element(By.CSS_SELECTOR, '.travel-history-table__scan-event-date > span')
            try:
                # Change Dayofweek, MM/DD/YYYY to DD/MM/YYYY
                date = date.text.split(", ")[-1]
                #date = date.split("/")
                #date = f"{date[1]}/{date[0]}/{date[2]}"

                log_data_with_time_message_and_location = category.find_elements(By.CSS_SELECTOR, '.travel-history__scan-event')
                for i in log_data_with_time_message_and_location:
                    location = i.find_element(By.XPATH, './/div[3]')
                    message = i.find_element(By.CSS_SELECTOR, '#status')
                    time = i.find_element(By.XPATH, './/div[1]/div[1]/div[1]/div[1]/span[1]')

                    event = base.ParcelEvent()
                    parsed_date = dateparser.parse(f"{date} {time.text}", languages=['ro'], locales=['ro'])
                    if parsed_date is not None:
                        event.date = parsed_date
                    event.message = message.text
                    event.location = location.text
                    event.company_name = self.company_name

                    parcel_info.events_log.append(event)
            except:
                continue

        # Remove all with empty message and location
        parcel_info.events_log = [x for x in parcel_info.events_log if x.message != "" and x.location != ""]

        parcel_info.events_log.sort(reverse=True)

        weight_xpath = '#shipment-facts-section > trk-shared-shipment-facts-new > div > div:nth-child(3) > div.body > table > tbody > tr:nth-child(1) > trk-shared-shipment-facts-list > td.fdx-u-text--normal.fdx-u-font-size--small.fdx-u-line-height--large.fdx-u-pl--4.fdx-u-pt--1.fdx-u-pb--1'
        weight = driver.find_element(By.CSS_SELECTOR, weight_xpath).text

        try:
            weight = float(weight.strip().split(" ")[-2])
        except:
            weight = 0

        parcel_info.tracking_numbers = [tracking_number]
        parcel_info.weight = weight

        to_xpath = "#container > ng-component > fdx-common-core > trk-shared-stylesheet-wrapper > div > div > trk-shared-detail-page > trk-shared-stylesheet-wrapper > div > div > trk-shared-detail-page-new > div > section.shipment-info-container > div.shipment-info-right-bar > trk-shared-status-progress-bar-new > trk-shared-status-progress-bar-renderer > div > div:nth-child(6) > div > div:nth-child(4) > span"
        to = driver.find_element(By.CSS_SELECTOR, to_xpath).text

        from_xpath = "#container > ng-component > fdx-common-core > trk-shared-stylesheet-wrapper > div > div > trk-shared-detail-page > trk-shared-stylesheet-wrapper > div > div > trk-shared-detail-page-new > div > section.shipment-info-container > div.shipment-info-right-bar > trk-shared-status-progress-bar-new > trk-shared-status-progress-bar-renderer > div > div:nth-child(2) > div > div:nth-child(4) > span"
        from_ = driver.find_element(By.CSS_SELECTOR, from_xpath).text

        parcel_info.to = to
        parcel_info.origin = from_
        parcel_info.provider = self.company_name
        parcel_info.days_in_transit = (datetime.now() - parcel_info.events_log[-1].date).days

        return parcel_info

base.TRACKERS.append(FedEx())

