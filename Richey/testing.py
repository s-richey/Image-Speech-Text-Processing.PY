from pdf2image import convert_from_path
import cv2
import pytesseract
import tempfile
import os

# Read image from which text needs to be extracted
IN = 'Programming-Project-2.pdf'
pages = convert_from_path(IN)

# Save the third page as a temporary image file
temp_image = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
pages[2].save(temp_image.name, 'PNG')

img = cv2.imread(temp_image.name)

# Preprocessing the image starts
# Convert the image to gray scale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Performing OTSU threshold
ret, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

# Specify structure shape and kernel size.
rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 30))

# Applying dilation on the threshold image
dilation = cv2.dilate(thresh1, rect_kernel, iterations=1)

# Finding contours
contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

# Sort contours from top to bottom
contours = sorted(contours, key=lambda x: cv2.boundingRect(x)[1])

# Creating a copy of the image
im2 = img.copy()

# Looping through the identified contours
# Then rectangular part is cropped and passed on
# to pytesseract for extracting text from it
for idx, cnt in enumerate(contours):
    x, y, w, h = cv2.boundingRect(cnt)

    # Cropping the text block for giving input to OCR
    cropped = im2[y:y + h, x:x + w]

    # Apply OCR on the cropped image
    text = pytesseract.image_to_string(cropped)

    # Print the extracted text from each contour region
    print(f"Contour {idx+1} Location - X: {x}, Y: {y}, Width: {w}, Height: {h}")
    print(text)

temp_image.close()
os.remove(temp_image.name)
