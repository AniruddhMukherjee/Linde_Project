import os
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

def ensure_project_paths_file_exists():
    """
    Ensure that the project_paths.csv file exists. 
    If it doesn't, create it with the necessary columns.
    """
    project_paths_file = "project_paths.csv"
    if not os.path.exists(project_paths_file):
        # Create the file with the required columns
        pd.DataFrame(columns=['File Name', 'File Path']).to_csv(project_paths_file, index=False)
        st.info("Created new project_paths.csv file.")

def delete_project(project_name):
    """
    Delete a project and its associated files.

    Args:
    project_name (str): The name of the project to be deleted.
    """
    data = pd.read_csv("Data.csv")
    data = data[data['Project'] != project_name]
    data.to_csv("Data.csv", index=False)

    project_paths_file = "project_paths.csv"
    project_paths_df = pd.read_csv(project_paths_file)
    project_file_path_df = project_paths_df.loc[project_paths_df['File Name'] == project_name, 'File Path']

    if not project_file_path_df.empty:
        project_dir = project_file_path_df.iloc[0]
        if os.path.exists(project_dir):
            for filename in os.listdir(project_dir):
                file_path = os.path.join(project_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    st.error(f"Failed to delete {file_path}. Reason: {e}")
            try:
                os.rmdir(project_dir)
            except Exception as e:
                st.error(f"Failed to delete project directory. Reason: {e}")

        project_paths_df = project_paths_df[project_paths_df['File Name'] != project_name]
        project_paths_df.to_csv(project_paths_file, index=False)
    
    st.success(f"Project '{project_name}' deleted successfully!")

def create_form():
    """
    Create and display a form for project creation in the sidebar.

    This function sets up a form in the Streamlit sidebar to collect project details,
    creates a new project directory, and updates the necessary CSV files when submitted.
    """
    st.markdown("""
    <style>
        [data-testid=stSidebar] {
            background-color: #D2E1EB;
        }
    </style>
    """, unsafe_allow_html=True)
    with st.sidebar.form("project_form"):
        st.header("Project Creation")
        project = st.text_input("Project Name")
        description = st.text_area('Description')
        created_by = st.text_input('Created By')
        team_lead = st.text_input('Team Lead')
        date = st.date_input('Date')
        submit = st.form_submit_button("Submit")

        if submit:
            if not project:
                st.error("Project name cannot be empty.")
                return

            # Ensure Data.csv exists
            if not os.path.exists("Data.csv"):
                pd.DataFrame(columns=['Project', 'Description', 'Created By', 'Team Lead', 'Date']).to_csv("Data.csv", index=False)

            # Add new project to Data.csv
            to_add = {'Project': [project], 'Description': [description], 'Created By': [created_by], 'Team Lead': [team_lead], 'Date': [date]}
            to_add = pd.DataFrame(to_add)
            to_add.to_csv("Data.csv", mode='a', header=False, index=False)
            st.success("Data added successfully")

            # Create project directory
            project_dir = os.path.join(os.getcwd(), "projects", project)
            os.makedirs(project_dir, exist_ok=True)

            # Create project-specific CSV file
            file_details_file = f"{project}.csv"
            file_details_path = os.path.join(project_dir, file_details_file)
            if not os.path.exists(file_details_path):
                columns = ['fileID', 'Title', 'Summary', 'Category', 'Date', 'Version']
                pd.DataFrame(columns=columns).to_csv(file_details_path, index=False)
                st.success(f"Container created successfully.")

            # Update project_paths.csv
            project_paths_path = "project_paths.csv"
            if os.path.exists(project_paths_path):
                project_paths_df = pd.read_csv(project_paths_path)
            else:
                project_paths_df = pd.DataFrame(columns=['File Name', 'File Path'])

            new_row = pd.DataFrame({'File Name': [project], 'File Path': [project_dir]})
            project_paths_df = pd.concat([project_paths_df, new_row], ignore_index=True)
            project_paths_df.to_csv(project_paths_path, index=False)

            st.success(f"Project '{project}' created successfully.")

def enter_values():
    """
    Handle the 'Create Project' button and form display logic.

    This function toggles the visibility of the project creation form and calls create_form()
    when the form should be displayed.
    """
    show_content = st.session_state.get('show_content', False)

    if st.button('Create Project'):
        show_content = not show_content
        st.session_state['show_content'] = show_content

    if show_content:
        create_form()

def table_size(data):
    """
    Calculate the appropriate height for the AgGrid table based on the number of rows.
    """
    row_height = 35
    header_height = 40
    min_height = 50
    max_height = 600
    calculated_height = min(max(min_height, len(data) * row_height + header_height), max_height)
    return calculated_height

def Table_data():
    """
    Display and manage the projects table using AgGrid.

    This function loads project data from Data.csv, configures and displays an AgGrid table,
    handles project selection, and provides options for saving changes and deleting projects.
    """
    global data
    data = pd.read_csv("Data.csv")
    gb = GridOptionsBuilder.from_dataframe(data)
    gb.configure_default_column(editable=False)
    gb.configure_column("Description", editable=True)
    gb.configure_columns(["Project", "Created By", "Team Lead", "Date"], editable=False)
    
    gb.configure_selection(selection_mode="single", use_checkbox=True)

    gridOptions = gb.build()

    ag_response = AgGrid(
        data,
        gridOptions=gridOptions,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=False,
        height=table_size(data),
    )
    updated_data = ag_response["data"]
    updated_df = pd.DataFrame(updated_data)

    selected_project = ag_response["selected_rows"]
    if selected_project is not None:
        if not selected_project.empty:
            selected_project_name = selected_project.iloc[0]["Project"]
            st.session_state["selected_project"] = selected_project_name
        else:
            # If no project is selected, keep the previously selected project
            st.session_state["selected_project"] = st.session_state.get("selected_project", None)
    else:
        # If selected_project is None, keep the previously selected project
        st.session_state["selected_project"] = st.session_state.get("selected_project", None)

    selected_project_name = st.session_state.get("selected_project", None)
    if selected_project_name:
        st.success(f"Currently project '{selected_project_name}' has been selected.")
    else:
        st.warning("No project is currently selected.")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Save Changes"):
            updated_data.to_csv("Data.csv", index=False)
            st.success("Data saved successfully!")

    with col3:
        #dialog_placeholder = st.empty()

        if "delete_dialog_open" not in st.session_state:
            st.session_state.delete_dialog_open = False

        if st.button("Delete Project"):
            if selected_project_name:
                st.session_state.delete_dialog_open = True
            else:
                st.warning("Please select a project to delete.")

        if st.session_state.delete_dialog_open:
            @st.experimental_dialog("Delete Project")
            def delete_project_dialog():
                st.write(f"Are you sure you want to delete the project '{selected_project_name}'?")
                col1, col2 = st.columns(2)
                if col1.button("Cancel"):
                    st.session_state.delete_dialog_open = False
                    st.rerun()
                if col2.button("Delete"):
                    delete_project(selected_project_name)
                    st.success(f"Project '{selected_project_name}' has been deleted.")
                    st.session_state.selected_project = None
                    st.session_state.delete_dialog_open = False
                    st.rerun()

            delete_project_dialog()

def projects_page():
    """
    Render the main projects page of the application.

    This function sets up the page layout, including logos and styling, and calls the necessary
    functions to display the project creation form and the projects table.
    """
    SIDEBAR_LOGO = "linde-text.png"
    MAINPAGE_LOGO = "linde_india_ltd_logo.jpeg"

    sidebar_logo = SIDEBAR_LOGO
    main_body_logo = MAINPAGE_LOGO

    st.markdown("""
<style>
[data-testid="stSidebarNav"] > div:first-child > img {
    width: 900px; /* Adjust the width as needed */
    height: auto; /* Maintain aspect ratio */
}
</style>
""", unsafe_allow_html=True)
    
    st.logo(sidebar_logo, icon_image=main_body_logo)
    st.title("Projects")
    cr, dele = st.columns(2)
    enter_values()
    Table_data()
 