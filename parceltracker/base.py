import re as regex
from datetime import datetime
import copy
import pycountry
from flag import flag

import concurrent.futures


class Colors:
    """ ANSI color codes """
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    END = "\033[0m"
    # cancel SGR codes if we don't write to a terminal
    if not __import__("sys").stdout.isatty():
        for _ in dir():
            if isinstance(_, str) and _[0] != "_":
                locals()[_] = ""
    else:
        # set Windows console in VT mode
        if __import__("platform").system() == "Windows":
            kernel32 = __import__("ctypes").windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            del kernel32


class ParcelEvent:
    company_name: str = ""
    date: datetime = datetime.now()
    location: str | None = None
    message: str = ""

    def pretty_print(self) -> str:
        final = f"[{Colors.BROWN}{self.company_name}{Colors.END}] {self.date.strftime('%d.%m.%Y %H:%M:%S')}"
        if self.location is not None and self.location != "":
            final += f" - {self.location}"
        final += f" - {self.message}"
        return final

    def __init__(self) -> None:
        self.company_name = ""
        self.date = datetime.now()
        self.location = None
        self.message = ""

    def __str__(self) -> str:
        return f"ParcelEvent(company_name={self.company_name}, date={self.date}, location={self.location}, message={self.message})"

    def __repr__(self) -> str:
        return str(self)

    # Compare dates
    def __lt__(self, other): return self.date < other.date
    def __le__(self, other): return self.date <= other.date
    def __gt__(self, other): return self.date > other.date
    def __ge__(self, other): return self.date >= other.date


class ParcelInfo:
    tracking_numbers: list[str] = []
    to: str = ""
    origin: str = ""
    weight: float = 0.0
    channel: str = ""
    provider: str = ""
    days_in_transit: int = 0

    events_log: list[ParcelEvent] = []

    def pretty_print(self) -> str:
        class Country:
            name: str = ""
            alpha_2: str = ""
            def __init__(self, name: str, alpha_2: str) -> None:
                self.name = name
                self.alpha_2 = alpha_2

        try:
            to = pycountry.countries.lookup(self.to.split()[-1])
        except LookupError:
            to = Country(self.to, "ZW")
        try:
            origin = pycountry.countries.lookup(self.origin.split()[-1])
        except LookupError:
            origin = Country(self.origin, "ZW")

        final = f"{Colors.PURPLE}Tracking numbers{Colors.END}: {', '.join(self.tracking_numbers)}\n"
        final += f"{Colors.PURPLE}To{Colors.END}: {to.name} {flag(to.alpha_2.upper())}\n"
        final += f"{Colors.PURPLE}Origin{Colors.END}: {origin.name} {flag(origin.alpha_2.upper())}\n"
        final += f"{Colors.PURPLE}Weight{Colors.END}: {self.weight}kg\n"
        final += f"{Colors.PURPLE}Channel{Colors.END}: {self.channel}\n"
        final += f"{Colors.PURPLE}Provider{Colors.END}: {self.provider}\n"
        final += f"{Colors.PURPLE}Days in transit{Colors.END}: {self.days_in_transit}\n"
        final += f"{Colors.PURPLE}Events{Colors.END}:\n"
        max_company_name_events = max([len(event.company_name) for event in self.events_log])
        for event in self.events_log:
            final += ' ' * (max_company_name_events - len(event.company_name) + 3)
            final += f"{event.pretty_print()}\n"
        return final

    def __init__(self) -> None:
        self.tracking_numbers = []
        self.events_log = []
        self.to = ""
        self.origin = ""
        self.weight = 0.0
        self.channel = ""
        self.provider = ""
        self.days_in_transit = 0

    def __str__(self) -> str:
        return f"ParcelInfo(tracking_numbers={self.tracking_numbers}, to={self.to}, origin={self.origin}, weight={self.weight}, channel={self.channel}, provider={self.provider}, days_in_transit={self.days_in_transit})"

    def __repr__(self) -> str:
        return str(self)


class ParcelTracker:
    company_name: str = "ExampleCompany"
    provider_domain: str = "example.com"
    tracking_number_regex: str = r''

    def get_parcel_info(self, tracking_number: str) -> ParcelInfo:
        parcel_info = ParcelInfo()
        return copy.deepcopy(parcel_info)


TRACKERS: list[ParcelTracker] = [ ]


def get_domain_from_url(url: str) -> str:
    domain = url.split('/')[2]
    if domain.startswith('www.'):
        return domain[4:]
    return domain


def find_tracker_by_domain(domain: str) -> ParcelTracker | None:
    for tracker in TRACKERS:
        if tracker.provider_domain == domain:
            return tracker
    return None


def find_trackers_by_tracking_number(tracking_number: str) -> list[ParcelTracker]:
    trackers = []
    for tracker in TRACKERS:
        if tracker.tracking_number_regex != "" and regex.match(tracker.tracking_number_regex, tracking_number) is not None:
            trackers.append(tracker)
    return trackers


def merge_parcels_info(parcels: list[ParcelInfo]) -> ParcelInfo:
    parcel_info = ParcelInfo()
    for parcel in parcels:
        parcel_info.tracking_numbers.extend(parcel.tracking_numbers)
        if parcel_info.to == "":
            parcel_info.to = parcel.to
        if parcel_info.origin == "":
            parcel_info.origin = parcel.origin
        if parcel_info.weight == 0.0:
            parcel_info.weight = parcel.weight
        if parcel_info.channel == "":
            parcel_info.channel = parcel.channel
        if parcel_info.provider == "":
            parcel_info.provider = parcel.provider
        if parcel_info.days_in_transit == 0:
            parcel_info.days_in_transit = parcel.days_in_transit
        parcel_info.events_log.extend(parcel.events_log)
    parcel_info.events_log.sort(reverse=True)
    return copy.deepcopy(parcel_info)


def get_parcel_info(tracking_number: str) -> ParcelInfo:
    tracker = find_trackers_by_tracking_number(tracking_number)
    if len(tracker) == 0:
        raise Exception(f"Could not find a tracker for tracking number {tracking_number}")

    parcels_info = []

    def get_parcel_info_wrapper(t):
        return t.get_parcel_info(tracking_number)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(get_parcel_info_wrapper, t) for t in tracker]
        concurrent.futures.wait(futures)
        for future in futures:
            parcels_info.append(future.result())

    return merge_parcels_info(parcels_info)


DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'no-cors',
    'Sec-Fetch-Site': 'same-site',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    }

from .trackers import yunexpress, speedy, fedex
