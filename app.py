import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_service import fetch_petition_data
from query_processor import process_natural_language_query
import json

# Page configuration
st.set_page_config(
    page_title="UK Parliament Petitions Query Tool",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main title
st.title("🏛️ UK Parliament Petitions Query Tool")
st.markdown("Query UK Parliament petition data using natural language powered by OpenAI")

# Initialize session state
if 'petition_data' not in st.session_state:
    st.session_state.petition_data = None
if 'query_results' not in st.session_state:
    st.session_state.query_results = None

# Sidebar for data management
with st.sidebar:
    st.header("Data Management")
    
    # Data loading section
    st.subheader("📊 Data Source")
    st.info("Data is fetched from UK Parliament petition database")
    
    if st.button("🔄 Load/Refresh Data", type="primary"):
        with st.spinner("Fetching petition data..."):
            try:
                data = fetch_petition_data()
                if data is not None and not data.empty:
                    st.session_state.petition_data = data
                    st.success(f"✅ Loaded {len(data)} petitions")
                else:
                    st.error("❌ No data received or data is empty")
            except Exception as e:
                st.error(f"❌ Error loading data: {str(e)}")
    
    # Data preview
    if st.session_state.petition_data is not None:
        st.subheader("📋 Data Overview")
        df = st.session_state.petition_data
        st.metric("Total Petitions", len(df))
        st.metric("Total Signatures", f"{df['Signatures Count'].sum():,}")
        st.metric("Avg Signatures", f"{df['Signatures Count'].mean():.0f}")
        
        # State distribution
        state_counts = df['State'].value_counts()
        st.subheader("📊 Petition States")
        for state, count in state_counts.items():
            st.write(f"**{str(state).title()}:** {count}")

# Main content area
if st.session_state.petition_data is not None:
    # Query interface
    st.header("🔍 Natural Language Query")
    
    # Sample queries
    st.subheader("💡 Sample Queries")
    sample_queries = [
        "Show me petitions with over 100,000 signatures",
        "What are the most popular petition topics?",
        "Find petitions related to healthcare or NHS",
        "Show closed petitions about environment or climate",
        "Which petitions have the highest signature counts?",
        "Show me petitions about education or schools",
        "Find petitions related to taxation or tax",
        "What petitions are about Brexit or EU?"
    ]
    
    cols = st.columns(2)
    for i, query in enumerate(sample_queries):
        col = cols[i % 2]
        if col.button(f"📝 {query}", key=f"sample_{i}"):
            st.session_state.query_input = query
    
    # Query input
    query = st.text_area(
        "Enter your question about the petition data:",
        value=st.session_state.get('query_input', ''),
        height=100,
        placeholder="e.g., 'Show me petitions with over 50,000 signatures about healthcare'"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        process_query = st.button("🚀 Process Query", type="primary", disabled=not query.strip())
    
    if process_query and query.strip():
        with st.spinner("Processing your query with OpenAI..."):
            try:
                result = process_natural_language_query(query, st.session_state.petition_data)
                st.session_state.query_results = result
            except Exception as e:
                st.error(f"❌ Error processing query: {str(e)}")
                st.session_state.query_results = None
    
    # Display results
    if st.session_state.query_results:
        st.header("📊 Query Results")
        
        result = st.session_state.query_results
        
        # Display interpretation
        if 'interpretation' in result:
            st.subheader("🧠 Query Interpretation")
            st.info(result['interpretation'])
        
        # Display filtered data
        if 'filtered_data' in result and not result['filtered_data'].empty:
            df_filtered = result['filtered_data']
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Matching Petitions", len(df_filtered))
            with col2:
                st.metric("Total Signatures", f"{df_filtered['Signatures Count'].sum():,}")
            with col3:
                st.metric("Average Signatures", f"{df_filtered['Signatures Count'].mean():.0f}")
            with col4:
                st.metric("Max Signatures", f"{df_filtered['Signatures Count'].max():,}")
            
            # Visualization
            st.subheader("📈 Visualization")
            
            if len(df_filtered) > 0:
                # Choose visualization based on data size
                if len(df_filtered) <= 20:
                    # Bar chart for smaller datasets
                    fig = px.bar(
                        df_filtered.head(20),
                        x='Signatures Count',
                        y='Petition',
                        orientation='h',
                        title="Petition Signatures",
                        color='State',
                        height=600
                    )
                    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                else:
                    # Histogram for larger datasets
                    fig = px.histogram(
                        df_filtered,
                        x='Signatures Count',
                        nbins=20,
                        title="Distribution of Signature Counts",
                        color='State'
                    )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # State distribution pie chart if multiple states
                if len(df_filtered['State'].unique()) > 1:
                    state_fig = px.pie(
                        df_filtered,
                        names='State',
                        title="Petition States Distribution"
                    )
                    st.plotly_chart(state_fig, use_container_width=True)
            
            # Data table
            st.subheader("📋 Detailed Results")
            
            # Format the dataframe for display
            display_df = df_filtered.copy()
            display_df['Signatures Count'] = display_df['Signatures Count'].apply(lambda x: f"{x:,}")
            display_df['URL'] = display_df['URL'].apply(lambda x: f"[View Petition]({x})")
            
            st.dataframe(
                display_df,
                use_container_width=True,
                column_config={
                    "URL": st.column_config.LinkColumn("Petition Link"),
                    "Signatures Count": st.column_config.TextColumn("Signatures"),
                    "State": st.column_config.TextColumn("Status"),
                    "Petition": st.column_config.TextColumn("Title", width="large")
                }
            )
            
            # Download option
            csv = df_filtered.to_csv(index=False)
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv,
                file_name="petition_query_results.csv",
                mime="text/csv"
            )
        
        else:
            st.warning("🔍 No petitions found matching your query criteria.")
        
        # Display analysis if available
        if 'analysis' in result:
            st.subheader("🔍 AI Analysis")
            st.markdown(result['analysis'])

    # Data preview section
    st.header("📊 Data Preview")
    
    # Display sample data
    df = st.session_state.petition_data
    
    # Quick stats
    st.subheader("📈 Quick Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        top_petition = df.loc[df['Signatures Count'].idxmax()]
        st.metric(
            "Most Signed Petition",
            f"{top_petition['Signatures Count']:,}",
            delta=top_petition['Petition'][:50] + "..."
        )
    
    with col2:
        avg_signatures = df['Signatures Count'].mean()
        st.metric("Average Signatures", f"{avg_signatures:.0f}")
    
    with col3:
        high_signature_count = len(df[df['Signatures Count'] > 10000])
        st.metric("Petitions > 10K Signatures", high_signature_count)
    
    # Top petitions table
    st.subheader("🏆 Top 10 Most Signed Petitions")
    top_petitions = df.nlargest(10, 'Signatures Count').copy()
    top_petitions['Signatures Count'] = top_petitions['Signatures Count'].apply(lambda x: f"{x:,}")
    top_petitions['URL'] = top_petitions['URL'].apply(lambda x: f"[View]({x})")
    
    st.dataframe(
        top_petitions,
        use_container_width=True,
        column_config={
            "URL": st.column_config.LinkColumn("Link"),
            "Signatures Count": st.column_config.TextColumn("Signatures"),
            "State": st.column_config.TextColumn("Status"),
            "Petition": st.column_config.TextColumn("Title", width="large")
        }
    )

else:
    # No data loaded yet
    st.info("👆 Please click 'Load/Refresh Data' in the sidebar to begin")
    
    # Show instructions
    st.header("📖 How to Use")
    st.markdown("""
    1. **Load Data**: Click the 'Load/Refresh Data' button in the sidebar
    2. **Ask Questions**: Use natural language to query the petition data
    3. **View Results**: See visualizations and filtered data based on your query
    4. **Explore**: Try different types of questions to discover insights
    
    **Example Queries:**
    - "Show me petitions with more than 100,000 signatures"
    - "What are the most popular topics?"
    - "Find healthcare-related petitions"
    - "Show closed petitions about climate change"
    """)

# Footer
st.markdown("---")
st.markdown("**Data Source:** UK Parliament Petitions | **Powered by:** OpenAI GPT-4o")
