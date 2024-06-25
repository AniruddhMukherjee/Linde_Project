import streamlit as st
import pandas as pd
import os
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

def questionnaire_table_size(questionnaire_data):
    # Calculate the height based on the number of rows
    row_height = 35  # Approximate height of each row in pixels
    header_height = 40  # Approximate height of the header in pixels
    min_height = 50  # Minimum height of the grid
    max_height = 600  # Maximum height of the grid
    calculated_height = min(max(min_height, len(questionnaire_data) * row_height + header_height), max_height)
    return calculated_height


def enter_name():
    st.subheader("1. Enter Report Name:")
    report_name = st.text_input("Enter Report Name:")
    if report_name:
        #st.write(f"Report Name: {report_name}")
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
    grid_response = AgGrid(
        questionnaire_data,
        gridOptions=gridOptions,
        fit_columns_on_grid_load=True,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        enable_enterprise_modules=False,
        key='questionnaire_grid',
        height=questionnaire_table_size(questionnaire_data)
    )
    
    selected_rows = grid_response["selected_rows"]
    
    if isinstance(selected_rows, pd.DataFrame) and not selected_rows.empty:
        selected_questionnaire = selected_rows.iloc[0]
        st.sidebar.title("Questionnaire Details")
        st.sidebar.write(f"**Name:** {selected_questionnaire['name']}")
        st.sidebar.write(f"**Category:** {selected_questionnaire['category']}")
        st.sidebar.write(f"**User:** {selected_questionnaire['user']}")
        st.sidebar.write(f"**Description:** {selected_questionnaire['description']}")
        st.sidebar.write(f"**Date:** {selected_questionnaire['Date']}")
        
        st.session_state.selected_category = selected_questionnaire['category']
        return selected_questionnaire
    elif isinstance(selected_rows, list) and len(selected_rows) > 0:
        selected_questionnaire = selected_rows[0]
        st.write("Selected Questionnaire:", selected_questionnaire)
        
        st.session_state.selected_category = selected_questionnaire['category']
        return selected_questionnaire
    else:
        st.warning("No questionnaire selected.")
        st.session_state.selected_category = None
        return None


def documents_table_size(filtered_data):
    # Calculate the height based on the number of rows
    row_height = 35  # Approximate height of each row in pixels
    header_height = 40  # Approximate height of the header in pixels
    min_height = 50  # Minimum height of the grid
    max_height = 600  # Maximum height of the grid
    calculated_height = min(max(min_height, len(filtered_data) * row_height + header_height), max_height)
    return calculated_height

def show_filtered_documents(project_file_path, questionnaire_name):
    if 'selected_category' not in st.session_state or st.session_state.selected_category is None:
        st.warning("Please select a questionnaire first to view relevant documents.")
        return

    project_data = pd.read_csv(project_file_path)
    
    filtered_data = project_data[project_data['Category'].str.contains(st.session_state.selected_category, case=False, na=False)]
    
    if filtered_data.empty:
        st.info(f"No documents found for the category: {st.session_state.selected_category}")
        return

    gb = GridOptionsBuilder.from_dataframe(filtered_data)
    gb.configure_default_column(editable=False)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gridOptions = gb.build()

    st.subheader("3. Documents to be assigned to the questionnaire:")
    ag_response = AgGrid(
        filtered_data,
        gridOptions=gridOptions,
        fit_columns_on_grid_load=True,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        enable_enterprise_modules=False,
        key='documents_grid',
        height=documents_table_size(filtered_data)
    )

    selected_docs = ag_response["selected_rows"]
    if isinstance(selected_docs, pd.DataFrame) and not selected_docs.empty:
        st.write("Client documents to assign to the questionnaire:")
        st.write(selected_docs)
        
        if st.button("Assign Documents"):
            assign_documents(questionnaire_name, selected_docs)

def assign_documents(questionnaire_name, selected_docs):
    report_name = st.session_state.get('report_name', 'default_report')
    file_name = f"{report_name}_assigned_documents.csv"
    
    assigned_documents = pd.DataFrame({
        'Questionnaire': [questionnaire_name] * len(selected_docs),
        'Documents': selected_docs['Title'].tolist()
    })
    
    if os.path.exists(file_name):
        existing_data = pd.read_csv(file_name)
        updated_data = pd.concat([existing_data, assigned_documents], ignore_index=True)
    else:
        updated_data = assigned_documents
    
    updated_data.to_csv(file_name, index=False)
    
    st.success(f"Documents assigned successfully! File saved as {file_name}")

def Reports_page():
    st.title("Reports")

    selected_project = st.session_state.get("selected_project", None)

    if not selected_project:
        st.warning("Please select a project first.")
        return

    data = pd.read_csv("Data.csv")
    project_data = data[data['Project'] == selected_project].iloc[0]

    st.sidebar.title("Project Information")
    st.sidebar.write(f"**Name:** '{selected_project}'")
    st.sidebar.write(f"**Team Lead**: {project_data['Team Lead']}")
    st.sidebar.write(f"**Description**: {project_data['Description']}")

    report_name = enter_name()
    st.session_state['report_name'] = report_name

    if not report_name:
        st.warning("Enter report name to Proceed!")
        return

    questionnaire_path = os.path.join(os.getcwd(), "questionnaires.csv")
    
    if not os.path.exists(questionnaire_path):
        st.error(f"Questionnaire file not found: {questionnaire_path}")
        return

    selected_questionnaire = show_questionnaires(questionnaire_path)

    if selected_questionnaire is not None:
        project_paths_file = "project_paths.csv"
        project_paths_path = os.path.join(os.getcwd(), project_paths_file)

        if os.path.exists(project_paths_path):
            project_paths_df = pd.read_csv(project_paths_path)
            project_file_path_df = project_paths_df.loc[project_paths_df['File Name'] == selected_project, 'File Path']
            if not project_file_path_df.empty:
                project_file_path = project_file_path_df.iloc[0]
                
                show_filtered_documents(project_file_path, selected_questionnaire['name'])

                #st.subheader("4. Generate Report")
                if st.button("Generate Report"):
                    if report_name:
                        st.success(f"Report '{report_name}' generated successfully for project '{selected_project}' using questionnaire '{selected_questionnaire['name']}'")
                        st.session_state.selected_questionnaire = selected_questionnaire
                    else:
                        st.warning("Please enter a report name before generating the report.")
            else:
                st.error(f"Project file path not found for project: {selected_project}")
        else:
            st.error(f"Project paths file not found: {project_paths_path}")
    else:
        st.info("Please select a questionnaire to proceed.")