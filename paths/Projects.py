import os
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

def delete_project(project_name):
    proceed = st.warning(f"Are you sure you want to delete the project '{project_name}'?", icon="⚠️")
    if proceed:
        # Delete the row from Data.csv
        data = pd.read_csv("Data.csv")
        data = data[data['Project'] != project_name]
        data.to_csv("Data.csv", index=False, mode='w')
        st.success(f"Project '{project_name}' deleted successfully!")

        # Delete the corresponding CSV file
        project_paths_file = "project_paths.csv"
        project_paths_path = os.path.join(os.getcwd(), project_paths_file)
        project_paths_df = pd.read_csv(project_paths_path)
        project_file_path_df = project_paths_df.loc[project_paths_df['File Name'] == project_name, 'File Path']

        if not project_file_path_df.empty:
            project_file_path = project_file_path_df.iloc[0]
            if os.path.exists(project_file_path):
                os.remove(project_file_path)
            else:
                st.warning(f"File path '{project_file_path}' does not exist.")

            # Remove the entry from project_paths.csv
            project_paths_df = project_paths_df[project_paths_df['File Name'] != project_name]
            project_paths_df.to_csv(project_paths_file, index=False)
        else:
            st.warning(f"No file path found for project '{project_name}'.")

def create_form():
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
            to_add = {'Project': [project], 'Description': [description], 'Created By': [created_by], 'Team Lead': [team_lead], 'Date': [date]}
            to_add = pd.DataFrame(to_add)
            to_add.to_csv("Data.csv", mode='a', header=False, index=False)
            st.success("Data added successfully")

            file_name_file = f'{project}'
            file_details_file = f"{project}.csv"
            file_details_path = os.path.join(os.getcwd(), file_details_file)
            if not os.path.exists(file_details_file):
                columns = ['fileID', 'Title', 'Summary', 'Category', 'Date', 'Version']
                pd.DataFrame(columns=columns).to_csv(file_details_file, index=False)
                st.success(f"Container created successfully.")

                # Store the file path and name in project_paths.csv
                project_paths_path = "project_paths.csv"
                if os.path.exists(project_paths_path):
                    project_paths_df = pd.read_csv(project_paths_path)
                else:
                    project_paths_df = pd.DataFrame(columns=['File Name', 'File Path'])

                new_row = pd.DataFrame({'File Name': [file_name_file], 'File Path': [file_details_path]})
                project_paths_df = pd.concat([project_paths_df, new_row], ignore_index=True)
                project_paths_df.to_csv(project_paths_path, index=False)
                st.success(f"File path stored")

def enter_values():
    show_content = st.session_state.get('show_content', False)

    # Create a button to toggle the visibility of the content
    if st.button('Create Project'):
        show_content = not show_content
        st.session_state['show_content'] = show_content

    # Display the content based on the state variable
    if show_content:
        create_form()

def Table_data():
    global data
    data = pd.read_csv("Data.csv")
    gb = GridOptionsBuilder.from_dataframe(data)
    gb.configure_default_column(editable=False)  # Make all columns non-editable by default
    gb.configure_column("Description", editable=True)  # Make the "Description" column editable
    gb.configure_columns(["Project", "Created By", "Team Lead", "Date"], editable=False)  # Explicitly make these columns non-editable

    # Add a radio button for selection
    gb.configure_selection(selection_mode="single", use_checkbox=True)

    gridOptions = gb.build()

    ag_response = AgGrid(
        data,
        gridOptions=gridOptions,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=False
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

    with col2:
        st.write("")

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
    st.title("Projects")
    cr, dele = st.columns(2)
    enter_values()
    Table_data()