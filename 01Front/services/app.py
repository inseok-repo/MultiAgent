import streamlit as st
import random, os
import time
import requests
import uuid
from dotenv import load_dotenv
load_dotenv()

random_uuid = uuid.uuid4()
#print(random_uuid)

# 세션 상태 유지용
if "session_id" not in st.session_state:
    st.session_state["session_id"] = random_uuid

st.write(f"uuid: {st.session_state['session_id']}")

API_URL = "http://35.209.240.229:8001/api/workflow"

st.title("'Multi Agent for MY DATA'")

# 채팅 히스토리 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 기존 메시지 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력
if prompt := st.chat_input("여기에 질문을 입력하세요"):
    # 사용자 메시지 히스토리 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    last_user_message = None
    for message in reversed(st.session_state.messages):
        if message["role"] == "user":
            last_user_message = message["content"]
            break

    #headers = {"Content-Type": "application/json"}
    data = {
        #"messages": [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        "message": last_user_message
    }

    with st.chat_message("assistant"):
        assistant_response_placeholder = st.empty()  
        typing_placeholder = st.empty() 
        typing_placeholder.markdown("답변을 생성하고 있습니다..")

    # 스트림으로 응답 수신
    response = requests.post(API_URL, json=data, stream=True)

    response_text = ""
    if response.status_code == 200:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                decoded_chunk = chunk.decode('utf-8')
                response_text += decoded_chunk
                
                assistant_response_placeholder.markdown(f"<p>{response_text}</p>", unsafe_allow_html=True)
        typing_placeholder.empty()
    else:
        st.error("Failed to get response from the server.")

    # 히스토리에 추가
    st.session_state.messages.append({"role": "assistant", "content": response_text})