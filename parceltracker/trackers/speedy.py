import requests
import dateparser
import re as regex
from bs4 import BeautifulSoup

from .. import base


class SpeedyTracker(base.ParcelTracker):
    company_name: str = "Speedy"
    provider_domain: str = "speedy.bg"
    tracking_number_regex: str = r'^[0-9]{11}$'


    def get_parcel_info(self, tracking_number: str) -> base.ParcelInfo:
        tracking_number = tracking_number.strip().upper()
        if regex.match(self.tracking_number_regex, tracking_number) is None:
            return base.ParcelInfo()

        parcel_info = super().get_parcel_info(tracking_number)

        parcel_info.tracking_numbers.append(tracking_number)

        response = requests.get(f'https://www.speedy.bg/en/track-shipment?shipmentNumber={tracking_number}', headers=base.DEFAULT_HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')

        thead = soup.find('thead')
        if thead is None:
            return parcel_info

        header_row = thead.find('tr')
        if header_row is None:
            return parcel_info
        keys = [th.get_text(strip=True) for th in header_row.find_all('th')]

        tbody = soup.find('tbody')
        if tbody is None:
            return parcel_info
        rows = tbody.find_all('tr')

        data = []

        for row in rows:
            row_data = {key: col.get_text(strip=True) for key, col in zip(keys, row.find_all('td'))}
            data.append(row_data)

        for row in data:
            parcel_event = base.ParcelEvent()
            date = dateparser.parse(row['Date'], languages=['ro'], locales=['ro'])
            if date is not None:
                parcel_event.date = date
            parcel_event.location = row['City/village']
            parcel_event.message = row['Operation']
            parcel_event.company_name = self.company_name
            parcel_info.events_log.append(parcel_event)

        parcel_info.events_log.sort(reverse=True)

        return parcel_info


base.TRACKERS.append(SpeedyTracker())

