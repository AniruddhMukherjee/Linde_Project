import streamlit as st
import pandas as pd
import os
from datetime import date
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
import shutil
import textwrap
import streamlit.components.v1 as components
from paths.manage_questions import manage_questions_page

# Initialize session state
if "questionnaires" not in st.session_state:
    st.session_state.questionnaires = []

# Function to save questionnaire data
def save_questionnaire_data(data, path):
    data.to_csv(path, index=False)

# Function to delete a questionnaire
def delete_questionnaire(questionnaire_data, questionnaire_name, questionnaire_path):
    questionnaire_data = questionnaire_data[questionnaire_data['name'] != questionnaire_name]
    save_questionnaire_data(questionnaire_data, questionnaire_path)

    # Delete the questionnaire folder
    questionnaire_dir = os.path.join("questionnaires", questionnaire_name.replace(" ", "_"))
    if os.path.exists(questionnaire_dir):
        shutil.rmtree(questionnaire_dir)

    st.success(f"Questionnaire '{questionnaire_name}' deleted successfully!")

# Function to update questionnaire data
def update_questionnaire_data(updated_df, questionnaire_path):
    updated_df.to_csv(questionnaire_path, index=False)
    st.success("Questionnaire data updated successfully!")

# Function to input new questionnaire data
def input_questionnaire_data(categories, questionnaire_path):
    st.markdown("""
<style>
    [data-testid=stSidebar] {
        background-color: #D2E1EB;
        width: 490px;
    }
</style>
""", unsafe_allow_html=True)

    # Initialize existing_data DataFrame
    existing_data = pd.DataFrame(columns=["name", "category", "user", "description", "start_date"])

    # Try to read existing data from the CSV file
    try:
        existing_data = pd.read_csv(questionnaire_path)
    except FileNotFoundError:
        pass  # File doesn't exist, continue with the empty DataFrame

    with st.sidebar.form("Create_Questionnaire"):
        st.title("Create new Questionnaire")
        # User inputs
        title = st.text_input("Title")
        category = st.selectbox("Category", categories)
        user_name = st.text_input("By User")
        description = st.text_area("Description")
        Date = st.date_input('Start Date', value=date.today())
        st.warning("Upload files in CSV only")
        # Allow file upload for questions
        uploaded_files = st.file_uploader("Upload Questions", type=["xlsx", "csv"], accept_multiple_files=True)
        questions = []
        if uploaded_files:
            for file in uploaded_files:
                if file.name.endswith(".xlsx") or file.name.endswith(".csv"):
                    questions_df = pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)
                    questions.extend(questions_df.values.flatten().tolist())

        submit = st.form_submit_button("Submit")

        # Save the questionnaire data on submit
        if submit:
            to_add = {"name": [title], "category": [category], "user": [user_name],
                      "description": [description], "Date": [Date]}
            to_add = pd.DataFrame(to_add)

            # Check if the questionnaire already exists
            if title in existing_data["name"].values:
                existing_data.loc[existing_data["name"] == title, :] = to_add.iloc[0]
            else:
                updated_data = pd.concat([existing_data, to_add], ignore_index=True)
                existing_data = updated_data

            existing_data.to_csv(questionnaire_path, index=False)
            st.success("Questionnaire data added/updated successfully!")

            # Create a directory for the questionnaire
            questionnaire_dir = os.path.join("questionnaires", title.replace(" ", "_"))
            os.makedirs(questionnaire_dir, exist_ok=True)

            # Save the questions in a separate CSV file
            questions_file = os.path.join(questionnaire_dir, f"{title.replace(' ', '_')}_questions.csv")
            pd.DataFrame({'Questions': questions}).to_csv(questions_file, index=False)
            st.success(f"Questions saved to '{questions_file}'")

            # Save the uploaded questions files in the questionnaire directory
            for file in uploaded_files:
                file_path = os.path.join(questionnaire_dir, file.name)
                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())
                st.success(f"Questions file '{file.name}' uploaded successfully!")

def get_questions(questionnaire_path, selected_questionnaire):
    questionnaire_dir = os.path.join("questionnaires", selected_questionnaire.replace(" ", "_"))
    questions_file = os.path.join(questionnaire_dir, f"{selected_questionnaire.replace(' ', '_')}_questions.csv")
    if os.path.exists(questions_file):
        questions_df = pd.read_csv(questions_file)
        return questions_df
    else:
        return pd.DataFrame({"Questions": ["No questions yet"]})

def add_questions_manually(questionnaire_path, selected_questionnaire):
    questionnaire_dir = os.path.join("questionnaires", selected_questionnaire.replace(" ", "_"))
    questions_file = os.path.join(questionnaire_dir, f"{selected_questionnaire.replace(' ', '_')}_questions.csv")

    existing_questions = []
    if os.path.exists(questions_file):
        questions_df = pd.read_csv(questions_file)
        existing_questions = questions_df['Questions'].tolist()

    st.header(f"Add New Questions for '{selected_questionnaire}'")

    # Option to upload CSV/Excel files
    uploaded_files = st.file_uploader("Upload Questions converted to CSV)", type=["csv", "xlsx"], accept_multiple_files=True)
    if uploaded_files:
        for file in uploaded_files:
            if file.name.endswith(".csv"):
                questions_df = pd.read_csv(file)
            elif file.name.endswith(".xlsx"):
                questions_df = pd.read_excel(file)
            else:
                st.warning(f"Unsupported file format: {file.name}")
                continue

            new_questions = questions_df['Questions'].tolist()
            existing_questions.extend(new_questions)

            st.success(f"{len(new_questions)} questions added from '{file.name}'!")

    # Option to manually enter new questions
    new_questions = st.text_area("Enter new questions, one per line:")

    if st.button("Add The questions"):
        if new_questions:
            new_questions = new_questions.split('\n')
            new_questions = [q.strip() for q in new_questions if q.strip()]
            all_questions = existing_questions + new_questions
            questions_df = pd.DataFrame({'Questions': all_questions})
            questions_df.to_csv(questions_file, index=False)
            st.success(f"{len(new_questions)} new questions added to '{selected_questionnaire}'!")
        else:
            st.warning("No new questions entered.")

def table_size(questionnaire_path):
    # Calculate the height based on the number of rows
    questionnaire_df = pd.read_csv(questionnaire_path)
    row_height = 35  # Approximate height of each row in pixels
    header_height = 40  # Approximate height of the header in pixels
    min_height = 35  # Minimum height of the grid
    max_height = 400  # Maximum height of the grid
    calculated_height = min(max(min_height, len(questionnaire_df) * row_height + header_height), max_height)
    return calculated_height

def show_questionnaires(questionnaire_path, categories):
    questionnaire_data = pd.read_csv(questionnaire_path)
    if 'questions' in questionnaire_data.columns:
        questionnaire_data_without_questions = questionnaire_data.drop("questions", axis=1)
    else:
        questionnaire_data_without_questions = questionnaire_data

    gb = GridOptionsBuilder.from_dataframe(questionnaire_data_without_questions)
    gb.configure_default_column(editable=True)
    gb.configure_column("category", editable=True, cellEditor="agSelectCellEditor", cellEditorParams={"values": categories})
    gb.configure_selection(selection_mode="single", use_checkbox=True)
    gridOptions = gb.build()
    ag_response = AgGrid(
        questionnaire_data_without_questions,
        gridOptions=gridOptions,
        editable=True,
        fit_columns_on_grid_load=True,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        enable_enterprise_modules=False,
        onGridReady=lambda params: (params.api.onSelectionChanged, lambda: setattr(st.session_state, 'selected_row_data', params.api.getSelectedRows())),
        height=table_size(questionnaire_path)
    )
    updated_data = ag_response['data']
    selected_rows = ag_response["selected_rows"]
    if selected_rows is not None:
        if not selected_rows.empty:
            selected_row = selected_rows.iloc[0]
            selected_questionnaire_name = selected_row['name']
            questions_df = get_questions(questionnaire_path, selected_questionnaire_name)
            # Display the buttons and questions table
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Changes"):
                    update_questionnaire_data(updated_data, questionnaire_path)
            
            with col2:
                if "delete_questionnaire_open" not in st.session_state:
                    st.session_state.delete_questionnaire_open = False

                if st.button("Delete Questionnaire"):
                    if selected_rows is not None and not selected_rows.empty:
                        selected_questionnaire_name = selected_rows.iloc[0]["name"]
                        st.session_state.delete_questionnaire_open = True
                    else:
                        st.warning("No questionnaire is currently selected.")

                if st.session_state.delete_questionnaire_open:
                    @st.experimental_dialog("Delete Questionnaire")
                    def delete_questionnaire_dialog(updated_data):
                        st.write(f"Are you sure you want to delete the questionnaire '{selected_questionnaire_name}'?")
                        col1, col2 = st.columns(2)
                        if col1.button("Cancel"):
                            st.session_state.delete_questionnaire_open = False
                            st.rerun()
                        if col2.button("Delete"):
                            current_data = pd.read_csv(questionnaire_path)
                            updated_data = updated_data[updated_data['name'] != selected_questionnaire_name]
                            update_questionnaire_data(updated_data, questionnaire_path)
                            delete_questionnaire(questionnaire_data, selected_questionnaire_name, questionnaire_path)
                            st.success(f"Questionnaire '{selected_questionnaire_name}' has been deleted.")
                            st.session_state.delete_questionnaire_open = False
                            st.rerun()

                    delete_questionnaire_dialog(updated_data)


            #with st.expander("Manage Questions"):
                #add_questions_manually(questionnaire_path, selected_questionnaire_name)


            selected_questionnaire_name = selected_row['name']
            questions_df = get_questions(questionnaire_path, selected_questionnaire_name)
            manage_questions_page(questionnaire_path, selected_questionnaire_name)
            # st.header(f"Questions in '{selected_questionnaire_name}' Questionnaire")
            # display_questions_table(questions_df)
        else:
            st.warning("No questionnaire is currently selected.")
    else:
        st.warning("No questionnaire is currently selected.")

def enter_values(categories, questionnaire_path):
    show_content = st.session_state.get('show_content', False)

    # Create a button to toggle the visibility of the content
    if st.button('New Questionnaire'):
        show_content = not show_content
        st.session_state['show_content'] = show_content

    # Display the content based on the state variable
    if show_content:
        input_questionnaire_data(categories, questionnaire_path)

# Main app
def Questionnaire_page():
    global selected_questionnaire
    st.title("Questionnaire Management")

    # Load categories from categories.csv
    categories_file = "categories.csv"
    categories_path = os.path.join(os.getcwd(), categories_file)
    if os.path.exists(categories_path):
        categories_df = pd.read_csv(categories_path)
        categories = categories_df["Categories"].tolist()
    else:
        categories = []

    # Load questionnaire data from questionnaires.csv
    questionnaire_path = os.path.join(os.getcwd(), "questionnaires.csv")
    if not os.path.exists(questionnaire_path):
        pd.DataFrame(columns=["name", "category", "user", "description", "start_date", "questions"]).to_csv(questionnaire_path, index=False)

    # Initialize selected_row_data in st.session_state
    if "selected_row_data" not in st.session_state:
        st.session_state.selected_row_data = None

    ds,bt = st.columns(2)
    # Display existing questionnaires
    st.header("Existing Questionnaires")
     # Create a new questionnaire
    enter_values(categories, questionnaire_path)
    #Display the questionnaires
    show_questionnaires(questionnaire_path, categories)

   

 