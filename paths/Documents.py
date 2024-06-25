import os
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

def save_data(data, path):
    data.to_csv(path, index=False)

def delete_files(project_data, selected_file_names, project_file_path):
    for file_name in selected_file_names:
        project_data = project_data[project_data['fileID'] != file_name]
    save_data(project_data, project_file_path)
    st.success(f"{len(selected_file_names)} file(s) deleted successfully!")

def update_project_data(updated_df, project_file_path):
    updated_df.to_csv(project_file_path, index=False)
    st.success("Project data updated successfully!")

def input_data(categories, project_file_path):
    st.markdown("""
<style>
    [data-testid=stSidebar] {
        background-color: #D2E1EB;
    }
</style>
""", unsafe_allow_html=True)

    with st.sidebar.form("Upload_Files"):
        # only select specific files
        uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "txt"])
        file_name = None  # Initialize file_name to None

        # user inputs
        title = st.text_input("Title")
        summary = st.text_area("Summary")

        # Multi-select dropdown for categories
        selected_categories = st.selectbox("Category", categories)

        date = st.date_input('Date')
        version = st.text_input("Version")
        submit = st.form_submit_button("Submit")

        # submitting and adding to the csv file
        if submit:
            if uploaded_file is not None:
                # fetch the file name
                file_name = uploaded_file.name

                # Check if the file has already been uploaded
                existing_data = pd.read_csv(project_file_path)
                if file_name in existing_data['fileID'].values:
                    st.warning(f"The file '{file_name}' has already been uploaded. Please choose a different file.")
                else:
                    to_add = {"fileID": [file_name], "Title": [title], "Summary": [summary],
                              "Category": [selected_categories], "Date": [date], "Version": [version]}
                    to_add = pd.DataFrame(to_add)

                    existing_data = pd.read_csv(project_file_path)
                    updated_data = pd.concat([existing_data, to_add], ignore_index=True)
                    updated_data.to_csv(project_file_path, index=False)
                    st.success("File data added successfully!")
            else:
                st.warning("Please upload files.")

def NewFile(categories, project_file_path):
    show_content = st.session_state.get('show_content', False)

    # Create a button to toggle the visibility of the content
    if st.button('Upload Documents'):
        show_content = not show_content
        st.session_state['show_content'] = show_content

    # Display the content based on the state variable
    if show_content:
        input_data(categories, project_file_path)

def table_size(project_data):
    # Calculate the height based on the number of rows
    row_height = 35  # Approximate height of each row in pixels
    header_height = 40  # Approximate height of the header in pixels
    min_height = 50  # Minimum height of the grid
    max_height = 600  # Maximum height of the grid
    calculated_height = min(max(min_height, len(project_data) * row_height + header_height), max_height)
    return calculated_height

def show_project_data(selected_project, project_file_path, categories):
    project_data = pd.read_csv(project_file_path)

    gb = GridOptionsBuilder.from_dataframe(project_data)
    gb.configure_column("fileID", editable=False)  # Make the fileID column non-editable
    gb.configure_default_column(editable=True)
    gb.configure_column("Category", editable=True, cellEditor="agSelectCellEditor", cellEditorParams={"values": categories})

    # Add checkboxes for multi-selection
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)

    gridOptions = gb.build()

    ag_response = AgGrid(
        project_data,
        gridOptions=gridOptions,
        editable=True,
        fit_columns_on_grid_load=True,
        update_mode=GridUpdateMode.MODEL_CHANGED,  # Change to MODEL_CHANGED
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        enable_enterprise_modules=False,
        height=table_size(project_data),
    )

    updated_data = ag_response['data']
    updated_df = pd.DataFrame(updated_data)

    selected_rows = ag_response["selected_rows"]
    if selected_rows is not None:
        if not selected_rows.empty:
            selected_row = selected_rows.iloc[0]
            st.success(f"Currently '{selected_row['Title']}' has been selected.")
        else:
            st.warning("No file is currently selected.")
    else:
        st.warning("No file is currently selected.")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Save Changes"):
            update_project_data(updated_df, project_file_path)

    with col2:
        st.write("")

    with col3:
    #dialog_placeholder = st.empty()

        if "delete_files_dialog_open" not in st.session_state:
            st.session_state.delete_files_dialog_open = False

        if st.button("Delete Files"):
            if selected_rows is not None and not selected_rows.empty:
                st.session_state.delete_files_dialog_open = True
            else:
                st.warning("No files are currently selected.")

        if st.session_state.delete_files_dialog_open:
            @st.experimental_dialog("Delete Files")
            def delete_files_dialog():
                selected_file_names = [row["fileID"] for row in selected_rows.to_dict("records")]
                st.write(f"Are you sure you want to delete the following files?\n\n{', '.join(selected_file_names)}")
                col1, col2 = st.columns(2)
                if col1.button("Cancel"):
                    st.session_state.delete_files_dialog_open = False
                    st.rerun()
                if col2.button("Delete"):
                    delete_files(updated_df, selected_file_names, project_file_path)
                    st.success(f"Selected files have been deleted.")
                    st.session_state.delete_files_dialog_open = False
                    st.rerun()
            delete_files_dialog()

def Documents_page():
    st.title("Documents")

    # Read project names from project_paths.csv
    project_paths_file = "project_paths.csv"
    project_paths_path = os.path.join(os.getcwd(), project_paths_file)

    if os.path.exists(project_paths_path):
        project_paths_df = pd.read_csv(project_paths_path)
        project_names = project_paths_df['File Name'].tolist()
    else:
        project_names = []

    # The selected project from the dropdown
    selected_project = st.session_state.get("selected_project", None)

    if selected_project:
        st.header(f"Upload Documents for Project: {selected_project}")
        st.write("Double click on save changes to SAVE!")
        project_file_path_df = project_paths_df.loc[project_paths_df['File Name'] == selected_project, 'File Path']
        if not project_file_path_df.empty:
            project_file_path = project_file_path_df.iloc[0]

            # Load categories from categories.csv
            categories_file = "categories.csv"
            categories_path = os.path.join(os.getcwd(), categories_file)
            if os.path.exists(categories_path):
                categories_df = pd.read_csv(categories_path)
                categories = categories_df["Categories"].tolist()
            else:
                categories = []
            NewFile(categories, project_file_path)
            show_project_data(selected_project, project_file_path, categories)
    else:
        st.warning("Please select a project first.")