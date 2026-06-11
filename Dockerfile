# पायथन का ऑफिशियल और रेडीमेड इमेज
FROM python:3.10-slim

# वर्किंग डायरेक्टरी सेट करना
WORKDIR /app

# पहले रिक्वायरमेंट्स फाइल कॉपी करना
COPY requirements.txt .

# पैकेजेस इंस्टॉल करना
RUN pip install --no-cache-dir -r requirements.txt

# बाकी सारा कोड कॉपी करना
COPY . .

# पोर्ट सेट करना जो रेलवे को चाहिए
EXPOSE 5000

# ऐप को रन करने की कमांड
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
