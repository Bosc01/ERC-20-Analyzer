# Token Transfer Monitor
Web application that tracks Ethereum token transfers using the Etherscan API.
## Features
- Monitor token transfers in real-time
- Support for popular tokens such as WETH, USDC, USDT
- View transfer details including addresses, amounts, and timestamps
- Export data to CSV format
- Clean and user-friendly interface
## How to Use
1. Get a free API key from [etherscan.io]
2. Choose a token from the dropdown or enter a custom contract address
3. Enter your API key in the sidebar
4. Click "Fetch New Data" to load recent transfers
5. View the results in the table below
## Installation
To run:
bash
pip install -r requirements.txt
streamlit run app.py
## Requirements
- Python
- Streamlit
- Pandas
- Requests
## About
This project demonstrates blockchain data visualization and API integration using Python and Streamlit.