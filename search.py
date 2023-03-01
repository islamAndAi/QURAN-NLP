import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
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


db = firestore.Client.from_service_account_info(key)

def inject_ga():
    GA_ID = "google_analytics"
    GA_JS = """
    <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-N39RFTGS8Q"></script>
        
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-N39RFTGS8Q');
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

class AyatSearch():

    def __init__(self, path):

        df = pd.read_csv('data/main_df.csv')
        arabic = []
        self.text=[]
        translation_col = list(df.columns)
        self.translation_col = [x for x in translation_col if "Translation" in x]

        tafaseer_col = list(df.columns)
        self.tafaseer_col = [x for x in tafaseer_col if "Tafaseer" in x]

        for index, row in df.iterrows():
            arabic.append(row['Arabic'])
            t = ""
            t += row['Name'] + " | " + str(row['Arabic'])+" | "+ str(row['Surah'])+" | "+str(row['Ayat'])+" | "
            t += row['EnglishTitle'] + " | " + str(row['ArabicTitle'])+" | "+ str(row['RomanTitle'])+" | "
            t += row['PlaceOfRevelation'] + " | "
            for j in self.translation_col:
                t += row[j] + " + "
            t += " | "
            for j in self.tafaseer_col:
                t+= row[j] + " + "
            t = t[:-3]
            self.text.append(t)
        
        self.vectorizer = TfidfVectorizer()
        self.X = self.vectorizer.fit_transform(self.text)
        
        
    def query(self, query, top_k=5):
        query_vec = self.vectorizer.transform([query])
        sim_scores = cosine_similarity(query_vec, self.X).flatten()
        top_indices = sim_scores.argsort()[::-1][:top_k]
        top_paragraphs = [self.text[i] for i in top_indices]
        return top_paragraphs

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

st.set_page_config(page_title="Islam & AI", page_icon = "images/islam_ai.png", initial_sidebar_state = 'auto')

option = st.selectbox('Select Language', languages.keys())

title = "Welcome to Islam & AI"
subtitle = "Your Personal AI Assistant that uses Quranic Ayats to search for your queries! Our model is based on Natural Language Processing techniques and is designed to help you find relevant information from the Quran quickly and easily."
subtitle2 = "This is the initial model for a very big project; please give feedback, share & let us know about any questions you might have"
subtitle3 = "If you have any queries or would like to collaborate, please do contact at this email address"

st.title(translate(languages[option], title))
st.write(translate(languages[option], subtitle))
st.write(translate(languages[option], subtitle2))
st.write(translate(languages[option], subtitle3))
st.write("alizahidrajaa@gmail.com")

st.write(translate(languages[option], "Enter your email address to get updates!"))
email = st.text_input("email", translate(languages[option], "user@domain.com"))

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

st.subheader(translate(languages[option], "Enter your query:"))
query = st.text_input("query", translate(languages[option], "Importance of Prayer"))

st.subheader(translate(languages[option], "Select the number of queries:"))
num = st.slider("num", 2, 25, 3)

if not query == "Importance of Prayer":
    timestamp = datetime.datetime.now()
    data = {"query": query, "number": num, "timestamp": timestamp, "language": option}
    doc_ref = db.collection("queries").add(data)


search = AyatSearch("data/main_df.csv")
query = GoogleTranslator(target='en').translate(query)
results = search.query(query, int(num))

st.title(f"**{translate(languages[option], 'Results:')}**")

for r in results:
    text = r.split(" | ")
    st.subheader(f"{text[1]}")
    
    st.write(f"**{translate(languages[option], 'Surah Name')}**")
    st.write(f"**-- {text[5]} | {text[4]} | {text[6]} | {text[0]}**")

    st.write(f"**- {translate(languages[option], f'Surah No. {text[2]} | Ayat No. {text[3]}')}**")

    st.write(f"**- {translate(languages[option], f'Surah Revealed in {text[7]}')}**")

    st.subheader(f"{translate(languages[option], 'Translations:')}")
    translations = text[-2].split(" + ")
    for i in range(len(translations)):
        if len(translations[i])>2:
            st.write(f"{i+1}: {translate(languages[option], search.translation_col[i])}")
            st.write(f"{translate(languages[option], translations[i])}")
            

    st.subheader(f"{translate(languages[option], 'Tafaseer:')}")
    tafaseer = text[-1].split(" + ")
    for i in range(len(tafaseer)):
        if len(tafaseer[i])>2:
            st.write(f"{i+1}: {translate(languages[option], search.tafaseer_col[i])}")
            st.write(f"{translate(languages[option], tafaseer[i])}")
        
    st.subheader("-"*70)
