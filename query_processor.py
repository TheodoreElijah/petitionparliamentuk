import os
import json
import pandas as pd
import re
from openai import OpenAI

# Initialize OpenAI client
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "default_key")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def process_natural_language_query(query, df):
    """
    Process a natural language query against the petition dataset using OpenAI.
    
    Args:
        query (str): The natural language query from the user
        df (pandas.DataFrame): The petition dataframe
        
    Returns:
        dict: Dictionary containing:
            - interpretation: What the AI understood from the query
            - filtered_data: DataFrame with results matching the query
            - analysis: Additional AI analysis of the results
    """
    try:
        # Generate data context for the AI
        data_context = generate_data_context(df)
        
        # Create the prompt for OpenAI
        system_prompt = f"""
        You are an expert data analyst specializing in UK Parliament petition data analysis.
        
        You have access to a dataset of UK Parliament petitions with the following structure:
        - Petition: The title/description of the petition
        - URL: Link to the petition page
        - State: Current status (closed, rejected, open, etc.)
        - Signatures Count: Number of people who signed the petition
        
        {data_context}
        
        Your task is to:
        1. Interpret the user's natural language query
        2. Determine what filtering, sorting, or analysis criteria should be applied
        3. Provide filtering instructions in JSON format
        4. Generate insights about the results
        
        Respond with JSON in this exact format:
        {{
            "interpretation": "Clear explanation of what you understood from the query",
            "filters": {{
                "signature_min": null or number,
                "signature_max": null or number,
                "states": null or array of states,
                "keywords": null or array of keywords to search in petition titles,
                "limit": null or number of top results to show,
                "sort_by": "signatures_desc" or "signatures_asc" or "alphabetical"
            }},
            "analysis_request": "What additional analysis should be provided for these results"
        }}
        """
        
        user_prompt = f"User query: {query}"
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        # Parse the response
        response_content = response.choices[0].message.content
        if response_content is None:
            raise ValueError("Empty response from OpenAI")
        ai_response = json.loads(response_content)
        
        # Apply filters to the dataframe
        filtered_df = apply_filters(df, ai_response.get('filters', {}))
        
        # Generate additional analysis
        analysis = generate_analysis(filtered_df, ai_response.get('analysis_request', ''), query)
        
        return {
            'interpretation': ai_response.get('interpretation', 'Query processed'),
            'filtered_data': filtered_df,
            'analysis': analysis,
            'raw_ai_response': ai_response
        }
        
    except Exception as e:
        # Fallback to simple keyword matching if AI fails
        fallback_result = fallback_query_processing(query, df)
        fallback_result['error'] = f"AI processing failed, using fallback: {str(e)}"
        return fallback_result

def generate_data_context(df):
    """Generate context about the dataset for the AI."""
    if df.empty:
        return "The dataset is currently empty."
    
    # Calculate key statistics
    total_petitions = len(df)
    total_signatures = df['Signatures Count'].sum()
    avg_signatures = df['Signatures Count'].mean()
    median_signatures = df['Signatures Count'].median()
    max_signatures = df['Signatures Count'].max()
    min_signatures = df['Signatures Count'].min()
    
    # Get state distribution
    state_counts = df['State'].value_counts()
    states_info = ", ".join([f"{count} {state}" for state, count in state_counts.items()])
    
    # Get signature ranges
    high_signature_petitions = len(df[df['Signatures Count'] > 100000])
    medium_signature_petitions = len(df[(df['Signatures Count'] >= 10000) & (df['Signatures Count'] <= 100000)])
    low_signature_petitions = len(df[df['Signatures Count'] < 10000])
    
    # Sample petition titles for context
    sample_titles = df['Petition'].head(5).tolist()
    
    context = f"""
    Current dataset contains {total_petitions:,} petitions with:
    - Total signatures across all petitions: {total_signatures:,}
    - Average signatures per petition: {avg_signatures:.0f}
    - Median signatures: {median_signatures:.0f}
    - Range: {min_signatures:,} to {max_signatures:,} signatures
    - High-impact petitions (>100K signatures): {high_signature_petitions}
    - Medium-impact petitions (10K-100K signatures): {medium_signature_petitions}
    - Lower-impact petitions (<10K signatures): {low_signature_petitions}
    - Petition states: {states_info}
    - Sample petition titles: {'; '.join(sample_titles[:3])}
    """
    
    return context

def apply_filters(df, filters):
    """Apply filtering criteria to the dataframe."""
    if df.empty:
        return df
    
    filtered_df = df.copy()
    
    # Apply signature range filters
    if filters.get('signature_min') is not None:
        filtered_df = filtered_df[filtered_df['Signatures Count'] >= filters['signature_min']]
    
    if filters.get('signature_max') is not None:
        filtered_df = filtered_df[filtered_df['Signatures Count'] <= filters['signature_max']]
    
    # Apply state filters
    if filters.get('states') and isinstance(filters['states'], list):
        # Case-insensitive state matching
        states_lower = [state.lower() for state in filters['states']]
        filtered_df = filtered_df[filtered_df['State'].str.lower().isin(states_lower)]
    
    # Apply keyword filters
    if filters.get('keywords') and isinstance(filters['keywords'], list):
        # Create a pattern that matches any of the keywords (case-insensitive)
        pattern = '|'.join([re.escape(keyword) for keyword in filters['keywords']])
        filtered_df = filtered_df[
            filtered_df['Petition'].str.contains(pattern, case=False, na=False)
        ]
    
    # Apply sorting
    sort_by = filters.get('sort_by', 'signatures_desc')
    if sort_by == 'signatures_desc':
        filtered_df = filtered_df.sort_values('Signatures Count', ascending=False)
    elif sort_by == 'signatures_asc':
        filtered_df = filtered_df.sort_values('Signatures Count', ascending=True)
    elif sort_by == 'alphabetical':
        filtered_df = filtered_df.sort_values('Petition', ascending=True)
    
    # Apply limit
    if filters.get('limit') and isinstance(filters['limit'], int) and filters['limit'] > 0:
        filtered_df = filtered_df.head(filters['limit'])
    
    return filtered_df.reset_index(drop=True)

def generate_analysis(filtered_df, analysis_request, original_query):
    """Generate additional analysis using OpenAI."""
    if filtered_df.empty:
        return "No petitions found matching the specified criteria."
    
    try:
        # Prepare data summary for analysis
        data_summary = create_analysis_summary(filtered_df)
        
        analysis_prompt = f"""
        Based on the following petition data analysis results, provide insights and observations:
        
        Original query: {original_query}
        Analysis request: {analysis_request}
        
        Data summary:
        {data_summary}
        
        Please provide:
        1. Key insights about the filtered results
        2. Notable patterns or trends
        3. Comparison with overall dataset context
        4. Any interesting observations about signature counts, topics, or states
        
        Keep the analysis concise but informative, focusing on the most relevant insights for the user's query.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a data analyst providing insights on UK Parliament petition data."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        # Fallback to basic statistical analysis
        return generate_basic_analysis(filtered_df)

def create_analysis_summary(df):
    """Create a summary of filtered data for analysis."""
    if df.empty:
        return "No data to analyze."
    
    total_petitions = len(df)
    total_signatures = df['Signatures Count'].sum()
    avg_signatures = df['Signatures Count'].mean()
    median_signatures = df['Signatures Count'].median()
    
    # State distribution
    state_counts = df['State'].value_counts()
    
    # Top petitions
    top_5 = df.nlargest(5, 'Signatures Count')
    
    summary = f"""
    Filtered Results Summary:
    - Total petitions: {total_petitions}
    - Total signatures: {total_signatures:,}
    - Average signatures: {avg_signatures:.0f}
    - Median signatures: {median_signatures:.0f}
    - State distribution: {dict(state_counts)}
    - Top 5 petitions by signatures:
    """
    
    for idx, row in top_5.iterrows():
        summary += f"\n  • {row['Petition'][:100]}... ({row['Signatures Count']:,} signatures, {row['State']})"
    
    return summary

def generate_basic_analysis(df):
    """Generate basic statistical analysis as fallback."""
    if df.empty:
        return "No petitions found matching your criteria."
    
    total_petitions = len(df)
    total_signatures = df['Signatures Count'].sum()
    avg_signatures = df['Signatures Count'].mean()
    
    # Find the most signed petition
    top_petition = df.loc[df['Signatures Count'].idxmax()]
    
    # State analysis
    state_counts = df['State'].value_counts()
    most_common_state = state_counts.index[0] if not state_counts.empty else "unknown"
    
    analysis = f"""
    **Analysis Results:**
    
    - Found **{total_petitions}** petitions matching your criteria
    - Combined total of **{total_signatures:,}** signatures
    - Average of **{avg_signatures:.0f}** signatures per petition
    - Most signed petition: "{top_petition['Petition'][:100]}..." with **{top_petition['Signatures Count']:,}** signatures
    - Most common status: **{most_common_state}** ({state_counts[most_common_state]} petitions)
    
    **Key Observations:**
    - The results show varying levels of public engagement
    - Petition success varies significantly across different topics
    """
    
    if total_signatures > 1000000:
        analysis += "\n- This query captured some highly successful petitions with substantial public support"
    elif total_signatures > 100000:
        analysis += "\n- This represents a good collection of petitions with notable public interest"
    else:
        analysis += "\n- These petitions represent more niche or specialized concerns"
    
    return analysis

def fallback_query_processing(query, df):
    """Simple fallback query processing using keyword matching."""
    query_lower = query.lower()
    
    # Simple keyword extraction and filtering
    signature_keywords = {
        'high': 100000, 'popular': 50000, 'most': None, 'top': None,
        'over 100k': 100000, 'above 50k': 50000, 'more than': None
    }
    
    filtered_df = df.copy()
    interpretation = f"Processed query using keyword matching: '{query}'"
    
    # Look for signature-related criteria
    for keyword, threshold in signature_keywords.items():
        if keyword in query_lower and threshold:
            filtered_df = filtered_df[filtered_df['Signatures Count'] >= threshold]
            interpretation += f" (filtered for signatures >= {threshold:,})"
            break
    
    # Look for state-related criteria
    if 'closed' in query_lower:
        filtered_df = filtered_df[filtered_df['State'].str.lower() == 'closed']
        interpretation += " (filtered for closed petitions)"
    elif 'rejected' in query_lower:
        filtered_df = filtered_df[filtered_df['State'].str.lower() == 'rejected']
        interpretation += " (filtered for rejected petitions)"
    elif 'open' in query_lower:
        filtered_df = filtered_df[filtered_df['State'].str.lower() == 'open']
        interpretation += " (filtered for open petitions)"
    
    # Look for topic keywords
    topic_keywords = [
        'health', 'nhs', 'education', 'school', 'tax', 'brexit', 'eu', 'environment',
        'climate', 'transport', 'housing', 'benefit', 'pension', 'immigration'
    ]
    
    for keyword in topic_keywords:
        if keyword in query_lower:
            filtered_df = filtered_df[
                filtered_df['Petition'].str.contains(keyword, case=False, na=False)
            ]
            interpretation += f" (filtered for '{keyword}' in title)"
            break
    
    # Sort by signatures descending
    filtered_df = filtered_df.sort_values('Signatures Count', ascending=False)
    
    # Limit results if asking for "top" or "most"
    if any(word in query_lower for word in ['top', 'most', 'highest']):
        filtered_df = filtered_df.head(20)
        interpretation += " (showing top 20 results)"
    
    return {
        'interpretation': interpretation,
        'filtered_data': filtered_df,
        'analysis': generate_basic_analysis(filtered_df)
    }
