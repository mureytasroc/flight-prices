CREATE TABLE itinerary (
  id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  source CHAR(3) NOT NULL,
  destination CHAR(3) NOT NULL,
  num_legs SMALLINT NOT NULL CHECK (num_legs > 0), -- the number of legs in the itinerary
  airline CHAR(2) NULL REFERENCES airline, -- null if the itinerary is multi-airline
  blacklisted_in_EU BOOLEAN NOT NULL -- When the flight has a marketing or/and operating airline that is identified as blacklisted by the European Commission.
);

