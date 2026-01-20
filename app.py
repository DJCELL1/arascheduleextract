import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Door Hardware Schedule Extractor", layout="wide")

def extract_door_hardware_data(pdf_path):
    """Extract door hardware data from PDF"""
    doors_data = []

    with pdfplumber.open(pdf_path) as pdf:
        current_door = None
        current_description = None
        current_dr_type = None

        for page in pdf.pages:
            text = page.extract_text()

            if not text or "Doors with hardware" not in text:
                continue

            lines = text.split('\n')

            for i, line in enumerate(lines):
                # Check if this is a door header (e.g., "D0.01 Accessible WC Timber")
                door_match = re.match(r'^(D\d+\.\d+)\s+(.+?)\s+(Timber|Alum|INAL)\s*$', line.strip())

                if door_match:
                    current_door = door_match.group(1)
                    current_description = door_match.group(2)
                    current_dr_type = door_match.group(3)
                    continue

                # Check if this is a product line with code, quantity, description, and finish
                # Pattern: CODE NUMBER Description FINISH
                product_match = re.match(r'^([A-Z0-9/-]+)\s+(\d+)\s+(.+?)\s+(SSS|SCP|SIL|PF)\s*$', line.strip())

                if product_match and current_door:
                    code = product_match.group(1)
                    quantity = product_match.group(2)
                    product_desc = product_match.group(3)
                    finish = product_match.group(4)

                    doors_data.append({
                        'Door': current_door,
                        'Description': current_description,
                        'Dr type': current_dr_type,
                        'Code': code,
                        'Quantity Product': quantity,
                        'Description Product': product_desc,
                        'Finish': finish
                    })

    return pd.DataFrame(doors_data)


def extract_door_hardware_data_v2(pdf_path):
    """Enhanced extraction using table detection"""
    all_data = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Only process pages with "Doors with hardware"
            text = page.extract_text()
            if not text or "Doors with hardware" not in text:
                continue

            # Extract tables from the page
            tables = page.extract_tables()

            current_door = None
            current_description = None
            current_dr_type = None

            for table in tables:
                for row in table:
                    if not row or len(row) < 3:
                        continue

                    # Check if this row contains door information (D0.XX pattern)
                    if row[0] and re.match(r'D\d+\.\d+', str(row[0])):
                        current_door = row[0]
                        current_description = row[1] if len(row) > 1 else ""
                        current_dr_type = row[2] if len(row) > 2 else ""

                    # Check if this row contains product information
                    elif current_door and row[0] and not re.match(r'D\d+\.\d+', str(row[0])):
                        code = row[0] if row[0] else ""

                        # Try to find quantity (usually a number)
                        quantity = ""
                        product_desc = ""
                        finish = ""

                        if len(row) > 1:
                            quantity = row[1] if row[1] and str(row[1]).strip().isdigit() else ""
                        if len(row) > 2:
                            product_desc = row[2] if row[2] else ""
                        if len(row) > 3:
                            finish = row[3] if row[3] else ""

                        # Only add if we have meaningful data
                        if code and code.strip() and code != 'Code':
                            all_data.append({
                                'Door': current_door,
                                'Description': current_description,
                                'Dr type': current_dr_type,
                                'Code': code,
                                'Quantity Product': quantity,
                                'Description Product': product_desc,
                                'Finish': finish
                            })

    return pd.DataFrame(all_data)


def main():
    st.title("🚪 Door Hardware Schedule Extractor")
    st.markdown("Extract door hardware data from PDF schedules")

    # File uploader
    uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])

    if uploaded_file:
        # Save uploaded file temporarily
        with open("temp_upload.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("Extracting data from PDF..."):
            df = extract_door_hardware_data_v2("temp_upload.pdf")

        if not df.empty:
            st.success(f"✅ Extracted {len(df)} product entries from {df['Door'].nunique()} doors")

            # Sidebar filters
            st.sidebar.header("Filters")

            # Door filter
            doors = ['All'] + sorted(df['Door'].unique().tolist())
            selected_door = st.sidebar.selectbox("Select Door", doors)

            # Door type filter
            door_types = ['All'] + sorted(df['Dr type'].dropna().unique().tolist())
            selected_type = st.sidebar.selectbox("Select Door Type", door_types)

            # Filter data
            filtered_df = df.copy()
            if selected_door != 'All':
                filtered_df = filtered_df[filtered_df['Door'] == selected_door]
            if selected_type != 'All':
                filtered_df = filtered_df[filtered_df['Dr type'] == selected_type]

            # Display tabs
            tab1, tab2, tab3 = st.tabs(["📊 Data Table", "📈 Summary", "📥 Export"])

            with tab1:
                st.dataframe(filtered_df, use_container_width=True, height=600)

            with tab2:
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Doors by Type")
                    door_type_summary = df.groupby('Dr type')['Door'].nunique().reset_index()
                    door_type_summary.columns = ['Door Type', 'Count']
                    st.dataframe(door_type_summary, use_container_width=True)

                    st.subheader("Products by Door")
                    products_by_door = df.groupby('Door').size().reset_index()
                    products_by_door.columns = ['Door', 'Product Count']
                    st.dataframe(products_by_door, use_container_width=True, height=400)

                with col2:
                    st.subheader("Product Quantity Summary")
                    product_summary = df.groupby(['Code', 'Description Product', 'Finish']).agg({
                        'Quantity Product': lambda x: x.astype(str).astype(int).sum() if x.notna().any() else 0
                    }).reset_index()
                    product_summary.columns = ['Code', 'Description', 'Finish', 'Total Quantity']
                    st.dataframe(product_summary.sort_values('Total Quantity', ascending=False),
                               use_container_width=True, height=400)

            with tab3:
                st.subheader("Export Options")

                col1, col2 = st.columns(2)

                with col1:
                    # Export to CSV
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name="door_hardware_schedule.csv",
                        mime="text/csv"
                    )

                with col2:
                    # Export to Excel
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        filtered_df.to_excel(writer, sheet_name='Door Hardware', index=False)

                        # Add summary sheet
                        product_summary = df.groupby(['Code', 'Description Product', 'Finish']).agg({
                            'Quantity Product': lambda x: x.astype(str).astype(int).sum() if x.notna().any() else 0
                        }).reset_index()
                        product_summary.to_excel(writer, sheet_name='Product Summary', index=False)

                    excel_data = output.getvalue()
                    st.download_button(
                        label="📥 Download as Excel",
                        data=excel_data,
                        file_name="door_hardware_schedule.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.warning("⚠️ No data extracted. Please check the PDF format.")
            st.info("The PDF should contain a 'Doors with hardware' section with door and product information.")

    else:
        st.info("👆 Please upload a PDF file to get started")

        # Show example format
        with st.expander("📋 Expected PDF Format"):
            st.markdown("""
            The PDF should have a structure like:

            **Door Level:**
            - Door number (e.g., D0.01)
            - Description (e.g., Accessible WC)
            - Door type (e.g., Timber, Alum, INAL)

            **Product Level (for each door):**
            - Code (e.g., MS2604PT)
            - Quantity (e.g., 1)
            - Product Description (e.g., dormakaba MS2604PT Privacy latch)
            - Finish (e.g., SSS, SCP, SIL, PF)
            """)


if __name__ == "__main__":
    main()
