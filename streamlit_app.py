import streamlit as st
import requests
from datetime import datetime
import json

# Define available endpoints
ENDPOINTS = {
    "Generate Hotel Description": "/generate-hotel-reservation",
    "Generate Master Itinerary": "/generate-master-itinerary",
    "Generate Extra Daily Contents": "/generate-extra-daily-contents",
    "Generate Free Format Content": "/generate-free-format-content"
}

# Define available models
MODELS = {
    "Claude 3.5 Sonnet v2": None,  # Default model doesn't need a model_id
    "LLama 3.0 70b": "us.meta.llama3-3-70b-instruct-v1:0"
}

def call_api(endpoint, data, api_key):
    base_url = "https://m0zpgns4ce.execute-api.us-east-1.amazonaws.com/stg-public"
    api_url = f"{base_url}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }

    try:
        response = requests.post(api_url, json=data, headers=headers)
        response.raise_for_status()

        if response.headers.get("Content-Type") == "application/json":
            return response.json()
        else:
            return {"error": "Unexpected response format from API. Expected JSON."}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# Streamlit UI
st.title("Travel Content Generator")

# Input for API key
api_key = st.text_input("Enter your API key:", type="password")

# Model selection
selected_model = st.selectbox(
    "Select Model",
    list(MODELS.keys()),
    index=0  # Default to first option (Claude)
)

# Endpoint selection
selected_endpoint = st.selectbox(
    "Select Content Type",
    list(ENDPOINTS.keys())
)

# Initialize session state for storing form values
if 'form_values' not in st.session_state:
    st.session_state.form_values = {}

# Input fields based on selected endpoint
if selected_endpoint == "Generate Free Format Content":
    # Required field for free format
    st.subheader("Required Information")
    prompt = st.text_area("Enter your prompt", height=100)
    
    # Optional destination and dates for free format
    with st.expander("Optional Trip Information", expanded=False):
        destination_name = st.text_input("Destination Name (Optional)")
        col1, col2 = st.columns(2)
        with col1:
            trip_start_date = st.date_input("Trip Start Date (Optional)")
        with col2:
            trip_end_date = st.date_input("Trip End Date (Optional)")
else:
    # Required fields for other endpoints
    st.subheader("Required Information")
    destination_name = st.text_input("Destination Name")
    col1, col2 = st.columns(2)
    with col1:
        trip_start_date = st.date_input("Trip Start Date")
    with col2:
        trip_end_date = st.date_input("Trip End Date")

# Optional fields in expander
with st.expander("Optional Client Information", expanded=False):
    client_age = st.number_input("Client Age", min_value=0, max_value=120, value=0)
    number_of_trips = st.number_input("Number of Previous Trips", min_value=0, value=0)
    days_to_birthday = st.number_input("Days to Birthday", min_value=0, value=0)
    places_visited = st.text_input(
        "Places Visited (comma-separated)",
        help="Enter places separated by commas, e.g.: Paris, Rome, Tokyo"
    )
    client_since = st.number_input("Client Since (years)", min_value=0, value=0)

# Add session state initialization for tracking generation state
if 'content_generated' not in st.session_state:
    st.session_state.content_generated = False
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = None

# Generate button
if st.button("Generate Content"):
    if not api_key:
        st.error("Please enter your API key.")
    elif selected_endpoint == "Generate Free Format Content" and not prompt:
        st.error("Please enter a prompt.")
    elif selected_endpoint != "Generate Free Format Content" and not destination_name:
        st.error("Please enter a destination name.")
    else:
        with st.spinner('Generating content...'):
            # Prepare the data payload
            # Prepare the data payload
            if selected_endpoint == "Generate Free Format Content":
                data = {"prompt": prompt}
                # Add optional destination and dates if provided
                if destination_name:
                    data["destination_name"] = destination_name
                if trip_start_date:
                    data["trip_start_date"] = trip_start_date.strftime('%Y-%m-%d')
                if trip_end_date:
                    data["trip_end_date"] = trip_end_date.strftime('%Y-%m-%d')
            else:
                data = {
                    "destination_name": destination_name,
                    "trip_start_date": trip_start_date.strftime('%Y-%m-%d'),
                    "trip_end_date": trip_end_date.strftime('%Y-%m-%d'),
                }

            # Add model_id if LLama is selected
            if MODELS[selected_model]:  # If model_id is not None
                data["model_id"] = MODELS[selected_model]

            # Add optional fields
            if client_age > 0:
                data["client_age"] = client_age
            if number_of_trips > 0:
                data["number_of_trips"] = number_of_trips
            if days_to_birthday > 0:
                data["days_to_birthday"] = days_to_birthday
            if places_visited:
                data["places_visited"] = [place.strip() for place in places_visited.split(",") if place.strip()]
            if client_since > 0:
                data["client_since"] = client_since

            # Store current form values
            st.session_state.form_values = data.copy()

            # Call API and get response
            response = call_api(ENDPOINTS[selected_endpoint], data, api_key)

            if "error" in response:
                st.error(f"Error: {response['error']}")
            else:
                st.success("Content generated successfully!")
                st.session_state.content_generated = True
                st.session_state.generated_content = response.get("result", "No content available")
                
                st.subheader("Generated Content")
                st.write(st.session_state.generated_content)

                with st.expander("View Raw Response"):
                    st.json(response)

# Feedback section
if st.session_state.content_generated:
    st.markdown("---")
    st.subheader("Feedback Section")
    feedback = st.text_area("Please provide your feedback for improving the content:", height=100)
    
    if st.button("Regenerate with Feedback"):
        if not feedback:
            st.warning("Please provide feedback before regenerating.")
        else:
            with st.spinner('Regenerating content with feedback...'):
                # Get the original data from session state
                data = st.session_state.form_values.copy()
                
                # Add feedback-related fields
                data.update({
                    "generated_content": st.session_state.generated_content,
                    "user_feedback": feedback
                })

                # Add model_id if LLama is selected
                if MODELS[selected_model]:
                    data["model_id"] = MODELS[selected_model]

                # Call API with feedback
                response = call_api(ENDPOINTS[selected_endpoint], data, api_key)

                if "error" in response:
                    st.error(f"Error: {response['error']}")
                else:
                    st.success("Content regenerated successfully!")
                    st.session_state.generated_content = response.get("result", "No content available")
                    
                    st.subheader("Updated Content")
                    st.write(st.session_state.generated_content)

                    with st.expander("View Raw Response"):
                        st.json(response)

# Add helpful information
st.markdown("---")
st.markdown("""
### Notes:
- For Free Format Content, only the prompt is required
- For other content types, Destination Name and Dates are required
- All dates should be in YYYY-MM-DD format
- Places visited should be comma-separated
- Optional fields can be left at 0 or empty if not applicable
- Claude 3.5 Sonnet v2 is the default model
- LLama 3.0 70b is available as an alternative model
""")