CREATE TABLE price (
  itinerary_id INT NOT NULL REFERENCES itinerary,
  recorded_at TIMESTAMPTZ NOT NULL, -- timestamp at which this price was recorded
  currency CHAR(3) NOT NULL, -- usually USD, but not always
  total_price DECIMAL(8,2) NOT NULL CHECK (total_price >= 0),
  checked_bag_price DECIMAL(6,2) NULL CHECK (checked_bag_price >= 0), -- if null, price determined by airline policy
  num_bookable_seats SMALLINT NOT NULL CHECK (1 <= num_bookable_seats AND num_bookable_seats <= 9) -- number of seats at this price bookable in a single request, in [1..9]
);
