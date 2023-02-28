import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import streamlit_analytics
from deep_translator import GoogleTranslator

class AyatSearch():

    def __init__(self, path):

        df = pd.read_csv('data/main_df.csv')
        arabic = []
        self.text=[]
        for index, row in df.iterrows():
            arabic.append(row['Arabic'])
            t = ""
            t += row['Name'] + "|" + str(row['Arabic'])+"|"+ str(row['Surah'])+"|"+str(row['Ayat'])+"|"
            t += row['EnglishTitle'] + "|" + str(row['ArabicTitle'])+"|"+ str(row['RomanTitle'])+"|"
            t += row['PlaceOfRevelation'] + "|"
            for j in range(1, 4):
                t += row['Translation' + str(j)] + ";"
            t += "|"
            for j in range(1, 3):
                t+= row['Tafaseer' + str(j)] + ";"
            t = t[:-1]
            self.text.append(t)
        
        self.vectorizer = TfidfVectorizer()
        self.X = self.vectorizer.fit_transform(self.text)
        
        
    def query(self, query, top_k=5):
        query_vec = self.vectorizer.transform([query])
        sim_scores = cosine_similarity(query_vec, self.X).flatten()
        top_indices = sim_scores.argsort()[::-1][:top_k]
        top_paragraphs = [self.text[i] for i in top_indices]
        return top_paragraphs

languages = {'Arabic': 'ar',
 'English': 'en',
 'French': 'fr',
 'Hindi': 'hi',
 'Pashto': 'ps',
 'Urdu': 'ur'}

streamlit_analytics.track(unsafe_password="!@#$")

with streamlit_analytics.track():
    st.set_page_config(page_title="Islam & AI", page_icon = "images/islam_ai.png", initial_sidebar_state = 'auto')
    
    st.title("Welcome to Islam & AI")
    st.write("Your personal AI assistant that uses Quranic Ayats to search for your queries! Our model is based on Natural Language Processing techniques and is designed to help you find relevant information from the Quran quickly and easily. Whether you have a question about Islamic beliefs, practices, or anything else related to Islam, just ask our AI assistant and it will provide you with the most relevant Quranic Ayats to answer your query.")
    st.write("This is the initial model for a very big project, please give feedback, share & let us know about any questions you might have")

    option = st.selectbox('Select Language', ('English', 'Urdu', 'Arabic', 'Pashto', 'Hindi', 'French'))

    st.subheader("Enter your query:")
    query = st.text_input("", "Importance of Prayer")
    
    st.subheader("Select the number of queries:")
    x = st.slider("", 2, 25, 3)
    
    search = AyatSearch("data/main_df.csv")
    query = GoogleTranslator(target='en').translate(query)
    results = search.query(query, int(x))

    st.title("**Results:**")

    for r in results:
        text = r.split("|")
        st.subheader(f"{text[1]}")
        st.write(f"**- Surah Name: {text[5]} | {text[4]} | {text[6]} | {text[0]}**")
        st.write(f"**- Surah No. {text[2]} | Ayat No. {text[3]}**")
        st.write(f"**- Surah Revealed in {text[7]}**")


        st.subheader("Translations:")
        translations = text[-2].split(";")
        for i in range(len(translations)):
            if len(translations[i])>2:
                lang = GoogleTranslator(target=languages[option]).translate(translations[i])
                st.write(f"{i+1}: {lang}")

        st.subheader("Tafaseer:")
        tafaseer = text[-1].split(";")
        for i in range(len(tafaseer)):
            if len(tafaseer[i])>2:
                lang = GoogleTranslator(target=languages[option]).translate(tafaseer[i])
                st.write(f"{i+1}: {lang}")
            
        st.subheader("-"*70)






