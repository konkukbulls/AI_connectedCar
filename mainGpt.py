import datetime
from datetime import datetime, timedelta
import time

import os
import speech_recognition as sr
from gtts import gTTS
import playsound

import openai
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

import pandas as pd
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

import subprocess
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db



cred = credentials.Certificate("Your-Key-Path")
firebase_admin.initialize_app(cred,{'databaseURL':'https://ai-connectcar-default-rtdb.asia-southeast1.firebasedatabase.app/'})

# API Key 설정
os.environ["OPENAI_API_KEY"] = "Your-API-KEY"


myCar_num = "1493384"#내 차의 번호

general_location_lat = "0"
general_location_long = "0"
general_location1 = (general_location_lat, general_location_long)

# 템플릿 정의
template_State = """
chatGPT는 다음과 같은 동작을 수행한다.

1. 사용자가 제공하는 문장을 통해 다음을 구별한다
    1) 전방 차량(앞 차량, 다른 차량) 문제 발생 -> txState
    2) 사용자의 차량(내 차량) 문제 발생 -> myState
    3) gpt가 판단할 수 없는 problem이 입력시 -> normalState

    
2. txState인 경우와 myState인 경우와 normalState를 나누어 다음과 같은 동작을 수행한다.
    1) txState인 경우 다음 조건에 따라 사용자가 제공하는 문장에서 키워드를 뽑아 [txState, problem, Service, report]라는 리스트를 생성한다.
    chatGPT는 [txState, problem, Service, report]라는 단답으로만 대답하면 된다.(코드 작성 필요없음)
    색상은 영어로 출력한다.

    a. problem (alcohol, drowsy, overload, threat, breakdown, lightOff, fire, fuelleak, unknown)
        음주운전 -> alcohol
        졸음운전 -> drowsy
        과적, 짐을 많이 실었다 -> overload
        차량고장 -> breakdown
        라이트꺼짐 -> lightOff
        화재, 연기발생 -> fire
        연료누출 -> fuelleak

    b. Service (unknown)

    c. report (112, 119, unknown)
        problem이 threat, alcohol일때 -> 112
        problem이 fire, fuelleak일때 -> 119

    
    2) myState인 경우 다음 조건에 따라 사용자가 제공하는 문장에서 키워드를 뽑아 [myState, problem, Service, report]라는 리스트를 생성한다.
    chatGPT는 [myState, problem, Service, report]라는 단답으로만 대답하면 된다.(코드 작성 필요없음)
    
    a. problem (SUA, blackIce, potHole, roadDefects, lowBattery, noBattery, fuelShortage, noFuel, unknown)
        급발진 -> SUA
        블랙아이스, 미끄러짐 -> blackIce
        포트홀, 도로파임 -> potHole
        도로 공사, 도로 결함 -> roadDefects
        배터리 적음, 배터리 부족 -> lowBattery
        배터리 없음 -> noBattery
        연료 부족, 연료 적음 -> fuelShortage
        연료 없음 -> noFuel

    b. Service (gasStation, chargeStation)
        problem이 lowBattery일때 -> chargeStation
        problem이 fuelShortage일때 -> gasStation

    c. report (112, 119, 0800482000)
        problem이 급발진일때 -> 112
        problem이 blackIce, potHole, roadDefects, noBattery, noFuel일때 -> 0800482000

    3) normalState인경우 chatGPT는 [normalState, unknown, unknown, unknown]라는 단답으로만 대답하면 된다.(코드 작성 필요없음))
"""

template_txState = """
chatGPT는 최대한 간결하고 친절하게 답변한다.
chatGPT는 차량의 인포테인먼트 시스템이다.
제공된 리스트의 두번째 원소는 사용자가 탑승한 차량의 전방에 있는 차량의 "상태"를 의미한다. "상태"에 따라 사용자에게 적절한 답변을 제공한다.
신고는 운전자가 하는 것이 아니라 인포테인먼트 시스템이 자동적으로 진행한다.
예시는 다음과 같다.

1. "상태"가 drowsy인 경우
예시) '앞 차량 운전자에게 확인해볼게요. 알려주셔서 감사합니다'

2. "상태"가 overload인 경우
예시) '앞 차량이 과적 상태인지 확인해볼게요. 알려주셔서 감사합니다'

3. "상태"가 threat, alcohol인 경우
예시) '앞 차량이 안전한지 확인해볼게요. 알려주셔서 감사힙니다'

4. "상태" breakdown, lightOff인 경우
예시 ) '앞 차량에게 해당 사항에 대한 알림을 보낼게요.'

5. "상태"가 fire, fuelleak인 경우
예시) '앞 차량이 안전한지 확인할게요. 운전자님도 해당 차량을 조심하여 안전운전하세요/조심히 비켜가세요.
"""

template_myState = """
chatGPT는 최대한 간결하고 친절하게 답변한다.
chatGPT는 차량의 인포테인먼트 시스템이다.
제공된 리스트의 가장 마지막 원소는 사용자가 탑승한 차량의 상태를 의미한다. "상태"에 따라 사용자에게 적절한 답변을 제공한다.
신고는 운전자가 하는 것이 아니라 인포테인먼트 시스템이 자동적으로 진행한다.
예시는 다음과 같다.

1. "상태"가 SUA인 경우
예시) '주변차량 운전자에게 경고를 전달할게요.'
이때 급발진 시 대처방안에 대해 운전자에게 차분히 전달한다.

2. "상태"가 blackIce, potHole, roadDefects인 경우
예시) '주변차량 운전자에게 경고를 전달할게요.'

3. "상태"가 noBattery, noFuel인 경우
예시) '안전한 곳에 차량을 정차하여주세요.'

4. "상태"가 lowBattery인 경우
예시) 충전이 필요하시겠네요.

5. "상태"가 fuelShortage인 경우
예시) 주유가 필요하시겠네요.
"""

templete_normalState = """
gpt는 현재 자동차의 인포테인먼트 시스템이다.
사용자의 요청에 친절하게 응답한다.
간결하게 답변하면 좋다.


"""


template판정 = """
사용자의 메시지를 통해 yes 또는 no로만 판단한다.

1. "아니", "필요없어", "싫어" 등의 부정표현 -> no
2. 이외의 경우 -> yes
"""
general_ref_my = db.reference(f'general/{myCar_num}/problem')
general_ref_my_location = db.reference(f'general/{myCar_num}/location')
general_ref_my_before = db.reference(f'general/{myCar_num}')
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
    
def gps_info(lat,lon):
    general_location_lat = lat
    general_location_long = lon
    general_location = (general_location_lat, general_location_long)

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
    greeting = "대기모드입니다"
    print(greeting)
    Text_input(general_ref_my,greeting,"rxText")
    
    text_to_voice(greeting)
   
    return voice_to_text()

def handle_exit():
    exit_message = "chatGPT를 종료합니다."
    print(exit_message)
    Text_input(general_ref_my,exit_message,"rxText")
    text_to_voice(exit_message)

def process_chatgpt_request(chat, template, user_input):
    system_message = SystemMessage(content=template)
    user_message = HumanMessage(content=user_input)
    response = chat.invoke([system_message, user_message])
    return response.content

def get_closest_charging_station(gps_car):
    # https://www.data.go.kr/data/15102458/fileData.do
    # CSV 파일 경로
    file_path = '한국전력공사_전기차충전소위경도_20240502.csv'
    
    # CSV 파일 로드
    charging_data = pd.read_csv(file_path, encoding='UTF-8')
    
    # 거리 계산 함수
    def calculate_distance(row):
        charging_station_coords = (row['위도'], row['경도'])
        return geodesic(gps_car, charging_station_coords).kilometers
    
    # 거리 계산
    charging_data['distance'] = charging_data.apply(calculate_distance, axis=1)
    
    # 가장 가까운 충전소 찾기
    closest_charging_station = charging_data.loc[charging_data['distance'].idxmin()]
    return closest_charging_station[['충전소명', '충전소주소', '위도', '경도', 'distance']]

# Nominatim 지오코더 초기화
geolocator = Nominatim(user_agent="geoapiExercises")

def geocode_address(address):
    try:
        location = geolocator.geocode(address)
        if location:
            return (location.latitude, location.longitude)
    except:
        return None

def get_closest_gas_station(gps_car):
    # https://www.data.go.kr/data/15128244/fileData.do
    # CSV 파일 경로
    file_path = '한국석유공사_인천지역 주유소 위치 현황_20240530 위도 경도 추가.csv'
    
    # CSV 파일 로드
    charging_data = pd.read_csv(file_path, encoding='cp949')
    
    # 거리 계산 함수
    def calculate_distance(row):
        charging_station_coords = (row['위도'], row['경도'])
        return geodesic(gps_car, charging_station_coords).kilometers
    
    # 거리 계산
    charging_data['distance'] = charging_data.apply(calculate_distance, axis=1)
    
    # 가장 가까운 충전소 찾기
    closest_charging_station = charging_data.loc[charging_data['distance'].idxmin()]
    return closest_charging_station[['상호명', '위도', '경도', 'distance']]


system_message_normal = SystemMessage(content=templete_normalState)
chatnormal = ChatOpenAI(model_name='gpt-4o', temperature=0.5)

def chatgpt_response(prompt, history):
    messages = [
        system_message_normal,
        *history,
        HumanMessage(content=prompt)
    ]
    response = chatnormal.invoke(messages)
    return response

def main():
    chat = ChatOpenAI(model_name='gpt-4o', temperature=0.5)
    # https://colab.research.google.com/drive/1uLeXxHLwCPoDgCznExw_iXewWAbnt4a9?usp=sharing#scrollTo=EtyIuMxgwxVu
    
    while True:
       
        print("checking")
        current_data_my_before = general_ref_my_before.get()

        if current_data_my_before.get('trigger') == "on":
            current_data_my = general_ref_my.get()
            txState = current_data_my.get('txState') 
            print("txstate:", txState)
            general_ref_my_before.update({'trigger': 'off'})  # 'off'에서 'on'으로 수정
            general_ref_my.update({'txState': ""})
            subprocess.run(["python", "keyword.py", myCar_num, txState])
            user_input = prompt_greeting()
        else :
            user_input = prompt_greeting()
        if '굿바이' in user_input:
            handle_exit()
            break
        if "GPT" in user_input:
            Text = "GPT 모드입니다."
            print(Text)
            Text_input(general_ref_my,Text,"rxText")
            text_to_voice(Text)
            
            while True:
                now = datetime.now()
                after_5sec = now + timedelta(seconds=5)
                current_data_my_before = general_ref_my_before.get()
                if current_data_my_before.get('trigger') == "on":
                    current_data_my = general_ref_my.get()
                    txState = current_data_my.get('txState') 
                    print("txstate:", txState)
                    general_ref_my_before.update({'trigger': 'off'})  # 'off'에서 'on'으로 수정
                    general_ref_my.update({'txState': ""})
                    subprocess.run(["python", "키워드 대화.py", myCar_num, txState])

                prompt = "무엇을 도와드릴까요?"
                print(prompt)
                Text_input(general_ref_my,prompt,"rxText")
                text_to_voice(prompt)
                user_input = voice_to_text()
                print(user_input)

                if not user_input and datetime.now() > after_5sec:
                    Text = "5초 동안 아무 응답이 없어 chatGPT를 종료합니다. 대기 모드로 돌아갑니다."
                    print(Text)
                    Text_input(general_ref_my,Text,"rxText")
                    text_to_voice(Text)
                    time.sleep(1)
                    break
                
                Text = process_chatgpt_request(chat, template_State, user_input)
                print(Text)
                
                if 'txState' in Text:
                    import picCap
                    picCap
                    import ocr_test
                    OCR_car_num = ocr_test.result_return()
                    print(OCR_car_num)
                    
                    general_ref = db.reference(f'general/{OCR_car_num}/problem')
                    current_data = general_ref.get()
                    general_ref_before = db.reference(f'general/{OCR_car_num}')
                    current_data_before = general_ref_before.get()
                    pared_text =  [item.strip() for item in Text[1:-1].split(',')]
                    
                    print(pared_text[1])
                    
                    State_input(general_ref,pared_text[1],"txState")
                    State_input(general_ref_before,"on","trigger")
                    txText = process_chatgpt_request(chat, template_txState, Text)
                    print(txText)
                    Text_input(general_ref_my,txText,"rxText")
                    text_to_voice(txText)

                    if 'threat' in Text:
                        txText = "경찰서에 신고할까요?"
                        print(txText)
                        Text_input(general_ref_my,txText,"rxText")
                        text_to_voice(txText)
                        sys_msg판정 = SystemMessage(content=template판정)
                        user_input판정 = voice_to_text()
                        user_msg판정 = HumanMessage(content=user_input판정)

                        print(user_input판정)
                        aimsg판정 = chat.invoke([sys_msg판정, user_msg판정])
                        txText = "알겠습니다."
                        print(txText)
                        Text_input(general_ref_my,txText,"rxText")
                        text_to_voice(txText)
                    
                        if 'yes' in aimsg판정.content:
                            txText = "경찰서에 신고하겠습니다."
                            print(txText)
                            Text_input(general_ref_my,txText,"rxText")
                            text_to_voice(txText)
                            Text = "[txState, threat, unknown, 112]"
                            print(Text)
                            pared_text =  [item.strip() for item in Text[1:-1].split(',')]
                            if pared_text[3] != "unkown":
                                if pared_text[3] == "112":
                                    general_ref_my_report.update({'112': 1})
                                    general_ref_my_report.update({'112': 0})
                                if pared_text[3] == "119":
                                    general_ref_my_report.update({'119': 1})
                                    general_ref_my_report.update({'119': 0})
                                if pared_text[3] == "0800482000":
                                    general_ref_my_report.update({'0800482000': 1})
                                    general_ref_my_report.update({'0800482000': 0})
                            break


                    elif 'alcohol' in Text:
                        txText = "경찰서에 신고할까요?"
                        print(txText)
                        Text_input(general_ref_my,txText,"rxText")
                        text_to_voice(txText)
                        sys_msg판정 = SystemMessage(content=template판정)
                        user_input판정 = voice_to_text()
                        user_msg판정 = HumanMessage(content=user_input판정)

                        print(user_input판정)
                        aimsg판정 = chat.invoke([sys_msg판정, user_msg판정])
                        txText = "알겠습니다."
                        print(txText)
                        Text_input(general_ref_my,txText,"rxText")
                        text_to_voice(txText)
                    
                        if 'yes' in aimsg판정.content:
                            txText = "경찰서에 신고하겠습니다."
                            print(txText)
                            Text_input(general_ref_my,txText,"rxText")
                            text_to_voice(txText)
                            Text = "[txState, alcohol, unknown, 112]"
                            print(Text)
                            pared_text =  [item.strip() for item in Text[1:-1].split(',')]
                            if pared_text[3] != "unkown":
                                if pared_text[3] == "112":
                                    general_ref_my_report.update({'112': 1})
                                    general_ref_my_report.update({'112': 0})
                                if pared_text[3] == "119":
                                    general_ref_my_report.update({'119': 1})
                                    general_ref_my_report.update({'119': 0})
                                if pared_text[3] == "0800482000":
                                    general_ref_my_report.update({'0800482000': 1})
                                    general_ref_my_report.update({'0800482000': 0})
                            break

                    
                        
                    elif 'fire' in Text:
                        txText = "소방서에 신고할까요?"
                        print(txText)
                        Text_input(general_ref_my,txText,"rxText")
                        text_to_voice(txText)
                        sys_msg판정 = SystemMessage(content=template판정)
                        user_input판정 = voice_to_text()
                        user_msg판정 = HumanMessage(content=user_input판정)

                        print(user_input판정)
                        aimsg판정 = chat.invoke([sys_msg판정, user_msg판정])
                        txText = "알겠습니다."
                        print(txText)
                        Text_input(general_ref_my,txText,"rxText")
                        text_to_voice(txText)
                    
                        if 'yes' in aimsg판정.content:
                            txText = "소방서에 신고하겠습니다."
                            print(txText)
                            Text_input(general_ref_my,txText,"rxText")
                            text_to_voice(txText)
                            Text = "[txState, fuelleak, unknown, 119]"
                            print(Text)
                            pared_text =  [item.strip() for item in Text[1:-1].split(',')]
                            if pared_text[3] != "unkown":
                                if pared_text[3] == "112":
                                    general_ref_my_report.update({'112': 1})
                                    general_ref_my_report.update({'112': 0})
                                if pared_text[3] == "119":
                                    general_ref_my_report.update({'119': 1})
                                    general_ref_my_report.update({'119': 0})
                                if pared_text[3] == "0800482000":
                                    general_ref_my_report.update({'0800482000': 1})
                                    general_ref_my_report.update({'0800482000': 0})
                            break
                    

                    elif 'fuelleak' in Text:
                        txText = "소방서에 신고할까요?"
                        print(txText)
                        Text_input(general_ref_my,txText,"rxText")
                        text_to_voice(txText)
                        sys_msg판정 = SystemMessage(content=template판정)
                        user_input판정 = voice_to_text()
                        user_msg판정 = HumanMessage(content=user_input판정)

                        print(user_input판정)
                        aimsg판정 = chat.invoke([sys_msg판정, user_msg판정])
                        txText = "알겠습니다."
                        print(txText)
                        Text_input(general_ref_my,txText,"rxText")
                        text_to_voice(txText)
                    
                        if 'yes' in aimsg판정.content:
                            txText = "소방서에 신고하겠습니다."
                            print(txText)
                            Text_input(general_ref_my,txText,"rxText")
                            text_to_voice(txText)
                            Text = "[txState, fuelleak, unknown, 119]"
                            print(Text)
                            pared_text =  [item.strip() for item in Text[1:-1].split(',')]
                            if pared_text[3] != "unkown":
                                if pared_text[3] == "112":
                                    general_ref_my_report.update({'112': 1})
                                    general_ref_my_report.update({'112': 0})
                                if pared_text[3] == "119":
                                    general_ref_my_report.update({'119': 1})
                                    general_ref_my_report.update({'119': 0})
                                if pared_text[3] == "0800482000":
                                    general_ref_my_report.update({'0800482000': 1})
                                    general_ref_my_report.update({'0800482000': 0})
                            break


                elif 'myState' in Text:
                    pared_text =  [item.strip() for item in Text[1:-1].split(',')]
                    
                    print(pared_text[1])
                    print(pared_text[3])
                    
                    Text_input(general_ref_my,pared_text[1],"myState")
                    myText = process_chatgpt_request(chat, template_myState, Text)
                    print(myText)
                    Text_input(general_ref_my,myText,"myText")
                    text_to_voice(myText)
                    
                    
                    # 배터리 부족 상태인 경우 충전소 정보 제공
                    if 'lowBattery' in Text:
                        myText = "근처 충전소 정보를 알려드릴까요?"
                        print(myText)
                        Text_input(general_ref_my,myText,"myText")
                        text_to_voice(myText)
                        sys_msg판정 = SystemMessage(content=template판정)
                        user_input판정 = voice_to_text()
                        user_msg판정 = HumanMessage(content=user_input판정)

                        print(user_input판정)
                        aimsg판정 = chat.invoke([sys_msg판정, user_msg판정])
                        myText = "알겠습니다."
                        print(myText)
                        Text_input(general_ref_my,myText,"myText")
                        text_to_voice(myText)                                     


                        if 'yes' in aimsg판정.content:
                            current_data_my_location = general_ref_my_location.get()
                            lat = current_data_my_location.get('lat')
                            lon = current_data_my_location.get('long')
                            print(lat)
                            print(lon)
                            general_location=(lat,lon)
                            gps_info(lat,lon)
                            charging_station_info = get_closest_charging_station(general_location)
                            chargeStation_name = charging_station_info['충전소명']
                            chargeStation_location_lat = charging_station_info['위도']#"{:.5f}".format(charging_station_info['위도'])
                            chargeStation_location_long = charging_station_info['경도']#"{:.5f}".format(charging_station_info['경도'])
                            print(chargeStation_name)
                            print(chargeStation_location_lat)
                            print(chargeStation_location_long)
                            State_input(general_ref_chargeName,chargeStation_name,"name")
                            State_input(general_ref_charge,chargeStation_location_lat,"lat")
                            State_input(general_ref_charge,chargeStation_location_long,"long")
                            
                            
                            myText = f"가장 가까운 충전소는 {charging_station_info['충전소명']}이며, 주소는 {charging_station_info['충전소주소']}입니다. 거리는 약 {charging_station_info['distance']:.2f} km입니다."
                            print(myText)
                            Text_input(general_ref_my,myText,"myText")
                            

                            text_to_voice(myText)
                            Text_input(general_ref_chargeName,chargeStation_name,"name")
                            Text_input(general_ref_charge,chargeStation_location_lat,"lat")
                            Text_input(general_ref_charge,chargeStation_location_long,"long")
                            
                            
                            break


                    # 연료 부족 상태인 경우 주유소 정보 제공
                    elif 'fuelShortage' in Text:
                        myText = "근처 주유소 정보를 알려드릴까요?"
                        print(myText)
                        Text_input(general_ref_my,myText,"myText")
                        text_to_voice(myText)
                        sys_msg판정 = SystemMessage(content=template판정)
                        user_input판정 = voice_to_text()
                        user_msg판정 = HumanMessage(content=user_input판정)

                        print(user_input판정)
                        aimsg판정 = chat.invoke([sys_msg판정, user_msg판정])
                        myText = "알겠습니다."
                        print(myText)
                        Text_input(general_ref_my,myText,"myText")
                        text_to_voice(myText)


                        if 'yes' in aimsg판정.content:
                            current_data_my_location = general_ref_my_location.get()
                            lat = current_data_my_location.get('lat')
                            lon = current_data_my_location.get('long')
                            print(lat)
                            print(lon)
                            general_location=(lat,lon)
                            
                            
                            gps_info(lat,lon)
                            gas_station_info = get_closest_gas_station(general_location)
                            gasStation_name = gas_station_info['상호명']
                            gasStation_location_lat = gas_station_info['위도']#"{:.6f}".format(gas_station_info['위도'])
                            gasStaiton_location_long = gas_station_info['경도']#"{:.6f}".format(gas_station_info['경도'])
                            print(gasStation_name)
                            print(gasStation_location_lat)
                            print(gasStaiton_location_long)
                            State_input(general_ref_gasName,gasStation_name,"name")
                            State_input(general_ref_gas,gasStation_location_lat,"lat")
                            State_input(general_ref_gas,gasStaiton_location_long,"long")
                            
                            
                            myText = f"가장 가까운 주유소는 {gas_station_info['상호명']}이며, 거리는 약 {gas_station_info['distance']:.2f} km입니다."
                            print(myText)
                            Text_input(general_ref_my,myText,"myText")
                            Text_input(general_ref_gas,gasStation_location_lat,"lat")
                            Text_input(general_ref_gas,gasStaiton_location_long,"long")
                            Text_input(general_ref_gasName,gasStation_name,"name")
                            
                            text_to_voice(myText)
                            

                            break
                    
                    elif 'SUA' in Text:
                        myText = "경찰서에 신고할까요?"
                        print(myText)
                        Text_input(general_ref_my,myText,"myText")
                        text_to_voice(myText)
                        sys_msg판정 = SystemMessage(content=template판정)
                        user_input판정 = voice_to_text()
                        user_msg판정 = HumanMessage(content=user_input판정)

                        print(user_input판정)
                        aimsg판정 = chat.invoke([sys_msg판정, user_msg판정])
                        myText = "알겠습니다."
                        print(myText)
                        Text_input(general_ref_my,myText,"myText")
                        text_to_voice(myText)
                    
                        if 'yes' in aimsg판정.content:
                            myText = "경찰서에 신고하겠습니다."
                            print(myText)
                            Text_input(general_ref_my,myText,"myText")
                            text_to_voice(myText)
                            Text = "[myState, SUA, unknown, 112]"
                            print(Text)
                            pared_text =  [item.strip() for item in Text[1:-1].split(',')]
                            if pared_text[3] != "unkown":
                                if pared_text[3] == "112":
                                    general_ref_my_report.update({'112': 1})
                                    general_ref_my_report.update({'112': 0})
                                if pared_text[3] == "119":
                                    general_ref_my_report.update({'119': 1})
                                    general_ref_my_report.update({'119': 0})
                                if pared_text[3] == "0800482000":
                                    general_ref_my_report.update({'0800482000': 1})
                                    general_ref_my_report.update({'0800482000': 0})
                            break
                                   
                    elif 'blackIce' in Text or 'potHole' in Text or 'roadDefects' in Text:
                        myText = "도로교통공단에 신고할까요?"
                        print(myText)
                        Text_input(general_ref_my,myText,"myText")
                        text_to_voice(myText)
                        sys_msg판정 = SystemMessage(content=template판정)
                        user_input판정 = voice_to_text()
                        user_msg판정 = HumanMessage(content=user_input판정)

                        print(user_input판정)
                        aimsg판정 = chat.invoke([sys_msg판정, user_msg판정])
                        myText = "알겠습니다."
                        print(myText)
                        Text_input(general_ref_my,myText,"myText")
                        text_to_voice(myText)
                    
                        if 'yes' in aimsg판정.content:
                            myText = "도로교통공단에 신고하겠습니다."
                            print(myText)
                            Text_input(general_ref_my,myText,"myText")
                            text_to_voice(myText)
                            Text = "[myState, blackIce, unknown, 0800482000]"
                            print(Text)
                            pared_text =  [item.strip() for item in Text[1:-1].split(',')]
                            if pared_text[3] != "unkown":
                                if pared_text[3] == "112":
                                    general_ref_my_report.update({'112': 1})
                                    general_ref_my_report.update({'112': 0})
                                if pared_text[3] == "119":
                                    general_ref_my_report.update({'119': 1})
                                    general_ref_my_report.update({'119': 0})
                                if pared_text[3] == "0800482000":
                                    general_ref_my_report.update({'0800482000': 1})
                                    general_ref_my_report.update({'0800482000': 0})
                            break

                    elif 'roadDefects' in Text:
                        myText = "도로교통공단에 신고할까요?"
                        print(myText)
                        Text_input(general_ref_my,myText,"myText")
                        text_to_voice(myText)
                        sys_msg판정 = SystemMessage(content=template판정)
                        user_input판정 = voice_to_text()
                        user_msg판정 = HumanMessage(content=user_input판정)

                        print(user_input판정)
                        aimsg판정 = chat.invoke([sys_msg판정, user_msg판정])
                        myText = "알겠습니다."
                        print(myText)
                        Text_input(general_ref_my,myText,"myText")
                        text_to_voice(myText)
                    
                        if 'yes' in aimsg판정.content:
                            myText = "도로교통공단에 신고하겠습니다."
                            print(myText)
                            Text_input(general_ref_my,myText,"myText")
                            text_to_voice(myText)
                            Text = "[myState, roadDefects, unknown, 0800482000]"
                            print(Text)
                            pared_text =  [item.strip() for item in Text[1:-1].split(',')]
                            if pared_text[3] != "unkown":
                                if pared_text[3] == "112":
                                    general_ref_my_report.update({'112': 1})
                                    general_ref_my_report.update({'112': 0})
                                if pared_text[3] == "119":
                                    general_ref_my_report.update({'119': 1})
                                    general_ref_my_report.update({'119': 0})
                                if pared_text[3] == "0800482000":
                                    general_ref_my_report.update({'0800482000': 1})
                                    general_ref_my_report.update({'0800482000': 0})
                            break
                    
                    elif 'noBattery' in Text:
                        myText = "도로교통공단에 신고할까요?"
                        print(myText)
                        Text_input(general_ref_my,myText,"myText")
                        text_to_voice(myText)
                        sys_msg판정 = SystemMessage(content=template판정)
                        user_input판정 = voice_to_text()
                        user_msg판정 = HumanMessage(content=user_input판정)

                        print(user_input판정)
                        aimsg판정 = chat.invoke([sys_msg판정, user_msg판정])
                        myText = "알겠습니다."
                        print(myText)
                        Text_input(general_ref_my,myText,"myText")
                        text_to_voice(myText)
                    
                        if 'yes' in aimsg판정.content:
                            myText = "도로교통공단에 신고하겠습니다."
                            print(myText)
                            Text_input(general_ref_my,myText,"myText")
                            text_to_voice(myText)
                            Text = "[myState, noBattery, unknown, 0800482000]"
                            print(Text)
                            pared_text =  [item.strip() for item in Text[1:-1].split(',')]
                            if pared_text[3] != "unkown":
                                if pared_text[3] == "112":
                                    general_ref_my_report.update({'112': 1})
                                    general_ref_my_report.update({'112': 0})
                                if pared_text[3] == "119":
                                    general_ref_my_report.update({'119': 1})
                                    general_ref_my_report.update({'119': 0})
                                if pared_text[3] == "0800482000":
                                    general_ref_my_report.update({'0800482000': 1})
                                    general_ref_my_report.update({'0800482000': 0})
                            break

                    elif 'noFuel' in Text:
                        myText = "도로교통공단에 신고할까요?"
                        print(myText)
                        Text_input(general_ref_my,myText,"myText")
                        text_to_voice(myText)
                        sys_msg판정 = SystemMessage(content=template판정)
                        user_input판정 = voice_to_text()
                        user_msg판정 = HumanMessage(content=user_input판정)

                        print(user_input판정)
                        aimsg판정 = chat.invoke([sys_msg판정, user_msg판정])
                        myText = "알겠습니다."
                        print(myText)
                        Text_input(general_ref_my,myText,"myText")
                        text_to_voice(myText)
                    
                        if 'yes' in aimsg판정.content:
                            myText = "도로교통공단에 신고하겠습니다."
                            print(myText)
                            Text_input(general_ref_my,myText,"myText")
                            text_to_voice(myText)
                            Text = "[myState, noFuel, unknown, 0800482000]"
                            print(Text)
                            pared_text =  [item.strip() for item in Text[1:-1].split(',')]
                            if pared_text[3] != "unkown":
                                if pared_text[3] == "112":
                                    general_ref_my_report.update({'112': 1})
                                    general_ref_my_report.update({'112': 0})
                                if pared_text[3] == "119":
                                    general_ref_my_report.update({'119': 1})
                                    general_ref_my_report.update({'119': 0})
                                if pared_text[3] == "0800482000":
                                    general_ref_my_report.update({'0800482000': 1})
                                    general_ref_my_report.update({'0800482000': 0})
                            break
                

                elif 'normalState' in Text:
                    historynormal = []
                    response = chatgpt_response(user_input, historynormal)
                    normalText = response.content
                    print(normalText)
                    print("trigger")
                    Text_input(general_ref_my,normalText,"nmText")
                    text_to_voice(normalText)
                    historynormal.append(HumanMessage(content=user_input))
                    historynormal.append(AIMessage(content=normalText))


                    while True:
                        user_input = voice_to_text()

                        sys_msg판정 = SystemMessage(content=template판정)
                        user_input판정 = user_input
                        user_msg판정 = HumanMessage(content=user_input판정)

                        print(user_input판정)
                        aimsg판정 = chat.invoke([sys_msg판정, user_msg판정])
                    
                        if 'no' in aimsg판정.content:
                            break

                        response = chatgpt_response(user_input, historynormal)
                        normalText = response.content
                        print(normalText)
                        Text_input(general_ref_my,normalText,"nmText")
                        text_to_voice(normalText)
                        historynormal.append(HumanMessage(content=user_input))
                        historynormal.append(AIMessage(content=normalText))



                    break

if __name__ == "__main__":
    main()
