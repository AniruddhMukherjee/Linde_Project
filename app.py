# Dependencies
import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import os
from pathlib import Path
from st_aggrid import AgGrid, GridUpdateMode, DataReturnMode, GridOptionsBuilder
import tempfile
from PIL import Image


# Import Files
import paths.Categories as categories_page
import paths.Projects as project_page
import paths.Documents as documents_page
import paths.Questionnaire as questionnaire_page


# set page config wide
st. set_page_config(layout="wide")


# The top menu bar
selected = option_menu(
   menu_title = None,
   options = ["Category", "Projects", "Docs", "Questionnaire", "Report"],
   icons=['list','files', 'upload','question','folder'], menu_icon="cast", default_index=1,
   orientation = "horizontal"
)


# The main files to read
data = pd.read_csv("Data.csv")
file_uploads = pd.read_csv("project_paths.csv")




def main():

    if selected == "Category":
        categories_page.Categories_page()

    if selected == "Projects":
        project_page.projects_page()

    if selected == "Docs":
        documents_page.Documents_page()

    if selected == "Questionnaire":
        questionnaire_page.Questionnaire_page()



if __name__ == "__main__":
    main()



###################################################
########### THE MAIN REPORTS GEN. PAGE ############
###################################################


# main report page
if selected == "Report":
   st.title("Reports Page")
   # The selected project from the dropdown
   selected_project = st.session_state.get("selected_project", None)


   if selected_project:
       st.subheader(f"Reports for project : {selected_project}")
   else:
       st.warning("Select Project")











