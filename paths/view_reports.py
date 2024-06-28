import streamlit as st
import pandas as pd
import os
import shutil
from st_aggrid import AgGrid, GridOptionsBuilder
import io
import base64
import xlsxwriter

def view_reports_page(selected_project, selected_questionnaire):
    #st.title(f"View Reports for {selected_project}")
    
    # Display project info in the sidebar
    data = pd.read_csv("Data.csv")
    project_data = data[data['Project'] == selected_project].iloc[0]
    st.sidebar.title("Project Information")
    st.sidebar.write(f"**Name:** '{selected_project}'")
    st.sidebar.write(f"**Team Lead:** {project_data['Team Lead']}")
    st.sidebar.write(f"**Description:** {project_data['Description']}")
    st.sidebar.divider()
    
    # Find generated reports
    reports = find_reports(selected_project)
    
    if reports:
        # Create an option menu to select reports
        st.subheader("Select Report")
        sel,dele = st.columns([3,1])
        selected_report = st.selectbox("Select Report",
                                       options=[report['name'] for report in reports],
                                       format_func=lambda x: f"{x}")
        
        if selected_report:
            report = next(r for r in reports if r['name'] == selected_report)
            display_report_details(report, selected_project, selected_questionnaire)
            
            # Delete report functionality
            if "delete_report_open" not in st.session_state:
                st.session_state.delete_report_open = False

            if st.button("Delete Report", key="delete1"):
                st.session_state.delete_report_open = True

            if st.session_state.delete_report_open:
                delete_report_dialog(report, selected_project)
    else:
        st.info("No reports found for this project.")

def find_reports(project_name):
    reports = []
    for file in os.listdir():
        if file.startswith(f"{project_name}_") and os.path.isdir(file):
            report_name = file.split('_', 1)[1]
            csv_file = os.path.join(file, "included_documents.csv")
            txt_file = os.path.join(file, "report.txt")
            completion_file = os.path.join(file, "questionnaire_completion.csv")
            if os.path.exists(csv_file) and os.path.exists(txt_file) and os.path.exists(completion_file):
                reports.append({
                    'name': report_name,
                    'dir': file,
                    'csv_path': csv_file,
                    'txt_path': txt_file,
                    'completion_path': completion_file
                })
    return reports

def table_size_drd(df):
    # Calculate the height based on the number of rows
    row_height = 35  # Approximate height of each row in pixels
    header_height = 40  # Approximate height of the header in pixels
    min_height = 50  # Minimum height of the grid
    max_height = 600  # Maximum height of the grid
    calculated_height = min(max(min_height, len(df) * row_height + header_height), max_height)
    return calculated_height

def table_size_drd2(completion_df):
    # Calculate the height based on the number of rows
    row_height = 35  # Approximate height of each row in pixels
    header_height = 40  # Approximate height of the header in pixels
    min_height = 50  # Minimum height of the grid
    max_height = 600  # Maximum height of the grid
    calculated_height = min(max(min_height, len(completion_df) * row_height + header_height), max_height)
    return calculated_height

def generate_excel_report(project_name, report, project_info, included_docs_df, completion_df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('Report')

        # Project details
        worksheet.write(0, 0, 'Project Name:')
        worksheet.write(0, 1, project_name)
        worksheet.write(1, 0, 'Team Lead:')
        worksheet.write(1, 1, project_info['Team Lead'])
        worksheet.write(2, 0, 'Description:')
        worksheet.write(2, 1, project_info['Description'])

        # Included documents table
        start_row = 4
        worksheet.write(start_row, 0, 'Included Documents:')
        included_docs_df.to_excel(writer, sheet_name='Report', startrow=start_row + 1, index=False)
        
        # Document count
        doc_count = len(included_docs_df)
        worksheet.write(start_row + doc_count + 2, 0, f'Total documents: {doc_count}')

        # Questionnaire completion table
        start_row = start_row + doc_count + 8  # 5 rows after the count
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
    #st.write(f"## Report for Project: {project_name}")
    
    # Display text report content
    with open(report['txt_path'], 'r') as f:
        content = f.readlines()
    
    # Extract report details
    report_details = {line.split(': ')[0]: line.split(': ')[1].strip() for line in content[:4]}
    
    # Display report details in the sidebar
    st.sidebar.title("Report Details")
    for key, value in report_details.items():
        st.sidebar.write(f"**{key}:** {value}")
    st.sidebar.divider()
    
    # Display included documents
    st.subheader("Included Documents")
    df = pd.read_csv(report['csv_path'])
    
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
    
    # Display questionnaire completion data
    st.subheader("Questionnaire Completion")
    completion_df = pd.read_csv(report['completion_path'])
    
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

    # Generate Excel report
    project_data = pd.read_csv("Data.csv")
    project_info = project_data[project_data['Project'] == project_name].iloc[0]
    excel_data = generate_excel_report(project_name, report, project_info, df, completion_df)

    # Create download button
    st.download_button(
        label="Download Excel Report",
        data=excel_data,
        file_name="project_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Add a divider before the delete button
    st.divider()

    # Delete report functionality
    if "delete_report_open" not in st.session_state:
        st.session_state.delete_report_open = False

        if st.session_state.delete_report_open:
            delete_report_dialog(report, project_name)

def table_size_drd(df):
    row_height = 35
    header_height = 40
    min_height = 50
    max_height = 600
    calculated_height = min(max(min_height, len(df) * row_height + header_height), max_height)
    return calculated_height

def table_size_drd2(completion_df):
    row_height = 35
    header_height = 40
    min_height = 50
    max_height = 600
    calculated_height = min(max(min_height, len(completion_df) * row_height + header_height), max_height)
    return calculated_height

def delete_report_dialog(report, project_name):
    @st.experimental_dialog("Delete Report")
    def delete_report_dialog_content():
        st.write(f"Are you sure you want to delete the report '{report['name']}' for project '{project_name}'?")
        col1, col2 = st.columns(2)
        if col1.button("Cancel"):
            st.session_state.delete_report_open = False
            st.rerun()
        if col2.button("Delete"):
            delete_report(report)
            st.success(f"Report '{report['name']}' has been deleted.")
            st.session_state.delete_report_open = False
            st.rerun()

    delete_report_dialog_content()

def delete_report(report):
    import shutil
    shutil.rmtree(report['dir'])




    # total lines of code 1394