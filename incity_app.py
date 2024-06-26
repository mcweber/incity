# ---------------------------------------------------
# Version: 26.06.2024
# Author: M. Weber
# ---------------------------------------------------
# ---------------------------------------------------

from datetime import datetime
import os
from dotenv import load_dotenv

import openai
from duckduckgo_search import DDGS

import streamlit as st

# Define Constants ---------------------------------------------------
CITY = ["Hamburg", "München", "Düsseldorf", "Berlin", "Frankfurt"]
LLM = "openai_gpt-4o"

load_dotenv()
openaiClient = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY_DVV'))

# Functions -----------------------------------------------------------

def web_search(query: str = "", limit: int = 10) -> list:
    results = DDGS().text(f"Nachrichten über '{query}'", max_results=limit)
    if results:
        return results
    else:
        return []
    
def ask_llm(temperature: float = 0.2, question: str = "", 
            history: list = [], web_results_str: str = "") -> str:
    # define prompt
    datum_context = f" Heute ist der {str(datetime.now().date())}."
    system_prompt = f"""
    Du bist ein Concierge in einem Hotel in {st.session_state.city}.
    Du weißt alles über die Stadt und kannst den Gästen Tipps geben.
    Deine Antwort besteht immer aus der Sektion "Aktuelle News aus der Stadt" und "Ausgehtipps für heute".
    """ 
    input_messages = [
                {"role": "system", "content": system_prompt + datum_context},
                {"role": "user", "content": question},
                {"role": "user", "content": "Gibt es zusätzliche Informationen aus dem Internet?"},
                {"role": "assistant", "content": 'Hier sind einige relevante Informationen aus einer Internet-Recherche:\n'  + web_results_str},
                {"role": "user", "content": 'Basierend auf den oben genannten Informationen, ' + question}
                ]
    response = openaiClient.chat.completions.create(
        model="gpt-4o",
        temperature=temperature,
        messages = input_messages
        )
    output = response.choices[0].message.content
    return output

# Main -----------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title='CITY Insight', initial_sidebar_state="collapsed")
    
    # Initialize Session State -----------------------------------------
    if 'city' not in st.session_state:
        st.session_state.city: str = "Hamburg"
        st.session_state.cityIndex: int = 0
        st.session_state.searchStatus: bool = False
   
    # Define City Selection -------------------------------------------
    swith_city = st.radio(label="Auswahl City", options=CITY, index=st.session_state.cityIndex, horizontal=True)
    if swith_city != st.session_state.city:
        st.session_state.city = swith_city
        st.session_state.cityIndex = CITY.index(swith_city)
        st.experimental_rerun()

    # Define Search Form ----------------------------------------------
    with st.form(key="searchForm"):
        question = st.text_input(label="", value=f"Ausgehtipps für heute in {st.session_state.city}")
        if st.form_submit_button("Suche absetzen") and question != "":
            st.session_state.searchStatus = True

    # Define Search & Search Results -------------------------------------------
    if st.session_state.searchStatus:   
        # Web Search ------------------------------------------------
        web_results_str = ""
        results = web_search(query=question, limit=10)
        with st.expander("WEB Suchergebnisse"):
            for result in results:
                st.write(f"{result['title']} [{result['href']}]")
                web_results_str += f"Titel: {result['title']}\nURL: {result['href']}\nBODY: {result['body']}\n"
        # LLM Search ------------------------------------------------
        summary = ask_llm(
            temperature=0.2,
            question=question,
            history=[],
            web_results_str=web_results_str
            )
        st.write(summary)
    st.session_state.searchStatus = False


if __name__ == "__main__":
    main()
