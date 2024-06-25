import streamlit as st
import pandas as pd
import os
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

def table_size(questions_df):
    # Calculate the height based on the number of rows
    row_height = 35  # Approximate height of each row in pixels
    header_height = 40  # Approximate height of the header in pixels
    min_height = 25  # Minimum height of the grid
    max_height = 400  # Maximum height of the grid
    calculated_height = min(max(min_height, len(questions_df) * row_height + header_height), max_height)
    return calculated_height

def manage_questions_page(questionnaire_path, selected_questionnaire):
    st.title(f"Manage Questions for '{selected_questionnaire}'")

    questionnaire_dir = os.path.join("questionnaires", selected_questionnaire.replace(" ", "_"))
    questions_file = os.path.join(questionnaire_dir, f"{selected_questionnaire.replace(' ', '_')}_questions.csv")

    # Load existing questions
    if os.path.exists(questions_file):
        questions_df = pd.read_csv(questions_file)
    else:
        questions_df = pd.DataFrame({"Questions": []})

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
        height=table_size(questions_df)
    )

    selected_questions = ag_response["selected_rows"]
    if selected_questions is not None:
        if not selected_questions.empty:  # Check if selected_questions is not an empty DataFrame
            pass  # st.write(f"Selected questions: {[row['Questions'] for _, row in selected_questions.iterrows()]}")

    ad, dl = st.columns([3, 1])
    add_new_questions(questions_df, questions_file, ad)
    delete_selected_questions(selected_questions, questions_df, questions_file, dl)


def add_new_questions(questions_df, questions_file, ad):
    with ad.expander("Add New Questions"):
        new_questions = st.text_area("Enter new questions, one per line:")

        if st.button("Add Questions"):
            if new_questions:
                new_questions = new_questions.split('\n')
                new_questions = [q.strip() for q in new_questions if q.strip()]
                questions_df = pd.concat([questions_df, pd.DataFrame({"Questions": new_questions})], ignore_index=True)
                questions_df.to_csv(questions_file, index=False)
                st.success(f"{len(new_questions)} new questions added!")
                st.rerun()  # Re-run the script to update the table
            else:
                st.warning("No new questions entered.")


def delete_selected_questions(selected_questions, questions_df, questions_file, dl):
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
                            questions_to_delete = selected_questions['Questions'].tolist()
                        elif isinstance(selected_questions, list):
                            if all(isinstance(q, dict) for q in selected_questions):
                                questions_to_delete = [q['Questions'] for q in selected_questions]
                            elif all(isinstance(q, str) for q in selected_questions):
                                questions_to_delete = selected_questions
                            else:
                                raise ValueError("Unexpected format of selected questions.")
                        else:
                            raise ValueError("Unexpected format of selected questions.")

                        # Perform deletion
                        updated_df = questions_df[~questions_df['Questions'].isin(questions_to_delete)]
                        updated_df.to_csv(questions_file, index=False)
                        st.success(f"{num_questions} question{'s' if num_questions > 1 else ''} {'have' if num_questions > 1 else 'has'} been deleted.")
                    except Exception as e:
                        st.error(f"An error occurred while deleting questions: {str(e)}")
                    finally:
                        st.session_state.delete_dialog_open = False
                        st.rerun()

            delete_questions_dialog()