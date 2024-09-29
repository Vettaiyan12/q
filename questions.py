import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json

load_dotenv()  # load all our environment variables
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Gemini Pro Response
def get_gemini_response(input):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(input)
    return response.text

# Extract and concatenate text from all pages of the given PDF file
def input_pdf_text(uploaded_file):
    if uploaded_file is not None:
        reader = pdf.PdfReader(uploaded_file)
        text = ""
        for page in range(len(reader.pages)):
            page = reader.pages[page]
            text += str(page.extract_text())
        return text
    return ""

# Prompt Template
input_prompt = """
Act as an experienced interviewer with deep understanding of the tech field, software engineering, data science, data analysis, and big data engineering. Your task is to generate interview questions and an evaluation matrix based on the given job description, years of experience required, and difficulty level. If a resume is provided, use it to tailor some questions, but if not, focus on the job description.

Job Description: {jd}
Resume: {resume}
Years of Experience: {years_of_experience}
Difficulty Level: {difficulty_level}

Generate a response in the following JSON format:
{{
    "general_questions": [
        "Question 1",
        "Question 2",
        ...
    ],
    "technical_questions": [
        "Question 1",
        "Question 2",
        ...
    ],
    "coding_questions": [
        {{
            "question": "Question 1",
            "difficulty": "Easy/Medium/Hard"
        }},
        {{
            "question": "Question 2",
            "difficulty": "Easy/Medium/Hard"
        }},
        ...
    ],
    "evaluation_matrix": [
        {{
            "skill": "Skill 1 (with years of experience if applicable)",
            "description": "Brief description of the skill"
        }},
        {{
            "skill": "Skill 2",
            "description": "Brief description of the skill"
        }},
        ...
    ]
}}

Notes:
1. Generate 5-7 general questions related to the job requirements and candidate's experience (if resume is provided).
2. Generate 5-7 technical questions specific to the technologies mentioned in the job description.
3. If the job description is related to coding, generate 2-3 coding questions. Otherwise, omit the "coding_questions" field.
4. Ensure that the questions are appropriate for the specified years of experience and difficulty level.
5. Identify 5-10 key skills from the job description for the evaluation matrix. Include years of experience if specified in the job description.
"""

# Streamlit app
st.set_page_config(layout="wide")
st.title("Interview Question Generator with Evaluation Matrix")

# Sidebar inputs
with st.sidebar:
    st.header("Input Parameters")
    jd = st.text_area("Job Description", key="jd", height=200)
    uploaded_file = st.file_uploader("Upload Candidate's Resume (Optional)", type="pdf", help="Please upload the pdf if available")
    years_of_experience = st.slider("Years of Experience Required", 0, 15, (1, 5))
    difficulty_level = st.selectbox("Difficulty Level", options=["Easy", "Medium", "Hard"])
    submit = st.button("Generate Questions and Evaluation Matrix")

# Main content area
if submit:
    if not jd:
        st.error("Please provide a job description in the sidebar.")
    else:
        with st.spinner("Generating questions and evaluation matrix..."):
            resume_text = input_pdf_text(uploaded_file) if uploaded_file else "No resume provided."
            
            # Prepare the input for the Gemini model
            gemini_input = input_prompt.format(
                jd=jd,
                resume=resume_text,
                years_of_experience=f"{years_of_experience[0]}-{years_of_experience[1]} years",
                difficulty_level=difficulty_level
            )
            
            # Get response from Gemini
            response = get_gemini_response(gemini_input)
            
            # Parse the JSON response
            try:
                data = json.loads(response)
                
                st.subheader("General Questions")
                for q in data.get("general_questions", []):
                    st.write(f"- {q}")
                
                st.subheader("Technical Questions")
                for q in data.get("technical_questions", []):
                    st.write(f"- {q}")
                
                if "coding_questions" in data:
                    st.subheader("Coding Questions")
                    for q in data["coding_questions"]:
                        st.write(f"- {q['question']} (Difficulty: {q['difficulty']})")
                
                st.subheader("Evaluation Matrix")
                matrix = "| **Skill** | **Rating (1-10)** | **Comments** |\n"
                matrix += "| --------- | ----------------- | ------------ |\n"
                for skill in data.get("evaluation_matrix", []):
                    matrix += f"| **{skill['skill']}** | | |\n"
                
                st.markdown(matrix)
                st.text("Copy the above matrix to use during the interview for rating the candidate.")
                
            except json.JSONDecodeError:
                st.error("Error parsing the response. Please try again.")
else:
    st.info("Fill in the required fields in the sidebar and click 'Generate Questions and Evaluation Matrix' to get started.")