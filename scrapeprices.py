import airportsdata
import argparse
from datetime import datetime, timedelta
from decimal import Decimal
from math import floor
import os
import psycopg2
import psycopg2.extras
import requests
from time import sleep
from tqdm import tqdm

KG_LBS = 2.20462262185
REQUEST_PAUSE_SECS = 0.5

parser = argparse.ArgumentParser()
parser.add_argument("-z", "--horizon", help="The number of days in the future to record flight prices (by departure date).", type=int)
args = parser.parse_args()

assert args.horizon >= 0, "Horizon argument must be positive"

airports = airportsdata.load()

auth_headers = {}
def refresh_bearer():
    global auth_headers
    sleep(REQUEST_PAUSE_SECS)
    res = requests.post(
            "https://test.api.amadeus.com/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": os.environ["AMADEUS_CLIENT_ID"],
                "client_secret": os.environ["AMADEUS_CLIENT_SECRET"]})
    res.raise_for_status()
    bearer_token = res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {bearer_token}"}

def auth_get(*args, **kwargs):
    headers = kwargs.get("headers", {})
    sleep(REQUEST_PAUSE_SECS)
    res = requests.get(*args, headers={**auth_headers, **headers}, **kwargs)
    if res.status_code == 401:
        refresh_bearer()
        res = requests.get(*args, headers={**auth_headers, **headers}, **kwargs)
    res.raise_for_status()
    return res.json()

iata_airports = {airport["iata"] for airport in airports.values() if airport["iata"]}

entities = {
  "airline": dict(),
  "aircraft": dict()
}
def pull_table(db_conn, table):
    with db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(f"SELECT * FROM {table}")
        for row in cur.fetchall():
            entities[table][row["iata_code"]] = row["name"]
def update_table(db_conn, table, new_entities):
    to_update = []
    existing_entities = entities[table]
    for iata_code, name in new_entities.items():
        if iata_code not in existing_entities or existing_entities[iata_code] != name:
            to_update.append((iata_code, name))
            existing_entities[iata_code] = name
    if to_update:
        with db_conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur, f"INSERT INTO {table} (iata_code, name) VALUES %s ON CONFLICT (iata_code) DO UPDATE SET name = EXCLUDED.name",
                to_update, template=None, page_size=100
            )

db_conn = psycopg2.connect(user="postgres",
                              password=os.environ["POSTGRES_PASSWORD"],
                              host="127.0.0.1",
                              port="5432",
                              database="flight_prices")

try:
    pull_table(db_conn, "airline")
    pull_table(db_conn, "aircraft")
    
    for days_in_future in range(1, args.horizon+1):
        departure_date = (datetime.today() + timedelta(days=days_in_future)).date()
        print(f"Saving flights and prices for departure date: {departure_date}")
        for iata_code in tqdm(iata_airports):
            destinations_res = auth_get("https://test.api.amadeus.com/v1/airport/direct-destinations",
                    params={"departureAirportCode": iata_code})
            for destination in destinations_res.get("data", []):
                recorded_at = datetime.utcnow()
                res = auth_get("https://test.api.amadeus.com/v2/shopping/flight-offers",
                        params={
                            "originLocationCode": iata_code,
                            "destinationLocationCode": destination["iataCode"],
                            "departureDate": departure_date,
                            "adults": 1,
                            "currencyCode": "USD"})
                if "dictionaries" in res:
                    update_table(db_conn, "airline", res["dictionaries"]["carriers"])
                    update_table(db_conn, "aircraft", res["dictionaries"]["aircraft"])
                for flight_offer in res.get("data", []):
                    num_bookable_seats = flight_offer["numberOfBookableSeats"]
                    price = flight_offer["price"]
                    currency = price["currency"]
                    total_price = Decimal(price["grandTotal"])
                    checked_bag_price = None
                    for additional_service in price.get("additionalServices", []):
                        if additional_service["type"] == "CHECKED_BAGS":
                            checked_bag_price = Decimal(additional_service["amount"])
                    for itinerary in flight_offer["itineraries"]:
                        with db_conn.cursor() as cur:
                            segments = itinerary["segments"]
                            destination_code = segments[-1]["arrival"]["iataCode"]
                            if not segments:
                                continue
                            airline = segments[0]["carrierCode"]
                            for segment in segments:
                                if segment["carrierCode"] != airline:
                                    airline = None
                            blacklisted_in_EU = any(segment.get("blacklistedInEU", False) for segment in segments)
                            cur.execute("""
                                INSERT INTO itinerary (source, destination, num_legs, airline, blacklisted_in_EU)
                                VALUES (%s,%s,%s,%s,%s)
                                RETURNING ID""",
                                (iata_code, destination_code, len(segments), airline, blacklisted_in_EU))
                            itinerary_id = cur.fetchone()[0]
                            cur.execute("INSERT INTO price (itinerary_id, recorded_at, currency, total_price, checked_bag_price, num_bookable_seats) VALUES (%s,%s,%s,%s,%s,%s)",
                                (itinerary_id, recorded_at, currency, total_price, checked_bag_price, num_bookable_seats))
                            flight_legs = []
                            segments_dict = dict()
                            for segment in segments:
                                segments_dict[segment["id"]] = segment
                            for traveler_pricing in flight_offer.get("travelerPricings", []):
                                for fare_detail in traveler_pricing.get("fareDetailsBySegment", []):
                                    segment_id = fare_detail["segmentId"]
                                    if segment_id not in segments_dict:
                                        continue
                                    segments_dict[segment_id] = {**fare_detail, **segments_dict[segment_id]}
                            for segment in segments_dict.values():
                                departure = segment["departure"]["iataCode"]
                                arrival = segment["arrival"]["iataCode"]
                                num_stops = len(segment.get("stops", []))
                                airline = segment["carrierCode"]
                                flight_number = segment["number"]
                                aircraft = segment.get("aircraft", {}).get("code")
                                operator = segment["operating"]["carrierCode"] if "operating" in segment else airline
                                cabin = segment.get("cabin")
                                fare_basis = segment.get("fareBasis")
                                class_ = segment.get("class")
                                num_incl_checked_bags = 0
                                incl_checked_bag_lbs = None
                                incl_checked_bags = segment.get("includedCheckedBags")
                                if incl_checked_bags and "quantity" in incl_checked_bags:
                                    num_incl_checked_bags = incl_checked_bags["quantity"]
                                    incl_checked_bag_lbs = incl_checked_bags.get("weight")
                                    if incl_checked_bag_lbs:
                                        if incl_checked_bags.get("weightUnit") == "KG":
                                            incl_checked_bag_lbs *= KG_LBS
                                        incl_checked_bag_lbs = floor(incl_checked_bag_lbs)
                                flight_legs.append((itinerary_id, departure, arrival, num_stops, airline, flight_number, aircraft, operator,
                                    cabin, fare_basis, class_, num_incl_checked_bags, incl_checked_bag_lbs))
                            psycopg2.extras.execute_values(
                                cur, """INSERT INTO flight_leg (itinerary_id, departure, arrival, num_stops, airline, flight_number, aircraft, operator,
                                    cabin, fare_basis, class, num_incl_checked_bags, incl_checked_bag_lbs) VALUES %s""",
                                flight_legs, template=None, page_size=100
                            )
                        db_conn.commit()
    print("Done!")
finally:
    db_conn.close()
