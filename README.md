# Binance Trade History

This repository contains a Flask web application that retrieves trade history data from the Binance API and provides various visualizations and analysis of the data.

## Requirements

To run this application, you need to have the following dependencies installed:

- Python (version 3.6 or later)
- Flask
- pandas
- seaborn
- matplotlib
- requests

You can install these dependencies by running the following command:

```
pip install -r requirements.txt
```

## Usage

1. Clone the repository:

```
git clone https://github.com/aalgohary/binance.git
cd binance-trade-history
```

2. Run the application:

```
python app.py
```

3. Access the application:

Open your web browser and navigate to `http://localhost:5500`. You will see a form where you can enter the start day and capital per month. Fill in the required information and click the "Retrieve Data" button.

4. View trade history and analysis:

After clicking the "Retrieve Data" button, the application will retrieve the trade history data from the Binance API and perform various calculations and visualizations. Once the processing is complete, you will be redirected to a page showing the trade history table, total net profit, winning percentage, profits per month, and cumulative profit percentage.

## Files

- `app.py`: The main Flask application file that handles the routing and data processing.
- `templates/index.html`: The HTML template file for the home page.
- `templates/trade_history.html`: The HTML template file for displaying the trade history and analysis.
- `static/styles.css`: CSS file for styling the web pages.
- `static/script.js`: JavaScript file for client-side functionality.
- `static/loading.gif`: Loading spinner image.

## Notes

- The application uses the Binance API to retrieve trade history data. You need to provide valid Binance API keys and secrets to access the data.
- The application calculates various metrics and visualizations based on the trade history data, including total net profit, winning percentage, profits per month, cumulative profit percentage, line chart, and heatmap.
- The trade history table and monthly profits table are displayed using HTML tables.
- The line chart is created using the Chart.js library.
- The heatmap is created using the seaborn and matplotlib libraries.
- The application saves the trade history table as a CSV file and the heatmap as an image file.

Feel free to explore and modify the code according to your needs. If you have any questions or issues, please open an issue on the repository page.
