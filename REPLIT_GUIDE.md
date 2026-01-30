# دليل نشر Replit | Replit Deployment Guide

## نظرة عامة | Overview

هذا الدليل يشرح كيفية نشر وتشغيل نظام تصميم الديكور الداخلي بالذكاء الاصطناعي على منصة Replit.

This guide explains how to deploy and run the Interior Design AI Suite on Replit platform.

---

## المتطلبات | Prerequisites

- حساب Replit مجاني أو مدفوع | Free or paid Replit account
- معرفة أساسية بـ Python | Basic Python knowledge

---

## خطوات النشر | Deployment Steps

### 1. إنشاء Repl جديد | Create New Repl

1. افتح [Replit.com](https://replit.com)
2. انقر على "Create Repl" أو "إنشاء Repl"
3. اختر "Import from GitHub" أو "استيراد من GitHub"
4. الصق رابط المستودع: `https://github.com/lil-fahad/furniture_ai_suite`
5. انقر "Import from GitHub"

**OR / أو:**

1. افتح Replit وانقر "Create"
2. اختر "Python" كلغة برمجة
3. قم برفع ملفات المشروع يدوياً

### 2. إعداد البيئة | Environment Setup

بمجرد استيراد المشروع، قم بتشغيل سكريبت الإعداد:

Once the project is imported, run the setup script:

```bash
bash setup_replit.sh
```

أو قم بالتثبيت اليدوي:

Or install manually:

```bash
pip install -r requirements-replit.txt
```

### 3. تكوين المتغيرات البيئية | Configure Environment Variables

في Replit، انتقل إلى "Secrets" (🔒 في الشريط الجانبي):

In Replit, go to "Secrets" (🔒 in the sidebar):

**Optional Variables:**

- `KAGGLE_USERNAME` - اسم مستخدم Kaggle (اختياري)
- `KAGGLE_KEY` - مفتاح API لـ Kaggle (اختياري)
- `GITHUB_TOKEN` - رمز GitHub (اختياري)
- `ALLOWED_ORIGINS` - النطاقات المسموح بها CORS (افتراضياً: *)

### 4. تشغيل التطبيق | Run the Application

انقر على زر "Run" الأخضر الكبير في الأعلى، أو استخدم:

Click the big green "Run" button at the top, or use:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

سيبدأ الخادم تلقائياً ويمكنك الوصول إلى واجهة API على:

The server will start automatically and you can access the API at:

```
https://[your-repl-name].[your-username].repl.co
```

### 5. الوصول إلى الوثائق | Access Documentation

افتح متصفح Replit المدمج أو استخدم الرابط لفتح:

Open Replit's built-in browser or use the link to open:

- **Swagger UI**: `https://[your-repl].repl.co/docs`
- **ReDoc**: `https://[your-repl].repl.co/redoc`

---

## الميزات المتاحة على Replit | Features Available on Replit

### ✅ الميزات المدعومة بالكامل | Fully Supported Features

1. **بحث منتجات Alibaba** | Alibaba Product Search
   ```bash
   POST /alibaba/search
   ```
   - البحث عن الأثاث | Search for furniture
   - تصفية حسب السعر والفئة | Filter by price and category
   - عرض معلومات الموردين | Display supplier information

2. **تحليل المخططات الأرضية** | Floor Plan Analysis
   ```bash
   POST /analyze-floor-plan
   ```
   - تحميل صور المخططات | Upload floor plan images
   - كشف الغرف تلقائياً | Automatic room detection
   - توصيات الأثاث | Furniture recommendations

3. **توصيات الأثاث** | Furniture Recommendations
   ```bash
   POST /furniture-recommendations
   ```
   - توصيات حسب نوع الغرفة | Recommendations by room type
   - مناسبة لمساحة الغرفة | Suitable for room size

4. **فئات Alibaba** | Alibaba Categories
   ```bash
   GET /alibaba/categories
   ```

5. **فحص الصحة** | Health Check
   ```bash
   GET /health
   ```

### ⚠️ الميزات التي تتطلب موارد إضافية | Features Requiring Additional Resources

هذه الميزات تعمل بشكل أفضل على أجهزة محلية أو خوادم سحابية بموارد أكثر:

These features work better on local machines or cloud servers with more resources:

1. **تنزيل مجموعات البيانات** | Dataset Downloads
   - يتطلب مساحة تخزين كبيرة | Requires large storage
   - بطيء على Replit المجاني | Slow on free Replit

2. **تدريب النماذج** | Model Training
   - يتطلب GPU | Requires GPU
   - يستهلك ذاكرة كبيرة | High memory consumption
   - غير موصى به على Replit | Not recommended on Replit

3. **التنبؤ بالنماذج المدربة** | Prediction with Trained Models
   - يتطلب ملفات النماذج | Requires model files
   - يحتاج PyTorch/TensorFlow | Needs PyTorch/TensorFlow

---

## نصائح للأداء على Replit | Performance Tips for Replit

### 1. استخدم Always On (للحسابات المدفوعة)

إذا كان لديك حساب Replit مدفوع، فعّل "Always On" لإبقاء التطبيق يعمل 24/7.

If you have a paid Replit account, enable "Always On" to keep the app running 24/7.

### 2. التخزين المؤقت | Caching

النظام يستخدم التخزين المؤقت تلقائياً لتحسين الأداء:

The system automatically uses caching for better performance:

- نتائج بحث Alibaba مخزنة لمدة 24 ساعة
- Alibaba search results cached for 24 hours

### 3. حدود الذاكرة | Memory Limits

على Replit المجاني:

On free Replit:

- تجنب تحميل ملفات كبيرة جداً | Avoid uploading very large files
- استخدم صور مخططات أرضية بحجم معقول (< 5MB) | Use reasonable floor plan images (< 5MB)

### 4. متغيرات البيئة | Environment Variables

استخدم "Secrets" بدلاً من ملفات `.env` للمعلومات الحساسة:

Use "Secrets" instead of `.env` files for sensitive information:

```python
import os
kaggle_key = os.getenv('KAGGLE_KEY')
```

---

## استكشاف الأخطاء | Troubleshooting

### المشكلة: التطبيق لا يبدأ | Problem: App Won't Start

**الحل | Solution:**

```bash
# أعد تثبيت التبعيات | Reinstall dependencies
pip install --upgrade -r requirements-replit.txt

# تحقق من السجلات | Check logs
cat /tmp/*.log
```

### المشكلة: خطأ في الذاكرة | Problem: Memory Error

**الحل | Solution:**

استخدم `requirements-replit.txt` بدلاً من `requirements.txt` - فهو أخف وزناً.

Use `requirements-replit.txt` instead of `requirements.txt` - it's lighter.

```bash
pip uninstall torch torchvision -y
pip install -r requirements-replit.txt
```

### المشكلة: خطأ في OpenCV | Problem: OpenCV Error

**الحل | Solution:**

تأكد من استخدام `opencv-python-headless`:

Make sure you're using `opencv-python-headless`:

```bash
pip uninstall opencv-python -y
pip install opencv-python-headless
```

### المشكلة: بطء التطبيق | Problem: Slow Application

**الحل | Solution:**

1. استخدم التخزين المؤقت المدمج | Use built-in caching
2. قلل حجم الصور قبل الرفع | Reduce image sizes before upload
3. فكر في الترقية إلى Replit المدفوع | Consider upgrading to paid Replit

---

## اختبار النظام | Testing the System

بعد بدء التطبيق، جرب هذه الاختبارات:

After starting the app, try these tests:

### 1. فحص الصحة | Health Check

```bash
curl https://[your-repl].repl.co/health
```

**النتيجة المتوقعة | Expected:**
```json
{
  "status": "healthy",
  "service": "Interior Design AI Suite",
  "version": "2.0.0"
}
```

### 2. بحث Alibaba | Alibaba Search

افتح المتصفح وانتقل إلى:

Open browser and go to:

```
https://[your-repl].repl.co/docs
```

جرب endpoint: `POST /alibaba/search` مع:

Try endpoint: `POST /alibaba/search` with:

```json
{
  "keyword": "sofa",
  "page": 1,
  "page_size": 5
}
```

### 3. توصيات الأثاث | Furniture Recommendations

```bash
curl "https://[your-repl].repl.co/furniture-recommendations?room_type=bedroom&area_sqm=20"
```

---

## الأمان | Security

### في بيئة Replit | In Replit Environment

1. **لا تشارك الأسرار** | Don't Share Secrets
   - استخدم Replit Secrets للمفاتيح الحساسة
   - Use Replit Secrets for sensitive keys

2. **CORS محدود** | Limited CORS
   - في الإنتاج، حدد النطاقات المسموح بها
   - In production, specify allowed origins

3. **حد معدل الطلبات** | Rate Limiting
   - النظام لديه حد معدل مدمج
   - System has built-in rate limiting

---

## التكاليف | Costs

### Replit المجاني | Free Replit

- ✅ مناسب للتجريب والتطوير | Good for testing and development
- ⚠️ يتوقف بعد فترة عدم نشاط | Stops after inactivity
- ⚠️ موارد محدودة | Limited resources

### Replit المدفوع (Hacker Plan) | Paid Replit

- ✅ Always On - يعمل 24/7
- ✅ موارد أكثر | More resources
- ✅ نطاق مخصص | Custom domain
- 💰 حوالي $7/شهر | ~$7/month

---

## الخطوات التالية | Next Steps

بعد النشر على Replit:

After deploying on Replit:

1. ✅ اختبر جميع الـ endpoints | Test all endpoints
2. ✅ راقب استخدام الموارد | Monitor resource usage
3. ✅ أضف domain مخصص (اختياري) | Add custom domain (optional)
4. ✅ فكر في الترقية للميزات المتقدمة | Consider upgrading for advanced features

---

## الدعم | Support

للمساعدة:

For help:

- 📖 اقرأ [README.md](README.md)
- 📊 راجع [TESTING_REPORT.md](TESTING_REPORT.md)
- 🔧 تحقق من [DEPLOYMENT.md](DEPLOYMENT.md)
- 💬 افتح issue على GitHub

---

## الخلاصة | Summary

✅ **Replit مناسب لـ | Replit is Good For:**
- التجريب السريع | Quick prototyping
- عرض المشروع | Project demos
- واجهة API الأساسية | Basic API interface
- بحث Alibaba | Alibaba search
- تحليل المخططات | Floor plan analysis

❌ **Replit غير مناسب لـ | Replit is NOT Good For:**
- تدريب النماذج | Model training
- معالجة مكثفة | Heavy processing
- تخزين كبير | Large storage needs

---

**تم إنشاء هذا الدليل بواسطة** | **Guide Created By:**
Professional Interior Design AI Suite Team

**التاريخ** | **Date:** 2026-01-30
