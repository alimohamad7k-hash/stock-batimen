import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

# ---------------------------------------------------------
# PAGE CONFIG & CUSTOM CSS (STYLING)
# ---------------------------------------------------------
st.set_page_config(
    page_title="نظام إدارة مخزون البناء والمشاريع",
    page_icon="🏗️",
    layout="wide"
)

st.markdown("""
    <style>
    h1, h2, h3 {
        color: #1E3A8A;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    [data-testid="stMetricValue"] {
        font-size: 24px !important;
        font-weight: bold;
        color: #0F766E;
    }
    [data-testid="stMetric"] {
        background-color: #F3F4F6;
        padding: 15px;
        border-radius: 12px;
        border-right: 5px solid #2563EB;
        box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.05);
    }
    .stDownloadButton>button {
        background-color: #16A34A !important;
        color: white !important;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 8px 16px;
    }
    .stDownloadButton>button:hover {
        background-color: #15803D !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC;
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
st.sidebar.markdown("---")

menu = [
    "📊 لوحة التحكم", 
    "📥 تسجيل دخول سلعة", 
    "📤 تسجيل خروج سلعة للورش", 
    "➕ إضافة مادة جديدة",
    "🔐 إدارة وتعديل المواد (محمي)",
    "📜 السجل والتقارير",
    "💾 النسخ الاحتياطي"
]
choice = st.sidebar.selectbox("القائمة الرئيسية", menu)

# ---------------------------------------------------------
# 1. DASHBOARD
# ---------------------------------------------------------
if choice == "📊 لوحة التحكم":
    st.title("📊 لوحة القيادة والمؤشرات الرئيسية")
    
    conn = get_connection()
    df_stock = pd.read_sql_query("SELECT * FROM inventory", conn)
    conn.close()
    
    if not df_stock.empty:
        df_stock['total_value'] = df_stock['quantity'] * df_stock['buy_price']
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 القيمة الإجمالية للسطوك", f"{df_stock['total_value'].sum():,.2f} DH")
        col2.metric("📦 عدد أنواع السلع", len(df_stock))
        
        low_stock_count = len(df_stock[df_stock['quantity'] <= df_stock['min_limit']])
        col3.metric("⚠️ مواد قريبة من النفاد", low_stock_count, delta_color="inverse")
        col4.metric("📈 متوسط سعر الشراء", f"{df_stock['buy_price'].mean():,.2f} DH")
        
        st.write("---")
        
        if low_stock_count > 0:
            st.error("⚠️ **تنبيه: السلع التالية وصلت للحد الأدنى للمخزون:**")
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
    st.subheader("📥 تسجيل دخول سلعة من المورد (مع تحديد ثمن الشراء)")
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
                custom_buy_price = st.number_input("ثمن الشراء من عند هاد المورد (DH):", min_value=0.0, value=default_buy)
            with col2:
                supplier = st.text_input("اسم المورد (Fournisseur):")
                ref_num = st.text_input("رقم الفاتورة أو البون (N° Bon):")
                notes = st.text_input("ملاحظات إضافية:")
            
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
                st.success(f"تمت إضافة الكمية للمادة '{selected_item}' بنجاح بثمن شراء {custom_buy_price} DH!")
                st.rerun()

# ---------------------------------------------------------
# 3. SORTIE / CHANTIER
# ---------------------------------------------------------
elif choice == "📤 تسجيل خروج سلعة للورش":
    st.subheader("📤 تسجيل خروج سلعة إلى ورش البناء (مع تحديد ثمن البيع للزبون)")
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
                custom_sell_price = st.number_input("ثمن البيع لهذا الزبون / الورش (DH):", min_value=0.0, value=default_sell)
            with col2:
                chantier = st.text_input("اسم الورش أو الزبون (Client / Chantier):")
                ref_num = st.text_input("رقم إذن الخروج (Bon de sortie):")
                notes = st.text_input("ملاحظات (اسم السائق / المسؤول):")
            
            if st.form_submit_button("🚀 تأكيد الخروج"):
                if item_row_data['quantity'] >= qty_out:
                    total_amt = qty_out * custom_sell_price
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("UPDATE inventory SET quantity = quantity - ? WHERE item_name = ?", (qty_out, selected_item))
                    c.execute("""
                        INSERT INTO transactions (item_name, type, quantity, unit_price, total_price, date, entity, ref_num, notes) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (selected_item, "خروج", qty_out, custom_sell_price, total_amt, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), chantier, ref_num, notes))
                    conn.commit()
                    conn.close()
                    st.success(f"تم تسجيل الخروج بنجاح بثمن بيع {custom_sell_price} DH للوحدة!")
                    st.rerun()
                else:
                    st.error("الكمية المطلوبة أكبر من المتوفر في السطوك!")

# ---------------------------------------------------------
# 4. ADD ITEM
# ---------------------------------------------------------
elif choice == "➕ إضافة مادة جديدة":
    st.subheader("➕ إضافة مادة بناء جديدة للقائمة")
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

        if st.form_submit_button("💾 إضافة المادة"):
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
                    st.error("هذه المادة توجد بالفعل!")
                finally:
                    conn.close()

# ---------------------------------------------------------
# 5. EDIT / DELETE ITEMS (PROTECTED BY PASSWORD)
# ---------------------------------------------------------
elif choice == "🔐 إدارة وتعديل المواد (محمي)":
    st.subheader("🔐 صفحة محمية: تعديل أو حذف المواد (المسؤول فقط)")
    
    ADMIN_PASSWORD = "admin123"
    password_input = st.text_input("أدخل كلمة سر المسؤول (Admin Password):", type="password")
    
    if password_input == ADMIN_PASSWORD:
        st.success("مرحبا بك يا باشا، تم التحقق بنجاح.")
        
        conn = get_connection()
        df_inv = pd.read_sql_query("SELECT * FROM inventory", conn)
        conn.close()
        
        if not df_inv.empty:
            selected_item = st.selectbox("اختر المادة للتعديل:", df_inv["item_name"].tolist())
            item_row = df_inv[df_inv["item_name"] == selected_item].iloc[0]
            
            with st.form("edit_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_min = st.number_input("تعديل حد التنبيه الأدنى:", min_value=0.0, value=float(item_row['min_limit']))
                    new_buy = st.number_input("تعديل ثمن الشراء الافتراضي (DH):", min_value=0.0, value=float(item_row['buy_price']))
                with col2:
                    new_sell = st.number_input("تعديل ثمن البيع الافتراضي (DH):", min_value=0.0, value=float(item_row['sell_price']))
                    new_unit = st.selectbox("تعديل الوحدة:", ["Sac", "Kg", "Tonne", "Unité", "m³", "Mètre"])
                
                if st.form_submit_button("✏️ تحديث البيانات"):
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
            st.subheader("❌ منطقة الخطر")
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
            
    elif password_input != "":
        st.error("❌ كلمة السر غير صحيحة!")

# ---------------------------------------------------------
# 6. HISTORIQUE & EXCEL
# ---------------------------------------------------------
elif choice == "📜 السجل والتقارير":
    st.subheader("📜 تاريخ الحركات ومجموع المبالغ اليومية")
    conn = get_connection()
    df_trans = pd.read_sql_query("""
        SELECT date, item_name, type, quantity, unit_price, total_price, entity, ref_num, notes 
        FROM transactions ORDER BY id DESC""", conn)
    conn.close()
    
    if not df_trans.empty:
        # استخراج التاريخ فقط (بدون توقيت الساعات) لحساب المجموع اليومي
        df_trans['day'] = pd.to_datetime(df_trans['date']).dt.strftime('%Y-%m-%d')
        
        # عرض الجدول بشكل منظّم ومفهوم باللغة العربية
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
        
        # حساب مجموع الفلوس لكل يوم حسب نوع الحركة (دخول أو خروج)
        # نقوم بتقسيم التاريخ إلى تاريخ فقط
        df_trans['date_only'] = pd.to_datetime(df_trans['date']).dt.date
        
        daily_summary = df_trans.groupby(['date_only', 'type'])['total_price'].sum().unstack(fill_value=0)
        
        # إعادة تسمية الأعمدة إن وجدت
        if 'دخول' in daily_summary.columns:
            daily_summary = daily_summary.rename(columns={'دخول': 'إجمالي المشتريات (دخول) DH'})
        if 'خروج' in daily_summary.columns:
            daily_summary = daily_summary.rename(columns={'خروج': 'إجمالي المبيعات (خروج) DH'})
            
        st.dataframe(daily_summary, use_container_width=True)
        
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
