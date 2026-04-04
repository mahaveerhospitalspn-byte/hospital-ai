
import streamlit as st
import pandas as pd
import os
from datetime import datetime

SALES_FILE = "Pharmacy_Sales.csv"

def pharmacy_dashboard():

    st.title("💊 Pharmacy Sales Dashboard")

    st.markdown("---")

    uploaded_file = st.file_uploader(
        "Upload Marg Sales CSV",
        type=["csv"]
    )

    if uploaded_file is not None:

        df_upload = pd.read_csv(uploaded_file)

        if os.path.exists(SALES_FILE):
            df_upload.to_csv(SALES_FILE, mode="a", header=False, index=False)
        else:
            df_upload.to_csv(SALES_FILE, index=False)

        st.success("Sales Data Imported Successfully")

    st.markdown("---")

    if os.path.exists(SALES_FILE):

        df = pd.read_csv(SALES_FILE, on_bad_lines="skip")

        if "Date" in df.columns and "Net Amount" in df.columns:

            df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)

            today = datetime.now().date()

            today_sale = df[df["Date"].dt.date == today]["Net Amount"].sum()

            month_sale = df[
                (df["Date"].dt.month == today.month) &
                (df["Date"].dt.year == today.year)
            ]["Net Amount"].sum()

            total_sale = df["Net Amount"].sum()

            col1, col2, col3 = st.columns(3)

            col1.metric("Today's Sale", f"₹ {today_sale:,.2f}")
            col2.metric("This Month", f"₹ {month_sale:,.2f}")
            col3.metric("Total Collection", f"₹ {total_sale:,.2f}")

        else:
            st.warning("CSV must contain 'Date' and 'Net Amount' columns")

    else:

        import streamlit as st
        import pandas as pd
        import os
        from datetime import datetime

        SALES_FILE = "Pharmacy_Sales.csv"

def pharmacy_dashboard():

    st.title("💊 Pharmacy Sales Dashboard")

    st.markdown("---")

    uploaded_file = st.file_uploader(
        "Upload Marg Sales CSV",
        type=["csv"]
    )

    if uploaded_file is not None:

        df_upload = pd.read_csv(uploaded_file)

        if os.path.exists(SALES_FILE):
            df_upload.to_csv(SALES_FILE, mode="a", header=False, index=False)
        else:
            df_upload.to_csv(SALES_FILE, index=False)

        st.success("Sales Data Imported Successfully")

    st.markdown("---")

    if os.path.exists(SALES_FILE):

        df = pd.read_csv(SALES_FILE, on_bad_lines="skip")

        if "Date" in df.columns and "Net Amount" in df.columns:

            df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)

            today = datetime.now().date()

            today_sale = df[df["Date"].dt.date == today]["Net Amount"].sum()

            month_sale = df[
                (df["Date"].dt.month == today.month) &
                (df["Date"].dt.year == today.year)
            ]["Net Amount"].sum()

            total_sale = df["Net Amount"].sum()

            col1, col2, col3 = st.columns(3)

            col1.metric("Today's Sale", f"₹ {today_sale:,.2f}")
            col2.metric("This Month", f"₹ {month_sale:,.2f}")
            col3.metric("Total Collection", f"₹ {total_sale:,.2f}")

        else:
            st.warning("CSV must contain 'Date' and 'Net Amount' columns")

    else:

        st.info("No Sales Data Available")