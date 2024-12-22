import streamlit as st
import pandas as pd

def show_dashboard(response, symptoms, solutions):
    st.title("Dashboard Analysis")

    if response:
        st.subheader("Analyzed Response")
        st.write(response)
        
        if symptoms:
            st.subheader("Symptoms Analysis")
            symptoms_df = pd.DataFrame(symptoms, columns=["Symptoms"])
            st.table(symptoms_df)

        if solutions:
            st.subheader("Solutions Analysis")
            solutions_df = pd.DataFrame(solutions, columns=["Solutions"])
            st.table(solutions_df)
    else:
        st.write("No analysis available. Please go back and process the invoice.")

if __name__ == "__main__":
    show_dashboard("Sample response", ["Symptom 1", "Symptom 2"], ["Solution 1", "Solution 2"])
