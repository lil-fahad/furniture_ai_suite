# Furniture AI Suite

تنزيل بيانات Kaggle → تجهيزها → تدريب موديلات متعددة → تصدير → واجهة API للتنبؤ.

## التشغيل السريع
```bash
# Windows
run_windows.bat

# Mac/Linux
bash run_unix.sh
```

ثم افتح: http://localhost:8000/docs

## دورة العمل من لوحة Swagger
1. POST /download — تنزيل الداتا (سيتخطّى الموجود).
2. POST /prepare — تنظيف + توحيد + تقسيم + تحجيم إلى 256.
3. POST /train — تدريب 3 موديلات (efficientnet_b0 / convnext_tiny / swin_tiny*). يحفظ Top-3 ويصدر TorchScript/ONNX.
4. POST /predict — ارفع صورة واحصل على التنبؤ.
5. GET /labels — عرض الفئات.
6. GET /results — نتائج أفضل 3.

> ضع kaggle.json في:
> - Windows: C:\Users\<USER>\.kaggle\kaggle.json
> - Mac/Linux: ~/.kaggle/kaggle.json
> أو في جذر المشروع وسيُنقل تلقائيًا.

## Configuration

إعدادات التدريب مخزنة في ملف [`model_config.yml`](model_config.yml). يمكن تعديل
الحجم الدُفعي، عدد العصور، معدل التعلم، أسماء النماذج، وعدد العمال. يحتوي الملف
أيضًا على قيمة `seed` لضمان قابلية التكرار.
