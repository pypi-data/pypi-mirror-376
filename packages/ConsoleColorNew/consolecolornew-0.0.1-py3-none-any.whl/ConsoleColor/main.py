import cv2





def testFunc():
	cap = cv2.VideoCapture(0)
	
	if not cap.isOpened():
		print("Error 1")
	
	ret, frame = cap.read()
	
	cap.release()
	
	if ret:
		cv2.imwrite("captured_photo.jpg", frame)
		print("Photo saved as captured_photo.jpg")
	else:
		print("Error 2")




def printColor(string, r=0, g=255, b=0):
	print(string)