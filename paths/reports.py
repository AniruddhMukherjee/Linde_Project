import streamlit as st
import pandas as pd
import os
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

def enter_name():
    st.subheader("1. Enter Report Name:")
    report_name = st.text_input("Enter Report Name:")
    if report_name:
        st.write(f"Report Name: {report_name}")
        return report_name
    return None

def load_questionnaires(questionnaire_path):
    try:
        questionnaire_data = pd.read_csv(questionnaire_path)
        return questionnaire_data
    except Exception as e:
        st.error(f"Error loading questionnaires: {str(e)}")
        return None

def show_questionnaires(questionnaire_path):
    questionnaire_data = pd.read_csv(questionnaire_path)
    
    gb = GridOptionsBuilder.from_dataframe(questionnaire_data)
    gb.configure_default_column(editable=False)
    gb.configure_selection(selection_mode="single", use_checkbox=True)
    gridOptions = gb.build()
    
    st.subheader("2. Select a Questionnaire:")
    ag_response = AgGrid(
        questionnaire_data,
        gridOptions=gridOptions,
        fit_columns_on_grid_load=True,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        enable_enterprise_modules=False,
        key='questionnaire_grid'
    )
    
    selected_rows = ag_response["selected_rows"]
    
    # Store the selected questionnaire in session state
    if selected_rows and len(selected_rows) > 0:
        # Convert the selected row to a dictionary
        selected_dict = dict(selected_rows[0])
        st.session_state.selected_questionnaire = selected_dict
    else:
        st.session_state.selected_questionnaire = None
    
    return st.session_state.selected_questionnaire













def display_questionnaire_details(questionnaire):
    st.sidebar.subheader("Questionnaire Details")
    for key, value in questionnaire.items():
        st.sidebar.write(f"{key}: {value}")







def Reports_page():
    st.title("Reports")

    selected_project = st.session_state.get("selected_project", None)

    if not selected_project:
        st.warning("Please select a project first.")
        return

    # Display project information
    data = pd.read_csv("Data.csv")
    project_data = data[data['Project'] == selected_project].iloc[0]

    st.sidebar.subheader("Project Information")
    st.sidebar.write(f"'{selected_project}' has been selected")
    st.sidebar.write(f"Team Lead: {project_data['Team Lead']}")
    st.sidebar.write(f"Description: {project_data['Description']}")

    # Step 1: Enter report name
    st.subheader("1. Enter Report Name:")
    report_name = st.text_input("Enter Report Name:")

    # Step 2: Select questionnaire
    questionnaire_path = os.path.join(os.getcwd(), "questionnaires.csv")
    
    if not os.path.exists(questionnaire_path):
        st.error(f"Questionnaire file not found: {questionnaire_path}")
        return

    selected_questionnaire = show_questionnaires(questionnaire_path)

    if selected_questionnaire:
        display_questionnaire_details(selected_questionnaire)

        # Step 3: Generate Report
        st.subheader("3. Generate Report")
        if st.button("Generate Report"):
            if report_name:
                st.success(f"Report '{report_name}' generated successfully for project '{selected_project}' using questionnaire '{selected_questionnaire['name']}'")
                # Add your report generation logic here
            else:
                st.warning("Please enter a report name before generating the report.")
    else:
        st.info("Please select a questionnaire to proceed.")