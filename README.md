# TripAdivsor Hotel Scraper
A web app that scrapes hotel details in [www.tripadvisor.com](TripAdvisor.com). 
## Languages used
The scraper is written primarily in **Python**, using Playwright and Selectolax. The scraper runs in asynchronous method in order to execute and scrape multiple URLs simultaneously. Then, the server is built using Flask, where the APIs are setup and executed.

Vue is used for the frontend for this web app, using the Vite tool.

Also, this uses SQLite as the database.
## Installation
Before everything else, make sure the latest versions of Python and NodeJS is installed on your machine.

### Backend
1. Create a virtual environment, and activate it
2. Run `pip install -r requirements.txt` to install backend dependencies
3. Run `playwright browsers` to install browsers to be used for Playwright
4. Run `python app.py` to start running the backend

## Frontend
1. Open another terminal, and navigate to the frontend folder using `cd frontend`
2. Install node packages using `npm install`
3. Then run `npm run dev`

## Additional setup
For scraping data, it is recommended to add proxies so that the process runs smoothly and your IP won't get blocked often. To add proxies, go to `settings.json` in the `backend\scraper` folder and add your proxy addresses there.
