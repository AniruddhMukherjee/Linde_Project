import streamlit as st
import pandas as pd
import os
import shutil
from st_aggrid import AgGrid, GridOptionsBuilder

def view_reports_page(selected_project, selected_questionnaire):
    st.title(f"View Reports for {selected_project}")
    
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
        selected_report = st.selectbox("", 
                                       options=[report['name'] for report in reports],
                                       format_func=lambda x: f"{x}")
        
        if selected_report:
            report = next(r for r in reports if r['name'] == selected_report)
            display_report_details(report, selected_project, selected_questionnaire)
            
            # Delete report functionality
            if "delete_report_open" not in st.session_state:
                st.session_state.delete_report_open = False

            if st.button("Delete Report"):
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

def display_report_details(report, project_name, selected_questionnaire):
    st.write(f"## Report for Project: {project_name}")
    
    # Display text report content
    with open(report['txt_path'], 'r') as f:
        content = f.readlines()
    
    # Extract report details
    report_details = {line.split(': ')[0]: line.split(': ')[1].strip() for line in content[:4]}
    
    # Display questionnaire details in the sidebar
    st.sidebar.title("Questionnaire Details")
    if selected_questionnaire is not None and isinstance(selected_questionnaire, dict):
        st.sidebar.write(f"**Name:** {selected_questionnaire.get('name', 'N/A')}")
        st.sidebar.write(f"**Category:** {selected_questionnaire.get('category', 'N/A')}")
        st.sidebar.write(f"**User:** {selected_questionnaire.get('user', 'N/A')}")
        st.sidebar.write(f"**Description:** {selected_questionnaire.get('description', 'N/A')}")
        st.sidebar.write(f"**Date:** {selected_questionnaire.get('date', 'N/A')}")
    else:
        st.sidebar.write("Questionnaire details not available")
    st.sidebar.divider()
    
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
           height=300, 
           width='100%',
           fit_columns_on_grid_load=True)
    
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
           height=400, 
           width='100%',
           fit_columns_on_grid_load=True)


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
    # Delete the entire report directory
    shutil.rmtree(report['dir'])