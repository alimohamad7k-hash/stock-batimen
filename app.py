import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

# ---------------------------------------------------------
# PAGE CONFIG & FIXED CLEAN CSS STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="نظام إدارة مخزون البناء والمشاريع",
    page_icon="🏗️",
    layout="wide"
)

st.markdown("""
    <style>
    .stApp {
        background-color: #F8FAFC;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    h1, h2, h3 {
        color: #0F172A;
        font-weight: 700;
    }
    div[data-baseweb="select"] > div, input[type="text"], input[type="number"], textarea {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border-color: #CBD5E1 !important;
    }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border-right: 6px solid #3B82F6;
    }
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 800;
        color: #1E3A8A;
    }
    [data-testid="stMetricLabel"] {
        font-size: 14px !important;
        color: #64748B;
        font-weight: 600;
    }
    .stButton>button {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        color: white !important;
        font-weight: bold;
        border-radius: 10px;
        border: none;
        padding: 10px 24px;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%);
    }
    .stDownloadButton>button {
        background: linear-gradient(135deg, #16A34A 0%, #15803D 100%) !important;
        color: white !important;
        font-weight: bold;
        border-radius: 10px;
        border: none;
        padding: 10px 20px;
    }
    section[data-testid="stSidebar"] {
        background-color: #0F172A;
        border-left: 1px solid #1E293B;
    }
    section[data-testid="stSidebar"] .stRadio, section[data-testid="stSidebar"] .stSelectbox label, section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div {
        color: #F8FAFC !important;
    }
    div[data-testid="stForm"] {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 16px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
    }
    .receipt-box {
        background-color: #ffffff;
        border: 2px solid #0F172A;
        padding: 30px;
        border-radius: 10px;
        color: #000000;
        font-family: Arial, sans-serif;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DATABASE INITIALIZATION
# ---------------------------------------------------------
DB_NAME = "stock_batimen_pro.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT UNIQUE NOT NULL,
            quantity REAL NOT NULL DEFAULT 0,
            min_limit REAL NOT NULL DEFAULT 5,
            buy_price REAL NOT NULL DEFAULT 0,
            sell_price REAL NOT NULL DEFAULT 0,
            unit TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            type TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL DEFAULT 0,
            total_price REAL DEFAULT 0,
            date TEXT NOT NULL,
            entity TEXT,
            ref_num TEXT,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_connection():
    return sqlite3.connect(DB_NAME)

# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------
st.sidebar.title("🏗️ BTP Stock Pro")
st.sidebar.markdown("<p style='color: #94A3B8; font-size: 13px;'>نظام إدارة وتتبع مواد البناء والمشاريع</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

menu = [
    "📊 لوحة التحكم", 
    "📥 تسجيل دخول سلعة", 
    "📤 تسجيل خروج سلعة للورش", 
    "🖨️ طباعة وصل التسليم (Bon de Livraison)",
    "➕ إضافة مادة جديدة",
    "🔐 إدارة وتعديل المواد والحركات (محمي)",
    "📜 السجل والتقارير",
    "💾 النسخ الاحتياطي"
]
choice = st.sidebar.selectbox("القائمة الرئيسية", menu)

# ---------------------------------------------------------
# 1. DASHBOARD
# ---------------------------------------------------------
if choice == "📊 لوحة التحكم":
    st.title("📊 لوحة القيادة والمؤشرات الرئيسية")
    st.markdown("<p style='color: #64748B;'>نظرة عامة على وضعية المخزون والقيمة الإجمالية للسلع.</p>", unsafe_allow_html=True)
    st.write("")
    
    conn = get_connection()
    df_stock = pd.read_sql_query("SELECT * FROM inventory", conn)
    conn.close()
    
    if not df_stock.empty:
        df_stock['total_value'] = df_stock['quantity'] * df_stock['buy_price']
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 قيمة السطوك", f"{df_stock['total_value'].sum():,.2f} DH")
        col2.metric("📦 أنواع السلع", len(df_stock))
        
        low_stock_count = len(df_stock[df_stock['quantity'] <= df_stock['min_limit']])
        col3.metric("⚠️ مواد قريبة من النفاد", low_stock_count)
        col4.metric("📈 متوسط ثمن الشراء", f"{df_stock['buy_price'].mean():,.2f} DH")
        
        st.write("---")
        
        if low_stock_count > 0:
            st.error("⚠️ **تنبيه هام: السلع التالية وصلت للحد الأدنى للمخزون أو أقل:**")
            low_df = df_stock[df_stock['quantity'] <= df_stock['min_limit']]
            st.dataframe(low_df[['item_name', 'quantity', 'min_limit', 'unit']], use_container_width=True)
            st.write("---")
            
        st.subheader("📋 جدول المخزون الحالي")
        search_query = st.text_input("🔍 بحث سريع في السطوك:", "")
        
        if search_query:
            filtered_df = df_stock[df_stock['item_name'].str.contains(search_query, case=False, na=False)]
        else:
            filtered_df = df_stock

        display_df = filtered_df.rename(columns={
            'item_name': 'المادة',
            'quantity': 'الكمية الحالية',
            'min_limit': 'الحد الأدنى',
            'unit': 'الوحدة',
            'buy_price': 'سعر الشراء الافتراضي (DH)',
            'sell_price': 'سعر البيع الافتراضي (DH)',
            'total_value': 'إجمالي القيمة (DH)'
        })
        st.dataframe(display_df.drop(columns=['id']), use_container_width=True)
    else:
        st.info("💡 لا توجد مواد مسجلة حتى الآن في النظام.")

# ---------------------------------------------------------
# 2. ENTRÉE / RÉCEPTION
# ---------------------------------------------------------
elif choice == "📥 تسجيل دخول سلعة":
    st.subheader("📥 تسجيل دخول سلعة من المورد (Fournisseur)")
    st.markdown("<p style='color: #64748B;'>أدخل تفاصيل الشحنة المستلمة مع تحديد ثمن الشراء الخاص بالمورد.</p>", unsafe_allow_html=True)
    st.write("")
    
    conn = get_connection()
    df_items = pd.read_sql_query("SELECT item_name, buy_price FROM inventory", conn)
    conn.close()
    
    if df_items.empty:
        st.warning("المرجو إضافة مواد في النظام أولاً.")
    else:
        with st.form("in_form"):
            col1, col2 = st.columns(2)
            with col1:
                selected_item = st.selectbox("اختر المادة:", df_items["item_name"].tolist())
                default_buy = float(df_items[df_items["item_name"] == selected_item]["buy_price"].values[0])
                qty_in = st.number_input("الكمية المضافة:", min_value=0.1, value=1.0)
                custom_buy_price = st.number_input("ثمن الشراء من عند المورد (DH):", min_value=0.0, value=default_buy)
            with col2:
                supplier = st.text_input("اسم المورد (Fournisseur):")
                ref_num = st.text_input("رقم الفاتورة أو البون (N° Bon):")
                notes = st.text_input("ملاحظات إضافية:")
            
            st.write("")
            if st.form_submit_button("✅ تأكيد تسجيل الدخول"):
                total_cost = qty_in * custom_buy_price
                conn = get_connection()
                c = conn.cursor()
                c.execute("UPDATE inventory SET quantity = quantity + ?, buy_price = ? WHERE item_name = ?", (qty_in, custom_buy_price, selected_item))
                c.execute("""
                    INSERT INTO transactions (item_name, type, quantity, unit_price, total_price, date, entity, ref_num, notes) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (selected_item, "دخول", qty_in, custom_buy_price, total_cost, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), supplier, ref_num, notes))
                conn.commit()
                conn.close()
                st.success(f"تمت إضافة الكمية للمادة '{selected_item}' بنجاح!")
                st.rerun()

# ---------------------------------------------------------
# 3. SORTIE / CHANTIER (WITH AUTOMATIC BL GENERATION)
# ---------------------------------------------------------
elif choice == "📤 تسجيل خروج سلعة للورش":
    st.subheader("📤 تسجيل خروج سلعة إلى ورش البناء (Chantier)")
    st.markdown("<p style='color: #64748B;'>حدد الكمية الخارجة وثمن البيع المخصص لكل ورش أو زبون لاستخراج وصل التسليم فوراً.</p>", unsafe_allow_html=True)
    st.write("")
    
    conn = get_connection()
    df_inv = pd.read_sql_query("SELECT item_name, quantity, sell_price, unit FROM inventory", conn)
    conn.close()
    
    if df_inv.empty:
        st.warning("لا توجد مواد مسجلة.")
    else:
        with st.form("out_form"):
            col1, col2 = st.columns(2)
            with col1:
                selected_item = st.selectbox("اختر المادة:", df_inv["item_name"].tolist())
                item_row_data = df_inv[df_inv["item_name"] == selected_item].iloc[0]
                default_sell = float(item_row_data['sell_price'])
                st.info(f"المتوفر حالياً: **{item_row_data['quantity']} {item_row_data['unit']}**")
                qty_out = st.number_input("الكمية الخارجة:", min_value=0.1, value=1.0)
                custom_sell_price = st.number_input("ثمن البيع للوحدة (DH):", min_value=0.0, value=default_sell)
            with col2:
                chantier = st.text_input("اسم الورشة أو الزبون (Client / Chantier):")
                ref_num = st.text_input("رقم بون الخروج (N° Bon):")
                notes = st.text_input("المسؤول أو السائق (Responsable / Notes):")
            
            st.write("")
            submit_out = st.form_submit_button("🚀 تأكيد الخروج وإصدار البون")
            
        if submit_out:
            if item_row_data['quantity'] >= qty_out:
                total_amt = qty_out * custom_sell_price
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                conn = get_connection()
                c = conn.cursor()
                c.execute("UPDATE inventory SET quantity = quantity - ? WHERE item_name = ?", (qty_out, selected_item))
                c.execute("""
                    INSERT INTO transactions (item_name, type, quantity, unit_price, total_price, date, entity, ref_num, notes) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (selected_item, "خروج", qty_out, custom_sell_price, total_amt, current_time, chantier, ref_num, notes))
                
                last_id = c.lastrowid
                conn.commit()
                conn.close()
                
                st.success("✅ تم تسجيل خروج السلعة بنجاح! إليك وصل التسليم الخاص بهذه العملية:")
                
                html_bon = f"""
                <div class="receipt-box">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0F172A; padding-bottom: 15px; margin-bottom: 25px;">
                        <div>
                            <h2 style="margin: 0; color: #0F172A; font-size: 22px;">شركة مواد البناء والخدمات</h2>
                            <p style="margin: 5px 0 0 0; font-size: 13px; color: #64748B;">Société de Matériaux de Construction</p>
                        </div>
                        <div style="text-align: left;">
                            <h3 style="margin: 0; color: #2563EB; font-size: 20px;">BON DE LIVRAISON</h3>
                            <p style="margin: 5px 0 0 0; font-size: 14px;"><b>رقم البون الداخلي (ID):</b> #{last_id}</p>
                            <p style="margin: 3px 0 0 0; font-size: 14px;"><b>التاريخ:</b> {current_time}</p>
                        </div>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; background-color: #F8FAFC; padding: 15px; border-radius: 8px; margin-bottom: 25px; border: 1px solid #E2E8F0;">
                        <div>
                            <p style="margin: 0 0 8px 0; font-size: 15px;">🏢 <b>اسم الورشة / الزبون:</b> <span style="color: #1E3A8A;">{chantier if chantier else 'غير محدد'}</span></p>
                            <p style="margin: 0; font-size: 15px;">📌 <b>رقم بون الخروج:</b> {ref_num if ref_num else '—'}</p>
                        </div>
                        <div>
                            <p style="margin: 0; font-size: 15px;">👤 <b>المسؤول / السائق:</b> <span style="color: #1E3A8A;">{notes if notes else '—'}</span></p>
                        </div>
                    </div>
                    
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px; text-align: center;">
                        <thead>
                            <tr style="background-color: #1E3A8A; color: white;">
                                <th style="padding: 12px; border: 1px solid #CBD5E1;">المادة (Désignation)</th>
                                <th style="padding: 12px; border: 1px solid #CBD5E1;">الكمية (Quantité)</th>
                                <th style="padding: 12px; border: 1px solid #CBD5E1;">ثمن البيع للوحدة (Prix Unitaire)</th>
                                <th style="padding: 12px; border: 1px solid #CBD5E1;">المبلغ الإجمالي (Total)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="padding: 14px; border: 1px solid #CBD5E1;"><b>{selected_item}</b></td>
                                <td style="padding: 14px; border: 1px solid #CBD5E1;"><b>{qty_out}</b></td>
                                <td style="padding: 14px; border: 1px solid #CBD5E1;">{custom_sell_price:,.2f} DH</td>
                                <td style="padding: 14px; border: 1px solid #CBD5E1; color: #16A34A; font-weight: bold;">{total_amt:,.2f} DH</td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <div style="display: flex; justify-content: space-between; margin-top: 50px; padding-top: 20px; border-top: 1px dashed #CBD5E1;">
                        <div style="text-align: center; width: 40%;">
                            <p style="margin-bottom: 40px;"><b>توقيع وخاتم الشركة</b></p>
                            <p>________________________________</p>
                        </div>
                        <div style="text-align: center; width: 40%;">
                            <p style="margin-bottom: 40px;"><b>توقيع المسؤول / المستلم</b></p>
                            <p>________________________________</p>
                        </div>
                    </div>
                </div>
                """
                # FIXED: Added unsafe_allow_html=True here!
                st.markdown(html_bon, unsafe_allow_html=True)
                st.write("")
                st.info("💡 للطباعة المباشرة: اضغط على **Ctrl + P** (أو Cmd + P في Mac) واطبع الوصل.")
            else:
                st.error("الكمية المطلوبة أكبر من المتوفر في السطوك!")

# ---------------------------------------------------------
# 4. BON DE LIVRAISON (PRINT & EXPORT ARCHIVE)
# ---------------------------------------------------------
elif choice == "🖨️ طباعة وصل التسليم (Bon de Livraison)":
    st.subheader("🖨️ أرشيف وربط وصولات التسليم (Bon de Livraison)")
    st.markdown("<p style='color: #64748B;'>اختر أي عملية خروج سابقة لاستخراج وصل التسليم الخاص بها.</p>", unsafe_allow_html=True)
    st.write("")
    
    conn = get_connection()
    df_out = pd.read_sql_query("SELECT * FROM transactions WHERE type='خروج' ORDER BY id DESC", conn)
    conn.close()
    
    if df_out.empty:
        st.info("لا توجد أي عمليات خروج مسجلة حتى الآن.")
    else:
        out_options = [f"عملية ID: {row['id']} | التاريخ: {row['date']} | الورش: {row['entity']} | المادة: {row['item_name']}" for _, row in df_out.iterrows()]
        selected_out_str = st.selectbox("اختر العملية المراد استخراج وصل لها:", out_options)
        
        if selected_out_str:
            selected_id = int(selected_out_str.split("|")[0].replace("عملية ID:", "").strip())
            trans_row = df_out[df_out['id'] == selected_id].iloc[0]
            
            st.write("---")
            st.markdown("### 📄 معاينة وصل التسليم")
            
            html_bon = f"""
            <div class="receipt-box">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0F172A; padding-bottom: 15px; margin-bottom: 25px;">
                    <div>
                        <h2 style="margin: 0; color: #0F172A; font-size: 22px;">شركة مواد البناء والخدمات</h2>
                        <p style="margin: 5px 0 0 0; font-size: 13px; color: #64748B;">Société de Matériaux de Construction</p>
                    </div>
                    <div style="text-align: left;">
                        <h3 style="margin: 0; color: #2563EB; font-size: 20px;">BON DE LIVRAISON</h3>
                        <p style="margin: 5px 0 0 0; font-size: 14px;"><b>رقم البون الداخلي (ID):</b> #{trans_row['id']}</p>
                        <p style="margin: 3px 0 0 0; font-size: 14px;"><b>التاريخ:</b> {trans_row['date']}</p>
                    </div>
                </div>
                
                <div style="display: flex; justify-content: space-between; background-color: #F8FAFC; padding: 15px; border-radius: 8px; margin-bottom: 25px; border: 1px solid #E2E8F0;">
                    <div>
                        <p style="margin: 0 0 8px 0; font-size: 15px;">🏢 <b>اسم الورشة / الزبون:</b> <span style="color: #1E3A8A;">{trans_row['entity'] if trans_row['entity'] else 'غير محدد'}</span></p>
                        <p style="margin: 0; font-size: 15px;">📌 <b>رقم بون الخروج:</b> {trans_row['ref_num'] if trans_row['ref_num'] else '—'}</p>
                    </div>
                    <div>
                        <p style="margin: 0; font-size: 15px;">👤 <b>المسؤول / السائق:</b> <span style="color: #1E3A8A;">{trans_row['notes'] if trans_row['notes'] else '—'}</span></p>
                    </div>
                </div>
                
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px; text-align: center;">
                    <thead>
                        <tr style="background-color: #1E3A8A; color: white;">
                            <th style="padding: 12px; border: 1px solid #CBD5E1;">المادة (Désignation)</th>
                            <th style="padding: 12px; border: 1px solid #CBD5E1;">الكمية (Quantité)</th>
                            <th style="padding: 12px; border: 1px solid #CBD5E1;">ثمن البيع للوحدة (Prix Unitaire)</th>
                            <th style="padding: 12px; border: 1px solid #CBD5E1;">المبلغ الإجمالي (Total)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding: 14px; border: 1px solid #CBD5E1;"><b>{trans_row['item_name']}</b></td>
                            <td style="padding: 14px; border: 1px solid #CBD5E1;"><b>{trans_row['quantity']}</b></td>
                            <td style="padding: 14px; border: 1px solid #CBD5E1;">{trans_row['unit_price']:,.2f} DH</td>
                            <td style="padding: 14px; border: 1px solid #CBD5E1; color: #16A34A; font-weight: bold;">{trans_row['total_price']:,.2f} DH</td>
                        </tr>
                    </tbody>
                </table>
                
                <div style="display: flex; justify-content: space-between; margin-top: 50px; padding-top: 20px; border-top: 1px dashed #CBD5E1;">
                    <div style="text-align: center; width: 40%;">
                        <p style="margin-bottom: 40px;"><b>توقيع وخاتم الشركة</b></p>
                        <p>________________________________</p>
                    </div>
                    <div style="text-align: center; width: 40%;">
                        <p style="margin-bottom: 40px;"><b>توقيع المسؤول / المستلم</b></p>
                        <p>________________________________</p>
                    </div>
                </div>
            </div>
            """
            # FIXED: Added unsafe_allow_html=True here too!
            st.markdown(html_bon, unsafe_allow_html=True)
            st.write("")
            st.info("💡 للطباعة المباشرة: اضغط على **Ctrl + P** (أو Cmd + P في جهاز Mac).")

# ---------------------------------------------------------
# 5. ADD ITEM
# ---------------------------------------------------------
elif choice == "➕ إضافة مادة جديدة":
    st.subheader("➕ إضافة مادة بناء جديدة للقائمة")
    st.markdown("<p style='color: #64748B;'>تسجيل مادة جديدة وتحديد وحدتها والحد الأدنى للتنبيه.</p>", unsafe_allow_html=True)
    st.write("")
    
    with st.form("add_item_form"):
        col1, col2 = st.columns(2)
        with col1:
            item_name = st.text_input("اسم المادة (Ciment, Fer 12, etc.):")
            unit = st.selectbox("وحدة القياس", ["Sac", "Kg", "Tonne", "Unité", "m³", "Mètre"])
            initial_qty = st.number_input("الكمية الأولية", min_value=0.0, value=0.0)
        with col2:
            min_limit = st.number_input("حد التنبيه الأدنى (Min Stock)", min_value=0.0, value=10.0)
            buy_price = st.number_input("سعر الشراء الافتراضي (DH)", min_value=0.0, value=0.0)
            sell_price = st.number_input("سعر البيع الافتراضي (DH)", min_value=0.0, value=0.0)

        st.write("")
        if st.form_submit_button("💾 إضافة المادة بنجاح"):
            if item_name.strip() != "":
                conn = get_connection()
                c = conn.cursor()
                try:
                    c.execute("""
                        INSERT INTO inventory (item_name, quantity, min_limit, buy_price, sell_price, unit) 
                        VALUES (?, ?, ?, ?, ?, ?)""", 
                        (item_name.strip(), initial_qty, min_limit, buy_price, sell_price, unit))
                    if initial_qty > 0:
                        c.execute("""
                            INSERT INTO transactions (item_name, type, quantity, unit_price, total_price, date, notes) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (item_name.strip(), "دخول", initial_qty, buy_price, initial_qty * buy_price, 
                             datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "مخزون أولي"))
                    conn.commit()
                    st.success("تمت إضافة المادة بنجاح!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("هذه المادة توجد بالفعل في السطوك!")
                finally:
                    conn.close()

# ---------------------------------------------------------
# 6. EDIT / DELETE ITEMS & TRANSACTIONS (PROTECTED BY PASSWORD)
# ---------------------------------------------------------
elif choice == "🔐 إدارة وتعديل المواد والحركات (محمي)":
    st.subheader("🔐 صفحة محمية: إدارة، تعديل، وتصحيح الأخطاء")
    st.markdown("<p style='color: #64748B;'>منطقة خاصة بالمسؤول لتعديل الأثمنة أو حذف الحركات الخاطئة.</p>", unsafe_allow_html=True)
    st.write("")
    
    ADMIN_PASSWORD = "admin123"
    password_input = st.text_input("أدخل كلمة سر المسؤول (Admin Password):", type="password")
    
    if password_input == ADMIN_PASSWORD:
        st.success("مرحبا بك يا مسؤول، تم التحقق بنجاح.")
        st.write("")
        
        tab1, tab2 = st.tabs(["🛠️ تعديل أو حذف المواد", "📜 إدارة وتصحيح الحركات السابقة"])
        
        with tab1:
            conn = get_connection()
            df_inv = pd.read_sql_query("SELECT * FROM inventory", conn)
            conn.close()
            
            if not df_inv.empty:
                selected_item = st.selectbox("اختر المادة للتعديل:", df_inv["item_name"].tolist(), key="inv_select")
                item_row = df_inv[df_inv["item_name"] == selected_item].iloc[0]
                
                with st.form("edit_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_min = st.number_input("تعديل حد التنبيه الأدنى:", min_value=0.0, value=float(item_row['min_limit']))
                        new_buy = st.number_input("تعديل ثمن الشراء الافتراضي (DH):", min_value=0.0, value=float(item_row['buy_price']))
                    with col2:
                        new_sell = st.number_input("تعديل ثمن البيع الافتراضي (DH):", min_value=0.0, value=float(item_row['sell_price']))
                        new_unit = st.selectbox("تعديل الوحدة:", ["Sac", "Kg", "Tonne", "Unité", "m³", "Mètre"])
                    
                    st.write("")
                    if st.form_submit_button("✏️ تحديث بيانات المادة"):
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("""
                            UPDATE inventory 
                            SET min_limit=?, buy_price=?, sell_price=?, unit=? 
                            WHERE item_name=?
                        """, (new_min, new_buy, new_sell, new_unit, selected_item))
                        conn.commit()
                        conn.close()
                        st.success("تم التحديث بنجاح!")
                        st.rerun()

                st.write("---")
                if st.button(f"🗑️ حذف المادة '{selected_item}' نهائياً"):
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("DELETE FROM inventory WHERE item_name=?", (selected_item,))
                    conn.commit()
                    conn.close()
                    st.warning("تم الحذف بنجاح!")
                    st.rerun()
            else:
                st.info("لا توجد مواد في المخزون للتعديل.")

        with tab2:
            st.write("اختر الحركة التي وقع فيها خطأ لحذفها وتصحيح المخزون تلقائياً:")
            conn = get_connection()
            df_trans = pd.read_sql_query("SELECT * FROM transactions ORDER BY id DESC", conn)
            conn.close()
            
            if not df_trans.empty:
                trans_options = [f"ID: {row['id']} | {row['date']} | {row['type']} | {row['item_name']} | كمية: {row['quantity']}" for index, row in df_trans.iterrows()]
                selected_trans_str = st.selectbox("اختر الحركة:", trans_options)
                
                if selected_trans_str:
                    trans_id = int(selected_trans_str.split("|")[0].replace("ID:", "").strip())
                    trans_row = df_trans[df_trans['id'] == trans_id].iloc[0]
                    
                    st.info(f"تفاصيل الحركة: المادة (**{trans_row['item_name']}**) | النوع: **{trans_row['type']}** | الكمية: **{trans_row['quantity']}**")
                    
                    if st.button("🗑️ حذف هذه الحركة وإصلاح السطوك"):
                        conn = get_connection()
                        c = conn.cursor()
                        if trans_row['type'] == 'دخول':
                            c.execute("UPDATE inventory SET quantity = quantity - ? WHERE item_name = ?", (trans_row['quantity'], trans_row['item_name']))
                        else:
                            c.execute("UPDATE inventory SET quantity = quantity + ? WHERE item_name = ?", (trans_row['quantity'], trans_row['item_name']))
                        
                        c.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
                        conn.commit()
                        conn.close()
                        st.success("تمت عملية الإصلاح بنجاح!")
                        st.rerun()
            else:
                st.info("لا توجد أي حركات مسجلة لتصحيحها.")
            
    elif password_input != "":
        st.error("❌ كلمة السر غير صحيحة!")

# ---------------------------------------------------------
# 6. HISTORIQUE & EXCEL
# ---------------------------------------------------------
elif choice == "📜 السجل والتقارير":
    st.subheader("📜 تاريخ الحركات ومجموع المبالغ اليومية")
    st.markdown("<p style='color: #64748B;'>سجل شامل لكل عمليات الدخول والخروج مع إمكانية التحميل بصيغة Excel.</p>", unsafe_allow_html=True)
    st.write("")
    
    conn = get_connection()
    df_trans = pd.read_sql_query("""
        SELECT date, item_name, type, quantity, unit_price, total_price, entity, ref_num, notes 
        FROM transactions ORDER BY id DESC""", conn)
    conn.close()
    
    if not df_trans.empty:
        df_trans['day'] = pd.to_datetime(df_trans['date']).dt.strftime('%Y-%m-%d')
        
        display_df = df_trans[['date', 'item_name', 'type', 'quantity', 'unit_price', 'total_price', 'entity', 'ref_num', 'notes']].rename(columns={
            'date': 'التاريخ والوقت',
            'item_name': 'المادة',
            'type': 'الحركة (دخول/خروج)',
            'quantity': 'الكمية',
            'unit_price': 'ثمن الوحدة (DH)',
            'total_price': 'المبلغ الإجمالي للحركة (DH)',
            'entity': 'الجهة (المورد/الورش)',
            'ref_num': 'المرجع',
            'notes': 'ملاحظات'
        })
        
        st.dataframe(display_df, use_container_width=True)
        
        st.write("---")
        st.subheader("📅 ملخص المجاميع المالية حسب الأيام")
        
        df_trans['date_only'] = pd.to_datetime(df_trans['date']).dt.date
        daily_summary = df_trans.groupby(['date_only', 'type'])['total_price'].sum().unstack(fill_value=0)
        
        if 'دخول' in daily_summary.columns:
            daily_summary = daily_summary.rename(columns={'دخول': 'إجمالي المشتريات (دخول) DH'})
        if 'خروج' in daily_summary.columns:
            daily_summary = daily_summary.rename(columns={'خروج': 'إجمالي المبيعات (خروج) DH'})
            
        st.dataframe(daily_summary, use_container_width=True)
        st.write("")
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            display_df.to_excel(writer, index=False, sheet_name='Historique_Stock')
            daily_summary.to_excel(writer, sheet_name='Totaux_Par_Jour')
        
        st.download_button(
            label="📊 تحميل السجل والتقارير بصيغة Excel",
            data=buffer.getvalue(),
            file_name=f"rapport_stock_{datetime.now().strftime('%Y_%m_%d')}.xlsx",
            mime="application/vnd.ms-excel"
        )
    else:
        st.info("لا توجد أي حركات مسجلة حتى الآن.")

# ---------------------------------------------------------
# 7. BACKUP DATABASE
# ---------------------------------------------------------
elif choice == "💾 النسخ الاحتياطي":
    st.subheader("💾 حفظ نسخة احتياطية من قاعدة البيانات")
    st.markdown("<p style='color: #64748B;'>تحميل نسخة أمان لملف قاعدة البيانات للاحتفاظ بها.</p>", unsafe_allow_html=True)
    st.write("")
    
    try:
        with open(DB_NAME, "rb") as fp:
            st.download_button(
                label="📥 تحميل ملف قاعدة البيانات (.db)",
                data=fp,
                file_name=f"stock_batimen_backup_{datetime.now().strftime('%Y_%m_%d')}.db",
                mime="application/x-sqlite3"
            )
    except FileNotFoundError:
        st.error("لم يتم العثور على قاعدة البيانات بعد.")
