# mock-yummy-rides-api
Mock server for [Yummy Rides' Corporate Integrations API](https://bump.sh/rodolfofrancoyummy/doc/corporate-integrations-api).


## Tech stack and architecture

This is a Docker Compose application that consists of two services:
- FastAPI application containing three API routers:
  - `endpoints`: The actual Yummy Rides API endpoints for creating a quotation, creating a trip, checking a trip's status, force cancelling and force completing a trip.
  - `webhook`: Endpoints that simulate an automatic operation of the Yummy Rides system, trigger the appropriate call to the webhook URL, and return a response containing the payload sent to the webhook.
  - `webhook-test`: Has a single endpoint to use for testing the webhook calls, which just logs the payload to the console and returns a successful response.
- MongoDB database to store and manage the data (namely: quotations, trips, and trip service types).


## Setup and use

1. Copy the `env-sample` file to `.env` and replace the values of the variables:
```bash
cp env-sample .env
```

2. Build and run the Docker Compose application:
```
docker compose build
docker compose up
```

Use `docker-compose` if `docker compose` doesn't work on your system.
