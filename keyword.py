import datetime
from datetime import datetime, timedelta
import time
import os

# 음성인식 관련 모듈
import speech_recognition as sr
from gtts import gTTS
import playsound

# chatGPT 관련 모듈
import openai

# langchain 관련 모듈
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory

# google map 관련 모듈
import requests
import googlemaps
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

import sys
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("Your-Key-Path")
firebase_admin.initialize_app(cred,{'databaseURL':'https://ai-connectcar-default-rtdb.asia-southeast1.firebasedatabase.app/'})





myCar_num = sys.argv[1]
myCar_num = "1493384"#내 차의 번호
keywords = sys.argv[2]

general_ref_my_location = db.reference(f'general/{myCar_num}/location')
general_ref_my_before = db.reference(f'general/{myCar_num}')
general_ref_my = db.reference(f'general/{myCar_num}/problem')
general_ref_my_before = db.reference(f'general/{myCar_num}')
general_ref_my_report = db.reference(f'general/{myCar_num}/report')
general_ref_restArea = db.reference(f'general/{myCar_num}/Service/restArea/location')
general_ref_restName = db.reference(f'general/{myCar_num}/Service/restArea')
current_data_my = general_ref_my.get()
current_data_my_before = general_ref_my_before.get()




current_data_my_location = general_ref_my_location.get()
lat = current_data_my_location.get('lat')
    
lon = current_data_my_location.get('long')

# 차량 gps (사용자의 위치)
general_location_lat = lat
general_location_long = lon
general_location = (general_location_lat, general_location_long) # 차량 gps 받아와서 수정



def Text_input(target,text,state):

    new_rxText = text
    target.update({state: new_rxText})
    target.update({state: ""})

def State_input(target,text,state):

    new_txState = text
    target.update({state: new_txState})
    

# chatGPT api_key 설정
openai.api_key = "sk-proj-7I3KRlNUGmhawlVzShdcT3BlbkFJ8GVHACJp2kdKEu3j1NlZ"

# Google Maps API Key 설정
google_maps_api_key = "AIzaSyCRlEG_EVmoWH-IkAkm9GX3nOw7VJ4gGpw"
gmaps = googlemaps.Client(key=google_maps_api_key)

# LangChain 설정
memory = ConversationBufferMemory()
chat = ChatOpenAI(model="gpt-4o", api_key=openai.api_key)

# 시스템 메시지
system_message = SystemMessage(content="You are a helpful assistant. Answer as concisely as possible. Do not include greetings.")


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
        
def find_nearest_highway_and_rest_area(gps_user):
    highway_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={general_location[0]},{general_location[1]}&radius=50000&type=road&key={google_maps_api_key}"
    highway_response = requests.get(highway_url)
    highways = highway_response.json().get('results', [])
    
    if not highways:
        return None, None

    nearest_highway = min(highways, key=lambda x: geodesic(gps_user, (x['geometry']['location']['lat'], x['geometry']['location']['lng'])).kilometers)
    
    rest_area_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={nearest_highway['geometry']['location']['lat']},{nearest_highway['geometry']['location']['lng']}&radius=50000&type=rest_area&key={google_maps_api_key}"
    rest_area_response = requests.get(rest_area_url)
    rest_areas = rest_area_response.json().get('results', [])
    
    if not rest_areas:
        return nearest_highway, None

    closest_rest_area = min(rest_areas, key=lambda x: geodesic(general_location, (x['geometry']['location']['lat'], x['geometry']['location']['lng'])).kilometers)
    
    return nearest_highway, closest_rest_area

def analyze_user_input(user_input):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Extract the type of information requested (e.g., 화장실, 먹거리, 주차장) from the following user input."},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content

def provide_rest_area_info():
    current_data_my_location = general_ref_my_location.get()
    lat = current_data_my_location.get('lat')
    
    lon = current_data_my_location.get('long')
    print(lat)
    print(lon)                        
    #gps_info(lat,lon)
    general_location = (lat,lon)
    nearest_highway, closest_rest_area = find_nearest_highway_and_rest_area(general_location)
    
    print(closest_rest_area)

    if nearest_highway and closest_rest_area:
        response_text = f"현재 가장 가까운 휴게소는 {closest_rest_area['name']}에 위치해 있으며, 약 {geodesic(general_location, (closest_rest_area['geometry']['location']['lat'], closest_rest_area['geometry']['location']['lng'])).kilometers:.2f} km 떨어져 있습니다."
        restArea_name = closest_rest_area['name']
        restArea_location_lat = closest_rest_area['geometry']['location']['lat']#"{:.5f}".format(closest_rest_area['geometry']['location']['lat'])
        restArea_location_long = closest_rest_area['geometry']['location']['lng']#"{:.5f}".format(closest_rest_area['geometry']['location']['lng'])
        State_input(general_ref_restName,restArea_name,"name")
        State_input(general_ref_restArea,restArea_location_lat,"lat")
        State_input(general_ref_restArea,restArea_location_long,"long")
        
        

    elif nearest_highway:
        response_text = f"현재 위치에서 가장 가까운 고속도로는 {nearest_highway['name']}입니다. 그러나 휴게소 정보를 찾을 수 없습니다."
    else:
        response_text = "현재 위치에서 가장 가까운 고속도로 정보를 찾을 수 없습니다."

    

    print(response_text)
    Text_input(general_ref_my,response_text,"txText")
    text_to_voice(response_text)
    return closest_rest_area['name'] if closest_rest_area else None

def chatgpt_response(prompt, history):
    messages = [
        system_message,
        *history,
        HumanMessage(content=prompt)
    ]
    response = chat.invoke(messages)
    return response


# 키워드를 가지고 대화 시작
# 키워드를 가지고 대화 시작
# keywords = "[txState, overload, unknown, 112]"  # 키워드 받아와서 수정


template = """
만약 사용자가 제공하는 리스트의 "상태"를 이용해 다음 조건에 따라 답을 내놓는다.
chatGPT는 차량의 인포테인먼트 시스템이며 최대한 친절하고 간결하게 답변한다.
한국어를 사용하여 답변한다.
예시를 그대로 사용하지 않고 변형하여 사용한다.
공익광고 문구를 참고해도 좋다.
신고는 운전자가 하는 것이 아니라 인포테인먼트 시스템이 자동으로 할 예정이다. 신고에 대해서는 언급하지 않는다.
이모티콘은 절대 사용하지 않는다.
인사말을 절대 사용하지 않는다.
"귀하"라는 단어를 절대 사용하지 않는다.
"112"는 "일일이", "119"는 "일일구", "0800482000"는 "공팔공 공사팔이 공공공"으로 읽는다.

1. "상태"는 현재 차량 운전자의 상태를 의미한다. "상태"는 다음과 같이 분류할 수 있다. 예시 답변을 참고하여 chatGPT가 적절한 답변을 생성하여 사용자(운전자)에게 제공한다.
1) "상태"가 "drowsy"이라면 현재 차량 운전자가 졸음운전을 하고 있다는 의미이다. 따라서 운전자에게 다음과 같은 답변을 제공하는 것이 좋다. "든든한 졸음방지"라는 문구는 사용하지 않는다. (예시: 많이 피곤하시면 스트레칭을 하시거나 쉬어가는것이 큰 도움이 돼요!)
2) "상태"가 "alcohol"이라면 현재 차량 운전자가 음주운전을 하고 있다는 의미이다. 따라서 운전자에게 다음과 같은 답변을 제공하는 것이 좋다. (예시: 음주운전은 살인행위와 같습니다. 음주를 하셨다면 대중교통이나 대리운전 서비스를 이용해주세요.)
3) "상태"가 "overload"이라면 현재 차량 운전자가 과적을 했다는 의미이다. 따라서 운전자에게 다음과 같은 답변을 제공하는 것이 좋다. "차량이 과적되었습니다."라는 잘못된 수동 표현은 사용하지 않는다. (예시: 차량이 과적상태인 것 같아요. 차량에 적재된 물건을 다시 확인해보는게 좋겠어요)
4) "상태"가 "threat"이라면 현재 차량 운전자가 위협운전을 하고 있다는 의미이다. 따라서 운전자에게 다음과 같은 답변을 제공하는 것이 좋다. (예시: 위협운전은 타인에게 큰 위협이 될 수 있어요)
5) "상태"가 "breakdown"이라면 현재 차량 후미부에 어떠한 문제가 생겼다는 의미이다. 따라서 운전자에게 다음과 같은 답변을 제공하는 것이 좋다. (예시: 안전한 곳에 정차하고 차량에 고장이 있는지 점검해보면 좋겠어요)
6) "상태"가 "lightOff"이라면 현재 차량 전조등이 꺼졌다는 의미이다. 따라서 운전자에게 다음과 같은 답변을 제공하는 것이 좋다. (예시: 전조등이 켜져있는지 확인해보세요)
7) "상태"가 "fire"이라면 차량에 화재가 발생했다는 의미이다. 따라서 운전자에게 다음과 같은 답변을 제공하는 것이 좋다. (예시: 차량에 화재가 발생한 것 같아요. 안전한 곳에 정차하세요)
8) "상태"가 "fuelLeak"이라면 현재 연료누출이 발생했다는 의미이다. 따라서 운전자에게 다음과 같은 답변을 제공하는 것이 좋다. (예시: 연료누출이 발생한 것 같아요. 안전한 곳에 정차하여 차량을 점검하세요)
9) "상태"가 "moveOver"이라면 후방에 긴급차량이 있으므로 길터주기가 필요하다는 의미이다. 따라서 운전자에게 다음과 같은 답변을 제공하는 것이 좋다. "길터주기에 동참해주세요"라는 문장을 꼭 넣어서 답변해줘 (예시: 길터주기가 필요합니다. 긴급차량의 통행에 방해가 되지 않도록 차량을 비켜주세요)
10) "상태"가 "intersection"이라면 바로 앞 교차로에 긴급차량이 지나가고 있으므로 주의해야한다는 의미이다. 따라서 운전자에게 다음과 같은 답변을 제공하는 것이 좋다. (예시: 바로 앞 교차로에 긴급차량이 통행중이니 서행해주세요)
"""

template판정 = """
사용자의 메시지를 통해 yes 또는 no로만 판단한다.

1. "그래", "좋아", "네", "오케이" 등의 긍정표현 -> yes
2. "아니", "필요없어", "싫어" 등의 부정표현 -> no
"""

sys_msg = SystemMessage(content=template)
user_msg = HumanMessage(content=keywords)

aimsg = chat.invoke([sys_msg, user_msg])

print(aimsg.content)
Text_input(general_ref_my,aimsg.content,"txText")
text_to_voice(aimsg.content)

if 'drowsy' in keywords:
    print("근처 휴게소 정보를 알려드릴까요?")
    Text_input(general_ref_my,"근처 휴게소 정보를 알려드릴까요?","txText")
    text_to_voice("근처 휴게소 정보를 알려드릴까요?")
    sys_msg판정 = SystemMessage(content=template판정)
    user_input판정 = voice_to_text()
    user_msg판정 = HumanMessage(content=user_input판정)

    print(user_input판정)
    aimsg판정 = chat.invoke([sys_msg판정, user_msg판정])
    print("알겠습니다.")
    Text_input(general_ref_my,"알겠습니다","txText")
    text_to_voice("알겠습니다.")


    history = []

    if 'yes' in aimsg판정.content:
        print("휴게소에 대한 정보를 제공하겠습니다.")
        Text_input(general_ref_my,"휴게소에 대한 정보를 제공하겠습니다.","txText")
        text_to_voice("휴게소에 대한 정보를 제공하겠습니다.")
        closest_rest_area_name = provide_rest_area_info()
        Text_input(general_ref_restArea,"","lat")
        Text_input(general_ref_restArea,"","long")
        Text_input(general_ref_restName,"","name")
        while True:
            user_input = voice_to_text()
            if closest_rest_area_name:
                user_input = f"{closest_rest_area_name} {user_input}"
            break
            # response = chatgpt_response(user_input, history)
            # response_text = response.content
            # print(response_text)
            # Text_input(general_ref_my,response_text,"txText")
            # text_to_voice(response_text)
            # history.append(HumanMessage(content=user_input))
            # history.append(AIMessage(content=response_text))