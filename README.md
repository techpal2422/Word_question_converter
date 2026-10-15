# Question Text to CSV Converter (Streamlit)

A Streamlit web app where users paste multiple-choice questions into a textbox, review extracted questions/options/answers, and download a CSV.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Community Cloud

1. Upload `app.py`, `requirements.txt`, and `README.md` to a GitHub repository.
2. Visit https://share.streamlit.io/ and sign in.
3. Create an app from the repository, using `app.py` as the main file.
4. Deploy.

## Paste format

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

Answers map to `option_1`, `option_2`, `option_3`, and `option_4` for Options A, B, C, and D respectively. The app also supports an optional Excel template to preserve column names and order.
