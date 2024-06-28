import os
import pandas as pd
import streamlit as st
import base64
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

def input_data(categories, project_dir):
    st.markdown("""
    <style>
        [data-testid=stSidebar] {
            background-color: #D2E1EB;
        }
    </style>
    """, unsafe_allow_html=True)

    project_name = os.path.basename(project_dir)
    project_file_path = os.path.join(project_dir, f"{project_name}.csv")

    with st.sidebar.form("Upload_Files"):
        uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "txt"])
        title = st.text_input("Title")
        summary = st.text_area("Summary")
        selected_categories = st.selectbox("Category", categories)
        date = st.date_input('Date')
        version = st.text_input("Version")
        submit = st.form_submit_button("Submit")

        if submit:
            if uploaded_file is not None:
                file_name = uploaded_file.name

                # Ensure the project CSV file exists
                if not os.path.exists(project_file_path):
                    pd.DataFrame(columns=['fileID', 'Title', 'Summary', 'Category', 'Date', 'Version']).to_csv(project_file_path, index=False)

                existing_data = pd.read_csv(project_file_path)
                if file_name in existing_data['fileID'].values:
                    st.warning(f"The file '{file_name}' has already been uploaded. Please choose a different file.")
                else:
                    # Save the uploaded file in the project directory
                    file_path = os.path.join(project_dir, file_name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    # Add new row to the project CSV
                    new_row = pd.DataFrame({
                        "fileID": [file_name],
                        "Title": [title],
                        "Summary": [summary],
                        "Category": [selected_categories],
                        "Date": [date],
                        "Version": [version]
                    })
                    updated_data = pd.concat([existing_data, new_row], ignore_index=True)
                    updated_data.to_csv(project_file_path, index=False)

                    st.success(f"File '{file_name}' uploaded and data added successfully!")
            else:
                st.warning("Please upload a file.")

    # Display current project data

def display_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def NewFile(categories, project_dir):
    show_content = st.session_state.get('show_content', False)

    # Create a button to toggle the visibility of the content
    if st.button('Upload Documents'):
        show_content = not show_content
        st.session_state['show_content'] = show_content

    # Display the content based on the state variable
    if show_content:
        input_data(categories, project_dir)

def table_size(project_data):
    # Calculate the height based on the number of rows
    row_height = 35  # Approximate height of each row in pixels
    header_height = 40  # Approximate height of the header in pixels
    min_height = 50  # Minimum height of the grid
    max_height = 600  # Maximum height of the grid
    calculated_height = min(max(min_height, len(project_data) * row_height + header_height), max_height)
    return calculated_height

def show_project_data(selected_project, project_file_path, categories, project_dir):
    project_data = pd.read_csv(project_file_path)

    gb = GridOptionsBuilder.from_dataframe(project_data)
    gb.configure_column("fileID", editable=False)  # Make the fileID column non-editable
    gb.configure_default_column(editable=True)
    gb.configure_column("Category", editable=True, cellEditor="agSelectCellEditor", cellEditorParams={"values": categories})

    # Add checkboxes for multi-selection
    gb.configure_selection(selection_mode="single", use_checkbox=True)

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
            col1, col2, col3 = st.columns([2,1,1])
            with col1:
                toggle_show_docs(selected_rows,project_dir)

            with col2:
                if st.button("Save Changes"):
                    update_project_data(updated_df, project_file_path)

            with col3:
            #dialog_placeholder = st.empty()

                if "delete_files_dialog_open" not in st.session_state:
                    st.session_state.delete_files_dialog_open = False

                if st.button("Delete File"):
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
    else:
        st.warning("No file is currently selected.")


    

def toggle_show_docs(selected_rows,project_dir):
    file = st.session_state.get('file', False)

    if st.button('Show File'):
        file = not file
        st.session_state['file'] = file

    if file:
        show_document(selected_rows,project_dir)   


def show_document(selected_rows,project_dir):
            if selected_rows is not None and not selected_rows.empty:
                selected_file = selected_rows.iloc[0]['fileID']
                file_path = os.path.join(project_dir, selected_file)
                if file_path.lower().endswith('.pdf'):
                    st.subheader(f"Viewing: {selected_file}")
                    display_pdf(file_path)
                elif file_path.lower().endswith(('.docx', '.txt')):
                    st.warning("Preview not available for Word or Text files.")
                else:
                    st.warning("Selected file is not a PDF, Word document, or text file.")
            
            else:
                st.warning("Select document first")

def Documents_page():
    st.title("Documents")

    project_paths_file = "project_paths.csv"
    project_paths_path = os.path.join(os.getcwd(), project_paths_file)

    if os.path.exists(project_paths_path):
        project_paths_df = pd.read_csv(project_paths_path)
        project_names = project_paths_df['File Name'].tolist()
    else:
        project_names = []

    selected_project = st.session_state.get("selected_project", None)

    if selected_project:
        st.header(f"Upload Documents for Project: {selected_project}")
        st.write("Double click on save changes to SAVE!")
        project_dir_df = project_paths_df.loc[project_paths_df['File Name'] == selected_project, 'File Path']
        if not project_dir_df.empty:
            project_dir = project_dir_df.iloc[0]

            categories_file = "categories.csv"
            categories_path = os.path.join(os.getcwd(), categories_file)
            if os.path.exists(categories_path):
                categories_df = pd.read_csv(categories_path)
                categories = categories_df["Categories"].tolist()
            else:
                categories = []
            NewFile(categories, project_dir)
            project_file_path = os.path.join(project_dir, f"{selected_project}.csv")
            show_project_data(selected_project, project_file_path, categories, project_dir)
    else:
        st.warning("Please select a project first.")
