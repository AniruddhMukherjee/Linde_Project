import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import io
import json
import database_manager as db_manager
from datetime import datetime
    
def view_reports_page(selected_project, selected_questionnaire, db_manager):
    """
    Display the main page for viewing reports of a selected project.

    Args:
    selected_project (str): The name of the selected project.
    selected_questionnaire (str): The name of the selected questionnaire.
    db_manager (DatabaseManager): Instance of the database manager.
    """
    
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
    
    # Get project details from database
    project_info = db_manager.get_project_details(selected_project)
    if project_info is not None:
        st.sidebar.title("Project Information")
        st.sidebar.write(f"**Name:** {selected_project}")
        st.sidebar.write(f"**Team Lead:** {project_info['team_lead']}")
        st.sidebar.write(f"**Description:** {project_info['description']}")
        st.sidebar.divider()
    else:
        st.error(f"Could not find project details for '{selected_project}'")
        return
    
    # Find reports from database
    reports = find_reports_db(db_manager, selected_project)
    
    if reports:
        st.subheader("Select Report")
        
        # Create columns for report selection and delete button
        col1, col2 = st.columns([3,1])
        
        with col1:
            selected_report = st.selectbox(
                "Choose a report to view",
                options=[report['name'] for report in reports],
                format_func=lambda x: f"{x}"
            )
        
        if selected_report:
            report = next(r for r in reports if r['name'] == selected_report)
            
            # Initialize session state for delete dialog if not exists
            if "delete_report_open" not in st.session_state:
                st.session_state.delete_report_open = False
            
            with col2:
                if st.button("Delete Report", key="delete1"):
                    st.session_state.delete_report_open = True

            if st.session_state.delete_report_open:
                delete_report_dialog_db(report, selected_project, db_manager)
            
            # Display report details
            try:
                display_report_details_db(report, selected_project, selected_questionnaire, db_manager)
            except Exception as e:
                st.error(f"Error displaying report details: {str(e)}")
                st.write("Please check the report data and try again.")
    else:
        st.info("No reports found for this project.")
        if st.button("Create New Report"):
            st.session_state.page = "create_report"
            st.rerun()
def find_reports_db(db_manager, project_name):
    """
    Find all reports associated with a given project from the database.

    Args:
    db_manager (DatabaseManager): Instance of the database manager.
    project_name (str): The name of the project to find reports for.

    Returns:
    list: A list of dictionaries containing report information.
    """
    conn = db_manager.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, num_docs, created_at, questionnaire
            FROM reports
            WHERE project = ?
        """, (project_name,))
        
        reports = []
        for row in cursor.fetchall():
            reports.append({
                'id': row[0],
                'name': row[1],
                'num_docs': row[2],
                'created_at': row[3],
                'questionnaire': row[4]
            })
        return reports
    finally:
        conn.close()

def get_report_documents(db_manager, report_id, doc_type):
    """
    Retrieve documents associated with a report from the database.

    Args:
    db_manager (DatabaseManager): Instance of the database manager.
    report_id (int): The ID of the report.
    doc_type (str): Type of documents to retrieve ('included' or 'assigned').

    Returns:
    list: List of document information.
    """
    conn = db_manager.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT content
            FROM report_documents
            WHERE report_id = ? AND type = ?
        """, (report_id, doc_type))
        
        result = cursor.fetchone()
        if result:
            return json.loads(result[0])
        return []
    finally:
        conn.close()

def display_report_details_db(report, project_name, selected_questionnaire, db_manager):
    """
    Display the details of a selected report from the database.

    Args:
    report (dict): The report information.
    project_name (str): The name of the project.
    selected_questionnaire (str): The name of the selected questionnaire.
    db_manager (DatabaseManager): Instance of the database manager.
    """
    # Display report details in the sidebar
    st.sidebar.title("Report Details")
    st.sidebar.write(f"**Report Name:** {report['name']}")
    st.sidebar.write(f"**Created At:** {report['created_at']}")
    st.sidebar.write(f"**Number of Documents:** {report['num_docs']}")
    st.sidebar.write(f"**Questionnaire:** {report['questionnaire']}")
    st.sidebar.divider()
    
    # Get and display included documents
    st.subheader("Included Documents")
    included_docs = get_report_documents(db_manager, report['id'], 'included')
    if included_docs:
        df = pd.DataFrame(included_docs)
        
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(editable=False, width=150)
        gb.configure_column("Summary", width=300)
        gridOptions = gb.build()
        
        AgGrid(df,
               gridOptions=gridOptions,
               width='100%',
               fit_columns_on_grid_load=True,
               enable_enterprise_modules=False,
               height=table_size_drd(df))
    
    # Get and display questionnaire completion data
    st.subheader("Questionnaire Completion")
    conn = db_manager.get_connection()
    try:
        # Fixed SQL query with properly quoted column alias
        completion_df = pd.read_sql_query("""
            SELECT 
                qr.question_id as 'question_number',
                qq.question as 'questions',
                qr.answer,
                qr.reference
            FROM questionnaire_responses qr
            JOIN questionnaire_questions qq 
                ON qr.question_id = qq.identifier 
                AND qq.questionnaire_name = ?
            WHERE qr.report_id = ?
            ORDER BY CAST(qr.question_id AS INTEGER)
        """, conn, params=(selected_questionnaire, report['id']))
        
        if not completion_df.empty:
            gb_completion = GridOptionsBuilder.from_dataframe(completion_df)
            gb_completion.configure_default_column(editable=True, width=150)
            gb_completion.configure_column("index", editable=False, width=100)
            gb_completion.configure_column("questions", editable=False, width=300)
            gridOptions_completion = gb_completion.build()
            
            AgGrid(completion_df,
                   gridOptions=gridOptions_completion,
                   height=table_size_drd2(completion_df),
                   width='100%',
                   fit_columns_on_grid_load=True,
                   enable_enterprise_modules=False)
    finally:
        conn.close()

    # Generate Excel report
    project_info = db_manager.get_project_details(project_name)
    excel_data = generate_excel_report(project_name, report, project_info, 
                                     pd.DataFrame(included_docs), completion_df)

    st.download_button(
        label="Download Excel Report",
        data=excel_data,
        file_name=f"{project_name}_{report['name']}_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.divider()

def delete_report_dialog_db(report, project_name, db_manager):
    """
    Display a confirmation dialog for deleting a report from the database.

    Args:
    report (dict): The report information.
    project_name (str): The name of the project.
    db_manager (DatabaseManager): Instance of the database manager.
    """
    @st.dialog("Delete Report")
    def delete_report_dialog_content():
        st.write(f"Are you sure you want to delete the report '{report['name']}' for project '{project_name}'?")
        col1, col2 = st.columns(2)
        if col1.button("Cancel"):
            st.session_state.delete_report_open = False
            st.rerun()
        if col2.button("Delete"):
            delete_report_db(report['id'], db_manager)
            st.success(f"Report '{report['name']}' has been deleted.")
            st.session_state.delete_report_open = False
            st.rerun()

    delete_report_dialog_content()

def delete_report_db(report_id, db_manager):
    """
    Delete a report and its associated data from the database.

    Args:
    report_id (int): The ID of the report to delete.
    db_manager (DatabaseManager): Instance of the database manager.
    """
    conn = db_manager.get_connection()
    try:
        cursor = conn.cursor()
        # Delete report documents
        cursor.execute("DELETE FROM report_documents WHERE report_id = ?", (report_id,))
        # Delete questionnaire responses
        cursor.execute("DELETE FROM questionnaire_responses WHERE report_id = ?", (report_id,))
        # Delete report
        cursor.execute("DELETE FROM reports WHERE id = ?", (report_id,))
        conn.commit()
    finally:
        conn.close()

# Helper functions remain the same
def table_size_drd(df):
    row_height = 35
    header_height = 40
    min_height = 50
    max_height = 600
    return min(max(min_height, len(df) * row_height + header_height), max_height)

def table_size_drd2(completion_df):
    row_height = 35
    header_height = 40
    min_height = 50
    max_height = 600
    return min(max(min_height, len(completion_df) * row_height + header_height), max_height)

def generate_excel_report(project_name, report, project_info, included_docs_df, completion_df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('Report')

        # Project details
        worksheet.write(0, 0, 'Project Name:')
        worksheet.write(0, 1, project_name)
        worksheet.write(1, 0, 'Team Lead:')
        worksheet.write(1, 1, project_info['team_lead'])
        worksheet.write(2, 0, 'Description:')
        worksheet.write(2, 1, project_info['description'])

        # Included documents table
        start_row = 4
        worksheet.write(start_row, 0, 'Included Documents:')
        included_docs_df.to_excel(writer, sheet_name='Report', startrow=start_row + 1, index=False)
        
        # Document count
        doc_count = len(included_docs_df)
        worksheet.write(start_row + doc_count + 2, 0, f'Total documents: {doc_count}')

        # Questionnaire completion table
        start_row = start_row + doc_count + 8
        worksheet.write(start_row, 0, 'Questionnaire Completion:')
        completion_df.to_excel(writer, sheet_name='Report', startrow=start_row + 1, index=False)

        # Auto-fit columnsstreamlit run 
        for i, col in enumerate(included_docs_df.columns):
            column_len = max(included_docs_df[col].astype(str).map(len).max(), len(col))
            worksheet.set_column(i, i, column_len + 2)

        for i, col in enumerate(completion_df.columns):
            column_len = max(completion_df[col].astype(str).map(len).max(), len(col))
            worksheet.set_column(i, i, column_len + 2)

    return output.getvalue()