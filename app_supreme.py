import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO
from hd_theme import apply_hd_theme, add_logo

st.set_page_config(page_title="Supreme Hardware Schedule Extractor", layout="wide")

# Apply Hardware Direct theme
apply_hd_theme()
add_logo()

def extract_supreme_hardware_data(pdf_path):
    """Extract door hardware data from Supreme format PDF"""
    all_data = []
    job_number = None
    job_name = None

    with pdfplumber.open(pdf_path) as pdf:
        current_door = None
        current_area = None
        current_description = None
        current_door_type = None
        current_notes = None
        in_door_section = False

        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue

            lines = text.split('\n')

            # Extract job number and name from first page header
            if page_num == 0 and not job_number:
                for i, line in enumerate(lines[:10]):
                    # Look for pattern like "SLH2410025: Tauranga Intermediate School Block D"
                    job_line_match = re.match(r'^([A-Z0-9]+)\s*:\s*(.+)', line.strip())
                    if job_line_match and not job_number:
                        potential_job = job_line_match.group(1)
                        potential_name = job_line_match.group(2).strip()
                        # Only accept if it looks like a job number
                        if re.match(r'^[A-Z]{2,}[0-9]+', potential_job):
                            job_number = potential_job
                            job_name = potential_name
                            continue

            # Check for Area headers (e.g., "Area: Ground Floor")
            area_match = re.match(r'^Area:\s*(.+)', line.strip())
            if area_match:
                current_area = area_match.group(1)
                in_door_section = True
                continue

            # Check for door header lines
            # Pattern: D0.01 Description Dr type
            # Example: D0.01 Accessible WC Timber
            door_match = re.match(r'^(D\d+\.\d+)\s+(.+?)\s+(Timber|Alum|INAL|Aluminium|Cavity Slider|Sliding\s+\w+)$', line.strip())

            if door_match:
                current_door = door_match.group(1)
                current_description = door_match.group(2).strip()
                current_door_type = door_match.group(3)
                current_notes = None
                continue

            # Check for notes in the door section
            # Notes appear as multi-line descriptions after door ID
            if current_door and not re.match(r'^[A-Z0-9\-/\.]+\s+', line.strip()) and line.strip() and not line.startswith('Code'):
                # This might be a note line
                if re.search(r'(supplied|manufacturer|grab rail|mm|track|gear|lock)', line, re.IGNORECASE):
                    if current_notes:
                        current_notes += ' ' + line.strip()
                    else:
                        current_notes = line.strip()
                    continue

            # Check if this is a product line
            # Pattern: CODE Description Quantity (with optional Finish at the end)
            # Skip header lines
            if line.strip() in ['Code Description Finish', 'Code Description Product', 'Quantity Product']:
                continue

            # Product pattern - matches code at start, then description, then number at end
            # The finish column appears separately as the last column (SSS, SCP, SIL, PF, etc.)
            product_match = re.match(r'^([A-Z0-9\-/\.]+)\s+(.+?)\s+(\d+)\s*([A-Z]{2,})?$', line.strip())

            if product_match and current_door:
                code = product_match.group(1)
                product_desc = product_match.group(2).strip()
                quantity = product_match.group(3)
                finish = product_match.group(4) if product_match.group(4) else ""

                all_data.append({
                    'Door': current_door,
                    'Area': current_area if current_area else "",
                    'Description': current_description if current_description else "",
                    'Door Type': current_door_type if current_door_type else "",
                    'Notes': current_notes if current_notes else "",
                    'Code': code,
                    'Product Description': product_desc,
                    'Quantity': quantity,
                    'Finish': finish
                })

    df = pd.DataFrame(all_data)
    # Add job info as metadata
    if not df.empty:
        df.attrs['job_number'] = job_number
        df.attrs['job_name'] = job_name
    return df


def main():
    st.title("🚪 Supreme Hardware Schedule Extractor")
    st.markdown("Extract door hardware data from Supreme Lock & Hardware PDF schedules")

    # File uploader
    uploaded_file = st.file_uploader("Upload Supreme Hardware Schedule PDF", type=['pdf'])

    if uploaded_file:
        # Save uploaded file temporarily
        with open("temp_upload_supreme.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("Extracting data from PDF..."):
            df = extract_supreme_hardware_data("temp_upload_supreme.pdf")

        if not df.empty:
            # Get job info for file naming
            job_number = df.attrs.get('job_number', '')
            job_name = df.attrs.get('job_name', '')

            # Create base filename from job info
            if job_number and job_name:
                base_filename = f"{job_number}_{job_name.replace(' ', '_')}"
                st.success(f"✅ Extracted {len(df)} product entries from {df['Door'].nunique()} doors")
                st.info(f"📋 Job: {job_number} - {job_name}")
            elif job_number:
                base_filename = f"{job_number}"
                st.success(f"✅ Extracted {len(df)} product entries from {df['Door'].nunique()} doors")
                st.info(f"📋 Job: {job_number}")
            else:
                base_filename = "supreme_hardware_schedule"
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
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Data Table", "📈 Summary", "🔍 Product Search", "🏷️ Items by Door Type", "📥 Export"])

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
                st.subheader("🏷️ Items Breakdown by Door Type")

                # Group by Door Type and Product
                door_type_breakdown = df.groupby(['Door Type', 'Code', 'Product Description']).agg({
                    'Quantity': lambda x: pd.to_numeric(x, errors='coerce').sum(),
                    'Door': 'count'  # Count how many doors use this item
                }).reset_index()
                door_type_breakdown.columns = ['Door Type', 'Code', 'Product Description', 'Total Quantity', 'Doors Using Item']
                door_type_breakdown = door_type_breakdown.sort_values(['Door Type', 'Total Quantity'], ascending=[True, False])

                # Get unique door types
                unique_door_types = sorted(df['Door Type'].dropna().unique().tolist())

                if unique_door_types:
                    # Create selector for door type
                    selected_breakdown_type = st.selectbox(
                        "Select Door Type to View Breakdown",
                        ['All Door Types'] + unique_door_types
                    )

                    if selected_breakdown_type == 'All Door Types':
                        # Show all door types with expandable sections
                        for door_type in unique_door_types:
                            door_type_data = door_type_breakdown[door_type_breakdown['Door Type'] == door_type]

                            if not door_type_data.empty:
                                total_items = len(door_type_data)
                                total_qty = door_type_data['Total Quantity'].sum()
                                num_doors = df[df['Door Type'] == door_type]['Door'].nunique()

                                with st.expander(f"**{door_type}** - {num_doors} doors, {total_items} unique items, {int(total_qty)} total quantity"):
                                    # Show summary metrics
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Number of Doors", num_doors)
                                    with col2:
                                        st.metric("Unique Items", total_items)
                                    with col3:
                                        st.metric("Total Quantity", int(total_qty))

                                    # Show detailed breakdown
                                    display_df = door_type_data[['Code', 'Product Description', 'Total Quantity', 'Doors Using Item']].copy()
                                    display_df['Total Quantity'] = display_df['Total Quantity'].astype(int)
                                    st.dataframe(display_df, use_container_width=True, height=400)
                    else:
                        # Show specific door type
                        door_type_data = door_type_breakdown[door_type_breakdown['Door Type'] == selected_breakdown_type]

                        if not door_type_data.empty:
                            # Show summary metrics
                            total_items = len(door_type_data)
                            total_qty = door_type_data['Total Quantity'].sum()
                            num_doors = df[df['Door Type'] == selected_breakdown_type]['Door'].nunique()

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Number of Doors", num_doors)
                            with col2:
                                st.metric("Unique Items", total_items)
                            with col3:
                                st.metric("Total Quantity", int(total_qty))

                            st.markdown("---")

                            # Show detailed breakdown
                            display_df = door_type_data[['Code', 'Product Description', 'Total Quantity', 'Doors Using Item']].copy()
                            display_df['Total Quantity'] = display_df['Total Quantity'].astype(int)
                            st.dataframe(display_df, use_container_width=True, height=500)

                            # Add download button for this door type
                            csv_data = display_df.to_csv(index=False)
                            st.download_button(
                                label=f"📥 Download {selected_breakdown_type} Breakdown CSV",
                                data=csv_data,
                                file_name=f"{base_filename}_{selected_breakdown_type.replace(' ', '_').lower()}.csv",
                                mime="text/csv"
                            )
                else:
                    st.info("No door type information found in the data.")

            with tab5:
                st.subheader("Export Options")

                # Row 1: Main exports
                col1, col2, col3 = st.columns(3)

                with col1:
                    # Export Doors CSV
                    doors_df = df.groupby('Door').agg({
                        'Description': 'first',
                        'Area': 'first',
                        'Door Type': 'first'
                    }).reset_index()

                    # Reorder and rename columns to match standard format
                    doors_export = pd.DataFrame({
                        'DoorNumber': doors_df['Door'],
                        'DoorDescription': doors_df['Description'],
                        'Area': doors_df['Area'],
                        'Stage': '',
                        'Stamping': '',
                        'IsKeyed': '',
                        'DoorHeight': '',
                        'DoorWidth': '',
                        'DoorThickness': '',
                        'Rating': '',
                        'HandingShortCode': '',
                        'DoorType': doors_df['Door Type'],
                        'DoorFinishShortCode': '',
                        'FrameTypeShortCode': '',
                        'FrameFinishShortCode': '',
                        'LockFunctionShortCode': ''
                    })

                    csv_doors = doors_export.to_csv(index=False)
                    doors_filename = f"{job_number}_Doors.csv" if job_number else "Doors.csv"
                    st.download_button(
                        label="📥 Doors CSV",
                        data=csv_doors,
                        file_name=doors_filename,
                        mime="text/csv",
                        help="Door-level information only"
                    )

                with col2:
                    # Export Door Hardware CSV
                    hardware_export = pd.DataFrame({
                        'DoorNumber': df['Door'],
                        'DoorDescription': df['Description'],
                        'Area': df['Area'],
                        'Stage': '',
                        'Stamping': '',
                        'Rating': '',
                        'HandingShortCode': '',
                        'DoorType': df['Door Type'],
                        'DoorFinishShortCode': '',
                        'FrameTypeShortCode': '',
                        'FrameFinishShortCode': '',
                        'LockFunctionShortCode': '',
                        'PartCode': df['Code'],
                        'Description': df['Product Description'],
                        'ProductQuantity': df['Quantity'],
                        'InstallQuantity': '',
                        'InstallNote': df['Notes'],
                        'Finish': df['Finish']
                    })

                    csv_hardware = hardware_export.to_csv(index=False)
                    hardware_filename = f"{job_number}_DoorHardware.csv" if job_number else "DoorHardware.csv"
                    st.download_button(
                        label="📥 Door Hardware CSV",
                        data=csv_hardware,
                        file_name=hardware_filename,
                        mime="text/csv",
                        help="Complete door hardware schedule with products"
                    )

                with col3:
                    # Export to Excel with multiple sheets
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        # Doors sheet
                        doors_export.to_excel(writer, sheet_name='Doors', index=False)

                        # Door Hardware sheet
                        hardware_export.to_excel(writer, sheet_name='Door Hardware', index=False)

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

                        # Items by Door Type
                        df_with_door_type = df[df['Door Type'].notna() & (df['Door Type'] != '')].copy()

                        if not df_with_door_type.empty:
                            door_type_breakdown = df_with_door_type.groupby(['Door Type', 'Code', 'Product Description']).agg({
                                'Quantity': lambda x: pd.to_numeric(x, errors='coerce').sum()
                            }).reset_index()
                            door_type_breakdown.columns = ['Door Type', 'Code', 'Product Description', 'Total Quantity']

                            unique_door_types = sorted(df_with_door_type['Door Type'].unique().tolist())

                            all_door_types_data = []
                            for door_type in unique_door_types:
                                door_type_data = door_type_breakdown[door_type_breakdown['Door Type'] == door_type]
                                if not door_type_data.empty:
                                    # Add header row
                                    all_door_types_data.append({
                                        'Code': f'{door_type}',
                                        'Product Description': '',
                                        'Total Quantity': ''
                                    })
                                    # Add data rows
                                    for _, row in door_type_data.iterrows():
                                        all_door_types_data.append({
                                            'Code': row['Code'],
                                            'Product Description': row['Product Description'],
                                            'Total Quantity': int(row['Total Quantity']) if pd.notna(row['Total Quantity']) else 0
                                        })
                                    # Add blank row
                                    all_door_types_data.append({
                                        'Code': '',
                                        'Product Description': '',
                                        'Total Quantity': ''
                                    })

                            if all_door_types_data:
                                combined_df = pd.DataFrame(all_door_types_data)
                                combined_df.to_excel(writer, sheet_name='Items by Door Type', index=False)

                    excel_data = output.getvalue()
                    st.download_button(
                        label="📥 Complete Excel",
                        data=excel_data,
                        file_name=f"{base_filename}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                st.info("💡 CSV exports match the standard format with job number in filename.")

        else:
            st.warning("⚠️ No data extracted. Please check the PDF format.")
            st.info("The PDF should be in Supreme Lock & Hardware schedule format.")

    else:
        st.info("👆 Please upload a PDF file to get started")

        # Show example format
        with st.expander("📋 Expected PDF Format (Supreme Hardware Schedule)"):
            st.markdown("""
            The PDF should have a structure like:

            **Header:**
            - Job Number: Project Name (e.g., SLH2410025: Tauranga Intermediate School Block D)

            **Area Section:**
            - Area: Ground Floor

            **Door Header:**
            - Door ID (e.g., D0.01, D0.02)
            - Description (e.g., Accessible WC, Unisex WC, Classroom 23)
            - Door Type (e.g., Timber, Alum, INAL)

            **Product Lines:**
            - Code (e.g., MS2604PT, L9D11S)
            - Product Description
            - Quantity (e.g., 1, 2, 3)
            - Finish (e.g., SSS, SCP, SIL)
            """)

            st.markdown("---")
            st.markdown("**Example:**")
            st.code("""
Area: Ground Floor

D0.01    Accessible WC    Timber
Code           Description                                        Quantity    Finish
MS2604PT       dormakaba MS2604PT Privacy latch                   1          SSS
L9D11S         Legge L9D11S Escape Mortice Deadlock.RH            1          SCP
6649RH/30SSS   dormakaba 6649RH/30SSS Noosa Lever Ext Ind Emr    1          SSS
            """)


if __name__ == "__main__":
    main()
