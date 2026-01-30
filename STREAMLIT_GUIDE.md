# دليل تشغيل Streamlit | Streamlit Deployment Guide

## نظرة عامة | Overview

هذا الدليل يشرح كيفية تشغيل نظام تصميم الديكور الداخلي بالذكاء الاصطناعي باستخدام واجهة Streamlit.

This guide explains how to run the Interior Design AI Suite using the Streamlit web interface.

---

## المتطلبات | Prerequisites

- Python 3.8+
- pip (Python package manager)
- 2GB+ RAM
- Modern web browser

---

## التثبيت السريع | Quick Installation

### الطريقة 1: التثبيت الكامل | Full Installation

للحصول على جميع الميزات بما في ذلك التدريب:

For all features including ML training:

```bash
# Install all dependencies
pip install -r requirements.txt

# Run Streamlit
streamlit run streamlit_app.py
```

### الطريقة 2: التثبيت الخفيف | Lightweight Installation

للميزات الأساسية فقط (بدون تدريب ML):

For basic features only (without ML training):

```bash
# Install lightweight dependencies
pip install -r requirements-replit.txt

# Run Streamlit
streamlit run streamlit_app.py
```

---

## بدء التشغيل | Starting the Application

### على نظام Linux/Mac

```bash
# Navigate to project directory
cd furniture_ai_suite

# Run Streamlit
streamlit run streamlit_app.py

# Or use the provided script
bash run_streamlit.sh
```

### على نظام Windows

```cmd
# Navigate to project directory
cd furniture_ai_suite

# Run Streamlit
streamlit run streamlit_app.py

# Or use the provided script
run_streamlit.bat
```

### مع خيارات مخصصة | With Custom Options

```bash
# Specify custom port
streamlit run streamlit_app.py --server.port 8502

# Run in headless mode (no browser auto-open)
streamlit run streamlit_app.py --server.headless true

# Specify address
streamlit run streamlit_app.py --server.address 0.0.0.0
```

---

## الوصول إلى التطبيق | Accessing the Application

بعد بدء التشغيل، افتح المتصفح على:

After starting, open your browser at:

```
http://localhost:8501
```

أو استخدم الرابط الذي يظهر في Terminal:

Or use the URL shown in the terminal:

```
Local URL: http://localhost:8501
Network URL: http://192.168.1.x:8501
```

---

## الميزات المتاحة | Available Features

### 🏠 الصفحة الرئيسية | Home Page

- نظرة عامة على النظام | System overview
- إحصائيات سريعة | Quick statistics
- حالة الوحدات | Module status

### 🔍 بحث Alibaba | Alibaba Search

**الميزات | Features:**
- بحث عن منتجات الأثاث | Search furniture products
- فلاتر متقدمة (السعر، الفئة) | Advanced filters (price, category)
- عرض النتائج مع الصور | Display results with images
- معلومات الموردين | Supplier information
- التسعير والحد الأدنى للطلب | Pricing and MOQ

**كيفية الاستخدام | How to Use:**
1. اختر "Alibaba Search" من القائمة الجانبية
2. أدخل كلمة البحث (مثل: sofa, chair, table)
3. اختياري: اضبط الفلاتر (السعر، الفئة، إلخ)
4. انقر "بحث" للحصول على النتائج

### 📐 محلل المخططات | Floor Plan Analyzer

**الميزات | Features:**
- رفع صور المخططات الأرضية | Upload floor plan images
- كشف الغرف تلقائياً | Automatic room detection
- تصنيف أنواع الغرف | Room type classification
- توصيات الأثاث لكل غرفة | Furniture recommendations per room
- تحليل المساحة | Area analysis

**كيفية الاستخدام | How to Use:**
1. اختر "Floor Plan Analyzer"
2. ارفع صورة المخطط (PNG, JPG)
3. اضبط إعدادات التحليل (اختياري)
4. انقر "تحليل المخطط"
5. اعرض النتائج والتوصيات

**أنواع الملفات المدعومة:**
- PNG
- JPG/JPEG
- الحجم الأقصى: 200 MB

### 💡 التوصيات | Furniture Recommendations

**الميزات | Features:**
- توصيات حسب نوع الغرفة | Recommendations by room type
- مراعاة مساحة الغرفة | Room size consideration
- اختيار الأسلوب | Style preferences
- نطاق الأسعار | Price ranges
- أولوية العناصر | Item priorities

**أنواع الغرف المدعومة:**
- غرفة المعيشة | Living Room
- غرفة النوم | Bedroom
- المطبخ | Kitchen
- الحمام | Bathroom
- المكتب | Office
- غرفة الطعام | Dining Room

### 📊 مجموعات البيانات | Datasets

**المعلومات المتاحة:**
- قائمة جميع مجموعات البيانات | List of all datasets
- تفاصيل كل مجموعة | Dataset details
- الحجم والملفات | Size and files
- الوصف | Description

### 💻 حالة النظام | System Status

**المعلومات المعروضة:**
- حالة النظام | System health
- الوحدات النشطة | Active modules
- إصدار النظام | System version
- التكوينات | Configuration

---

## التكوين | Configuration

### ملف config.toml

الموقع: `.streamlit/config.toml`

Location: `.streamlit/config.toml`

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
port = 8501
enableCORS = false
maxUploadSize = 200

[browser]
gatherUsageStats = false
```

### المتغيرات البيئية | Environment Variables

```bash
# Optional: Kaggle credentials
export KAGGLE_USERNAME="your_username"
export KAGGLE_KEY="your_api_key"

# Optional: GitHub token
export GITHUB_TOKEN="your_token"

# Optional: CORS origins (for API backend)
export ALLOWED_ORIGINS="*"
```

---

## استكشاف الأخطاء | Troubleshooting

### المشكلة: التطبيق لا يبدأ
### Problem: Application won't start

**الحل | Solution:**

```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check if port is available
lsof -i :8501  # Linux/Mac
netstat -ano | findstr :8501  # Windows
```

### المشكلة: خطأ في استيراد الوحدات
### Problem: Module import errors

**الحل | Solution:**

```bash
# Install missing modules
pip install streamlit pandas numpy pillow opencv-python-headless

# Verify installation
python -c "import streamlit; print(streamlit.__version__)"
```

### المشكلة: خطأ في رفع الصور
### Problem: Image upload error

**الأسباب المحتملة | Possible Causes:**
- حجم الملف كبير جداً (> 200 MB)
- نوع الملف غير مدعوم
- مشكلة في الذاكرة

**الحل | Solution:**
- قلل حجم الصورة قبل الرفع
- تأكد من نوع الملف (PNG, JPG)
- أعد تشغيل التطبيق

### المشكلة: بطء التطبيق
### Problem: Slow performance

**الحل | Solution:**

```bash
# Run with limited features (demo mode)
pip install -r requirements-replit.txt

# Close other applications
# Use smaller images for floor plans
# Clear browser cache
```

### المشكلة: OpenCV لا يعمل
### Problem: OpenCV not working

**الحل | Solution:**

```bash
# For headless environments (servers)
pip uninstall opencv-python
pip install opencv-python-headless

# For GUI environments (desktops)
pip install opencv-python
```

---

## النشر | Deployment

### النشر على Streamlit Cloud

1. **رفع الكود إلى GitHub**
   ```bash
   git add .
   git commit -m "Add Streamlit interface"
   git push origin main
   ```

2. **الذهاب إلى Streamlit Cloud**
   - افتح [share.streamlit.io](https://share.streamlit.io)
   - سجل دخول باستخدام GitHub
   - انقر "New app"

3. **تكوين التطبيق**
   - Repository: `lil-fahad/furniture_ai_suite`
   - Branch: `main`
   - Main file: `streamlit_app.py`

4. **النشر**
   - انقر "Deploy"
   - انتظر حتى يكتمل النشر
   - احصل على الرابط: `https://[app-name].streamlit.app`

### النشر على Heroku

```bash
# Create Procfile
echo "web: streamlit run streamlit_app.py --server.port=$PORT" > Procfile

# Create runtime.txt
echo "python-3.10.0" > runtime.txt

# Deploy
heroku create your-app-name
git push heroku main
```

### النشر على AWS/Azure/GCP

راجع [DEPLOYMENT.md](DEPLOYMENT.md) لمزيد من التفاصيل.

See [DEPLOYMENT.md](DEPLOYMENT.md) for more details.

---

## الأداء | Performance

### نصائح لتحسين الأداء | Performance Tips

1. **استخدام التخزين المؤقت**
   - Streamlit يخزن النتائج تلقائياً
   - استخدم `@st.cache_data` للدوال البطيئة

2. **تقليل حجم الصور**
   - قبل الرفع، قلل الدقة إلى 2048x2048
   - استخدم ضغط JPEG

3. **التحميل الكسول**
   - الوحدات يتم تحميلها عند الحاجة
   - وضع Demo متاح بدون ML

4. **إدارة الذاكرة**
   - أغلق التطبيقات الأخرى
   - استخدم requirements-replit.txt للبيئات المحدودة

---

## الاختبار | Testing

### اختبار الوظائف | Feature Testing

```bash
# Test basic functionality
streamlit run streamlit_app.py

# Navigate through all pages
# Test each feature:
#   - Alibaba search
#   - Floor plan upload
#   - Recommendations
#   - System status
```

### اختبار الأداء | Performance Testing

```bash
# Monitor resource usage
# Check loading times
# Test with different image sizes
# Verify mobile responsiveness
```

---

## الأمان | Security

### أفضل الممارسات | Best Practices

1. **لا تشارك بيانات الاعتماد**
   - استخدم متغيرات البيئة
   - لا تضع مفاتيح API في الكود

2. **حدود الرفع**
   - الحد الأقصى: 200 MB
   - أنواع مدعومة فقط: PNG, JPG

3. **CORS**
   - مكوّن بشكل آمن
   - محدد في production

4. **التحقق من المدخلات**
   - جميع المدخلات محققة
   - معالجة الأخطاء موجودة

---

## الأسئلة الشائعة | FAQ

### هل يمكن استخدام Streamlit مع FastAPI؟
### Can I use Streamlit with FastAPI?

نعم! يمكنك تشغيل كلاهما معاً:

Yes! You can run both together:

```bash
# Terminal 1: Run FastAPI
uvicorn app:app --port 8000

# Terminal 2: Run Streamlit
streamlit run streamlit_app.py --server.port 8501
```

### هل Streamlit مجاني؟
### Is Streamlit free?

نعم، Streamlit مفتوح المصدر ومجاني.

Yes, Streamlit is open source and free.

Streamlit Cloud أيضاً مجاني للمشاريع العامة.

Streamlit Cloud is also free for public projects.

### هل يعمل على الهاتف؟
### Does it work on mobile?

نعم! Streamlit responsive ويعمل على:
- 📱 الهواتف | Mobile phones
- 💻 الأجهزة اللوحية | Tablets
- 🖥️ أجهزة الكمبيوتر | Desktops

### كم سرعة التطبيق؟
### How fast is the application?

- التحميل الأولي: 2-5 ثواني
- بحث Alibaba: < 1 ثانية
- تحليل المخططات: 2-5 ثواني
- التوصيات: فوري

---

## الدعم | Support

للمساعدة والدعم:

For help and support:

- 📖 اقرأ [README.md](README.md)
- 📚 راجع [API_EXAMPLES.md](API_EXAMPLES.md)
- 🧪 اقرأ [TESTING_REPORT.md](TESTING_REPORT.md)
- 💬 افتح issue على GitHub
- 📧 تواصل مع الفريق

---

## الخلاصة | Summary

✅ **Streamlit Interface:**
- واجهة ويب سهلة الاستخدام | Easy-to-use web interface
- جميع الميزات متاحة | All features available
- responsive ويعمل على جميع الأجهزة | Responsive on all devices
- سهل النشر | Easy to deploy

✅ **الميزات الرئيسية:**
- بحث Alibaba | Alibaba search
- تحليل المخططات | Floor plan analysis
- التوصيات الذكية | Smart recommendations
- إدارة البيانات | Data management
- مراقبة النظام | System monitoring

✅ **الاستخدام:**
```bash
streamlit run streamlit_app.py
```

---

**تم إنشاء هذا الدليل بواسطة** | **Guide Created By:**
Professional Interior Design AI Suite Team

**التاريخ** | **Date:** 2026-01-30
