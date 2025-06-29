import streamlit as st
import pandas as pd
import requests
import sqlite3
import os
from datetime import datetime

st.set_page_config(page_title="Token Monitor", layout="wide")
st.title("Token Transfer Monitor")
st.write("Track Ethereum token transfers in real time")

def setup_db():
    conn = sqlite3.connect("transfers.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transfers (
            hash TEXT PRIMARY KEY,
            block_num INTEGER,
            time_stamp INTEGER,
            from_addr TEXT,
            to_addr TEXT,
            amount TEXT,
            symbol TEXT,
            decimals INTEGER
        )
    ''')
    conn.commit()
    conn.close()

setup_db()

st.sidebar.header("Configuration")

token_choice = st.sidebar.selectbox("Choose Token:", [
    "WETH", 
    "USDC", 
    "USDT", 
    "Other"
])

if token_choice == "WETH":
    default_contract = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
elif token_choice == "USDC":  
    default_contract = "0xA0b86a33E6441E64b8c2B1B2B4FACc5A8cC6A3A7"
elif token_choice == "USDT":
    default_contract = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
else:
    default_contract = ""

if token_choice == "Other":
    contract = st.sidebar.text_input("Enter Contract Address:", placeholder="0x...")
    if not contract:
        st.sidebar.warning("Please enter a contract address")
else:
    contract = st.sidebar.text_input("Contract Address:", value=default_contract)

api_key = st.sidebar.text_input("Etherscan API Key:", type="password", 
                               help="Get your free API key from etherscan.io")

st.sidebar.write("")

if st.sidebar.button("Fetch New Data", type="primary"):
    if not api_key:
        st.error("Please enter your Etherscan API key first!")
    elif not contract:
        st.error("Please enter a token contract address!")
    else:
        st.info(f"Fetching recent transfers for {token_choice}...")
        
        with st.spinner("Getting data from Etherscan..."):
            try:
                etherscan_url = "https://api.etherscan.io/api"
                request_params = {
                    'module': 'account',
                    'action': 'tokentx',
                    'contractaddress': contract,
                    'page': 1,
                    'offset': 50,
                    'sort': 'desc',
                    'apikey': api_key
                }
                
                api_response = requests.get(etherscan_url, params=request_params)
                response_data = api_response.json()
                
                if response_data['status'] == '1':
                    transfer_list = response_data['result']
                    
                    database_connection = sqlite3.connect("transfers.db")
                    db_cursor = database_connection.cursor()
                    
                    successful_saves = 0
                    for transaction in transfer_list:
                        try:
                            db_cursor.execute('''
                                INSERT OR REPLACE INTO transfers 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                transaction['hash'],
                                int(transaction['blockNumber']),
                                int(transaction['timeStamp']),
                                transaction['from'],
                                transaction['to'],
                                transaction['value'],
                                transaction['tokenSymbol'],
                                int(transaction['tokenDecimal'])
                            ))
                            successful_saves += 1
                        except Exception as save_error:
                            continue
                    
                    database_connection.commit()
                    database_connection.close()
                    
                    st.success(f"Successfully saved {successful_saves} transfers to database!")
                
                else:
                    st.error(f"Etherscan API returned an error: {response_data.get('message', 'Unknown error')}")
                    
            except Exception as error:
                st.error(f"Something went wrong: {error}")
                st.write("This might be a network issue or invalid API key.")

st.header("Recent Token Transfers")

try:
    db_connection = sqlite3.connect("transfers.db")
    transfers_dataframe = pd.read_sql_query('''
        SELECT hash, block_num, time_stamp, from_addr, to_addr, amount, symbol, decimals
        FROM transfers 
        ORDER BY time_stamp DESC 
        LIMIT 25
    ''', db_connection)
    db_connection.close()
    
    if not transfers_dataframe.empty:
        transfers_dataframe['Time'] = transfers_dataframe['time_stamp'].apply(
            lambda timestamp: datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        )
        transfers_dataframe['Transaction Hash'] = transfers_dataframe['hash'].apply(
            lambda hash_value: f"{hash_value[:12]}...{hash_value[-8:]}"
        )
        transfers_dataframe['From Address'] = transfers_dataframe['from_addr'].apply(
            lambda address: f"{address[:10]}...{address[-6:]}"
        )
        transfers_dataframe['To Address'] = transfers_dataframe['to_addr'].apply(
            lambda address: f"{address[:10]}...{address[-6:]}"
        )
        
        def format_token_amount(row):
            try:
                actual_amount = float(row['amount']) / (10 ** row['decimals'])
                if actual_amount >= 1000:
                    return f"{actual_amount/1000:.2f}K {row['symbol']}"
                else:
                    return f"{actual_amount:.4f} {row['symbol']}"
            except:
                return f"{row['amount']} {row['symbol']}"
        
        transfers_dataframe['Token Amount'] = transfers_dataframe.apply(format_token_amount, axis=1)
        
        display_table = transfers_dataframe[['Transaction Hash', 'block_num', 'Time', 'From Address', 'To Address', 'Token Amount']]
        display_table.columns = ['Transaction Hash', 'Block Number', 'Date & Time', 'From', 'To', 'Amount']
        
        st.dataframe(display_table, use_container_width=True, hide_index=True)
        
        csv_data = display_table.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv_data,
            file_name=f"token_transfers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        st.info(f"Showing {len(transfers_dataframe)} most recent transfers")
    else:
        st.info("No transfer data found. Click 'Fetch New Data'")
        
except Exception as database_error:
    st.error(f"Database error: {database_error}")
    st.write("Try fetching new data to create database.")



st.write("---")
st.write("Built with Streamlit")