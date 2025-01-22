from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
from fuzzywuzzy import process
from googletrans import Translator
import logging
from functools import lru_cache
import unicodedata
from gtts import gTTS
import os
import hashlib
import tempfile

# Create cache directory if it doesn't exist
AUDIO_CACHE_DIR = "audio_cache"
if not os.path.exists(AUDIO_CACHE_DIR):
    os.makedirs(AUDIO_CACHE_DIR)

def is_gujarati(text):
    """Check if the text contains Gujarati characters."""
    for char in text:
        if '\u0A80' <= char <= '\u0AFF':  # Unicode range for Gujarati
            return True
    return False

app = Flask(__name__)

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Load the Excel data with caching
@lru_cache(maxsize=1)  # Cache the result to avoid reloading the file unnecessarily
def load_chat_data():
    try:
        logging.info("Loading Excel file...")
        df = pd.read_excel('data.xlsx')
        # df = pd.read_excel('data_final.xlsx', encoding='utf-8')

        logging.info("Excel file loaded successfully.")
        return df
    except Exception as e:
        logging.error(f"Error loading Excel file: {e}")
        return None

df = load_chat_data()

@app.route('/')
def home():
    return render_template('index.html')

@lru_cache(maxsize=50)  # Cache translation results for frequently used phrases
def translate_query(query, src_lang, dest_lang='en'):
    """
    Translate the query from the source language to the destination language using Google Translator.
    """
    try:
        logging.info(f"Translating query from {src_lang} to {dest_lang}: {query}")
        translator = Translator()
        translated_text = translator.translate(query, src=src_lang, dest=dest_lang).text
        logging.info(f"Translation successful: {translated_text}")
        return translated_text
    except Exception as e:
        logging.error(f"Translation error: {e}")
        return None

# @app.route('/get_response', methods=['POST'])
# def get_response():
#     user_query = request.form.get('query', '').strip()
#     selected_language = request.form.get('language', 'english').lower()

#     if not user_query:
#         return jsonify({'reply': "Your query cannot be empty."})

#     # Translate the query if the language is not English
#     if selected_language != 'english':
#         translated_query = translate_query(user_query, src_lang=selected_language)
#         if translated_query is None:
#             return jsonify({'reply': "Translation service is currently unavailable."})
#     else:
#         translated_query = user_query

#     # Find the best response
#     response = get_best_match_response(translated_query)
#     return jsonify({'reply': response})

@app.route('/get_response', methods=['POST'])
def get_response():
    user_query = request.form.get('query', '').strip()
    selected_language = request.form.get('language', 'english').lower()

    if not user_query:
        return jsonify({'reply': "Your query cannot be empty."})

    # Skip translation completely for Gujarati text
    if is_gujarati(user_query):
        response = get_best_match_response(user_query)
        return jsonify({'reply': response})

    # For non-Gujarati text, proceed with translation if needed
    if selected_language != 'english':
        translated_query = translate_query(user_query, src_lang=selected_language)
        if translated_query is None:
            return jsonify({'reply': "Translation service is currently unavailable."})
        query_to_match = translated_query
    else:
        query_to_match = user_query

    response = get_best_match_response(query_to_match)
    return jsonify({'reply': response})


# def get_best_match_response(query, threshold=70):
#     if df is not None:
#         # Ensure queries are stripped and in lowercase for matching (for English queries)
#         queries = df['Query'].dropna().str.strip()

#         # Check if the language is Gujarati (or any other non-English language)
#         if 'gu' in query:  # Adjust this if you want to specifically handle Gujarati
#             queries = queries.str.strip()  # Keep Gujarati as-is
#         else:
#             queries = queries.str.lower()  # For English, convert to lowercase

#         responses = df['Response'].dropna().values

#         # Perform the match
#         best_match = process.extractOne(query.lower(), queries)  # Make sure comparison is done in lowercase for English

#         if best_match and best_match[1] >= threshold:
#             response_index = list(queries).index(best_match[0])
#             logging.debug(f"Best match found: {best_match} -> Response: {responses[response_index]}")
#             return responses[response_index]

#     logging.warning("No suitable match found.")
#     return "Sorry, I don't understand."

# def get_best_match_response(query, threshold=70):
#     """
#     Match the query with the predefined queries in the Excel file and return the best response.
#     """
#     if df is not None:
#         queries = df['Query'].dropna().values
#         responses = df['Response'].dropna().values

#         best_match = process.extractOne(query, queries)
#         if best_match and best_match[1] >= threshold:
#             response_index = list(queries).index(best_match[0])
#             logging.debug(f"Best match found: {best_match} -> Response: {responses[response_index]}")
#             return responses[response_index]

#     logging.warning("No suitable match found.")
#     return "Sorry, I don't understand."

def get_best_match_response(query, threshold=75):
    if df is not None:
        queries = df['Query'].dropna().values
        responses = df['Response'].dropna().values
        
        # For Gujarati text
        if is_gujarati(query):
            query_stripped = query.strip()
            gujarati_queries = [(i, q.strip()) for i, q in enumerate(queries) if is_gujarati(q)]
            
            if gujarati_queries:
                # Try exact match first
                for idx, q in gujarati_queries:
                    if query_stripped == q:
                        return responses[idx]
                
                # Try substring match
                for idx, q in gujarati_queries:
                    if query_stripped in q:
                        return responses[idx]
                
                # Use fuzzy matching as last resort
                normalized_queries = [q for _, q in gujarati_queries]
                best_match = process.extractOne(query_stripped, normalized_queries)
                if best_match and best_match[1] >= 75:  # Lower threshold for better matching
                    match_index = normalized_queries.index(best_match[0])
                    return responses[gujarati_queries[match_index][0]]
        else:
            # For non-Gujarati text
            normalized_query = query.strip().lower()
            normalized_queries = [q.strip().lower() for q in queries]
            best_match = process.extractOne(normalized_query, normalized_queries)
            if best_match and best_match[1] >= threshold:
                return responses[normalized_queries.index(best_match[0])]

    return "માફ કરશો, મને સમજાયું નહીં." if is_gujarati(query) else "Sorry, I don't understand."




@app.route('/get_suggestions', methods=['POST'])
def get_suggestions():
    query = request.form.get('query', '').strip()
    
    if not query:
        return jsonify({'suggestions': []})

    if df is not None:
        queries = df['Query'].dropna().values
        
        # First determine if the input is Gujarati
        is_gujarati_query = is_gujarati(query)
        
        # Filter queries based on language
        if is_gujarati_query:
            # For Gujarati text
            query_stripped = query.strip()
            gujarati_queries = [q.strip() for q in queries if is_gujarati(q)]
            
            # Try exact substring matches first
            exact_matches = [q for q in gujarati_queries if query_stripped.lower() in q.lower()]
            if exact_matches:
                return jsonify({'suggestions': exact_matches[:5]})
            
            # If no exact matches, use fuzzy matching
            matches = process.extract(query_stripped, gujarati_queries, limit=5)
            suggestions = [match[0] for match in matches if match[1] >= 75]
            return jsonify({'suggestions': suggestions})
        else:
            # For English text
            # Filter out Gujarati queries first
            english_queries = [q.strip() for q in queries if not is_gujarati(q)]
            normalized_query = query.lower().strip()
            
            # Try exact substring matches first
            exact_matches = [q for q in english_queries if normalized_query in q.lower()]
            if exact_matches:
                return jsonify({'suggestions': exact_matches[:5]})
            
            # If no exact matches, use fuzzy matching
            matches = process.extract(normalized_query, english_queries, limit=5)
            suggestions = [match[0] for match in matches if match[1] >= 60]
            return jsonify({'suggestions': suggestions})

    return jsonify({'suggestions': []})



@app.route('/get_speech', methods=['POST'])
def get_speech():
    text = request.form.get('text', '')
    language = request.form.get('language', 'en')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # Generate a unique filename based on text and language
    filename = hashlib.md5(f"{text}{language}".encode()).hexdigest() + '.mp3'
    filepath = os.path.join(AUDIO_CACHE_DIR, filename)
    
    # Check if audio file already exists in cache
    if not os.path.exists(filepath):
        try:
            # Convert text to speech
            tts = gTTS(text=text, lang='gu' if language == 'gu' else 'en', slow=False)
            # Save to cache
            tts.save(filepath)
        except Exception as e:
            logging.error(f"TTS Error: {e}")
            return jsonify({'error': 'TTS generation failed'}), 500
    
    return send_file(filepath, mimetype='audio/mpeg')

if __name__ == '__main__':
    app.run(debug=True)
