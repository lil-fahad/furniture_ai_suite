"""
Furniture Design Suite - Floor Plan Based Interior Design
نظام تصميم الأثاث - تصميم الديكور الداخلي بناءً على مخطط البناء

هذا التطبيق يوفر واجهة ويب سهلة الاستخدام لـ:
- رفع مخططات البناء (Floor Plans)
- تحليل الغرف تلقائياً
- اقتراح الأثاث المناسب لكل غرفة
- تصميم داخلي ذكي باستخدام الذكاء الاصطناعي
"""

import streamlit as st
import requests
from PIL import Image
import io
import json
import pandas as pd
from pathlib import Path
import os

# Import local modules
try:
    from alibaba_scraper import AlibabaFurnitureScraper
    from floor_plan_analyzer import FloorPlanAnalyzer
    import numpy as np
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="نظام تصميم الأثاث | Furniture Design Suite",
    page_icon="🪑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #ff7f0e;
        margin-top: 1rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'alibaba_results' not in st.session_state:
    st.session_state.alibaba_results = None
if 'floor_plan_results' not in st.session_state:
    st.session_state.floor_plan_results = None

# Constants for translations
ROOM_TYPE_AR = {
    'living_room': 'غرفة المعيشة',
    'bedroom': 'غرفة النوم',
    'master_bedroom': 'غرفة النوم الرئيسية',
    'dining_room': 'غرفة الطعام',
    'kitchen': 'المطبخ',
    'bathroom': 'الحمام',
    'office': 'المكتب',
    'storage_or_hallway': 'التخزين/الممر'
}

FURNITURE_AR = {
    'sofa': 'أريكة',
    'coffee_table': 'طاولة قهوة',
    'tv_stand': 'حامل تلفاز',
    'armchair': 'كرسي مريح',
    'bookshelf': 'رف كتب',
    'bed': 'سرير',
    'king_bed': 'سرير كبير',
    'nightstand': 'طاولة جانبية',
    'nightstands_pair': 'طاولتان جانبيتان',
    'wardrobe': 'خزانة ملابس',
    'dresser': 'خزانة أدراج',
    'chair': 'كرسي',
    'seating_area': 'منطقة جلوس',
    'dining_table': 'طاولة طعام',
    'dining_table_small': 'طاولة طعام صغيرة',
    'dining_chairs': 'كراسي طعام',
    'buffet': 'بوفيه',
    'china_cabinet': 'خزانة صيني',
    'bar_stools': 'كراسي بار',
    'kitchen_island': 'جزيرة مطبخ',
    'vanity': 'طاولة زينة',
    'storage_cabinet': 'خزانة تخزين',
    'towel_rack': 'حامل مناشف',
    'general_storage': 'تخزين عام'
}

PRIORITY_INFO = {
    'essential': {'ar': 'أساسي', 'emoji': '⭐', 'color': '#28a745'},
    'recommended': {'ar': 'موصى به', 'emoji': '💡', 'color': '#ffc107'},
    'optional': {'ar': 'اختياري', 'emoji': '💭', 'color': '#6c757d'}
}

def display_analysis_results(results):
    """Display the floor plan analysis results with furniture recommendations."""
    if not results.get('success'):
        st.error("❌ فشل التحليل | Analysis failed")
        return
    
    st.markdown(f"## 📊 نتائج التحليل | Analysis Results")
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🚪 عدد الغرف | Rooms Detected", results['rooms_detected'])
    with col2:
        total_furniture = sum(len(room.get('recommendations', [])) for room in results.get('rooms', []))
        st.metric("🪑 قطع الأثاث المقترحة | Furniture Items", total_furniture)
    with col3:
        essential_count = sum(
            1 for room in results.get('rooms', [])
            for rec in room.get('recommendations', [])
            if rec.get('priority') == 'essential'
        )
        st.metric("⭐ الأثاث الأساسي | Essential Items", essential_count)
    
    st.markdown("---")
    
    # Display each room
    for room in results.get('rooms', []):
        room_type = room.get('type', 'unknown')
        room_name_ar = ROOM_TYPE_AR.get(room_type, room_type)
        room_name_en = room_type.replace('_', ' ').title()
        
        with st.expander(f"🚪 الغرفة {room['id']}: {room_name_ar} | {room_name_en}", expanded=True):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown(f"**📏 المساحة | Area:** {room.get('area', 0):,} بكسل")
                st.markdown(f"**🏷️ النوع | Type:** {room_name_ar}")
            
            with col2:
                st.markdown("### 🪑 الأثاث المقترح | Recommended Furniture")
                
                recommendations = room.get('recommendations', [])
                if not recommendations:
                    st.info("لا توجد توصيات لهذه الغرفة")
                else:
                    for rec in recommendations:
                        item = rec.get('item', 'unknown')
                        priority = rec.get('priority', 'optional')
                        
                        item_ar = FURNITURE_AR.get(item, item)
                        item_en = item.replace('_', ' ').title()
                        prio = PRIORITY_INFO.get(priority, PRIORITY_INFO['optional'])
                        
                        st.markdown(
                            f"{prio['emoji']} **{item_ar}** ({item_en}) - "
                            f"<span style='color: {prio['color']}'>{prio['ar']}</span>",
                            unsafe_allow_html=True
                        )

def render_header():
    """Render the application header."""
    st.markdown('<h1 class="main-header">🪑 نظام تصميم الأثاث | Furniture Design Suite</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem;">ارفع مخطط البناء واحصل على توصيات الأثاث المناسب لكل غرفة</p>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center;">Upload your floor plan and get furniture recommendations for each room</p>', unsafe_allow_html=True)
    st.markdown("---")

def render_home():
    """Render the home page with main floor plan upload feature."""
    st.markdown('<h2 class="sub-header">📐 ارفع مخطط البناء | Upload Floor Plan</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    ### 🏠 كيف يعمل النظام؟ | How it works?
    
    1. **ارفع مخطط البناء** - Upload your floor plan image (PNG, JPG, JPEG)
    2. **التحليل التلقائي** - The system will automatically detect rooms
    3. **توصيات الأثاث** - Get AI-powered furniture recommendations for each room
    """)
    
    st.markdown("---")
    
    # Main floor plan upload
    uploaded_file = st.file_uploader(
        "📁 اختر ملف مخطط البناء | Select Floor Plan File",
        type=['png', 'jpg', 'jpeg'],
        help="ارفع صورة مخطط البناء للحصول على تحليل الغرف وتوصيات الأثاث"
    )
    
    if uploaded_file is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📋 مخطط البناء المرفوع | Uploaded Floor Plan")
            image = Image.open(uploaded_file)
            st.image(image, caption="مخطط البناء", use_container_width=True)
        
        with col2:
            st.markdown("### ⚙️ إعدادات التحليل | Analysis Settings")
            min_room_area = st.slider("الحد الأدنى لمساحة الغرفة (بكسل)", 1000, 20000, 5000)
            
            if st.button("🔍 تحليل المخطط واقتراح الأثاث | Analyze & Recommend", type="primary", use_container_width=True):
                with st.spinner("جاري تحليل المخطط... | Analyzing floor plan..."):
                    try:
                        if MODULES_AVAILABLE:
                            # Convert image to bytes
                            img_byte_arr = io.BytesIO()
                            image.save(img_byte_arr, format='PNG')
                            img_byte_arr = img_byte_arr.getvalue()
                            
                            # Create analyzer
                            analyzer = FloorPlanAnalyzer(min_room_area=min_room_area)
                            
                            # Analyze
                            import cv2
                            nparr = np.frombuffer(img_byte_arr, np.uint8)
                            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                            preprocessed = analyzer.preprocess(img)
                            rooms = analyzer.detect_rooms(preprocessed)
                            
                            results = {
                                'success': True,
                                'rooms_detected': len(rooms),
                                'rooms': []
                            }
                            
                            for i, room in enumerate(rooms):
                                recommendations = analyzer.recommend_furniture(room)
                                results['rooms'].append({
                                    'id': i + 1,
                                    'type': room['type'],
                                    'area': room['area_pixels'],
                                    'recommendations': recommendations
                                })
                            
                            st.session_state.floor_plan_results = results
                            st.success(f"✅ تم التحليل! تم اكتشاف {len(rooms)} غرفة | Found {len(rooms)} room(s)")
                        else:
                            # Demo mode
                            st.session_state.floor_plan_results = {
                                'success': True,
                                'rooms_detected': 3,
                                'rooms': [
                                    {
                                        'id': 1,
                                        'type': 'living_room',
                                        'area': 150000,
                                        'recommendations': [
                                            {'item': 'sofa', 'priority': 'essential'},
                                            {'item': 'coffee_table', 'priority': 'essential'},
                                            {'item': 'tv_stand', 'priority': 'recommended'},
                                            {'item': 'armchair', 'priority': 'optional'},
                                        ]
                                    },
                                    {
                                        'id': 2,
                                        'type': 'bedroom',
                                        'area': 80000,
                                        'recommendations': [
                                            {'item': 'bed', 'priority': 'essential'},
                                            {'item': 'wardrobe', 'priority': 'essential'},
                                            {'item': 'nightstand', 'priority': 'recommended'},
                                        ]
                                    },
                                    {
                                        'id': 3,
                                        'type': 'kitchen',
                                        'area': 45000,
                                        'recommendations': [
                                            {'item': 'dining_table_small', 'priority': 'recommended'},
                                            {'item': 'bar_stools', 'priority': 'optional'},
                                        ]
                                    }
                                ]
                            }
                            st.success("✅ تم التحليل (وضع تجريبي) | Analysis complete (demo mode)")
                            
                    except Exception as e:
                        st.error(f"❌ خطأ في التحليل: {str(e)}")
        
        # Display results
        if st.session_state.floor_plan_results:
            st.markdown("---")
            display_analysis_results(st.session_state.floor_plan_results)
    else:
        # Show example when no file uploaded
        st.info("👆 ارفع مخطط البناء للبدء | Upload a floor plan to get started")
        
        st.markdown("### 📝 أمثلة على أنواع الغرف | Room Types We Detect:")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            - 🛋️ غرفة المعيشة (Living Room)
            - 🛏️ غرفة النوم (Bedroom)
            - 🍽️ غرفة الطعام (Dining Room)
            """)
        with col2:
            st.markdown("""
            - 🍳 المطبخ (Kitchen)
            - 🚿 الحمام (Bathroom)
            - 💼 المكتب (Office)
            """)
        with col3:
            st.markdown("""
            - 📦 التخزين (Storage)
            - 🚶 الممر (Hallway)
            - 🛏️ غرفة النوم الرئيسية (Master Bedroom)
            """)

def render_alibaba_search():
    """Render the Alibaba furniture search interface."""
    st.markdown('<h2 class="sub-header">🔍 Alibaba Furniture Search | بحث أثاث Alibaba</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    Search for furniture products on Alibaba marketplace.
    ابحث عن منتجات الأثاث في سوق Alibaba.
    """)
    
    # Search form
    col1, col2 = st.columns([3, 1])
    
    with col1:
        keyword = st.text_input(
            "Search Keyword | كلمة البحث",
            placeholder="e.g., modern sofa, dining table, office chair",
            help="Enter the type of furniture you're looking for"
        )
    
    with col2:
        page_size = st.number_input(
            "Results per page",
            min_value=1,
            max_value=20,
            value=5,
            help="Number of results to display"
        )
    
    # Advanced filters
    with st.expander("🔧 Advanced Filters | فلاتر متقدمة"):
        col1, col2 = st.columns(2)
        with col1:
            min_price = st.number_input("Minimum Price (USD)", min_value=0, value=0)
            category = st.selectbox(
                "Category | الفئة",
                ["", "sofa", "chair", "table", "bed", "cabinet", "desk", "other"]
            )
        with col2:
            max_price = st.number_input("Maximum Price (USD)", min_value=0, value=10000)
            page = st.number_input("Page Number", min_value=1, value=1)
    
    if st.button("🔍 Search | بحث", type="primary"):
        if not keyword:
            st.error("❌ Please enter a search keyword | الرجاء إدخال كلمة بحث")
            return
        
        with st.spinner("Searching Alibaba... | جاري البحث في Alibaba..."):
            try:
                if MODULES_AVAILABLE:
                    scraper = AlibabaFurnitureScraper()
                    results = scraper.search_furniture(
                        keyword=keyword,
                        page=page,
                        page_size=page_size
                    )
                    
                    if results.get('success'):
                        st.session_state.alibaba_results = results
                        st.success(f"✅ Found {results.get('total_results', 0)} products!")
                    else:
                        st.error(f"❌ Search failed: {results.get('error', 'Unknown error')}")
                else:
                    # Demo mode
                    st.session_state.alibaba_results = {
                        'success': True,
                        'total_results': 3,
                        'products': [
                            {
                                'id': f'demo-{i}',
                                'title': f'Demo {keyword} Product {i+1}',
                                'price': {'amount': 100 + i*50, 'currency': 'USD'},
                                'image_url': 'https://via.placeholder.com/300',
                                'supplier': {'name': f'Demo Supplier {i+1}', 'rating': 4.5},
                                'moq': 10,
                                'url': '#'
                            }
                            for i in range(3)
                        ]
                    }
                    st.success("✅ Demo results generated!")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Display results
    if st.session_state.alibaba_results:
        results = st.session_state.alibaba_results
        products = results.get('products', [])
        
        if products:
            st.markdown(f"### 📦 Results ({len(products)} products)")
            
            for i, product in enumerate(products):
                with st.container():
                    col1, col2, col3 = st.columns([1, 2, 1])
                    
                    with col1:
                        if product.get('image_url'):
                            st.image(product['image_url'], use_container_width=True)
                    
                    with col2:
                        st.markdown(f"**{product.get('title', 'N/A')}**")
                        st.markdown(f"💰 Price: ${product.get('price', {}).get('amount', 'N/A')} {product.get('price', {}).get('currency', 'USD')}")
                        st.markdown(f"🏭 Supplier: {product.get('supplier', {}).get('name', 'N/A')} (⭐ {product.get('supplier', {}).get('rating', 'N/A')})")
                        st.markdown(f"📦 MOQ: {product.get('moq', 'N/A')} pieces")
                    
                    with col3:
                        if product.get('url') and product['url'] != '#':
                            st.link_button("View Product", product['url'], use_container_width=True)
                        st.button(f"Add to Cart", key=f"cart_{i}", disabled=True, use_container_width=True)
                    
                    st.markdown("---")

def render_floor_plan_analyzer():
    """Render the floor plan analyzer interface."""
    st.markdown('<h2 class="sub-header">📐 Floor Plan Analyzer | محلل المخططات الأرضية</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    Upload a floor plan image to analyze rooms and get furniture recommendations.
    قم بتحميل صورة مخطط أرضي لتحليل الغرف والحصول على توصيات الأثاث.
    """)
    
    uploaded_file = st.file_uploader(
        "Upload Floor Plan Image | تحميل صورة المخطط",
        type=['png', 'jpg', 'jpeg'],
        help="Upload a floor plan image (PNG, JPG, or JPEG)"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        min_room_area = st.slider("Minimum Room Area (pixels)", 1000, 20000, 5000)
    with col2:
        wall_thickness = st.slider("Wall Thickness (pixels)", 1, 20, 5)
    
    if uploaded_file is not None:
        # Display uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Floor Plan", use_container_width=True)
        
        if st.button("🔍 Analyze Floor Plan | تحليل المخطط", type="primary"):
            with st.spinner("Analyzing floor plan... | جاري تحليل المخطط..."):
                try:
                    if MODULES_AVAILABLE:
                        # Convert image to bytes
                        img_byte_arr = io.BytesIO()
                        image.save(img_byte_arr, format='PNG')
                        img_byte_arr = img_byte_arr.getvalue()
                        
                        # Create analyzer
                        analyzer = FloorPlanAnalyzer(
                            min_room_area=min_room_area,
                            wall_thickness=wall_thickness
                        )
                        
                        # Analyze
                        import cv2
                        import numpy as np
                        nparr = np.frombuffer(img_byte_arr, np.uint8)
                        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        preprocessed = analyzer.preprocess_image(img)
                        rooms = analyzer.detect_rooms(preprocessed)
                        
                        results = {
                            'success': True,
                            'rooms_detected': len(rooms),
                            'rooms': []
                        }
                        
                        for i, room in enumerate(rooms):
                            room_info = analyzer.classify_room(room)
                            recommendations = analyzer.recommend_furniture(room_info)
                            results['rooms'].append({
                                'id': i + 1,
                                'type': room_info['room_type'],
                                'area': room_info['area'],
                                'recommendations': recommendations
                            })
                        
                        st.session_state.floor_plan_results = results
                        st.success(f"✅ Analysis complete! Found {len(rooms)} room(s).")
                    else:
                        # Demo mode
                        st.session_state.floor_plan_results = {
                            'success': True,
                            'rooms_detected': 1,
                            'rooms': [{
                                'id': 1,
                                'type': 'living_room',
                                'area': 150000,
                                'recommendations': [
                                    {'item': 'sofa', 'priority': 'essential', 'quantity': 1},
                                    {'item': 'coffee_table', 'priority': 'essential', 'quantity': 1},
                                    {'item': 'tv_stand', 'priority': 'recommended', 'quantity': 1},
                                ]
                            }]
                        }
                        st.success("✅ Demo analysis complete!")
                        
                except Exception as e:
                    st.error(f"❌ Analysis failed: {str(e)}")
    
    # Display results
    if st.session_state.floor_plan_results:
        results = st.session_state.floor_plan_results
        
        if results.get('success'):
            st.markdown(f"### 📊 Analysis Results | نتائج التحليل")
            st.metric("Rooms Detected | الغرف المكتشفة", results['rooms_detected'])
            
            for room in results.get('rooms', []):
                with st.expander(f"🚪 Room {room['id']}: {room['type'].replace('_', ' ').title()}"):
                    st.markdown(f"**Area:** {room['area']:,} pixels²")
                    
                    st.markdown("**Furniture Recommendations:**")
                    for rec in room.get('recommendations', []):
                        priority_emoji = "⭐" if rec['priority'] == 'essential' else "💡"
                        st.markdown(f"{priority_emoji} **{rec['item'].replace('_', ' ').title()}** - {rec['priority']} (Qty: {rec['quantity']})")

def render_furniture_recommendations():
    """Render the furniture recommendations interface."""
    st.markdown('<h2 class="sub-header">💡 Furniture Recommendations | توصيات الأثاث</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    Get AI-powered furniture recommendations based on room type and size.
    احصل على توصيات الأثاث بالذكاء الاصطناعي بناءً على نوع الغرفة والحجم.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        room_type = st.selectbox(
            "Room Type | نوع الغرفة",
            ["living_room", "bedroom", "kitchen", "bathroom", "office", "dining_room"],
            format_func=lambda x: x.replace('_', ' ').title()
        )
    
    with col2:
        area_sqm = st.number_input(
            "Room Area (m²) | مساحة الغرفة",
            min_value=5.0,
            max_value=200.0,
            value=20.0,
            step=1.0
        )
    
    style = st.selectbox(
        "Style Preference | تفضيل الأسلوب",
        ["modern", "classic", "minimalist", "industrial", "scandinavian", "traditional"]
    )
    
    if st.button("💡 Get Recommendations | احصل على التوصيات", type="primary"):
        with st.spinner("Generating recommendations... | جاري إنشاء التوصيات..."):
            # Generate recommendations based on room type
            recommendations_map = {
                'living_room': [
                    {'item': 'Sofa', 'priority': 'Essential', 'price_range': '$500-$2000'},
                    {'item': 'Coffee Table', 'priority': 'Essential', 'price_range': '$100-$500'},
                    {'item': 'TV Stand', 'priority': 'Recommended', 'price_range': '$200-$800'},
                    {'item': 'Side Table', 'priority': 'Optional', 'price_range': '$50-$300'},
                    {'item': 'Bookshelf', 'priority': 'Optional', 'price_range': '$150-$600'},
                ],
                'bedroom': [
                    {'item': 'Bed', 'priority': 'Essential', 'price_range': '$300-$2000'},
                    {'item': 'Wardrobe', 'priority': 'Essential', 'price_range': '$400-$1500'},
                    {'item': 'Nightstand', 'priority': 'Recommended', 'price_range': '$100-$400'},
                    {'item': 'Dresser', 'priority': 'Recommended', 'price_range': '$300-$1000'},
                    {'item': 'Mirror', 'priority': 'Optional', 'price_range': '$50-$300'},
                ],
                'kitchen': [
                    {'item': 'Dining Table', 'priority': 'Essential', 'price_range': '$300-$1500'},
                    {'item': 'Dining Chairs', 'priority': 'Essential', 'price_range': '$200-$800'},
                    {'item': 'Kitchen Island', 'priority': 'Recommended', 'price_range': '$500-$2000'},
                    {'item': 'Bar Stools', 'priority': 'Optional', 'price_range': '$100-$400'},
                ],
                'office': [
                    {'item': 'Office Desk', 'priority': 'Essential', 'price_range': '$200-$1000'},
                    {'item': 'Office Chair', 'priority': 'Essential', 'price_range': '$150-$800'},
                    {'item': 'Bookshelf', 'priority': 'Recommended', 'price_range': '$150-$600'},
                    {'item': 'File Cabinet', 'priority': 'Optional', 'price_range': '$100-$500'},
                ],
            }
            
            recommendations = recommendations_map.get(room_type, [
                {'item': 'Custom Furniture', 'priority': 'Varies', 'price_range': 'Contact for quote'}
            ])
            
            st.success("✅ Recommendations generated!")
            
            st.markdown(f"### 🪑 Recommendations for {room_type.replace('_', ' ').title()} ({area_sqm}m²)")
            st.markdown(f"**Style:** {style.title()}")
            
            # Display as cards
            for rec in recommendations:
                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        priority_emoji = {"Essential": "⭐", "Recommended": "💡", "Optional": "💭"}.get(rec['priority'], "📌")
                        st.markdown(f"{priority_emoji} **{rec['item']}**")
                    with col2:
                        st.markdown(f"**{rec['priority']}**")
                    with col3:
                        st.markdown(f"`{rec['price_range']}`")
                    st.markdown("---")

def render_datasets():
    """Render the datasets information."""
    st.markdown('<h2 class="sub-header">📊 Datasets Information | معلومات مجموعات البيانات</h2>', unsafe_allow_html=True)
    
    # Load datasets catalog
    catalog_path = Path("datasets_catalog.json")
    if catalog_path.exists():
        with open(catalog_path) as f:
            datasets = json.load(f)
        
        st.markdown(f"**Total Datasets:** {len(datasets)}")
        
        for ds in datasets:
            with st.expander(f"📁 {ds['name']}"):
                st.markdown(f"**Owner:** {ds['owner']}")
                st.markdown(f"**Dataset:** {ds['dataset']}")
                st.markdown(f"**Description:** {ds.get('description', 'N/A')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Files:** {ds.get('files', 'N/A')}")
                with col2:
                    st.markdown(f"**Size:** {ds.get('size', 'N/A')}")
    else:
        st.info("📂 Datasets catalog not found. Please ensure datasets_catalog.json exists.")

def render_system_status():
    """Render system status and monitoring."""
    st.markdown('<h2 class="sub-header">💻 System Status | حالة النظام</h2>', unsafe_allow_html=True)
    
    # System information
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("System Version", "2.0.0")
        st.metric("Python Version", "3.10+")
    
    with col2:
        status = "🟢 Healthy" if MODULES_AVAILABLE else "🟡 Limited"
        st.metric("System Status", status)
        st.metric("Modules Loaded", "All" if MODULES_AVAILABLE else "Partial")
    
    with col3:
        st.metric("API Endpoints", "13")
        st.metric("Supported Models", "3")
    
    st.markdown("---")
    
    # Module status
    st.markdown("### 📦 Module Status")
    
    modules = [
        ("Alibaba Scraper", MODULES_AVAILABLE),
        ("Floor Plan Analyzer", MODULES_AVAILABLE),
        ("Model Training", MODULES_AVAILABLE),
        ("Data Processing", MODULES_AVAILABLE),
        ("Inference Engine", MODULES_AVAILABLE),
    ]
    
    for module, status in modules:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{module}**")
        with col2:
            if status:
                st.success("✅ Active")
            else:
                st.warning("⚠️ Demo Mode")
    
    st.markdown("---")
    
    # Configuration
    st.markdown("### ⚙️ Configuration")
    
    config_items = [
        ("CORS Origins", os.getenv("ALLOWED_ORIGINS", "*")),
        ("Environment", os.getenv("ENVIRONMENT", "development")),
        ("Log Level", "INFO"),
    ]
    
    for key, value in config_items:
        st.markdown(f"**{key}:** `{value}`")

def main():
    """Main application function."""
    render_header()
    
    # Sidebar navigation
    st.sidebar.title("🧭 التنقل | Navigation")
    
    pages = {
        "📐 رفع المخطط | Upload Plan": render_home,
        "💡 توصيات الأثاث | Recommendations": render_furniture_recommendations,
        "🔍 بحث المنتجات | Search Products": render_alibaba_search,
        "💻 حالة النظام | System Status": render_system_status,
    }
    
    selection = st.sidebar.radio("اختر الصفحة | Select Page", list(pages.keys()))
    
    # Information in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ حول النظام | About")
    st.sidebar.info("""
    **🪑 نظام تصميم الأثاث**
    **Furniture Design Suite**
    
    ارفع مخطط البناء واحصل على توصيات الأثاث المناسب لكل غرفة.
    
    Upload your floor plan and get AI-powered furniture recommendations.
    
    الإصدار | Version: 2.0.0
    """)
    
    # Quick help in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💡 نصائح | Tips")
    st.sidebar.markdown("""
    - استخدم صور واضحة للمخطط
    - تأكد من وضوح حدود الغرف
    - يمكنك تعديل إعدادات التحليل
    """)
    
    # Render selected page
    pages[selection]()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; padding: 2rem;'>
        <p>© 2026 نظام تصميم الأثاث | Furniture Design Suite</p>
        <p>صُمم بـ ❤️ باستخدام الذكاء الاصطناعي | Powered by AI</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
