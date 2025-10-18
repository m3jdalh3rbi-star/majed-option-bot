# استخدم نسخة بايثون ثابتة 3.10
FROM python:3.10-slim

# إعداد مجلد العمل
WORKDIR /app

# نسخ الملفات إلى الحاوية
COPY . /app

# تثبيت المكتبات المطلوبة
RUN pip install --no-cache-dir -r requirements.txt

# تحديد المنفذ
EXPOSE 8000

# أمر التشغيل
CMD ["python", "bot.py"]
