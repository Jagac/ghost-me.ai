import httpx

files = {"file": ("file.pdf", open("/home/jagac/ghostme/pdfproducer/Jagos Perovic_Resume.pdf", "rb"))}
headers = {"X-API-Key": "test"}
response = httpx.post("http://localhost:8080/uploadfile/", files=files, headers=headers)
print(response)



# response = httpx.post("http://localhost:8080/trigger-scraper-task/")
# print(response.json())