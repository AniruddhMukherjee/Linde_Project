# Dependencies
import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

# Import Files
import paths.Categories as categories_page
import paths.Projects as project_page
import paths.Documents as documents_page
import paths.Questionnaire as questionnaire_page
import paths.reports as reports_page

# set page config wide
st. set_page_config(layout="wide")

# The main files to read
data = pd.read_csv("Data.csv")
file_uploads = pd.read_csv("project_paths.csv")

# The top menu bar
selected = option_menu(
   menu_title = None,
   options = ["Category", "Projects", "Docs", "Questionnaire", "Report"],
   icons=['list','files', 'upload','question','folder'], menu_icon="cast", default_index=1,
   orientation = "horizontal"
)

def main():
    """
    Main function to control the flow of the application.
    
    This function checks the selected menu option and calls the appropriate
    page function from the imported modules.
    """
    if selected == "Category":
        categories_page.Categories_page()

    if selected == "Projects":
        project_page.projects_page()

    if selected == "Docs":
        documents_page.Documents_page()

    if selected == "Questionnaire":
        questionnaire_page.Questionnaire_page()

    if selected == "Report":
        reports_page.Reports_page()

if __name__ == "__main__":
    main()

# total lines of code 1979 ~ 2000