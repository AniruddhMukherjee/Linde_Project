import streamlit as st
import pandas as pd

data = pd.read_csv("questionnaires/xs/Questions - Sheet1.csv")
st.table(data)