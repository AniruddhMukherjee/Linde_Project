import pandas as pd
import streamlit as st
import os
from st_aggrid import AgGrid, GridUpdateMode, DataReturnMode, GridOptionsBuilder

categories_file = "categories.csv"
categories_path = os.path.join(os.getcwd(), categories_file)

# Adds the category to the file
def add_category():
    with st.expander("Add a new category"):
        new_category = st.text_input("Click enter to add categories")
        if new_category and st.button("Add Category"):
            categories_df = pd.read_csv(categories_path)
            new_row = pd.DataFrame({"Categories": [new_category]})
            updated_categories = pd.concat([categories_df, new_row], ignore_index=True)
            updated_categories.to_csv(categories_path, index=False)
            st.success(f"Category '{new_category}' added successfully!")
            st.rerun()

def table_size(categories_df):
    # Calculate the height based on the number of rows
    row_height = 35  # Approximate height of each row in pixels
    header_height = 40  # Approximate height of the header in pixels
    min_height = 50  # Minimum height of the grid
    max_height = 600  # Maximum height of the grid
    calculated_height = min(max(min_height, len(categories_df) * row_height + header_height), max_height)
    return calculated_height

# Displays the categories
def display_categories(categories_df):
    gb = GridOptionsBuilder.from_dataframe(categories_df)
    gb.configure_default_column(editable=False)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_default_column(fontSize=50)

    gridOptions = gb.build()

    ag_response = AgGrid(
        categories_df,
        gridOptions=gridOptions,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=False,
        height=table_size(categories_df)
    )

    updated_data = ag_response["data"]
    updated_df = pd.DataFrame(updated_data)

    selected_rows = ag_response["selected_rows"]

    col1, col2 = st.columns(2)
    with col1:
        add_category()

    with col2:
        if st.button("Delete Category"):
            if selected_rows is not None and not selected_rows.empty:
                st.session_state.delete_dialog_open = True
            else:
                st.warning("No category is currently selected.")

        if st.session_state.delete_dialog_open:
            @st.experimental_dialog("Delete Category")
            def delete_category_dialog(updated_df):
                st.write(f"Are you sure you want to delete the selected categories?")
                col1, col2 = st.columns(2)
                if col1.button("Cancel"):
                    st.session_state.delete_dialog_open = False
                    st.rerun()
                if col2.button("Delete"):
                    updated_df = updated_df[~updated_df["Categories"].isin([row["Categories"] for _, row in selected_rows.iterrows()])]
                    updated_df.to_csv(categories_path, index=False)
                    st.success("Categories deleted successfully!")
                    st.session_state.delete_dialog_open = False
                    st.rerun()

            delete_category_dialog(updated_df)

# main categories page
def Categories_page():
    st.title("Categories")
    categories_file = "categories.csv"
    categories_path = os.path.join(os.getcwd(), categories_file)
    if not os.path.exists(categories_path):
        pd.DataFrame(columns=["Categories"]).to_csv(categories_path, index=False)

    categories_df = pd.read_csv(categories_path)
    #st.write(categories_df)
    display_categories(categories_df)