# Import Streamlit for creating UI
import streamlit as st

# Import time for the line by line delay
import time

# Import graph and pdf generating function from graph.py 
from graph import app, generate_pdf

# Streams text line by line
def stream_lines(text):
    for line in text.split("\n"):
        yield line + "\n"
        time.sleep(0.15)

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

    result = {}

    # Live progress of each node
    with st.status("Researching...", expanded=True) as status:

        for event in app.stream(
            {"user_query": query},
            stream_mode="updates"
        ):
            for node, output in event.items():

                if node == "research_agent":
                    st.write("🌐 Research Agent: gathered information")

                elif node == "summarizer_node":
                    st.write("📋 Summarizer Agent: synthesized findings")

                elif node == "review_node":
                    decision = output.get("approved", "").strip()

                    if decision.startswith("YES"):
                        st.write("✅ Review Agent: approved the summary")
                    else:
                        st.write("🔄 Review Agent: needs improvement, retrying")

                result.update(output)

        status.update(label="Research complete", state="complete", expanded=False)

    st.subheader("📄 Research Summary")
    st.write_stream(stream_lines(result["summary"]))

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