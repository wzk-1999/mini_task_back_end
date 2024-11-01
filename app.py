import json

from flask import Flask, request, Response, stream_with_context
import requests
from flask_cors import CORS

from scraper import process_website
from config import Config
from volcenginesdkarkruntime import Ark

from utilities import pgsqlUtilities

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})
# CORS(app)

client = Ark(api_key=Config().ARK_API_KEY)


def generate_classification_prompt(url, keywords):
    """Construct a prompt to generate a visitor classification based on keywords."""
    keyword_str = ', '.join(keywords)
    return f"Based on the website '{url}' with focus on {keyword_str}, generate 8 comma seperated keywords to describe the visitor's potential industry and interest, only return keywords and comma"

@app.route('/api/v1/scrape_by_url', methods=['POST'])
def scrape_by_url():
    return Response(stream_with_context(_stream_response()), content_type='text/event-stream')


def _stream_response():
    data = request.get_json()
    url = data.get('url')
    session_id = request.headers.get('Session-ID')

    if not url or not session_id:
        yield f"data: {json.dumps({'error': 'URL and Session ID are required'})}\n\n"
        return

    # Step 1: Scrape and process website content
    website_entry = process_website(url)

    # Step 2: Generate classification prompt and question
    classification_prompt = generate_classification_prompt(url, website_entry.keywords)
    question_prompt = (
        f"Generate a multi-option question to test the user's interest about the '{url}' website, "
        f"{', '.join(website_entry.keywords)}, format the question and options using markdown format with checkboxes (- [ ]) "
        "only return the question and options."
    )
    pgsqlUtilities.store_message(session_id, question_prompt, 'user')

    # Retrieve conversation ID from API
    api_url = f"{Config().API_LINK_GET_CONVERSATION_ID}?user_id={session_id}"
    headers = {'Authorization': f'Bearer {Config().LLM_API_KEY}'}
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        data = json.loads(response.text)
        conversation_id = data.get('data', {}).get('id')
        if not conversation_id:
            yield f"data: {json.dumps({'error': 'Failed to obtain a valid conversation_id from the API.'})}\n\n"
            return
    else:
        yield f"data: {json.dumps({'error': f'API request failed with status code {response.status_code}'})}\n\n"
        return

    # Step 3: Prepare request for LLM to generate question
    data = {
        "conversation_id": conversation_id,
        "messages": [{"role": "user", "content": question_prompt}],
        "quote":True
    }
    headers = {"Authorization": f"Bearer {Config().LLM_API_KEY}"}

    try:
        # Send request to LLM for question generation
        llm_response = requests.post(Config().LLM_API_URL, headers=headers, json=data, stream=True)

        if llm_response.status_code == 200:
            answer = ""
            for chunk in llm_response.iter_lines():
                if chunk:
                    try:
                        if chunk.startswith(b'data:'):
                            chunk = chunk[len(b'data:'):].decode('utf-8')
                        line_data = json.loads(chunk)
                        if line_data.get('retcode') == 0:
                            data_content = line_data['data']
                            if isinstance(data_content, bool) and data_content:
                                # Store generated question in DB
                                pgsqlUtilities.store_message(session_id, answer, 'assistant')
                                pgsqlUtilities.store_message(session_id, classification_prompt, 'user')

                                # Send non-streaming request to generate profile with classification_prompt
                                data = {
                                    "conversation_id": conversation_id,
                                    "messages": [{"role": "user", "content": classification_prompt}],
                                    "stream": False,
                                    "quote": True
                                }
                                try:
                                    llm_response = requests.post(Config().LLM_API_URL, headers=headers, json=data,
                                                                 stream=False)
                                    if llm_response.status_code == 200:
                                        line_data = llm_response.content

                                        if line_data.startswith(b'data:'):
                                            # print("yes")
                                            line_data = line_data[len(b'data:'):].decode('utf-8')
                                        # print(line_data)
                                        data_content = json.loads(line_data)
                                        if data_content.get('retcode') == 0:
                                            answer =data_content['data']['answer']
                                            yield f"data: {json.dumps({'profile': answer,'reference':data_content['data']['reference']})}\n\n"
                                            pgsqlUtilities.store_message(session_id, answer, 'assistant')
                                            return
                                except Exception:
                                    yield f"data: {json.dumps({'error': 'Request to generate profile failed.'})}\n\n"
                                return
                            elif isinstance(data_content, dict) and 'answer' in data_content:
                                answer = data_content['answer']
                                yield f"data: {json.dumps({'message': answer,'reference':data_content['reference']})}\n\n"
                    except json.JSONDecodeError:
                        continue
        else:
            yield f"data: {json.dumps({'error': 'Failed to get a valid response.'})}\n\n"
            return

    except requests.RequestException as e:
        yield f"data: {json.dumps({'error': f'Error connecting to LLM API: {str(e)}'})}\n\n"


def _response_ark():
    data = request.get_json()
    url = data.get('url')
    session_id = request.headers.get('Session-ID')

    if not url or not session_id:
        yield f"data: {json.dumps({'error': 'URL and Session ID are required'})}\n\n"
        return

    # Step 1: Scrape and process website content
    website_entry = process_website(url)

    # Step 2: Generate classification prompt and question
    classification_prompt = generate_classification_prompt(url, website_entry.keywords)
    question_prompt = f"Generate a multi-option question to test the user's interest about the website, {', '.join(website_entry.keywords), ' format the question and options using markdown format with checkboxes (- [ ]), only return the question and options'}."
    pgsqlUtilities.store_message(session_id, question_prompt, 'user')

    # Step 3: Prepare request for LLM to generate initial profile and question
    api_url = f"{Config().LLM_API_URL}"
    headers = {
        "Authorization": f"Bearer {Config().LLM_API_KEY}",  # Replace with your API key
        "Content-Type": "application/json"
    }
    data = {
        "model": Config().LLM_API_MODEL,
        "messages": [{"role": "user", "content": question_prompt}],
        "temperature": 0.1
    }

    try:
        # 使用火山飞舟进行非流式调用
        llm_response = requests.post(api_url, headers=headers, json=data)

        if llm_response.status_code == 200:
            llm_response_text = llm_response.content.decode('utf-8')
            llm_response_dict = json.loads(llm_response_text)
            answer = llm_response_dict['choices'][0]['message']['content']
            pgsqlUtilities.store_message(session_id, answer, 'assistant')
            yield f"data: {json.dumps({'message': answer})}\n\n"
        else:
            yield f"data: {json.dumps({'error': "failed to return answer"})}\n\n"

    except requests.RequestException as e:
        return {
            "error": f"Error connecting to LLM API: {str(e)}"
        }

@app.route('/api/v1/submit_answer', methods=['POST'])
def address_user_option():
    return Response(stream_with_context(_stream_response_chat()), content_type='text/event-stream')

def _stream_response_chat():
    data = request.get_json()
    options = data.get('selectedOptions')
    session_id = request.headers.get('Session-ID')

    if not options or not session_id:
        yield f"data: {json.dumps({'error': 'Options and Session ID are required'})}\n\n"
        return

    # Step 2: Define prompts for classification and question generation
    classification_prompt = "Based on the chat history, generate 8 keywords to classify the visitor's potential industry and interest, returning only comma-separated keywords."
    question_prompt = (
        f"User selected {options}. Based on the history, generate another multi-option question to refine the user's interest. format the question and options using markdown format with checkboxes (- [ ]). only return question and options"
    )
    pgsqlUtilities.store_message(session_id, question_prompt, 'user')

    # Step 3: Obtain conversation_id via API
    api_url = f"{Config().API_LINK_GET_CONVERSATION_ID}?user_id={session_id}"
    headers = {'Authorization': f'Bearer {Config().LLM_API_KEY}'}
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        conversation_id = response.json().get('data', {}).get('id')
        if not conversation_id:
            yield f"data: {json.dumps({'error': 'Invalid conversation ID from API'})}\n\n"
            return
    else:
        yield f"data: {json.dumps({'error': 'Failed to retrieve conversation ID'})}\n\n"
        return

    # Step 4: Send request to LLM API for question generation
    llm_request_data = {
        "conversation_id": conversation_id,
        "messages": pgsqlUtilities.get_chat_history(session_id),
        "quote": True
    }

    print(pgsqlUtilities.get_chat_history(session_id))

    try:
        llm_response = requests.post(Config().LLM_API_URL, headers=headers, json=llm_request_data, stream=True)
        if llm_response.status_code == 200:
            answer = ""
            for chunk in llm_response.iter_lines():
                if chunk:
                    try:
                        chunk_data = chunk.decode('utf-8')
                        if chunk_data.startswith('data:'):
                            chunk_data = chunk_data[len('data:'):]
                        line_data = json.loads(chunk_data)

                        # Process successful data
                        if line_data.get('retcode') == 0:
                            data_content = line_data['data']
                            if isinstance(data_content, bool) and data_content:
                                pgsqlUtilities.store_message(session_id, answer, 'assistant')
                                pgsqlUtilities.store_message(session_id, classification_prompt, 'user')
                                print(pgsqlUtilities.get_chat_history(session_id))
                                # Generate profile using classification prompt
                                profile_request_data = {
                                    "conversation_id": conversation_id,
                                    "messages": pgsqlUtilities.get_chat_history(session_id),
                                    "quote": True,
                                    "stream": False,
                                }
                                llm_response = requests.post(
                                    Config().LLM_API_URL, headers=headers, json=profile_request_data, stream=False
                                )

                                if llm_response.status_code == 200:
                                    line_data = llm_response.content

                                    if line_data.startswith(b'data:'):
                                        # print("yes")
                                        line_data = line_data[len(b'data:'):].decode('utf-8')
                                    # print(line_data)
                                    data_content = json.loads(line_data)
                                    if data_content.get('retcode') == 0:
                                        answer = data_content['data']['answer']
                                        yield f"data: {json.dumps({'profile': answer,'reference':data_content['data']['reference']})}\n\n"
                                        pgsqlUtilities.store_message(session_id, answer, 'assistant')
                                        return
                                return
                            elif isinstance(data_content, dict) and 'answer' in data_content:
                                answer = data_content['answer']
                                yield f"data: {json.dumps({'message': answer,'reference':data_content['reference']})}\n\n"
                    except json.JSONDecodeError:
                        continue
        else:
            yield f"data: {json.dumps({'error': 'Failed to get a valid response.'})}\n\n"
            return

    except requests.RequestException as e:
        yield f"data: {json.dumps({'error': f'Connection error: {str(e)}'})}\n\n"



if __name__ == '__main__':
    app.run(debug=True)
