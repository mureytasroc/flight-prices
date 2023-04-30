# flight-prices

This script loads flights data from the [Amadeus API](https://developers.amadeus.com/self-service/category/air) (namely, the [airport routes](https://developers.amadeus.com/self-service/category/air/api-doc/flight-offers-search/api-reference) and [flight offers](https://developers.amadeus.com/self-service/category/air/api-doc/flight-offers-search/api-reference) endpoints) into a local Postgres/TimescaleDB database.

Eventually, the data in this database will be used to predict future airfare price drops. This was inspired by my friend saving $400 on a flight (SAN-NYC) by waiting for a price drop. When a huge drop like this occurs it is an obvious buying opportunity, but smaller drops are less clear. When is the right time to buy? This project aims to eventually answer that question, taking into account lots of filters and details of the flight you're hoping to book.

If you want to set up your own flights database using this script, you should install necessary dependencies using [Poetry](https://github.com/python-poetry/poetry), with `poetry install`.

You should also set up a local PostgreSQL 12 / TimescaleDB instance, with a database called `flight_prices`. Within this database, you should create all the tables specified in [`/database`](/database). Change the password of the `postgres` user and save it as an environment variable, as described below.

A number of environment variables are required for this script to work properly (replace `EXAMPLE` with the value of your secret). You will have to sign up for free API credentials with Amadeus.
```
export AMADEUS_CLIENT_ID=EXAMPLE
export AMADEUS_CLIENT_SECRET=EXAMPLE
export POSTGRES_PASSWORD=EXAMPLE
```

Then, you can run this script with `poetry run -- python scrapeprices.py --horizon=1`. The `horizon` is the number of days in the future to lookahead for flights (1 in this example command).

To run this script as a cron job every midnight, you should set it up as a systemd unit (assuming you are running on Linux):

`sudo vim /etc/systemd/system/scrapeprices.service`

(Replace the python link in the below config to the output of `poetry run which python`, and the `EXAMPLE` values in the environment variables with your actual values.)

```
[Unit]
Description=Scrapeprices Service
Wants=scrapeprices.timer

[Service]
ExecStart=/home/mureytasroc/.cache/pypoetry/virtualenvs/flight-prices-JLnVbR-A-py3.11/bin/python /home/mureytasroc/git/flight-prices/scrapeprices.py --horizon=31
Restart=on-failure
User=mureytasroc

# Script environment variables
Environment=AMADEUS_CLIENT_ID=EXAMPLE
Environment=AMADEUS_CLIENT_SECRET=EXAMPLE
Environment=POSTGRES_PASSWORD=EXAMPLE

[Install]
WantedBy=multi-user.target
```

`sudo vim /etc/systemd/system/scrapeprices.timer`

```
[Unit]
Description=Scrapes flight price data daily
Requires=scrapeprices.service

[Timer]
Unit=scrapeprices.service
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

(You can change the `horizon` parameter in the script to whatever you want, based on your available resources.)

`sudo systemctl daemon-reload`
`sudo systemctl enable scrapeprices.service`
`sudo systemctl start scrapeprices.service`
