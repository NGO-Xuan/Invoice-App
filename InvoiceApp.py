from fpdf import FPDF
import streamlit as st
import pandas as pd
import io

from datetime import datetime  # ✅ Ensure datetime is imported

# ✅ Initialize invoice_date in session state
if "invoice_date" not in st.session_state:
    st.session_state.invoice_date = datetime.today().date()


# Load the Excel file
@st.cache_data
def load_data():
    file_path = r"C:\Users\ngox\Documents\Personal Info\Price - Invoice\Price List.xlsx"
    df = pd.read_excel(file_path, engine="openpyxl")
    return df

df = load_data()

# Store invoice data in session state
if "invoice_data" not in st.session_state:
    st.session_state.invoice_data = pd.DataFrame(columns=["Brand", "NDC#", "Qty", "Expiration", "Condition", "Price", "Total"])

if "tracking_number" not in st.session_state:
    st.session_state.tracking_number = ""

# Create tabs
tab1, tab2 = st.tabs(["Price Search", "Invoice"])

# ------------------------- 🔹 TAB 1: PRICE SEARCH 🔹 -------------------------
with tab1:
    st.title("📊 Price Search Dashboard")

    # Search Inputs
    brand = st.text_input("🔍 Search by Brand:")
    ref_ndc = st.text_input("🔍 Search by Ref# (NDC):")
    item_type = st.text_input("🔍 Search by Type:")

    # Filter Data
    filtered_df = df.copy()
    if brand:
        filtered_df = filtered_df[filtered_df["Brand"].astype(str).str.contains(brand, case=False, na=False)]
    if ref_ndc:
        filtered_df = filtered_df[filtered_df["Ref# (NDC)"].astype(str).str.contains(ref_ndc, case=False, na=False)]
    if item_type:
        filtered_df = filtered_df[filtered_df["Type"].astype(str).str.contains(item_type, case=False, na=False)]

    # Show the filtered table
    st.write(f"Showing {len(filtered_df)} results:")

    # Add a "Select" button next to each row
    for i, row in filtered_df.iterrows():
        cols = st.columns(len(filtered_df.columns) + 1)  # Extra column for the button
        for j, col_name in enumerate(filtered_df.columns):
            cols[j].write(row[col_name])  # Display each column in its respective cell

        # "Select" button to add to invoice
        if cols[-1].button("➕ Select", key=f"select_{i}"):
            selected_data = pd.DataFrame([row[["Brand", "Ref# (NDC)", "Price"]]])
            selected_data.rename(columns={"Ref# (NDC)": "NDC#"}, inplace=True)
            selected_data["Qty"] = 1  # Default quantity
            selected_data["Expiration"] = ""
            selected_data["Condition"] = ""
            selected_data["Total"] = selected_data["Price"] * selected_data["Qty"]

            # Replace NaN with empty strings
            selected_data = selected_data.fillna("")

            # Append to invoice session state
            st.session_state.invoice_data = pd.concat([st.session_state.invoice_data, selected_data], ignore_index=True)
            st.success(f"✅ {row['Brand']} added to Invoice!")

with tab2:
    st.title("🧾 Invoice")

    if not st.session_state.invoice_data.empty:
        # **User selects Invoice Date**
        st.session_state.invoice_date = st.date_input("📅 Select Invoice Date:", st.session_state.invoice_date)

        # **Display only ONE table (Editable)**
        updated_invoice = st.data_editor(st.session_state.invoice_data, num_rows="dynamic", key="invoice_table")

        # **Refresh Button to Update Totals**
        if st.button("🔄 Refresh Totals"):
            # ✅ Recalculate the "Total" column when button is clicked
            updated_invoice["Total"] = updated_invoice["Qty"].astype(float) * updated_invoice["Price"].astype(float)

            # ✅ Save the updated values back to session state
            st.session_state.invoice_data = updated_invoice

            st.success("✅ Totals updated!")

        # **Calculate the Total Invoice Sum**
        total_invoice_sum = st.session_state.invoice_data["Total"].sum()

        # **Append "Total Invoice" Row**
        total_row = pd.DataFrame([{
            "Brand": "**Total Invoice**",
            "NDC#": "",
            "Qty": "",
            "Expiration": "",
            "Condition": "",
            "Price": "",
            "Total": total_invoice_sum
        }])

        invoice_with_total = pd.concat([st.session_state.invoice_data, total_row], ignore_index=True)

        # **Tracking & Payment Information**
        col1, col2 = st.columns([2, 1])
        with col1:
            st.session_state.tracking_number = st.text_input("📦 Tracking #", st.session_state.tracking_number)
        with col2:
            st.write("🚚 UPS")

        st.write(" ")
        st.write("💳 **Please Make Payment to Paypal**")
        st.write("Zelle: **derek@stripbuyer.com**")
        st.write(" ")

        st.write("🏢 **Strip Buyer Surplus LLC**")
        st.write("2664 Alfreda Way")
        st.write("Redding, CA 96002")

        st.write(" ")

        # **Buttons to save invoice**
        col1, col2 = st.columns(2)

        # 📄 Save to PDF
        with col2:
            if st.button("🖨️ Save to PDF"):
                pdf = FPDF(orientation="L", unit="mm", format="A4")  # Landscape mode for wider tables
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.add_page()

                # **Set Font**
                pdf.set_font("Arial", style="B", size=14)

                # **Invoice Date (Top Right)**
                invoice_date = st.session_state.invoice_date.strftime("%Y-%m-%d")
                pdf.cell(250, 10, "", border=0)  # Create space before date
                pdf.cell(25, 10, f"Invoice Date: {invoice_date}", ln=True, align="R")  # Align right

                # **Invoice Title (Centered)**
                pdf.cell(275, 10, "Invoice", ln=True, align="C")
                pdf.ln(10)

                pdf.set_font("Arial", size=10)

                # **Define Column Names & Adjusted Widths**
                col_names = ["Brand", "NDC#", "Qty", "Expiration", "Condition", "Price", "Total"]
                col_widths = [60, 40, 20, 35, 35, 25, 40]  # Adjusted widths to ensure full visibility

                # **Table Headers**
                for col, width in zip(col_names, col_widths):
                    pdf.cell(width, 10, col, border=1, align="C")
                pdf.ln()

                # **Table Data**
                for _, row in invoice_with_total.iterrows():
                    for col, width in zip(col_names, col_widths):
                        pdf.cell(width, 10, str(row[col]), border=1, align="C")
                    pdf.ln()

                # **Tracking & Payment Information**
                pdf.ln(10)
                pdf.set_font("Arial", size=12)
                pdf.cell(0, 10, f"Tracking #: {st.session_state.tracking_number}   UPS", ln=True)
                pdf.ln(5)
                pdf.cell(0, 10, "Please Make Payment to Paypal", ln=True)
                pdf.cell(0, 10, "Zelle: derek@stripbuyer.com", ln=True)
                pdf.ln(5)
                pdf.cell(0, 10, "Strip Buyer Surplus LLC", ln=True)
                pdf.cell(0, 10, "2664 Alfreda Way", ln=True)
                pdf.cell(0, 10, "Redding, CA 96002", ln=True)
                pdf.ln(10)

                # **Save PDF & Allow Download**
                pdf_output_data = pdf.output(dest="S").encode("latin1")
                pdf_output = io.BytesIO(pdf_output_data)

                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_output,
                    file_name="invoice.pdf",
                    mime="application/pdf"
                )
                st.success("✅ Invoice saved as PDF!")
