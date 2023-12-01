from datetime import datetime
import requests
import dateparser
import re as regex

from .. import base


class YunExpressTracker(base.ParcelTracker):
    company_name: str = "YunExpress"
    provider_domain: str = "yuntrack.com"
    tracking_number_regex: str = r'^[A-Z]{2}[0-9]{16}$'


    def get_parcel_info(self, tracking_number: str) -> base.ParcelInfo:
        tracking_number = tracking_number.strip().upper()
        if regex.match(self.tracking_number_regex, tracking_number) is None:
            return base.ParcelInfo()

        parcel_info = super().get_parcel_info(tracking_number)
        headers = {
            'Referer': 'https://www.yuntrack.com/',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'authorization,content-type',
            'Origin': 'https://www.yuntrack.com',
        }
        headers.update(base.DEFAULT_HEADERS)

        session = requests.Session()
        session.options('https://services.yuntrack.com/Track/Query', headers=headers)
        response = session.post('https://services.yuntrack.com/Track/Query', headers=headers, json={"NumberList":[
            tracking_number
            ],"CaptchaVerification":"","Year":0})
        data = response.json()
        parcel_info.tracking_numbers.append(data['ResultList'][0]['TrackInfo']['WaybillNumber'])
        parcel_info.tracking_numbers.append(data['ResultList'][0]['TrackInfo']['TrackingNumber'])
        parcel_info.channel = data['ResultList'][0]['TrackInfo']['ChannelCodeOut']
        parcel_info.provider = data['ResultList'][0]['TrackInfo']['ProviderName']
        parcel_info.weight = data['ResultList'][0]['TrackInfo']['Weight']
        parcel_info.origin = data['ResultList'][0]['TrackInfo']['OriginCountryCode']
        parcel_info.to = data['ResultList'][0]['TrackInfo']['DestinationCountryCode']

        date = dateparser.parse(data['ResultList'][0]['TrackInfo']['CreatedOn'])
        if date is not None:
            current_date = datetime.now()
            parcel_info.days_in_transit = (current_date - date).days

        for event in data['ResultList'][0]['TrackInfo']['TrackEventDetails']:
            parcel_event = base.ParcelEvent()
            date = dateparser.parse(event['CreatedOn'])
            if date is not None:
                parcel_event.date = date
            location = event['ProcessLocation']
            if location is not None and location != "":
                parcel_event.location = location
            parcel_event.message = event['ProcessContent']
            parcel_event.company_name = self.company_name
            parcel_info.events_log.append(parcel_event)

        tracker_other = base.find_tracker_by_domain(base.get_domain_from_url(data['ResultList'][0]['TrackInfo']['ProviderSite']))
        if tracker_other is not None and len(parcel_info.tracking_numbers) > 1:
            parcel_info_new = tracker_other.get_parcel_info(parcel_info.tracking_numbers[1])
            parcel_info.events_log.extend(parcel_info_new.events_log)

        parcel_info.events_log.sort(reverse=True)

        return parcel_info


base.TRACKERS.append(YunExpressTracker())
