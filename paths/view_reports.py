import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import pandas as pd
import io

def view_reports_page(selected_project, selected_questionnaire):
    """
    Display the main page for viewing reports of a selected project.

    Args:
    selected_project (str): The name of the selected project
    selected_questionnaire (str): The name of the selected questionnaire
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
    project_data = st.session_state.db_manager.get_project_details(selected_project)
    if project_data is not None:
        st.sidebar.title("Project Information")
        st.sidebar.write(f"**Name:** '{selected_project}'")
        st.sidebar.write(f"**Team Lead:** {project_data['team_lead']}")
        st.sidebar.write(f"**Description:** {project_data['description']}")
        st.sidebar.divider()
    
    # Query reports from database
    reports = get_reports_from_db(selected_project)
    
    if reports:
        st.subheader("Select Report")
        sel, dele = st.columns([3,1])
        selected_report = st.selectbox("Select Report",
                                     options=[report['name'] for report in reports],
                                     format_func=lambda x: f"{x}")
        
        if selected_report:
            report = next(r for r in reports if r['name'] == selected_report)
            display_report_details(report, selected_project, selected_questionnaire)
            
            if "delete_report_open" not in st.session_state:
                st.session_state.delete_report_open = False

            if st.button("Delete Report", key="delete1"):
                st.session_state.delete_report_open = True

            if st.session_state.delete_report_open:
                delete_report_dialog(report, selected_project)
    else:
        st.info("No reports found for this project.")

def get_reports_from_db(project_name):
    """
    Get all reports for a project from the database.
    
    Args:
    project_name (str): The name of the project
    
    Returns:
    list: List of report dictionaries
    """
    conn = st.session_state.db_manager.get_connection()
    try:
        query = """
        SELECT id, name, questionnaire, num_docs, created_at
        FROM reports
        WHERE project = ?
        """
        df = pd.read_sql_query(query, conn, params=(project_name,))
        
        reports = []
        for _, row in df.iterrows():
            reports.append({
                'id': row['id'],
                'name': row['name'],
                'questionnaire': row['questionnaire'],
                'num_docs': row['num_docs'],
                'created_at': row['created_at']
            })
        return reports
    except Exception as e:
        st.error(f"Error retrieving reports: {e}")
        return []
    finally:
        conn.close()

def table_size_drd(df):
    """Calculate the appropriate height for the AgGrid table."""
    row_height = 35
    header_height = 40
    min_height = 50
    max_height = 600
    return min(max(min_height, len(df) * row_height + header_height), max_height)

def generate_excel_report(project_name, report, project_info, included_docs_df, completion_df):
    """Generate an Excel report with project details and data."""
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
        
        doc_count = len(included_docs_df)
        worksheet.write(start_row + doc_count + 2, 0, f'Total documents: {doc_count}')

        # Questionnaire completion table
        start_row = start_row + doc_count + 8
        worksheet.write(start_row, 0, 'Questionnaire Completion:')
        completion_df.to_excel(writer, sheet_name='Report', startrow=start_row + 1, index=False)

        # Auto-fit columns
        for i, col in enumerate(included_docs_df.columns):
            column_len = max(included_docs_df[col].astype(str).map(len).max(), len(col))
            worksheet.set_column(i, i, column_len + 2)

        for i, col in enumerate(completion_df.columns):
            column_len = max(completion_df[col].astype(str).map(len).max(), len(col))
            worksheet.set_column(i, i, column_len + 2)

    return output.getvalue()

def display_report_details(report, project_name, selected_questionnaire):
    """Display the details of a selected report."""
    conn = st.session_state.db_manager.get_connection()
    try:
        # Get included documents
        query = """
        SELECT content
        FROM report_documents
        WHERE report_id = ? AND type = 'included'
        """
        included_docs = pd.read_sql_query(query, conn, params=(report['id'],))
        if not included_docs.empty:
            included_docs_df = pd.DataFrame(eval(included_docs['content'].iloc[0]))
        else:
            included_docs_df = pd.DataFrame()

        # Get questionnaire completion data
        query = """
        SELECT question_id, answer, reference
        FROM questionnaire_responses
        WHERE report_id = ?
        """
        completion_df = pd.read_sql_query(query, conn, params=(report['id'],))

        # Display report details in sidebar
        st.sidebar.title("Report Details")
        st.sidebar.write(f"**Report Name:** {report['name']}")
        st.sidebar.write(f"**Created At:** {report['created_at']}")
        st.sidebar.write(f"**Number of Documents:** {report['num_docs']}")
        st.sidebar.divider()

        # Display included documents
        st.subheader("Included Documents")
        if not included_docs_df.empty:
            gb = GridOptionsBuilder.from_dataframe(included_docs_df)
            gb.configure_default_column(editable=False, width=150)
            gb.configure_column("Summary", width=300)
            gridOptions = gb.build()
            
            AgGrid(included_docs_df,
                  gridOptions=gridOptions,
                  width='100%',
                  fit_columns_on_grid_load=True,
                  enable_enterprise_modules=False,
                  height=table_size_drd(included_docs_df))

        # Display questionnaire completion
        st.subheader("Questionnaire Completion")
        if not completion_df.empty:
            gb_completion = GridOptionsBuilder.from_dataframe(completion_df)
            gb_completion.configure_default_column(editable=True, width=150)
            gb_completion.configure_column("question_id", editable=False, width=100)
            gridOptions_completion = gb_completion.build()
            
            AgGrid(completion_df,
                  gridOptions=gridOptions_completion,
                  height=table_size_drd(completion_df),
                  width='100%',
                  fit_columns_on_grid_load=True,
                  enable_enterprise_modules=False)

        # Generate Excel report
        project_info = st.session_state.db_manager.get_project_details(project_name)
        excel_data = generate_excel_report(project_name, report, project_info, included_docs_df, completion_df)

        st.download_button(
            label="Download Excel Report",
            data=excel_data,
            file_name="project_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.divider()

    except Exception as e:
        st.error(f"Error displaying report details: {e}")
    finally:
        conn.close()

def delete_report_dialog(report, project_name):
    """Display confirmation dialog for deleting a report."""
    @st.experimental_dialog("Delete Report")
    def delete_report_dialog_content():
        st.write(f"Are you sure you want to delete the report '{report['name']}' for project '{project_name}'?")
        col1, col2 = st.columns(2)
        if col1.button("Cancel"):
            st.session_state.delete_report_open = False
            st.rerun()
        if col2.button("Delete"):
            delete_report(report['id'])
            st.success(f"Report '{report['name']}' has been deleted.")
            st.session_state.delete_report_open = False
            st.rerun()

    delete_report_dialog_content()

def delete_report(report_id):
    """Delete a report from the database."""
    conn = st.session_state.db_manager.get_connection()
    cursor = conn.cursor()
    try:
        # Delete report documents first (due to foreign key constraint)
        cursor.execute("DELETE FROM report_documents WHERE report_id = ?", (report_id,))
        # Delete questionnaire responses
        cursor.execute("DELETE FROM questionnaire_responses WHERE report_id = ?", (report_id,))
        # Delete the report
        cursor.execute("DELETE FROM reports WHERE id = ?", (report_id,))
        conn.commit()
    except Exception as e:
        st.error(f"Error deleting report: {e}")
    finally:
        conn.close()