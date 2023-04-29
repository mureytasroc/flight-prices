CREATE TYPE cabin AS ENUM ('ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST');

CREATE TABLE flight_leg (
  itinerary_id INT NOT NULL REFERENCES itinerary,
  departure_id CHAR(3) NOT NULL REFERENCES airport,
  arrival_id CHAR(3) NOT NULL REFERENCES airport,
  num_stops SMALLINT NOT NULL CHECK (num_stops >= 0), -- Number of stops planned on the segment for technical or operation purpose i.e. refueling
  airline CHAR(2) NOT NULL REFERENCES airline, -- The airline marketing the flight
  flight_number VARCHAR(4) NOT NULL, -- The flight number as assigned by the airline
  operator CHAR(2) NOT NULL REFERENCES airline, -- The operating airline
  cabin cabin NOT NULL, -- quality of service offered in the cabin where the seat is located in this flight. Economy, premium economy, business or first class
  fare_basis VARCHAR(32) -- Fare basis specifying the rules of a fare. Usually, though not always, is composed of the booking class code followed by a set of letters and digits representing other characteristics of the ticket, such as refundability, minimum stay requirements, discounts or special promotional elements.
);
