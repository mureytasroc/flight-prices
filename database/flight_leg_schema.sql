CREATE TYPE cabin AS ENUM ('ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST');

CREATE TABLE flight_leg (
  itinerary_id INT NOT NULL REFERENCES itinerary,
  departure CHAR(3) NOT NULL,
  arrival CHAR(3) NOT NULL,
  num_stops SMALLINT NOT NULL CHECK (num_stops >= 0), -- Number of stops planned on the segment for technical or operation purpose i.e. refueling
  airline CHAR(2) NOT NULL REFERENCES airline, -- The airline marketing the flight
  flight_number VARCHAR(4) NOT NULL, -- The flight number as assigned by the airline
  aircraft CHAR(3) NULL REFERENCES aircraft, -- The aircraft operating the flight
  operator CHAR(2) NOT NULL REFERENCES airline, -- The operating airline
  cabin cabin NULL, -- quality of service offered in the cabin where the seat is located in this flight. Economy, premium economy, business or first class
  fare_basis VARCHAR(32) NULL, -- Fare basis specifying the rules of a fare. Usually, though not always, is composed of the booking class code followed by a set of letters and digits representing other characteristics of the ticket, such as refundability, minimum stay requirements, discounts or special promotional elements.
  class CHAR(1) NULL, -- The code of the booking class, a.k.a. class of service or Reservations/Booking Designator (RBD)
  num_incl_checked_bags SMALLINT NULL, -- number of free checked bags for this flight leg
  incl_checked_bag_lbs SMALLINT NULL -- max allowed weight in lbs of checked bag (rounded down)
);
