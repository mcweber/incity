# ---------------------------------------------------
# Version: 30.06.2024
# Author: M. Weber
# ---------------------------------------------------
# change websearch to Tavily
# ---------------------------------------------------

from datetime import datetime
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

import openai
# from duckduckgo_search import DDGS
from tavily import TavilyClient

import streamlit as st

# Define Constants ---------------------------------------------------
CITY = ["Hamburg", "München", "Düsseldorf", "Berlin", "Frankfurt", "Dießen am Ammersee", "Würzburg", "Karlsruhe", "Bremen"]
KATEGORIEN = ["Restaurant & Bars", "Kino & Theater", "Konzerte", "Szene"]
LLM = "openai_gpt-4o"
HEUTE = str(datetime.now().date())
TEMPERATURE = 0.1

load_dotenv()
openaiClient = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY_DVV'))
tavilyClient = TavilyClient(api_key=os.environ.get('TAVILY_API_KEY_PRIVAT'))

# Functions -----------------------------------------------------------

def web_search(limit: int = 10) -> list:
    query = f"Ausgehtipps für den {HEUTE} in {st.session_state.city} für {', '.join(KATEGORIEN)}"
    # results = DDGS().text(keywords=query, max_results=limit)
    response = tavilyClient.search(query=query, max_results=limit, include_raw_content=True)
    results = response['results']
    if results:
        return results
    else:
        return []
    
def write_summary(content: str = "", url: str = "") -> str:
    text = ""
    if url != "":
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A"}
        try:
            response = requests.get(url, headers=headers)
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return "error", "error"
        soup = BeautifulSoup(response.text, 'html.parser')
        if soup.body:
            text = soup.get_text()
    elif content != "":
        text = content
    if text != "":
        input_messages = [
                {"role": "user", "content": f"Schreibe eine Zusammenfassung des folgendes Textes: {text}."},
                ]
        response = openaiClient.chat.completions.create(
            model="gpt-4o",
            temperature=TEMPERATURE,
            messages = input_messages
            )
        summary = response.choices[0].message.content
    else:
        summary = ""
    return summary

def ask_llm(web_results_str: str = "") -> str:
    # Define System Prompt ------------------------------------------
    #datum_context = f" Heute ist der {HEUTE}."
    system_prompt = f"""
    Du bist ein Concierge in einem Hotel in {st.session_state.city}.
    Du weißt alles über die Stadt und kannst den Gästen Tipps geben.
    Heute ist der {HEUTE}.
    Deine Antwort bezieht sich immer auf den heutigen Tag und die genannte Stadt.
    Die Antwort besteht immer aus der Sektion {KATEGORIEN}.
    Die Antwort gibt immer konkrete Tipps, die sich auf eine bestimmte Aktivität beziehen.
    Die Antwort beinhaltet immer einen weiterführenden Link, entweder auf die konkrete Aktivität oder auf eine Webseite, die weitere Informationen bietet.
    """ 
    input_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "assistant", "content": 'Hier sind relevante und aktuelle Informationen aus einer Internet-Recherche:\n'  + web_results_str},
                {"role": "user", "content": 'Basierend auf den oben genannten Informationen, stelle die besten Tipps zusammen.'}
                ]
    response = openaiClient.chat.completions.create(
        model="gpt-4o",
        temperature=TEMPERATURE,
        messages = input_messages
        )
    output = response.choices[0].message.content
    return output

# Main -----------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title='CITY Insight')
    st.title("CITY Insight")
    st.write("Version: 30.06.2024 Status: POC")
    
    # Initialize Session State -----------------------------------------
    if 'city' not in st.session_state:
        st.session_state.city: str = "Hamburg"
        st.session_state.cityIndex: int = 0
        st.session_state.searchStatus: bool = False
   
    # Define Search Form ----------------------------------------------
    with st.form(key="new_search_form"):
        switch_city = st.radio(label="Wähle Stadt aus:", options=CITY, index=st.session_state.cityIndex, horizontal=True)
        if switch_city != st.session_state.city:
            st.session_state.city = switch_city
            st.session_state.cityIndex = CITY.index(switch_city)
        # question = st.text_input(label="", value=f"Ausgehtipps für heute in {st.session_state.city}")
        if st.form_submit_button("Generiere Vorschläge"):
            st.session_state.searchStatus = True

    # Define Search & Search Results -------------------------------------------
    if st.session_state.searchStatus:   
        # Web Search ------------------------------------------------
        web_results_str = ""
        results = web_search(limit=10)
        with st.expander("WEB Suchergebnisse"):
            for result in results:
                if result['score'] < 0.9:
                    continue
                # summary = write_summary(result['href])
                summary = write_summary(content=result['raw_content'])
                if summary  != "":
                    # st.write(f"{result['title']} [{result['href']}]\n{result['body'][:1000]}...")
                    # web_results_str += f"Titel: {result['title']}\nURL: {result['href']}\nSUMMARY: {summary}\n"
                    st.write(f"[{result['score']}] {result['title']} [{result['url']}]")
                    web_results_str += f"Titel: {result['title']}\nURL: {result['url']}\nSUMMARY: {summary}\n"
        # LLM Search ------------------------------------------------
        st.write(ask_llm(web_results_str=web_results_str))
        st.session_state.searchStatus = False


if __name__ == "__main__":
    main()
