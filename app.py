import streamlit as st

st.set_page_config(
    page_title="Urban Design Image Analysis - Redirecting", layout="wide"
)

st.title("Urban Design Image Analysis Tool")

st.markdown(
    """
## This application has been updated!

The application has been restructured to use Streamlit's multi-page framework.

Please run the application using:
```
streamlit run Home.py
```

or click the "Rerun" button above to load the new Home page.
"""
)

# Rerun to load the new home page
st.rerun()
