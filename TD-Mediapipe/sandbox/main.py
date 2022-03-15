import cv2
import mediapipe as mp
import numpy as np
from google.protobuf.json_format import MessageToDict


def face_detection_demo_static():
    mp_face_detection = mp.solutions.face_detection
    mp_drawing = mp.solutions.drawing_utils

    # For static images:
    image_files = ['samples/img/garrett-jackson-auTAb39ImXg-unsplash.jpg']
    with mp_face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5) as face_detection:
        for idx, file in enumerate(image_files):
            image = cv2.imread(file)
            # Convert the BGR image to RGB and process it with MediaPipe Face Detection.
            results = face_detection.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

            # Draw face detections of each face.
            if not results.detections:
                continue

            annotated_image = image.copy()
            for detection in results.detections:
                nose_tip_x = mp_face_detection.get_key_point(detection, mp_face_detection.FaceKeyPoint.NOSE_TIP).x
                nose_tip_y = mp_face_detection.get_key_point(detection, mp_face_detection.FaceKeyPoint.NOSE_TIP).y

                print(nose_tip_x, nose_tip_y)

                print(mp_face_detection.get_key_point(
                    detection, mp_face_detection.FaceKeyPoint.LEFT_EYE))
                print(mp_face_detection.get_key_point(
                    detection, mp_face_detection.FaceKeyPoint.RIGHT_EYE))

                mp_drawing.draw_detection(annotated_image, detection)
            cv2.imwrite('output/annotated_image' + str(idx) + '.png', annotated_image)


def face_detection_demo_webcam():
    mp_face_detection = mp.solutions.face_detection
    mp_drawing = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(0)
    with mp_face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5) as face_detection:
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                # If loading a video, use 'break' instead of 'continue'.
                continue

            # To improve performance, optionally mark the image as not writeable to
            # pass by reference.
            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = face_detection.process(image)

            # Draw the face detection annotations on the image.
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            if results.detections:
                for detection in results.detections:
                    mp_drawing.draw_detection(image, detection)
            # Flip the image horizontally for a selfie-view display.
            cv2.imshow('MediaPipe Face Detection', cv2.flip(image, 1))
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break
    cap.release()


def hands_detection_demo_webcam():
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    mp_hands = mp.solutions.hands

    # For webcam input:
    cap = cv2.VideoCapture(0)

    with mp_hands.Hands(
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5) as hands:
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                # If loading a video, use 'break' instead of 'continue'.
                continue

            # To improve performance, optionally mark the image as not writeable to
            # pass by reference.
            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            results = hands.process(image)

            # Draw the hand annotations on the image.
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        image,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style())

            # Flip the image horizontally for a selfie-view display.
            cv2.imshow('MediaPipe Hands', cv2.flip(image, 1))

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()


def hands_detection_analyze_landmark():
    drawing_module = mp.solutions.drawing_utils
    hands_module = mp.solutions.hands

    with hands_module.Hands(static_image_mode=True) as hands:
        image = cv2.imread('samples/img/kira-auf-der-heide-QyCH5jwrD_A-unsplash.jpg')

        # input to hands_module should be mirrored and the color should be in RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.flip(image, 1)

        results = hands.process(image)
        image_height, image_width, _ = image.shape

        for idx, hand_handedness in enumerate(results.multi_handedness):
            handedness_dict = MessageToDict(hand_handedness)['classification'][0]
            print(handedness_dict)

        if results.multi_hand_landmarks is not None:
            for handLandmarks in results.multi_hand_landmarks:
                for point in hands_module.HandLandmark:
                    normalized_landmark = handLandmarks.landmark[point]
                    pixel_coordinates_landmark = \
                        drawing_module._normalized_to_pixel_coordinates(
                            normalized_landmark.x, normalized_landmark.y,
                            image_width, image_height)

                    print(point)
                    print(pixel_coordinates_landmark)
                    print(normalized_landmark)


def holistic_demo():
    mp_drawing = mp.solutions.drawing_utils
    mp_holistic = mp.solutions.holistic

    cap = cv2.VideoCapture(0)

    # create black image with the same size as camera frame
    _, frame = cap.read()
    im_height, im_width, ch = frame.shape
    blank_image = np.zeros([im_height, im_width, ch], dtype=np.uint8)

    with mp_holistic.Holistic(
            min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        while cap.isOpened():
            ret, frame = cap.read()

            # recolor feed to RGB and mirror it because I use front camera here
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = cv2.flip(image, 1)
            results = holistic.process(image)

            annotated_image = blank_image.copy()

            # Draw face landmarks
            mp_drawing.draw_landmarks(annotated_image, results.face_landmarks, mp_holistic.FACEMESH_TESSELATION)

            # Draw hands
            mp_drawing.draw_landmarks(annotated_image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
            mp_drawing.draw_landmarks(annotated_image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS)

            # Pose detection
            mp_drawing.draw_landmarks(annotated_image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS)

            cv2.imshow('Annotated Image', annotated_image)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()


def holistic_demo_with_styling():
    mp_drawing = mp.solutions.drawing_utils
    mp_holistic = mp.solutions.holistic

    # the color is in BGR
    hand_landmarks_style = mp_drawing.DrawingSpec(color=(255, 0, 0),
                                                  thickness=2,
                                                  circle_radius=2)

    hand_connection_style = mp_drawing.DrawingSpec(color=(255, 0, 255),
                                                   thickness=2,
                                                   circle_radius=2)

    face_landmarks_style = mp_drawing.DrawingSpec(color=(0, 239, 236),
                                                  thickness=1,
                                                  circle_radius=1)

    face_connection_style = mp_drawing.DrawingSpec(color=(255, 255, 255),
                                                   thickness=1,
                                                   circle_radius=1)

    cap = cv2.VideoCapture(0)

    # create black image with the same size as camera frame
    _, frame = cap.read()
    im_height, im_width, ch = frame.shape
    blank_image = np.zeros([im_height, im_width, ch], dtype=np.uint8)

    with mp_holistic.Holistic(
            min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        while cap.isOpened():
            ret, frame = cap.read()

            # recolor feed to RGB and mirror it because I use front camera here
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = cv2.flip(image, 1)
            results = holistic.process(image)

            annotated_image = blank_image.copy()

            # Draw face landmarks
            mp_drawing.draw_landmarks(annotated_image,
                                      results.face_landmarks, mp_holistic.FACEMESH_TESSELATION,
                                      face_landmarks_style,
                                      face_connection_style)

            # Draw hands
            mp_drawing.draw_landmarks(annotated_image,
                                      results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
                                      hand_landmarks_style,
                                      hand_connection_style)
            mp_drawing.draw_landmarks(annotated_image,
                                      results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
                                      hand_landmarks_style,
                                      hand_connection_style)

            # Pose detection
            mp_drawing.draw_landmarks(annotated_image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS)

            cv2.imshow('Annotated Image', annotated_image)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    holistic_demo_with_styling()
