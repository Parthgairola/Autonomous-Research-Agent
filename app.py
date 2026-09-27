# Import Streamlit for creating UI
import streamlit as st

# Import graph and pdf generating function from graph.py 
from graph import app, generate_pdf

# Agent Image
st.image("assets/agent_image.png", use_container_width=True)

# Title
st.title("🔎 Autonomous Research Agent")

# Description
st.write(
    "Explore any topic and get a concise research summary. "
    "The agent uses three stages: a Research Agent gathers information "
    "from multiple sources, a Summarizer Agent synthesizes the findings, "
    "and a Review Agent validates the final summary before delivering it. "
    "You can also download the final summary as a PDF report."
)

# User Query
query = st.chat_input("What would you like to explore?")

if query:
        # Loader
        with st.spinner("🌐 Gathering information , 📋 Synthesizing findings , 🔎 Validating results......"):

            result = app.invoke({
                "user_query": query
            })

        st.subheader("📄 Research Summary")
        st.write(result["summary"])

        # PDF Generator
        generate_pdf(result["summary"])

        # PDF Downloader
        with open("summary.pdf", "rb") as file:

            # PDF Download Button
            st.download_button(
                label="📄 Download PDF",
                data=file,
                file_name="research_report.pdf",
                mime="application/pdf"
            )
