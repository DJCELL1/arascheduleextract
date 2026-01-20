# ARA Hardware Schedule Extractor - User Guide

## Overview
The ARA Hardware Schedule Extractor is a web application that extracts door hardware data from ARA format PDF schedules and provides multiple viewing and export options.

## Getting Started

### 1. Access the Application
- Open the Streamlit app in your web browser
- You'll see the Hardware Direct branded interface with the upload area

### 2. Upload Your PDF
- Click the **"Upload ARA Hardware Schedule PDF"** button
- Select your ARA format hardware schedule PDF file
- The app will automatically extract all door and product information

### 3. View Extracted Data
After successful extraction, you'll see:
- ✅ Success message showing the number of products and doors extracted
- 📋 Job information (if available in the PDF header)

---

## Using the Sidebar Filters

The sidebar provides powerful filtering options to narrow down your data:

### Available Filters:
- **Select Area**: Filter by area/location (e.g., Block C, Level 01)
- **Select Door**: Filter by specific door ID
- **Select Door Type**: Filter by door type (Timber, Aluminium, etc.)
- **Select Room Type**: Filter by room description (Entry, Bathroom, etc.)

**Tip**: All filters work together - you can combine multiple filters to find exactly what you need.

---

## Application Tabs

### Tab 1: 📊 Data Table
**What it shows**: Complete table of all door hardware data

**Columns**:
- Door ID
- Area/Location
- Room Description
- Door Type
- Product Code
- Product Description
- Quantity
- Notes (if any)

**Features**:
- Sortable columns (click column header)
- Searchable
- Scrollable view
- Applies all sidebar filters

---

### Tab 2: 📈 Summary
**What it shows**: Statistical breakdown of your hardware schedule

**Left Column**:
- **Doors by Area**: Count of doors in each area
- **Doors by Type**: Count of each door type (Timber, Aluminium, etc.)
- **Doors by Room Type**: Count of doors by room function

**Right Column**:
- **Product Quantity Summary**: Total quantities needed for each product across all doors
- **Products per Door**: Shows which doors have the most hardware items

**Use Cases**:
- Quick overview of project scope
- Identify most common door types
- See total quantities needed per product

---

### Tab 3: 🔍 Product Search
**What it shows**: Search functionality to find specific products

**How to Use**:
1. Enter a search term (product code or description)
2. Results show all matching products across all doors
3. Summary metrics display:
   - Total Doors using this product
   - Total Quantity needed
   - Number of unique products found

**Examples**:
- Search "HINGE" to find all hinge products
- Search "8456" to find specific product codes
- Search "MSB" to find all Matt Satin Brass items

---

### Tab 4: 🏷️ Items by Door Type
**What it shows**: Hardware items grouped and totaled by door type

**Viewing Options**:
1. **All Door Types**: Expandable sections for each door type
   - Shows door count, unique items, and total quantity
   - Click to expand and see detailed breakdown

2. **Specific Door Type**: Select from dropdown
   - Shows detailed table with:
     - Product Code
     - Product Description
     - Total Quantity (summed across all doors of this type)
     - Doors Using Item (count of doors)

**Download Option**:
- When viewing a specific door type, download CSV for just that type

**Use Cases**:
- Order all hardware for Timber doors
- Calculate quantities needed per door type
- Compare hardware across different door types

---

### Tab 5: 📥 Export
**What it shows**: Three export options for your data

#### Option 1: Schedule CSV
**Contains**:
- Main door hardware schedule data table
- Filtered by your sidebar selections
- All door details with product codes, descriptions, and quantities

**File naming**: `JobNumber_JobName_schedule.csv`

**Best for**:
- Complete schedule documentation
- Opening in Excel or Google Sheets
- Sharing full project data
- Integration with other systems

---

#### Option 2: Door Type Summary CSV
**Contains**:
- Items grouped by door type
- Product codes, descriptions, and total quantities
- Format: Door type header, then products below

**Example format**:
```
Timber
Code,Product Description,Total Quantity
5292-MSB,"85mm Skirting Doorstop...",14
8456-MSB,"NIDO Privacy Set...",6

Aluminium
Code,Product Description,Total Quantity
5263L-PC,"WB 5263L Overhead...",1
```

**File naming**: `JobNumber_JobName_door_type_summary.csv`

**Best for**:
- Ordering hardware by door type
- Quick quantity reference
- Supplier quotations
- Simple ordering lists

---

#### Option 3: Complete Excel
**Contains 4 sheets**:

1. **Door Hardware**: Complete data table (filtered)
2. **Product Summary**: Total quantities for each product
3. **Area Summary**: Door counts by area and type
4. **Items by Door Type**: Products grouped by door type with quantities

**File naming**: `JobNumber_JobName.xlsx`

**Best for**:
- Comprehensive reports
- Multiple stakeholders
- Professional documentation
- Pivot tables and advanced analysis
- Complete project overview

---

## Export File Naming

All exports are automatically named using job information from the PDF:

**Format**: `JobNumber_JobName.extension`

**Examples**:
- `12345_Villa_Project_schedule.csv` (main schedule)
- `12345_Villa_Project_door_type_summary.csv` (items by door type)
- `12345_Villa_Project.xlsx` (complete Excel workbook)
- `12345_Villa_Project_timber.csv` (specific door type from tab 4)

**Note**: If no job information is found in the PDF, files default to `ara_hardware_schedule.extension`

---

## Tips & Best Practices

### Getting Clean Extractions
1. **Ensure PDF Quality**: Best results with clear, text-based PDFs (not scanned images)
2. **Check Job Info**: Look for job number/name display after upload to confirm extraction
3. **Review Door Counts**: Compare extracted door count with your expectations

### Efficient Workflow
1. **Upload PDF** → Check extraction success
2. **Use Summary Tab** → Get overview of project
3. **Apply Filters** → Narrow down to specific areas/types
4. **Export Excel** → Get comprehensive multi-sheet report
5. **Use Door Type Tab** → Order by door type if needed

### Common Use Cases

**Scenario 1: Ordering All Hardware by Door Type**
- Go to Export tab
- Download "Door Type Summary CSV"
- Send to supplier for quoting
- Easy to reference: one section per door type

**Scenario 2: Complete Project Documentation**
- Go to Export tab
- Download "Complete Excel"
- Share with project team
- Contains all data organized in multiple sheets

**Scenario 3: Finding a Specific Product**
- Go to Product Search tab
- Search by code or description
- See all doors using that product
- Check total quantities needed

**Scenario 4: Calculating Hardware for One Area**
- Use Area filter in sidebar
- Go to Summary tab
- View product quantities for that area only
- Download "Schedule CSV" with filtered data

**Scenario 5: Ordering Just One Door Type**
- Go to Items by Door Type tab
- Select specific door type (e.g., "Timber")
- Review quantities and items
- Download CSV for just that type
- Send to specialized supplier

---

## Troubleshooting

### No Data Extracted
**Possible Issues**:
- PDF is not in ARA format
- PDF is a scanned image (not text-based)
- PDF has non-standard formatting

**Solutions**:
- Check PDF can be text-selected (not an image)
- Verify PDF follows ARA format structure
- Contact support with sample PDF

### Missing Door Types
**Possible Issues**:
- Door type not specified in PDF
- Non-standard door type names

**Solutions**:
- Check original PDF for door type information
- Items will still be extracted, just without type grouping

### Export Errors
**Possible Issues**:
- Empty door types in data
- Special characters in filenames

**Solutions**:
- App automatically handles empty door types
- Special characters are replaced with underscores

---

## Expected PDF Format

The app expects ARA Hardware Schedule format with:

### Door Header Format:
```
[Door ID] [Area] [Description] [Door Type]
```
**Examples**:
- `8.C.ED-02 Block C - 2B-T08-S Entry Timber`
- `14.E.ID-01 Block E - 2B-T07-N Garage Alum-Ext`
- `D005A Level 01 Bathroom Aluminium`

### Product Line Format:
```
[Code] [Description] [Quantity]
```
**Example**:
```
8456-MSB     NIDO Privacy Set 57mm Backset Linear Knurl MSB     1
LW10075LLSSS LW HINGE 100MMX75MMX2.5MM LIFT OFF - LH MOQ=30     3
5292-MSB     85mm Skirting Doorstop Slimline - Linear Knurl     1
```

### Optional Header Information:
- Job No / Job Number
- Project Name / Job Name

These are extracted automatically for file naming.

---

## Support

For issues or questions:
1. Check this user guide first
2. Review the "Expected PDF Format" section
3. Verify your PDF matches the ARA format
4. Contact Hardware Direct support with:
   - Screenshot of the issue
   - Sample PDF (if possible)
   - Error message (if any)

---

## Hardware Direct Branding

This application features Hardware Direct's signature orange (#F47920) and dark grey (#2B2B2B) branding throughout the interface for a professional, consistent experience.

---

**Version**: 1.0
**Last Updated**: January 2026
**Developed for**: Hardware Direct
