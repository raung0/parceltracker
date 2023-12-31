import sys

from parceltracker import base

def main():
    if len(sys.argv) < 2:
        print("Usage: main.py <tracking_number>")
        return

    tracking_number = sys.argv[1]

    parcel_info = base.get_parcel_info(tracking_number)
    if parcel_info.to == '':
        print("Failed to get parcel information for tracking number: {}".format(tracking_number))
        return

    print(parcel_info.pretty_print())

if __name__ == "__main__":
    main()

