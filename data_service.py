import requests
import pandas as pd
import streamlit as st
import json

# Google Apps Script URL for petition data
PETITION_DATA_URL = "https://script.googleusercontent.com/macros/echo?user_content_key=AehSKLjpBMhTA3z5r9d4tIE8bXH8_yoJx1JXDdPFBLY1Y1ZMzFpcE_5QrMptlGIyxwTvKepnxf_q9zS6XES-Micm_xN263CdIXLeyqV6k1uh0yjVkRfCzw7AU3r_KVgHtIvhNuMSxc71QP1omNFoAgUN1g11mlSbRbdzsGScYJ-tItwbMz4XvhggUheeqiDsLKUSgAsa8KjorD83Guv978RzoGghWJ1xr67KrySu4vgLfsNCF7jvhFOA_fR62WlQVUqCO3V0uh0xRYGoZFpqS1liFzuqsi2K9w&lib=Mnv4iSODQPAVnoyklcKaVOSTmmKHkEHEC"

def fetch_petition_data():
    """
    Fetch petition data from the Google Apps Script URL.
    
    Returns:
        pandas.DataFrame: DataFrame containing petition data with columns:
                         - Petition: Title of the petition
                         - URL: Link to the petition
                         - State: Current status (closed, rejected, etc.)
                         - Signatures Count: Number of signatures
    """
    try:
        # Make request to the Google Apps Script endpoint with redirect following
        response = requests.get(PETITION_DATA_URL, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        
        # Convert to DataFrame
        # The first row contains headers, so we use it to create column names
        if len(data) > 1:
            headers = data[0]  # First row contains headers
            rows = data[1:]    # Remaining rows contain data
            
            # Create DataFrame
            df = pd.DataFrame(rows, columns=headers)
            
            # Convert signatures count to numeric, handling any non-numeric values
            df['Signatures Count'] = pd.to_numeric(df['Signatures Count'], errors='coerce')
            
            # Remove any rows with invalid signature counts
            df = df.dropna(subset=['Signatures Count'])
            
            # Convert signatures count to integer
            df['Signatures Count'] = df['Signatures Count'].astype(int)
            
            # Clean up text fields
            df['Petition'] = df['Petition'].astype(str).str.strip()
            df['URL'] = df['URL'].astype(str).str.strip()
            df['State'] = df['State'].astype(str).str.strip()
            
            # Sort by signature count descending
            df = df.sort_values('Signatures Count', ascending=False)
            
            # Reset index
            df = df.reset_index(drop=True)
            
            return df
        else:
            raise ValueError("No data received from the petition API")
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch petition data from API: {str(e)}")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse petition data as JSON: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing petition data: {str(e)}")

def get_data_summary(df):
    """
    Generate a summary of the petition data for context.
    
    Args:
        df (pandas.DataFrame): The petition dataframe
        
    Returns:
        str: A summary string describing the data
    """
    if df is None or df.empty:
        return "No petition data available."
    
    total_petitions = len(df)
    total_signatures = df['Signatures Count'].sum()
    avg_signatures = df['Signatures Count'].mean()
    max_signatures = df['Signatures Count'].max()
    
    # Get state distribution
    states = df['State'].value_counts()
    state_summary = ", ".join([f"{count} {state}" for state, count in states.items()])
    
    # Get top topics (simplified - just looking at common words)
    petition_text = " ".join(df['Petition'].astype(str))
    
    summary = f"""
    Dataset Summary:
    - Total petitions: {total_petitions:,}
    - Total signatures: {total_signatures:,}
    - Average signatures per petition: {avg_signatures:.0f}
    - Highest signature count: {max_signatures:,}
    - Petition states: {state_summary}
    - Sample petition titles: {', '.join(df['Petition'].head(3).tolist())}
    """
    
    return summary

def validate_data(df):
    """
    Validate the petition data structure and content.
    
    Args:
        df (pandas.DataFrame): The petition dataframe
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if df is None:
        return False, "DataFrame is None"
    
    if df.empty:
        return False, "DataFrame is empty"
    
    required_columns = ['Petition', 'URL', 'State', 'Signatures Count']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        return False, f"Missing required columns: {missing_columns}"
    
    # Check for valid signature counts
    if df['Signatures Count'].isna().any():
        return False, "Some petition signature counts are missing or invalid"
    
    if (df['Signatures Count'] < 0).any():
        return False, "Some petition signature counts are negative"
    
    # Check for empty petition titles
    if df['Petition'].isna().any() or (df['Petition'].str.strip() == '').any():
        return False, "Some petition titles are missing or empty"
    
    return True, "Data validation passed"
