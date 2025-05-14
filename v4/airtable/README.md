# 📊 Airtable Integration for Telecom Products

This directory contains scripts for setting up and populating Airtable bases with telecom product data. There are two main approaches: using the Metadata API (requires Personal Access Token) or manually creating the tables and fields.

## 🔍 Prerequisites

1. An Airtable account
2. Personal Access Token for Airtable API (for automated setup)
3. Python 3.7+
4. Required Python packages:
   - `requests`
   - `python-dotenv`
   - `logging`

## ⚙️ Environment Setup

Create a `.env` file in your project root with your Airtable credentials:

```
AIRTABLE_TOKEN=your_personal_access_token_here
```

## 📝 Script Overview

### 1. Creating Tables and Fields

#### Option A: Using the Metadata API (Automated) 🚀

Use [`create_table.py`](./create_table.py) to automatically create a base with the proper tables and fields:

```bash
python v4/airtable/create_table.py
```

This script:
- Creates a new base called "Telecom Products"
- Creates "Products" and "Pricing Tiers" tables with all required fields
- Sets up appropriate field types (single select, multiple select, etc.)
- Creates views for filtering data

#### Option B: Manual Setup with Setup Script 🔧

1. First, manually create an empty base in Airtable
2. Run the setup script to create tables and fields:

```bash
python v4/airtable/setup_airtable.py --base-id your_base_id_here
```

#### Option C: Fully Manual Setup ✏️

If you prefer to set up everything manually in the Airtable UI:

1. Create a new base
2. Create two tables: "Data1" and "Data2"
3. Set up fields as follows:

**Table 1: "Data1"**
- Name (Single line text)
- Type (Single select)
    - Add options: Data, Minutes
- Price (Number, decimal)
- Validity (Single select)
    - Add options: Daily, Weekly, Monthly
- ValidityDuration (Number, integer)
- Description (Long text)
- Keywords (Multiple select)
    - Add options: Budget, Standard, Premium, Unlimited, Night
- IsActive (Checkbox)
- SortOrder (Number, integer)

**Table 2: "Data2"**
- Name (Single line text)
- PriceTier (Single select)
    - Add options: Budget, Standard, Premium
- MinPrice (Number, decimal)
- MaxPrice (Number, decimal)
- ProductType (Single select)
    - Add options: Data, Minutes

### 2. Setting Up Select Field Options 🔤

If you've created tables but need to add select options, run:

```bash
python v4/airtable/setup_select_options.py
```

This will initialize all select fields with their proper options.

### 3. Populating Data 📥

After setting up tables and fields, populate with sample data:

```bash
python v4/airtable/populate_data.py --base-id your_base_id_here --sample
```

For custom data from CSV files:

```bash
python v4/airtable/populate_data.py --base-id your_base_id_here --data-csv path/to/data.csv --minutes-csv path/to/minutes.csv
```

### 4. Troubleshooting Data Insertion 🐛

If you encounter errors when inserting data, use the debug script:

```bash
python v4/airtable/debug_data1.py
```

This will test inserting various fields to identify what's causing the error.

## 📋 Detailed Instructions for Manual Table Setup

If you're setting up tables manually in the Airtable UI:

1. Go to [Airtable](https://airtable.com) and log in
2. Create a new base (or use an existing one)
3. Create a table named "Data1"
4. Add fields one by one:
   - Click "+" to add a new field
   - Name the field (e.g., "Name")
   - Select the field type (e.g., "Single line text")
   - For select fields, add options after creating the field:
     - Click the dropdown arrow in the column header
     - Select "Customize field type"
     - Add your options (e.g., for "Type": Data, Minutes)
     - Choose colors for each option if desired
   - For "Keywords" field, make sure to select "Multiple select" type
5. Repeat for the "Data2" table

## 🔄 Recommended Workflow

1. **Setup**: Either use automated setup with [`create_table.py`](./create_table.py) or manual setup with the Airtable UI
2. **Verify**: Check that tables and fields are created correctly
3. **Initialize Options**: Run [`setup_select_options.py`](./setup_select_options.py) if using manual setup
4. **Populate**: Run [`populate_data.py`](./populate_data.py) with sample data or your own CSV files
5. **Troubleshoot**: If issues occur, run [`debug_data1.py`](./debug_data1.py) to diagnose

## 📝 Notes on Field Types

- **Single Select**: Allows choosing one option from a list
- **Multiple Select**: Allows choosing multiple options from a list
- When populating data:
  - Single select fields expect a string value
  - Multiple select fields expect an array of string values

## ⚠️ Common Issues

1. **422 Errors**: Usually caused by:
   - Trying to use a value not in the predefined options for a select field
   - Using a string instead of an array for multiple select fields
   - Using an array instead of a string for single select fields

2. **Permission Issues**:
   - Ensure your token has proper permissions
   - Personal Access Tokens need proper scope configuration

3. **Field Type Mismatches**:
   - Ensure data types match field settings (e.g., numbers for number fields)

## 📚 Scripts Reference

| Script | Purpose |
|--------|---------|
| [`create_table.py`](./create_table.py) | Creates base, tables, fields using Metadata API |
| [`create_table_alt.py`](./create_table_alt.py) | Alternative method for table creation |
| [`setup_airtable.py`](./setup_airtable.py) | Sets up fields in existing tables |
| [`setup_select_options.py`](./setup_select_options.py) | Initializes select options in existing fields |
| [`populate_data.py`](./populate_data.py) | Adds records to tables |
| [`debug_data1.py`](./debug_data1.py) | Diagnoses insertion issues |