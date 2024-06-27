import datetime
from datetime import datetime, timedelta
import time

import os
import speech_recognition as sr
from gtts import gTTS
import playsound

import openai
import requests
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

import googlemaps
import pandas as pd
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from geopy import distance

import osmnx as ox
import networkx as nx

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("Your-Key-PATH")
firebase_admin.initialize_app(cred,{'databaseURL':'https://ai-connectcar-default-rtdb.asia-southeast1.firebasedatabase.app/'})

myCar_num = "1190987"

# API Key 설정
os.environ["OPENAI_API_KEY"] = "Your-Key-PATH"

# 차량 gps
emergency_location_lat = 37.5416
emergency_location_long = 127.0785

emergency_location = (emergency_location_lat, emergency_location_long)
general_location = (37.5416, 127.0785) # 테스트를 위한 임의값

general_ref_my = db.reference(f'emergency/{myCar_num}/problem')
general_ref_my_before = db.reference(f'emergency/{myCar_num}')
general_ref_my_report = db.reference(f'general/{myCar_num}/report')
general_ref_charge = db.reference(f'general/{myCar_num}/Service/chargeStation/location')
general_ref_chargeName = db.reference(f'general/{myCar_num}/Service/chargeStation')
general_ref_gas = db.reference(f'general/{myCar_num}/Service/gasStation/location')
general_ref_gasName = db.reference(f'general/{myCar_num}/Service/gasStation')
current_data_my = general_ref_my.get()
current_data_my_before = general_ref_my_before.get()



def Text_input(target,text,state):
    new_rxText = text
    target.update({state: new_rxText})
    target.update({state: ""})

def State_input(target,text,state):
    new_txState = text
    target.update({state: new_txState})
    


# 템플릿 정의
template_emergency = """
chatGPT는 다음과 같은 동작을 수행한다.

    사용자가 제공하는 문장에서 키워드를 뽑아 [emergency, egState]라는 리스트를 생성한다.
    chatGPT는 [emergency, moveOver] 또는 [emergency, intersection]이라는 단답으로만 대답하면 된다.(코드 작성 필요없음)

    egState는 다음 둘 중에 하나를 선택한다.
    a. moveOver (사용자가 길터주기에 대한 요청을 했을 경우. 앞에 차들 비켜줘, 길이 막혀있어, 빨리 가야해)
    b. intersection (사용자가 교차로 경고에 대한 요청을 했을 경우. 교차로 경고 해줘, 교차로에 차들이 많아)
"""

template판정 = """
사용자의 메시지를 통해 yes 또는 no로만 판단한다.

1. "그래", "좋아", "네", "오케이" 등의 긍정표현 -> yes
2. "아니", "필요없어", "싫어" 등의 부정표현 -> no
"""

def text_to_voice(text):
    tts = gTTS(text=text, lang='ko')
    filename = 'voice.mp3'
    tts.save(filename)
    playsound.playsound(filename)
    os.remove(filename)

def voice_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("말씀해 주세요: ")
        audio = recognizer.listen(source)
        try:
            return recognizer.recognize_google(audio, language="ko-KR")
        except Exception as e:
            print("Exception: " + str(e))
            return ""

def prompt_greeting():
    greeting = "대기모드입니다."
    print(greeting)
    Text_input(general_ref_my,greeting,"egText")
    text_to_voice(greeting)
    return voice_to_text()

def handle_exit():
    exit_message = "chatGPT를 종료합니다."
    print(exit_message)
    text_to_voice(exit_message)

def process_chatgpt_request(chat, template, user_input):
    system_message = SystemMessage(content=template)
    user_message = HumanMessage(content=user_input)
    response = chat.invoke([system_message, user_message])
    return response.content

def get_closest_intersection(user_location):
    # 주어진 위치를 중심으로 OSMnx 그래프를 다운로드
    G = ox.graph_from_point(user_location, dist=1000, network_type='all')
    # 사용자의 위치와 가장 가까운 노드를 찾음
    nearest_intersection = ox.distance.nearest_nodes(G, user_location[1], user_location[0])
    # 가장 가까운 노드의 위치 출력
    nearest_intersection_point = (G.nodes[nearest_intersection]['y'], G.nodes[nearest_intersection]['x'])
    # Nominatim 지오코더 초기화
    geolocator = Nominatim(user_agent="geoapiExercises")
    return nearest_intersection_point


def main():
    chat = ChatOpenAI(model_name='gpt-4o', temperature=0.5)
    # https://colab.research.google.com/drive/1uLeXxHLwCPoDgCznExw_iXewWAbnt4a9?usp=sharing#scrollTo=EtyIuMxgwxVu

    while True:
        user_input = prompt_greeting()
        if '굿바이' in user_input:
            handle_exit()
            break

        if "GPT" in user_input:
            print("GPT 모드입니다.")
            Text_input(general_ref_my,"GPT 모드입니다","egText")
            text_to_voice("GPT 모드입니다.")
            
            while True:
                
                prompt = "무엇을 도와드릴까요?"
                print(prompt)
                Text_input(general_ref_my,prompt,"egText")
                text_to_voice(prompt)
                user_input = voice_to_text()
                print(user_input)
                
                response = process_chatgpt_request(chat, template_emergency, user_input)
                print(response)
                

                if 'moveOver' in response:
                    egText = "길터주기를 시행하겠습니다."
                    print(egText)
                    Text_input(general_ref_my,egText,"egText")
                    text_to_voice(egText)
                    import picCap
                    picCap
                    import ocr_test

                    OCR_car_num = ocr_test.result_return()
                    print(OCR_car_num)
                

                    general_ref = db.reference(f'general/{OCR_car_num}/problem')
                    current_data = general_ref.get()
                    general_ref_before = db.reference(f'general/{OCR_car_num}')
                    current_data_before = general_ref_before.get()
                    pared_text =  [item.strip() for item in response[1:-1].split(',')]
                    State_input(general_ref,pared_text[1],"txState")
                    State_input(general_ref_before,"on","trigger")
                    
                    # 길터주기(홍해) 시퀀스 시행
                    break

                elif 'intersection' in response:
                    egText = "교차로 경고를 시행하겠습니다."
                    print(egText)
                    Text_input(general_ref_my,egText,"egText")
                    text_to_voice(egText)
                    intersectionGPS = get_closest_intersection(emergency_location)
                    print(intersectionGPS)

                    intersectionGPS_lat = intersectionGPS[1]
                    intersectionGPS_long = intersectionGPS[0]

                    import picCap
                    picCap
                    import ocr_test

                    OCR_car_num = ocr_test.result_return()
                    print(OCR_car_num)

                    general_ref = db.reference(f'general/{OCR_car_num}/problem')
                    current_data = general_ref.get()
                    general_ref_before = db.reference(f'general/{OCR_car_num}')
                    current_data_before = general_ref_before.get()
                    pared_text =  [item.strip() for item in response[1:-1].split(',')]
                    print(pared_text[1])
                    State_input(general_ref,pared_text[1],"txState")
                    State_input(general_ref_before,"on","trigger")

                    break

if __name__ == "__main__":
    main()
