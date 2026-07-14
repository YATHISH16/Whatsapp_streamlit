# Whatsapp_Analyzer_streamlit

WhatsApp Chat Analyzer: A powerful data analytics web application built with Python and Streamlit that transforms raw WhatsApp chat exports into comprehensive, visual PDF reports.


📌 Project Overview
This application automates the process of parsing WhatsApp chat logs (.txt files) and extracting deep behavioral insights. Users can upload their exported chat files to instantly visualize communication patterns, media sharing habits, and word usage statistics, all downloadable as a polished PDF document.


📊 Key Features

Chat Parsing: 
Converts unstructured text data into organized Pandas DataFrames.

Timeline Analysis:
Tracks messaging frequency across days, months, and years.

Activity Heatmaps: 
Identifies peak messaging hours and most active days of the week.

User Statistics: 
Compares total messages, word counts, and media shared per participant.

Word Cloud Generation: 
Visualizes the most frequently used words, excluding common stopwords.

PDF Report Engine: 
Generates and formats an executive summary report for offline viewing.

Interactive UI: 
Offers a clean, responsive interface powered entirely by Streamlit.

🛠️ Tech StackFrontend/Hosting:
Streamlit

Data Processing: 
Python, Pandas, NumPy

Text Analysis:
NLTK, WordCloud

Data Visualization:
Matplotlib, Seaborn, Plotly

PDF Generation:
FPDF2 / ReportLab
