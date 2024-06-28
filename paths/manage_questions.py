import pandas as pd
import streamlit as st
import os
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, ColumnsAutoSizeMode

def custom_sort_key(index):
    """
    Create a custom sorting key for questionnaire indices.

    Args:
    index (str): The index string to be converted into a sorting key.

    Returns:
    list: A list of parts, with numeric parts converted to integers for proper sorting.
    """
    parts = index.split('.')
    return [int(part) if part.isdigit() else part for part in parts]

def manage_questions_page(questionnaire_path, selected_questionnaire):
    """
    Manage the questions page for a selected questionnaire.

    Args:
    questionnaire_path (str): The path to the questionnaires directory.
    selected_questionnaire (str): The name of the selected questionnaire.
    """
    st.title(f"Manage Questions for '{selected_questionnaire}'")

    questionnaire_dir = os.path.join("questionnaires", selected_questionnaire.replace(" ", "_"))
    questions_file = os.path.join(questionnaire_dir, f"{selected_questionnaire.replace(' ', '_')}_questions.csv")

    # Load existing questions or upload new file
    if os.path.exists(questions_file):
        questions_df = pd.read_csv(questions_file)
        #st.write("Loaded existing CSV file")
    else:
        st.write("No existing questions file found. Please upload a CSV file.")
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        if uploaded_file is not None:
            questions_df = pd.read_csv(uploaded_file)
            questions_df.to_csv(questions_file, index=False)
            st.success("CSV file successfully uploaded and saved.")
        else:
            st.warning("Please upload a CSV file to continue.")
            return

    # Ensure the DataFrame has the correct structure
    if 'index' not in questions_df.columns or 'questions' not in questions_df.columns:
        # If not, try to restructure it
        if len(questions_df.columns) == 1:
            # Split the single column into index and questions
            questions_df = pd.DataFrame({
                'index': questions_df.iloc[::2, 0].reset_index(drop=True),
                'questions': questions_df.iloc[1::2, 0].reset_index(drop=True)
            })
            # Save the restructured DataFrame
            questions_df.to_csv(questions_file, index=False)
            st.success("CSV file structure corrected and saved.")
        else:
            st.error("CSV file structure is incorrect and cannot be automatically fixed.")
            return

    # Debug information
    #st.write("DataFrame columns:", questions_df.columns)
    #st.write("First few rows of the DataFrame:", questions_df.head())

    # Ensure Index column is treated as string
    questions_df['index'] = questions_df['index'].astype(str)

    # Sort the dataframe by Index
    questions_df = questions_df.sort_values(by="index", key=lambda x: x.map(custom_sort_key))

    # Display existing questions using AgGrid
    gb = GridOptionsBuilder.from_dataframe(questions_df)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_default_column(editable=False)
    gridOptions = gb.build()

    ag_response = AgGrid(
        questions_df,
        gridOptions=gridOptions,
        fit_columns_on_grid_load=True,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        enable_enterprise_modules=False,
        height=table_size(questions_df),
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS  # Add this line
    )

    selected_questions = ag_response["selected_rows"]

    ad, dl = st.columns([3, 1])
    add_new_questions(questions_df, questions_file, ad)
    delete_selected_questions(selected_questions, questions_df, questions_file, dl)

def add_new_questions(questions_df, questions_file, ad):
    """
    Add new questions to the questionnaire.

    Args:
    questions_df (pd.DataFrame): The DataFrame containing existing questions.
    questions_file (str): The path to the CSV file storing the questions.
    ad: The Streamlit column object for adding questions.
    """
    with ad.popover("Add New Questions"):
        new_index = st.text_input("Enter the index for the new question (e.g., 1.3):")
        new_question = st.text_area("Enter the new question:")

        if st.button("Add Question"):
            if new_index and new_question:
                new_row = pd.DataFrame({"index": [new_index], "questions": [new_question]})
                questions_df = pd.concat([questions_df, new_row], ignore_index=True)
                questions_df = questions_df.sort_values(by="index", key=lambda x: x.map(custom_sort_key))
                questions_df.to_csv(questions_file, index=False)
                st.success("New question added!")
                st.rerun()
            else:
                st.warning("Please enter both an index and a question.")

def delete_selected_questions(selected_questions, questions_df, questions_file, dl):
    """
    Delete selected questions from the questionnaire.

    Args:
    selected_questions (list or pd.DataFrame): The questions selected for deletion.
    questions_df (pd.DataFrame): The DataFrame containing all questions.
    questions_file (str): The path to the CSV file storing the questions.
    dl: The Streamlit column object for deleting questions.
    """
    with dl:
        if "delete_dialog_open" not in st.session_state:
            st.session_state.delete_dialog_open = False

        if st.button("Delete Selected Questions"):
            if selected_questions is not None and len(selected_questions) > 0:
                st.session_state.delete_dialog_open = True
                # Store the number of questions to delete in session state
                if isinstance(selected_questions, pd.DataFrame):
                    st.session_state.num_questions_to_delete = len(selected_questions)
                elif isinstance(selected_questions, list):
                    st.session_state.num_questions_to_delete = len(selected_questions)
                else:
                    st.session_state.num_questions_to_delete = 0
            else:
                st.warning("Please select questions to delete.")

        if st.session_state.delete_dialog_open:
            @st.experimental_dialog("Delete Questions")
            def delete_questions_dialog():
                num_questions = st.session_state.num_questions_to_delete
                st.write(f"You are about to delete {num_questions} question{'s' if num_questions > 1 else ''}. Are you sure?")
                col1, col2 = st.columns(2)
                if col1.button("Cancel"):
                    st.session_state.delete_dialog_open = False
                    st.rerun()
                if col2.button("Delete"):
                    try:
                        # Handle different possible formats of selected_questions
                        if isinstance(selected_questions, pd.DataFrame):
                            questions_to_delete = selected_questions['index'].tolist()
                        elif isinstance(selected_questions, list):
                            if all(isinstance(q, dict) for q in selected_questions):
                                questions_to_delete = [q['index'] for q in selected_questions]
                            elif all(isinstance(q, str) for q in selected_questions):
                                questions_to_delete = selected_questions
                            else:
                                raise ValueError("Unexpected format of selected questions.")
                        else:
                            raise ValueError("Unexpected format of selected questions.")

                        # Perform deletion
                        updated_df = questions_df[~questions_df['index'].isin(questions_to_delete)]
                        updated_df.to_csv(questions_file, index=False)
                        st.success(f"{num_questions} question{'s' if num_questions > 1 else ''} {'have' if num_questions > 1 else 'has'} been deleted.")
                    except Exception as e:
                        st.error(f"An error occurred while deleting questions: {str(e)}")
                    finally:
                        st.session_state.delete_dialog_open = False
                        st.rerun()

            delete_questions_dialog()

def table_size(questions_df):
    """Calculate the appropriate height for the AgGrid table based on the number of rows."""
    row_height = 35
    header_height = 40
    min_height = 25
    max_height = 400
    calculated_height = min(max(min_height, len(questions_df) * row_height + header_height), max_height)
    return calculated_height
