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
    return GoogleTranslator(target=language).translate(query)


languages = {'English': 'en',
 'Urdu': 'ur',
 'Hindi': 'hi',
 'Arabic': 'ar', 
 'Pashto': 'ps',
 'French': 'fr',
 'Chinese': 'zh-CN',
 'Turkish': 'tr',
 'Spanish': 'es',
 'German': 'de',
 'Danish': 'da',
 'Russian': 'ru',
 'Italian': 'it',
 'Japanese': 'ja',
 'Kazakh': 'kk',
 'Azerbaijani': 'az',
 }

with streamlit_analytics.track(unsafe_password="!@#$"):
    st.set_page_config(page_title="Islam & AI", page_icon = "images/islam_ai.png", initial_sidebar_state = 'auto')
    
    option = st.selectbox('Select Language', languages.keys())

    title = "Welcome to Islam & AI"
    subtitle = "Your personal AI assistant that uses Quranic Ayats to search for your queries! Our model is based on Natural Language Processing techniques and is designed to help you find relevant information from the Quran quickly and easily. Whether you have a question about Islamic beliefs, practices, or anything else related to Islam, just ask our AI assistant and it will provide you with the most relevant Quranic Ayats to answer your query."
    subtitle2 = "This is the initial model for a very big project, please give feedback, share & let us know about any questions you might have"
    
    st.title(translate(languages[option], title))

    st.write(translate(languages[option], subtitle))

    st.write(translate(languages[option], subtitle2))

    st.subheader(translate(languages[option], "Enter your query:"))

    query = st.text_input("", translate(languages[option], "Importance of Prayer"))
    
    st.subheader(translate(languages[option], "Select the number of queries:"))
    x = st.slider("", 2, 25, 3)
    
    search = AyatSearch("data/main_df.csv")
    query = GoogleTranslator(target='en').translate(query)
    results = search.query(query, int(x))

    st.title(f"**{translate(languages[option], 'Results:')}**")

    for r in results:
        text = r.split(" | ")
        st.subheader(f"{text[1]}")
        
        st.write(f"**- {translate(languages[option], 'Surah Name')}**")
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






