import streamlit as st
import pandas as pd
import os
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

from paths.view_reports import view_reports_page

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
        st.sidebar.divider()
        
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
        st.table(selected_docs)
        
    return selected_docs

def assign_documents_and_generate_report(questionnaire_name, selected_docs, report_name, selected_project, questionnaire_data):
    success_messages = []
    error_messages = []

    try:
        # Create a directory for the report
        report_dir = f"{selected_project}_{report_name}"
        os.makedirs(report_dir, exist_ok=True)
        success_messages.append(f"Report directory created: {report_dir}")

        # Handle different possible formats of selected_docs
        if isinstance(selected_docs, pd.DataFrame):
            doc_titles = selected_docs['Title'].tolist()
        elif isinstance(selected_docs, list) and all(isinstance(doc, dict) for doc in selected_docs):
            doc_titles = [doc['Title'] for doc in selected_docs]
        elif isinstance(selected_docs, list) and all(isinstance(doc, str) for doc in selected_docs):
            doc_titles = selected_docs
        else:
            raise ValueError("Invalid format for selected documents")

        # Assigned documents CSV
        assigned_file = os.path.join(report_dir, "assigned_documents.csv")
        assigned_documents = pd.DataFrame({
            'Project': [selected_project] * len(doc_titles),
            'Questionnaire': [questionnaire_name] * len(doc_titles),
            'Documents': doc_titles
        })
        assigned_documents.to_csv(assigned_file, index=False)
        success_messages.append(f"Documents assigned successfully! File saved as {assigned_file}")

        # Included documents CSV
        included_file = os.path.join(report_dir, "included_documents.csv")
        if isinstance(selected_docs, pd.DataFrame):
            selected_docs.to_csv(included_file, index=False)
        else:
            pd.DataFrame({'Title': doc_titles}).to_csv(included_file, index=False)
        success_messages.append(f"Included documents saved as {included_file}")

        # Load the questions from the existing CSV file
        questionnaire_dir = os.path.join("questionnaires", questionnaire_name.replace(" ", "_"))
        questions_file = os.path.join(questionnaire_dir, f"{questionnaire_name.replace(' ', '_')}_questions.csv")
        
        if os.path.exists(questions_file):
            questions_df = pd.read_csv(questions_file)
        else:
            raise FileNotFoundError(f"Questions file not found: {questions_file}")

        # Questionnaire completion CSV
        completion_file = os.path.join(report_dir, "questionnaire_completion.csv")
        questions_df['Answer'] = ''
        questions_df['Reference'] = ''
        questions_df.to_csv(completion_file, index=False)
        success_messages.append(f"Questionnaire completion file saved as {completion_file}")

        # Text report
        report_text_file = os.path.join(report_dir, "report.txt")
        with open(report_text_file, 'w') as f:
            f.write(f"Project: {selected_project}\n")
            f.write(f"Report Name: {report_name}\n")
            f.write(f"Questionnaire: {questionnaire_name}\n")
            f.write(f"Number of Assigned Documents: {len(doc_titles)}\n")
            f.write("\nAssigned Documents:\n")
            for doc in doc_titles:
                f.write(f"- {doc}\n")
        success_messages.append(f"Detailed report saved as {report_text_file}")

        # If all operations are successful, show a single success message
        st.success("All parameters checked and report generated successfully!")
        
    except Exception as e:
        error_messages.append(str(e))

    # If there are any error messages, display them
    for error in error_messages:
        st.error(f"Error: {error}")

    # If there are no errors but some operations failed, show individual success messages
    if not error_messages and len(success_messages) < 5:
        for message in success_messages:
            st.success(message)

    return report_dir if not error_messages else None


def Reports_page():
    st.title("Reports")
    selected_project = st.session_state.get("selected_project", None)

    if not selected_project:
        st.warning("Please select a project first.")
        return

    data = pd.read_csv("Data.csv")
    project_data = data[data['Project'] == selected_project].iloc[0]

    # Add the button to the sidebar
    if st.session_state.get('view_reports', False):
        if st.sidebar.button("Back to Reports"):
            st.session_state.view_reports = False
            st.experimental_rerun()
    else:
        if st.sidebar.button("View Reports"):
            st.session_state.view_reports = True
            st.experimental_rerun()

    if st.session_state.get('view_reports', False):
        selected_questionnaire = st.session_state.get('selected_questionnaire', None)
        view_reports_page(selected_project, selected_questionnaire)  # Call the function from view_reports.py
    else:
        display_reports_page(selected_project, project_data)

def display_reports_page(selected_project, project_data):
    st.sidebar.title("Project Information")
    st.sidebar.write(f"**Name:** '{selected_project}'")
    st.sidebar.write(f"**Team Lead**: {project_data['Team Lead']}")
    st.sidebar.write(f"**Description**: {project_data['Description']}")
    st.sidebar.divider()

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
        st.session_state.selected_questionnaire = selected_questionnaire
        project_paths_file = "project_paths.csv"
        project_paths_path = os.path.join(os.getcwd(), project_paths_file)

        if os.path.exists(project_paths_path):
            project_paths_df = pd.read_csv(project_paths_path)
            project_file_path_df = project_paths_df.loc[project_paths_df['File Name'] == selected_project, 'File Path']
            if not project_file_path_df.empty:
                project_dir = project_file_path_df.iloc[0]
                project_file_path = os.path.join(project_dir, f"{selected_project}.csv")
                
                selected_docs = show_filtered_documents(project_file_path, selected_questionnaire['name'])

                if selected_docs is not None and len(selected_docs) > 0:
                    if st.button("Create Report"):
                        if report_name:
                            questionnaire_data = load_questionnaires(questionnaire_path)
                            questionnaire_details = questionnaire_data[questionnaire_data['name'] == selected_questionnaire['name']]
                        
                            report_dir = assign_documents_and_generate_report(
                                selected_questionnaire['name'], 
                                selected_docs, 
                                report_name, 
                                selected_project,
                                questionnaire_details
                            )
                            if report_dir:
                                st.session_state.setdefault('generated_reports', {}).setdefault(selected_project, []).append({
                                    'name': report_name,
                                    'path': report_dir,
                                    'questionnaire': selected_questionnaire['name']
                                })
                            st.session_state.selected_questionnaire = selected_questionnaire
                        else:
                            st.warning("Please enter a report name before generating the report.")
                else:
                    st.info("Select Docs for Report Generation")
            else:
                st.error(f"Project file path not found for project: {selected_project}")
        else:
            st.error(f"Project paths file not found: {project_paths_path}")
    else:
        st.info("Please select a questionnaire to proceed.")