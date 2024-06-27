import cv2
import time

# 웹캠으로부터 영상 캡처 객체 생성
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("웹캠을 열 수 없습니다.")
    exit()

print("웹캠이 열렸습니다. 1초 동안 프레임을 표시합니다.")

center_crop_size = 0.6  # 중앙 부분 크기 설정 (예: 원본의 60%)

start_time = time.time()
while True:
    # 현재 프레임 읽기
    ret, frame = cap.read()
    if not ret:
        print("프레임을 캡처할 수 없습니다.")
        break

    height, width, _ = frame.shape

    # 중앙 좌표 계산
    center_x, center_y = width // 2, height // 2
    crop_width = int(width * center_crop_size)
    crop_height = int(height * center_crop_size)

    # 중앙 부분 잘라내기
    cropped_frame = frame[
        center_y - crop_height // 2 : center_y + crop_height // 2,
        center_x - crop_width // 2 : center_x + crop_width // 2
    ]

    # 중앙 부분 확대 (원본 크기로)
    enlarged_frame = cv2.resize(cropped_frame, (width, height), interpolation=cv2.INTER_LINEAR)

    # 확대된 프레임 보여주기
    cv2.imshow('Webcam - Zoomed', enlarged_frame)

    # 1초 동안 프레임을 표시
    if time.time() - start_time > 3:
        break

    # ESC 키를 누르면 종료 (예외 상황)
    if cv2.waitKey(1) & 0xFF == 27:
        break

# 1초 대기
time.sleep(1)

# 마지막 프레임 캡처 및 중앙 부분 확대 후 저장
ret, frame = cap.read()
if ret:
    height, width, _ = frame.shape

    # 중앙 좌표 계산
    center_x, center_y = width // 2, height // 2
    crop_width = int(width * center_crop_size)
    crop_height = int(height * center_crop_size)

    # 중앙 부분 잘라내기
    cropped_frame = frame[
        center_y - crop_height // 2 : center_y + crop_height // 2,
        center_x - crop_width // 2 : center_x + crop_width // 2
    ]

    # 중앙 부분 확대 (원본 크기로)
    enlarged_frame = cv2.resize(cropped_frame, (width, height), interpolation=cv2.INTER_LINEAR)

    # 이미지 저장
    save_path = 'neww.jpg'  # 원하는 저장 경로로 변경
    cv2.imwrite(save_path, enlarged_frame)
    print(f"이미지가 저장되었습니다: {save_path}")
else:
    print("이미지를 캡처할 수 없습니다.")

# 캡처 객체 해제 및 창 닫기
cap.release()
cv2.destroyAllWindows()
