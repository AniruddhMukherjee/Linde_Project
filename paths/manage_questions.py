import streamlit as st
import pandas as pd
import os
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

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
                st.experimental_rerun()  # Re-run the script to update the table
            else:
                st.warning("No new questions entered.")


def delete_selected_questions(selected_questions, questions_df, questions_file, dl):
    if dl.button("Delete Selected Questions"):
        if selected_questions is not None:
            if not selected_questions.empty:  # Check if selected_questions is not an empty DataFrame
                remaining_questions = [q for q in questions_df["Questions"].tolist() if q not in selected_questions["Questions"].tolist()]
                if remaining_questions:
                    questions_df = pd.DataFrame({"Questions": remaining_questions})
                    questions_df.to_csv(questions_file, index=False)
                    st.success(f"{len(selected_questions)} questions deleted!")
                    st.experimental_rerun()  # Re-run the script to update the table
                else:
                    st.warning("No questions remaining after deletion.")
            else:
                st.warning("No questions selected for deletion.")
        else:
            st.warning("No questions selected for deletion.")