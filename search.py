import streamlit as st
from deep_translator import GoogleTranslator
import pathlib
from bs4 import BeautifulSoup
import logging
import shutil
from google.cloud import firestore
import datetime
import time
import re



key = {
  "type": st.secrets["type"],
  "project_id": st.secrets["project_id"],
  "private_key_id": st.secrets["private_key_id"],
  "private_key": st.secrets["private_key"],
  "client_email": st.secrets["client_email"],
  "client_id": st.secrets["client_id"],
  "auth_uri": st.secrets["auth_uri"],
  "token_uri": st.secrets["token_uri"],
  "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
  "client_x509_cert_url": st.secrets["client_x509_cert_url"],
}
GID = st.secrets["GID"]

db = firestore.Client.from_service_account_info(key)

def inject_ga():
    GA_ID = "google_analytics"
    GA_JS = """
    <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=""" + GID + """"></script>
        
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', '""" + GID + """');
        </script>
    """

    # Insert the script in the head tag of the static template inside your virtual
    index_path = pathlib.Path(st.__file__).parent / "static" / "index.html"
    logging.info(f'editing {index_path}')
    soup = BeautifulSoup(index_path.read_text(), features="html.parser")
    if not soup.find(id=GA_ID): 
        bck_index = index_path.with_suffix('.bck')
        if bck_index.exists():
            shutil.copy(bck_index, index_path)  
        else:
            shutil.copy(index_path, bck_index)  
        html = str(soup)
        new_html = html.replace('<head>', '<head>\n' + GA_JS)
        index_path.write_text(new_html)

inject_ga()



def translate(language, query):
    # return query
    return GoogleTranslator(target=language).translate(query)


languages = {
 'English': 'en',
 'Urdu': 'ur',
 'Pashto': 'ps',
 'Sindhi': 'sd',
 'Arabic': 'ar', 
 'Azerbaijani': 'az',
 'Albanian': 'sq',
 'Bengali': 'bn',
 'Bhojpuri': 'bho',
 'Bosnian': 'bs',
 'Chinese (simplified)': 'zh-CN',
 'Chinese (traditional)': 'zh-TW',
 'Danish': 'da',
 'Dutch': 'nl',
 'French': 'fr',
 'German': 'de',
 'Gujarati': 'gu',
 'Hindi': 'hi',
 'Hebrew': 'iw',
 'Italian': 'it',
 'Japanese': 'ja',
 'Kannada': 'kn',
 'Korean': 'ko',
 'Kurdish (kurmanji)': 'ku',
 'Kurdish (sorani)': 'ckb',
 'Kyrgyz': 'ky',
 'Kazakh': 'kk',
 'Malay': 'ms',
 'Malayalam': 'ml',
 'Marathi': 'mr',
 'Persian': 'fa',
 'Russian': 'ru',
 'Spanish': 'es',
 'Turkish': 'tr',
 'Turkmen': 'tk',
 'Tamil': 'ta',
 'Tajik': 'tg',
 'Uzbek': 'uz',
 'Ukrainian': 'uk',
 }

# Streamlit Starting

st.set_page_config(page_title="Islam & AI", page_icon = "images/islam_ai.png", initial_sidebar_state = 'auto')

hide_footer_style = """
    <style>
    .reportview-container .main footer {visibility: hidden;}    
    #MainMenu {
            visibility: hidden;
        }

    footer {
             visibility: hidden;
        }
    </style>
    
    """
st.markdown(hide_footer_style, unsafe_allow_html=True)

meta_data = """<head>
<meta name="title" content="Islam & AI">
<meta name="description" content="Empowering Islamic Education with Artificial Intelligence">
<meta property="og:type" content="website">
<meta property="og:url" content="https://islam-ai.streamlit.app/">
<meta property="og:title" content="Islam & AI">
<meta property="og:description" content="Empowering Islamic Education with Artificial Intelligence">
<meta property="twitter:card" content="summary_large_image">
<meta property="twitter:url" content="https://islam-ai.streamlit.app/">
<meta property="twitter:title" content="Islam & AI">
<meta property="twitter:description" content="Empowering Islamic Education with Artificial Intelligence">
</head>
"""
st.markdown(meta_data, unsafe_allow_html=True)

streamlit_style = """
    <style>
    @import url('https://fonts.googleapis.com/css?family=Work Sans');

    html, body, [class*="css"]  {
    font-family: 'Work Sans';
    }
    </style>
    """
st.markdown(streamlit_style, unsafe_allow_html=True)

option = st.selectbox('Select Language', languages.keys())

betaversion = "Website Shifted to => "

title = "Welcome to Islam & AI"
subtitle = "We are excited to present a new and innovative way of using Artificial Intelligence in the field of Islam, which has never been used before! Our AI model is specially designed to quickly and easily find relevant information from the Quran based on your queries, using Natural Language Processing techniques."
subtitle2 = "This is just the beginning of a large project, and we need your support! Your queries and feedback will help us improve our AI model and cover all aspects of Islam. We welcome your suggestions and questions as we embark on this exciting journey."
subtitle3 = "We welcome your Queries, Feedback, and Collaboration! Please do not hesitate to contact us at this email address"

st.title(translate(languages[option], title))
st.write(translate(languages[option], subtitle))
st.write(translate(languages[option], subtitle2))
st.write(translate(languages[option], subtitle3))
st.write("alizahidrajaa@gmail.com")

st.title(translate(languages[option], betaversion) + "[IslamAndAi.com](https://islamandai.com/query-beta)")
st.write(translate(languages[option], "Enter your email address to get updates!"))
email = st.text_input("email", "user@domain.com")

if not email == "user@domain.com" :
    if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        # create a dictionary to store the data
        timestamp = datetime.datetime.now()
        data = {"email": email, "timestamp": timestamp}
        doc_ref = db.collection("emails").add(data)
        alert = st.warning(translate(languages[option], "Email saved successfully!")) # Display the success
        time.sleep(2) # Wait for 2 seconds
        alert.empty()
    else:
        alert = st.warning(translate(languages[option], "Invalid email!")) # Display the success
        time.sleep(2) # Wait for 2 seconds
        alert.empty()

import datetime

start_date = datetime.datetime(2023, 3, 1)
current_date = datetime.datetime.now()

time_delta = current_date - start_date

days = time_delta.days
hours, remainder = divmod(time_delta.seconds, 3600)
minutes, seconds = divmod(remainder, 60)

footer = """<style>
a:link , a:visited{
color: green;
background-color: transparent;
text-decoration: underline;
}

a:hover,  a:active {
color: green;
background-color: transparent;
text-decoration: underline;
}

.footer {
left: 0;
bottom: 0;
width: 100%;
color: green;
text-align: center;
}
</style>
<div class="footer">
<p>Copyright @ 2023 - Islam & AI <a style='display: block; text-align: center;' href="https://islamandai.com/" target="_blank">Contact</a> """ + f"{days} days, {hours} hours, and {minutes} minutes since the start of this project" + """</p>
</div>
"""
st.markdown(footer,unsafe_allow_html=True)