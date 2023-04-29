CREATE TABLE itinerary (
  id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  source_id CHAR(3) NOT NULL REFERENCES airport,
  destination_id CHAR(3) NOT NULL REFERENCES airport,
  legs SMALLINT NOT NULL CHECK (legs > 0), -- the number of legs in the itinerary
  airline CHAR(2) NULL REFERENCES airline, -- null if the itinerary is multi-airline
  one_way BOOLEAN NOT NULL, -- If true, the flight offer can be combined with other oneWays flight-offers to complete the whole journey (one-Way combinable feature).
  non_homogenous BOOLEAN NOT NULL, -- If true, upon completion of the booking, this pricing solution is expected to yield multiple records (a record contains booking information confirmed and stored, typically a Passenger Name Record (PNR), in the provider GDS or system)
  refundable BOOLEAN NOT NULL, -- If true, the fare is refundable upon cancellation
  no_restriction BOOLEAN NOT NULL, -- Not specified in Amadeus docs (TODO: investigate)
  no_penalty BOOLEAN NOT NULL, -- Not specified in Amadeus docs (TODO: investigate) maybe no change fees
  blacklisted_in_EU BOOLEAN NOT NULL -- When the flight has a marketing or/and operating airline that is identified as blacklisted by the European Commission.
);

