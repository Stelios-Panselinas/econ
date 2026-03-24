import streamlit as st
import json
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px

# --- CONFIG ---
st.set_page_config(page_title="Cloud Wealth Tracker", layout="centered")
st.title("☁️ Cloud-Synced Finance Tracker")

# --- GOOGLE SHEETS SETUP ---
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Ensure 'credentials.json' is in your script folder!
    creds_dict = json.loads(st.secrets["google_creds"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def load_data():
    try:
        client = get_gspread_client()
        # Change this to match your actual Google Sheet name
        sheet = client.open("Monthly_Finances").sheet1
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
        if not df.empty:
            df['Date_Sort'] = pd.to_datetime(df['Month'], format='%B %Y')
            return df.sort_values(by="Date_Sort")
        return df
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return pd.DataFrame()

data = load_data()

# --- SIDEBAR: ENTRY ---
st.sidebar.header("📝 Log a Month")
with st.sidebar.form("entry_form", clear_on_submit=True):
    month_val = st.date_input("Month")
    month_str = month_val.strftime("%B %Y")
    
    start_bal = st.number_input("Starting $", min_value=0.0)
    income = st.number_input("Income $", min_value=0.0)
    end_bal = st.number_input("Ending $", min_value=0.0)
    notes = st.text_area("Notes")
    
    if st.form_submit_button("Sync to Cloud"):
        expenses = (start_bal + income) - end_bal
        new_row = [month_str, start_bal, income, end_bal, expenses, notes]
        
        client = get_gspread_client()
        sheet = client.open("Monthly_Finances").sheet1
        
        # Check if month exists to update it, else append
        cell = sheet.find(month_str)
        if cell:
            sheet.update(f"A{cell.row}:F{cell.row}", [new_row])
        else:
            sheet.append_row(new_row)
            
        st.sidebar.success("Synced successfully!")
        st.rerun()

# --- DASHBOARD ---
if not data.empty:
    latest = data.iloc[-1]
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Latest Income", f"${latest['Income']:,.2f}")
    m2.metric("Expenses", f"${latest['Expenses']:,.2f}")
    m3.metric("Ending Balance", f"${latest['End_Balance']:,.2f}")

    # Chart
    fig = px.bar(data, x="Month", y=["Income", "Expenses"], barmode="group",
                 color_discrete_sequence=["#00CC96", "#EF553B"])
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 History")
    st.dataframe(data.drop(columns=['Date_Sort'], errors='ignore'), use_container_width=True)
else:
    st.info("No data found in Google Sheets. Add your first month!")
