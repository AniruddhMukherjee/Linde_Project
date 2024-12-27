import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
import json
from datetime import datetime
from database_manager import db_manager
from new_paths.view_reportsnew import view_reports_page

def questionnaire_table_size(questionnaire_data):
    """Keep the original implementation as it's just UI calculation"""
    row_height = 35
    header_height = 40
    min_height = 50
    max_height = 600
    calculated_height = min(max(min_height, len(questionnaire_data) * row_height + header_height), max_height)
    return calculated_height

def enter_name():
    """Keep the original implementation as it's just UI input"""
    st.subheader("1. Enter Report Name:")
    report_name = st.text_input("Enter Report Name:")
    if report_name:
        return report_name
    return None

def load_questionnaires(questionnaire_path):
    """Modified to load from database instead of CSV"""
    try:
        questionnaire_data = db_manager.get_all_questionnaires()
        return questionnaire_data
    except Exception as e:
        st.error(f"Error loading questionnaires: {str(e)}")
        return None

def show_questionnaires(questionnaire_path):
    """Modified to use database instead of CSV"""
    questionnaire_data = db_manager.get_all_questionnaires()
    
    if questionnaire_data.empty:
        st.warning("No questionnaires found in the database.")
        return None
    
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
    
    if selected_rows is not None and len(selected_rows) > 0:
        selected_questionnaire = selected_rows.iloc[0]
        st.sidebar.title("Questionnaire Details")
        st.sidebar.write(f"**Name:** {selected_questionnaire['name']}")
        st.sidebar.write(f"**Category:** {selected_questionnaire['category']}")
        st.sidebar.write(f"**User:** {selected_questionnaire['user']}")
        st.sidebar.write(f"**Description:** {selected_questionnaire['description']}")
        st.sidebar.write(f"**Date:** {selected_questionnaire['date']}")
        st.sidebar.divider()
        
        st.session_state.selected_category = selected_questionnaire['category']
        return selected_questionnaire
    
    st.warning("No questionnaire selected.")
    st.session_state.selected_category = None
    return None

def documents_table_size(document_data):
    """Calculate the optimal height for the documents table based on the number of rows."""
    row_height = 35
    header_height = 40
    min_height = 50
    max_height = 600
    calculated_height = min(max(min_height, len(document_data) * row_height + header_height), max_height)
    return calculated_height

def show_filtered_documents(questionnaire_name):
    """Modified to use database instead of CSV"""
    if 'selected_category' not in st.session_state or st.session_state.selected_category is None:
        st.warning("Please select a questionnaire first to view relevant documents.")
        return None

    conn = db_manager.get_connection()
    query = """
    SELECT * FROM file_details 
    WHERE project = ? AND category LIKE ?
    """
    
    filtered_data = pd.read_sql_query(
        query, 
        conn, 
        params=(st.session_state.get("selected_project"), 
                f"%{st.session_state.selected_category}%")
    )
    
    if filtered_data.empty:
        st.info(f"No documents found for the category: {st.session_state.selected_category}")
        return None

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
    
    if selected_docs is None or len(selected_docs) == 0:
        st.warning("Please select one or more documents to proceed.")
        return None
    
    st.write("Client documents to assign to the questionnaire:")
    st.table(pd.DataFrame(selected_docs))
    
    return selected_docs

def assign_documents_and_generate_report(questionnaire_name, selected_docs, report_name, selected_project, questionnaire_data):
    """Modified to use database instead of file system"""
    try:
        # Create report in database
        docs_to_process = []
        if isinstance(selected_docs, dict):
            docs_to_process.append(selected_docs)
        elif isinstance(selected_docs, list):
            docs_to_process = selected_docs
        
        
        if docs_to_process:
            st.warning("No valid documents selected. Please select some documents to generate a report.")
            return None
        
        num_docs = len(selected_docs)
        report_id = db_manager.create_report(
            selected_project,
            questionnaire_name,
            report_name,
            num_docs
        )
        
        if report_id is None:
            st.error("Failed to create report in database")
            return None

        # Save assigned documents
        doc_titles = [doc.get('title', doc.get('title')) for doc in docs_to_process]
        db_manager.save_assigned_documents(report_id, doc_titles)

        # Save included documents (full document details)
        db_manager.save_included_documents(report_id, docs_to_process)

        # Get questionnaire questions and create completion entries
        questions_df = db_manager.get_questionnaire_questions(questionnaire_name)
        
        if questions_df is not None and not questions_df.empty:
            db_manager.update_questionnaire_completion(questions_df, report_id)
        
        st.success("Report generated successfully!")
        return report_id

    except Exception as e:
        st.write(e)
        import traceback
        print(traceback.format_exc())
        return None



def Reports_page():
    """Main function remains largely the same, but uses database for data retrieval"""
    st.title("Reports")
    selected_project = st.session_state.get("selected_project", None)

    if not selected_project:
        st.warning("Please select a project first.")
        return

    # Get project data from database instead of CSV
    project_data = db_manager.get_project_details(selected_project)
    if project_data is None:
        st.error("Project not found in database.")
        return

    # Rest of the view toggle logic remains the same
    if st.session_state.get('view_reports', False):
        if st.sidebar.button("Back to Reports"):
            st.session_state.view_reports = False
            st.rerun()
    else:
        if st.sidebar.button("View Reports"):
            st.session_state.view_reports = True
            st.rerun()

    if st.session_state.get('view_reports', False):
        selected_questionnaire = st.session_state.get('selected_questionnaire', None)
        view_reports_page(selected_project, selected_questionnaire, db_manager)
    else:
        display_reports_page(selected_project, project_data)

def display_reports_page(selected_project, project_data):
    """Modified to use project data from database"""
    SIDEBAR_LOGO = "linde-text.png"
    MAINPAGE_LOGO = "linde_india_ltd_logo.jpeg"

    sidebar_logo = SIDEBAR_LOGO
    main_body_logo = MAINPAGE_LOGO

    st.markdown("""
    <style>
    [data-testid="stSidebarNav"] > div:first-child > img {
        width: 900px;
        height: auto;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.logo(sidebar_logo, icon_image=main_body_logo)
    st.sidebar.title("Project Information")
    st.sidebar.write(f"**Name:** '{selected_project}'")
    st.sidebar.write(f"**Team Lead**: {project_data['team_lead']}")
    st.sidebar.write(f"**Description**: {project_data['description']}")
    st.sidebar.divider()

    report_name = enter_name()
    st.session_state['report_name'] = report_name

    if not report_name:
        st.warning("Enter report name to Proceed!")
        return

    selected_questionnaire = show_questionnaires(None)  # path parameter no longer needed
    
    if selected_questionnaire is not None:
        
        st.session_state.selected_questionnaire = selected_questionnaire
        selected_docs = show_filtered_documents(selected_questionnaire['name'])
        if selected_docs is not None and len(selected_docs) > 0:
            
            if st.button("Create Report"):
                if report_name:
                    questionnaire_data = load_questionnaires(None)
                    questionnaire_details = questionnaire_data[
                        questionnaire_data['name'] == selected_questionnaire['name']
                    ]
                
                    report_id = assign_documents_and_generate_report(
                        selected_questionnaire['name'],
                        selected_docs,
                        report_name,
                        selected_project,
                        questionnaire_details
                    )
                    if report_id:
                        st.success(f"Report created successfully with ID: {report_id}")
                else:
                    st.warning("Please enter a report name before generating the report.")
        else:
            st.info("Select Docs for Report Generation")
    else:
        st.info("Please select a questionnaire to proceed.")