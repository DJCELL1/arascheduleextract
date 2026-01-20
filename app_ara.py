import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="ARA Hardware Schedule Extractor", layout="wide")

def extract_ara_hardware_data(pdf_path):
    """Extract door hardware data from ARA format PDF"""
    all_data = []

    with pdfplumber.open(pdf_path) as pdf:
        current_door = None
        current_area = None
        current_description = None
        current_rating = None
        current_handing = None
        current_door_type = None
        current_notes = None

        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split('\n')

            for i, line in enumerate(lines):
                line = line.strip()

                # Check for notes
                if line.startswith('Notes:'):
                    current_notes = line.replace('Notes:', '').strip()
                    continue

                # Check if this is a door header line
                # Pattern: Door_ID Area Description [Rating] [Handing] Door_Type
                # Examples:
                # 8.C.ED-02 Block C - 2B-T08-S Entry Alum-Ext
                # 14.E.ID-01 Block E - 2B-T07-N Garage Timber
                # 16.B.ID-03 Block E - 3B-ALT-N Study Sliding Aluminium
                # 001.D001A Level 00 Entry Timber
                # D005A Level 01 Bathroom Aluminium
                door_match = re.match(r'^((?:\d+\.[A-Z]\.[EI]D-\d+|\d+\.D\d+[A-Z]?|D\d+[A-Z]{1,2}))\s+(.+?)(?:\s+(Timber|Alum-Ext|Cavity Slider|Sliding\s+Timber|Sliding\s+Aluminium|Aluminium|INAL))?$', line)

                if door_match:
                    # Parse the door header
                    door_id = door_match.group(1)
                    rest_of_line = door_match.group(2)
                    door_type_match = door_match.group(3)

                    # Split rest_of_line to get area and description
                    # Format: "Block C - XXX Description" or "001 Description" or "Level 00 Description"
                    parts = rest_of_line.split()

                    # Find where the area ends (after the villa code like "2B-T08-S" or simple area like "001" or "Level 00")
                    area_parts = []
                    desc_parts = []
                    found_villa_code = False

                    for i, part in enumerate(parts):
                        # Check for villa code pattern (e.g., 2B-T08-S)
                        if re.match(r'\d+[A-Z]-[A-Z]\d+-[A-Z]', part):
                            area_parts.append(part)
                            found_villa_code = True
                        # Check for simple numeric area (e.g., 001, 101)
                        elif not found_villa_code and re.match(r'^\d+$', part) and i == 0:
                            area_parts.append(part)
                            found_villa_code = True
                        # Check for "Level XX" pattern
                        elif not found_villa_code and part == "Level" and i + 1 < len(parts):
                            area_parts.append(part)
                            area_parts.append(parts[i + 1])
                            parts[i + 1] = ""  # Mark as consumed
                            found_villa_code = True
                        elif not found_villa_code and part != "":
                            area_parts.append(part)
                        elif part != "":
                            desc_parts.append(part)

                    current_door = door_id
                    current_area = ' '.join(area_parts)
                    current_description = ' '.join(desc_parts) if desc_parts else ""
                    current_door_type = door_type_match if door_type_match else ""
                    current_rating = ""
                    current_handing = ""

                    # Check if "Sliding" is in the description, move it to handing
                    if "Sliding" in current_door_type:
                        current_handing = "Sliding"
                        current_door_type = current_door_type.replace("Sliding", "").strip()

                    continue

                # Check if this is a product line
                # Pattern: CODE Description NUMBER
                # Skip lines that are headers
                if line in ['Code Description Product', 'Door Area Description Rating Handing Door Type']:
                    continue

                # Product line pattern: starts with alphanumeric code
                product_match = re.match(r'^([A-Z0-9\-/\.]+)\s+(.+?)\s+(\d+)$', line)

                if product_match and current_door:
                    code = product_match.group(1)
                    product_desc = product_match.group(2)
                    quantity = product_match.group(3)

                    all_data.append({
                        'Door': current_door,
                        'Area': current_area,
                        'Description': current_description,
                        'Rating': current_rating,
                        'Handing': current_handing,
                        'Door Type': current_door_type,
                        'Notes': current_notes if current_notes else "",
                        'Code': code,
                        'Product Description': product_desc,
                        'Quantity': quantity
                    })

    return pd.DataFrame(all_data)


def extract_ara_hardware_data_v2(pdf_path):
    """Enhanced extraction using table detection for ARA format"""
    all_data = []

    with pdfplumber.open(pdf_path) as pdf:
        current_door = None
        current_area = None
        current_description = None
        current_rating = None
        current_handing = None
        current_door_type = None
        current_notes = None

        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue

            # Extract text lines for parsing
            lines = text.split('\n')

            for line in lines:
                line = line.strip()

                # Skip empty lines and headers
                if not line or line in ['Code Description Product', 'Door Area Description Rating Handing Door Type']:
                    continue

                # Check for Block section headers (e.g., "Block C - 2B-T08-S", "Block E - 3B-ALT-N")
                if re.match(r'^Block [A-Z] - [\w-]+$', line):
                    continue

                # Check for notes
                if line.startswith('Notes:'):
                    current_notes = line.replace('Notes:', '').strip()
                    continue

                # Check if this is a door header
                # More flexible pattern to capture various formats
                # Pattern matches: 8.C.ED-02, 14.E.ID-01, 16.B.ID-03, 001.D001A, D005A, etc.
                door_pattern = r'^((?:\d+\.[A-Z]\.[EI]D-\d+|\d+\.D\d+[A-Z]?|D\d+[A-Z]{1,2}))\s+'
                if re.match(door_pattern, line):
                    # Extract door ID - use flexible pattern
                    door_id_match = re.match(r'^((?:\d+\.[A-Z]\.[EI]D-\d+|\d+\.D\d+[A-Z]?|D\d+[A-Z]{1,2}))\s+(.+)$', line)
                    if door_id_match:
                        current_door = door_id_match.group(1)
                        rest = door_id_match.group(2)

                        # Parse the rest: Area Description [Handing] Door_Type
                        # Look for door types at the end
                        door_types = ['Timber', 'Alum-Ext', 'Cavity Slider', 'Aluminium', 'INAL']
                        current_door_type = ""
                        current_handing = ""

                        for dt in door_types:
                            if rest.endswith(dt):
                                current_door_type = dt
                                rest = rest[:-(len(dt))].strip()
                                break
                            elif rest.endswith(f'Sliding {dt}'):
                                current_handing = "Sliding"
                                current_door_type = dt
                                rest = rest[:-(len(f'Sliding {dt}'))].strip()
                                break

                        # Parse area and description
                        # Area format: "Block C - XXX" or "Block E - XXX" or "001" or "Level 00"
                        area_match = re.match(r'(Block [A-Z] - [\w-]+)\s+(.+)$', rest)
                        if area_match:
                            current_area = area_match.group(1)
                            current_description = area_match.group(2)
                        else:
                            # Try to match simple numeric area or "Level XX"
                            level_match = re.match(r'((?:Level\s+\d+|\d+))\s+(.+)$', rest)
                            if level_match:
                                current_area = level_match.group(1)
                                current_description = level_match.group(2)
                            else:
                                current_area = rest
                                current_description = ""

                        current_rating = ""
                        current_notes = ""
                        continue

                # Check if this is a product line
                product_match = re.match(r'^([A-Z0-9\-/\.]+)\s+(.+?)\s+(\d+)$', line)

                if product_match and current_door:
                    code = product_match.group(1)
                    product_desc = product_match.group(2)
                    quantity = product_match.group(3)

                    all_data.append({
                        'Door': current_door,
                        'Area': current_area,
                        'Description': current_description,
                        'Rating': current_rating,
                        'Handing': current_handing,
                        'Door Type': current_door_type,
                        'Notes': current_notes,
                        'Code': code,
                        'Product Description': product_desc,
                        'Quantity': quantity
                    })

    return pd.DataFrame(all_data)


def main():
    st.title("🚪 ARA Hardware Schedule Extractor")
    st.markdown("Extract door hardware data from ARA format PDF schedules")

    # File uploader
    uploaded_file = st.file_uploader("Upload ARA Hardware Schedule PDF", type=['pdf'])

    if uploaded_file:
        # Save uploaded file temporarily
        with open("temp_upload.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("Extracting data from PDF..."):
            df = extract_ara_hardware_data_v2("temp_upload.pdf")

        if not df.empty:
            st.success(f"✅ Extracted {len(df)} product entries from {df['Door'].nunique()} doors")

            # Sidebar filters
            st.sidebar.header("Filters")

            # Area filter
            areas = ['All'] + sorted(df['Area'].dropna().unique().tolist())
            selected_area = st.sidebar.selectbox("Select Area", areas)

            # Door filter
            doors = ['All'] + sorted(df['Door'].unique().tolist())
            selected_door = st.sidebar.selectbox("Select Door", doors)

            # Door type filter
            door_types = ['All'] + sorted(df['Door Type'].dropna().unique().tolist())
            selected_type = st.sidebar.selectbox("Select Door Type", door_types)

            # Description filter
            descriptions = ['All'] + sorted(df['Description'].dropna().unique().tolist())
            selected_description = st.sidebar.selectbox("Select Room Type", descriptions)

            # Filter data
            filtered_df = df.copy()
            if selected_area != 'All':
                filtered_df = filtered_df[filtered_df['Area'] == selected_area]
            if selected_door != 'All':
                filtered_df = filtered_df[filtered_df['Door'] == selected_door]
            if selected_type != 'All':
                filtered_df = filtered_df[filtered_df['Door Type'] == selected_type]
            if selected_description != 'All':
                filtered_df = filtered_df[filtered_df['Description'] == selected_description]

            # Display tabs
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Data Table", "📈 Summary", "🔍 Product Search", "📥 Export"])

            with tab1:
                st.dataframe(filtered_df, use_container_width=True, height=600)

            with tab2:
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Doors by Area")
                    area_summary = df.groupby('Area')['Door'].nunique().reset_index()
                    area_summary.columns = ['Area', 'Door Count']
                    st.dataframe(area_summary, use_container_width=True)

                    st.subheader("Doors by Type")
                    door_type_summary = df.groupby('Door Type')['Door'].nunique().reset_index()
                    door_type_summary.columns = ['Door Type', 'Door Count']
                    st.dataframe(door_type_summary, use_container_width=True)

                    st.subheader("Doors by Room Type")
                    room_summary = df.groupby('Description')['Door'].nunique().reset_index()
                    room_summary.columns = ['Room Type', 'Door Count']
                    st.dataframe(room_summary.sort_values('Door Count', ascending=False), use_container_width=True)

                with col2:
                    st.subheader("Product Quantity Summary")
                    product_summary = df.groupby(['Code', 'Product Description']).agg({
                        'Quantity': lambda x: pd.to_numeric(x, errors='coerce').sum()
                    }).reset_index()
                    product_summary.columns = ['Code', 'Description', 'Total Quantity']
                    product_summary = product_summary.sort_values('Total Quantity', ascending=False)
                    st.dataframe(product_summary, use_container_width=True, height=400)

                    st.subheader("Products per Door")
                    products_by_door = df.groupby('Door').size().reset_index()
                    products_by_door.columns = ['Door', 'Product Count']
                    st.dataframe(products_by_door.sort_values('Product Count', ascending=False),
                               use_container_width=True, height=300)

            with tab3:
                st.subheader("🔍 Search Products")

                search_term = st.text_input("Search by product code or description")

                if search_term:
                    search_results = df[
                        df['Code'].str.contains(search_term, case=False, na=False) |
                        df['Product Description'].str.contains(search_term, case=False, na=False)
                    ]

                    if not search_results.empty:
                        st.success(f"Found {len(search_results)} matching products")

                        # Show summary
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Total Doors", search_results['Door'].nunique())
                            st.metric("Total Quantity", pd.to_numeric(search_results['Quantity'], errors='coerce').sum())

                        with col2:
                            st.metric("Unique Products", search_results['Code'].nunique())

                        # Show detailed results
                        st.dataframe(search_results, use_container_width=True, height=400)
                    else:
                        st.warning("No matching products found")

            with tab4:
                st.subheader("Export Options")

                col1, col2, col3 = st.columns(3)

                with col1:
                    # Export to CSV
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name="ara_hardware_schedule.csv",
                        mime="text/csv"
                    )

                with col2:
                    # Export to Excel with multiple sheets
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        # Main data
                        filtered_df.to_excel(writer, sheet_name='Door Hardware', index=False)

                        # Product summary
                        product_summary = df.groupby(['Code', 'Product Description']).agg({
                            'Quantity': lambda x: pd.to_numeric(x, errors='coerce').sum()
                        }).reset_index()
                        product_summary.columns = ['Code', 'Description', 'Total Quantity']
                        product_summary.to_excel(writer, sheet_name='Product Summary', index=False)

                        # Area summary
                        area_summary = df.groupby(['Area', 'Door Type'])['Door'].nunique().reset_index()
                        area_summary.columns = ['Area', 'Door Type', 'Door Count']
                        area_summary.to_excel(writer, sheet_name='Area Summary', index=False)

                    excel_data = output.getvalue()
                    st.download_button(
                        label="📥 Download as Excel",
                        data=excel_data,
                        file_name="ara_hardware_schedule.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                with col3:
                    # Export product summary only
                    product_summary = df.groupby(['Code', 'Product Description']).agg({
                        'Quantity': lambda x: pd.to_numeric(x, errors='coerce').sum()
                    }).reset_index()
                    product_csv = product_summary.to_csv(index=False)
                    st.download_button(
                        label="📥 Product Summary CSV",
                        data=product_csv,
                        file_name="product_summary.csv",
                        mime="text/csv"
                    )

        else:
            st.warning("⚠️ No data extracted. Please check the PDF format.")
            st.info("The PDF should be in ARA Hardware Schedule format with door and product information.")

    else:
        st.info("👆 Please upload a PDF file to get started")

        # Show example format
        with st.expander("📋 Expected PDF Format (ARA Hardware Schedule)"):
            st.markdown("""
            The PDF should have a structure like:

            **Door Header:**
            - Door ID (e.g., 8.C.ED-02, 9.C.ID-01)
            - Area (e.g., Block C - 2B-T08-S)
            - Description (e.g., Entry, Garage, Bathroom)
            - Handing (optional, e.g., Sliding)
            - Door Type (e.g., Timber, Alum-Ext, Cavity Slider)

            **Product Lines (for each door):**
            - Code (e.g., 8492-MSB)
            - Product Description (e.g., NIDO Lumina Rose Passage Set Linear Knurl MSB)
            - Quantity (e.g., 1, 2, 3)

            **Optional:**
            - Notes (e.g., "Vingard Lock by others")
            """)

            st.markdown("---")
            st.markdown("**Example:**")
            st.code("""
8.C.ID-04    Block C - 2B-T08-S    Bathroom    Timber
Code         Description                                      Product
8456-MSB     NIDO Privacy Set 57mm Backset Linear Knurl MSB  1
LW10075LLSSS LW HINGE 100MMX75MMX2.5MM LIFT OFF - LH MOQ=30  3
5292-MSB     85mm Skirting Doorstop Slimline - Linear Knurl  1
            """)


if __name__ == "__main__":
    main()
