import re
import csv
import io

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Question Text to CSV Converter",
    page_icon="📝",
    layout="wide",
)

st.title("📝 Question Text to CSV Converter")
st.write(
    "Paste your questions into the textbox below. The app extracts each question, "
    "Options A–D, and the correct answer, then prepares a downloadable CSV."
)

st.markdown(
    """
**Expected format**
```text
1. What is the capital of France?
Option A: Berlin
Option B: Paris
Option C: Rome
Option D: Madrid
Answer: Option B

2. Which planet is known as the Red Planet?
Option A: Earth
Option B: Venus
Option C: Mars
Option D: Jupiter
Answer: Option C
```
"""
)

with st.sidebar:
    st.header("Default column values")
    question_type = st.text_input("question_type", "single_choice")
    question_group = st.text_input("question_group", "119")
    question_level = st.text_input("question_level", "easy")
    marks = st.text_input("marks", "1")
    st.caption("These values are applied to every question.")

st.subheader("1. Paste your questions")
pasted_text = st.text_area(
    "Paste the complete question text here",
    height=360,
    placeholder=(
        "1. Type your question here\n"
        "Option A: First option\n"
        "Option B: Second option\n"
        "Option C: Third option\n"
        "Option D: Fourth option\n"
        "Answer: Option A"
    ),
)

with st.expander("Optional: Upload an Excel template"):
    template_file = st.file_uploader(
        "Excel template (.xlsx)",
        type=["xlsx"],
        help="Optional. If uploaded, the CSV will use the template's exact column headers and order.",
    )

DEFAULT_COLUMNS = [
    "question_type",
    "question_group",
    "question_level",
    "marks",
    "question",
    "option_1",
    "option_2",
    "option_3",
    "option_4",
    "answer",
]

def parse_questions(raw_text):
    """Parse numbered questions and Option A-D / Answer labels."""
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    # Normalize Word-like bullets and whitespace while retaining line boundaries.
    text = text.replace("\u00a0", " ")
    start_pattern = re.compile(
        r"(?im)^\s*(?:(?:question)\s*)?\d+\s*[\.\):\-]\s*"
    )
    starts = list(start_pattern.finditer(text))

    chunks = []
    if starts:
        for i, match in enumerate(starts):
            end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
            chunks.append(text[match.start():end].strip())
    else:
        # Also accept unnumbered questions that begin with "Question:"
        # by splitting on those labels.
        qstarts = list(re.finditer(r"(?im)^\s*question\s*[:\-]\s*", text))
        if qstarts:
            for i, match in enumerate(qstarts):
                end = qstarts[i + 1].start() if i + 1 < len(qstarts) else len(text)
                chunks.append(text[match.start():end].strip())
        elif text.strip():
            chunks = [text.strip()]

    parsed = []
    for chunk in chunks:
        q_match = re.match(
            r"(?is)^\s*(?:(?:question)\s*)?\d+\s*[\.\):\-]\s*(.*)$",
            chunk,
        )
        if q_match:
            body = q_match.group(1).strip()
        else:
            body = re.sub(r"(?is)^\s*question\s*[:\-]\s*", "", chunk).strip()

        option_matches = list(re.finditer(
            r"(?im)(?:^|\n)\s*(?:option\s*)?([A-D])\s*[:.)\-]\s*",
            body,
        ))
        # If the labels appear inline, try a less strict pattern.
        if len(option_matches) < 4:
            option_matches = list(re.finditer(
                r"(?i)\boption\s*([A-D])\s*[:.)\-]\s*",
                body,
            ))

        answer_match = re.search(
            r"(?i)\banswer\s*[:\-]\s*(?:option\s*)?([A-D])\b",
            body,
        )

        if not option_matches:
            continue

        question = body[:option_matches[0].start()].strip(" \n:-")
        question = re.sub(r"(?i)^\s*question\s*[:\-]\s*", "", question).strip()
        options = {}

        for i, match in enumerate(option_matches):
            end = option_matches[i + 1].start() if i + 1 < len(option_matches) else len(body)
            option_text = body[match.end():end]
            option_text = re.split(r"(?i)\banswer\s*[:\-]", option_text)[0]
            options[match.group(1).upper()] = option_text.strip(" \n;|\t")

        answer_letter = answer_match.group(1).upper() if answer_match else ""
        answer_value = (
            f"option_{ord(answer_letter) - ord('A') + 1}"
            if answer_letter else ""
        )

        parsed.append({
            "question_type": question_type,
            "question_group": question_group,
            "question_level": question_level,
            "marks": marks,
            "question": question,
            "option_1": options.get("A", ""),
            "option_2": options.get("B", ""),
            "option_3": options.get("C", ""),
            "option_4": options.get("D", ""),
            "answer": answer_value,
            "_answer_letter": answer_letter,
        })
    return parsed

if st.button("Parse questions", type="primary", use_container_width=True):
    st.session_state["parse_clicked"] = True
    st.session_state["raw_questions"] = pasted_text

if st.session_state.get("parse_clicked"):
    raw_text = st.session_state.get("raw_questions", "")
    if not raw_text.strip():
        st.warning("Paste your questions into the textbox first.")
    else:
        parsed = parse_questions(raw_text)
        if not parsed:
            st.error(
                "I couldn't detect any questions with four options. Check the format above, "
                "and make sure the options are labelled A, B, C, D and answers use 'Answer: Option A' (or B, C, D)."
            )
        else:
            rows = [{k: v for k, v in item.items() if not k.startswith("_")} for item in parsed]
            review_df = pd.DataFrame(rows)

            missing_answers = sum(1 for item in parsed if not item["answer"])
            incomplete_options = sum(
                1 for item in parsed
                if any(not item.get(f"option_{i}") for i in range(1, 5))
            )
            col1, col2, col3 = st.columns(3)
            col1.metric("Questions detected", len(parsed))
            col2.metric("Missing answers", missing_answers)
            col3.metric("Questions with missing options", incomplete_options)

            st.subheader("2. Review and edit")
            edited_df = st.data_editor(
                review_df,
                use_container_width=True,
                num_rows="dynamic",
                key="questions_editor",
            )
            st.caption(
                "Please check the question text, options, and answer mapping before downloading."
            )

            if template_file is not None:
                try:
                    template_df = pd.read_excel(template_file)
                    template_headers = list(template_df.columns)
                    normalized_headers = {str(col).strip().lower(): col for col in template_headers}
                    remapped = pd.DataFrame()
                    for col in template_headers:
                        key = str(col).strip().lower()
                        if key in {str(c).strip().lower() for c in edited_df.columns}:
                            source_col = next(c for c in edited_df.columns if str(c).strip().lower() == key)
                            remapped[col] = edited_df[source_col]
                        else:
                            remapped[col] = ""
                    output_df = remapped
                    st.info("Using the Excel template's column names and order.")
                except Exception as exc:
                    st.error(f"Could not read the Excel template: {exc}")
                    output_df = edited_df
            else:
                output_df = edited_df

            csv_data = output_df.to_csv(
                index=False,
                quoting=csv.QUOTE_MINIMAL,
            ).encode("utf-8-sig")

            st.subheader("3. Download")
            st.download_button(
                "⬇️ Download CSV file",
                data=csv_data,
                file_name="converted_questions.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True,
            )

st.divider()
st.caption(
    "This app parses the text you paste into the box. If a question is formatted unusually, "
    "review the extracted table before downloading. Avoid pasting confidential material into a public deployment."
)
