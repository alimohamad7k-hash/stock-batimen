import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

st.set_page_config(
    page_title="نظام إدارة مخزون البناء والمشاريع",
    page_icon="🏗️",
    layout="wide"
)

# ---------------------------------------------------------
# DATABASE INITIALIZATION
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect("stock_materiux.db")
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
    return sqlite3.connect("stock_materiux.db")

# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------
st.sidebar.title("🏗️ BTP Stock Pro")
st.sidebar.markdown("---")

menu = [
    "📊 لوحة التحكم (Dashboard)", 
    "📥 تسجيل دخول (Réception)", 
    "📤 تسجيل خروج (Sortie / Chantier)", 
    "➕ إضافة مادة جديدة",
    "✏️ إدارة وتعديل المواد (مقبوض بالأمن)",
    "📜 السجل والتقارير",
    "💾 النسخ الاحتياطي (Backup)"
]
choice = st.sidebar.selectbox("القائمة الرئيسية", menu)

# ---------------------------------------------------------
# 1. DASHBOARD
# ---------------------------------------------------------
if choice == "📊 لوحة التحكم (Dashboard)":
    st.title("📊 لوحة القيادة والمؤشرات الرئيسية")
    
    conn = get_connection()
    df_stock = pd.read_sql_query("SELECT * FROM inventory", conn)
    conn.close()
    
    if not df_stock.empty:
        df_stock['total_value'] = df_stock['quantity'] * df_stock['buy_price']
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 قيمة المخزون الإجمالية", f"{df_stock['total_value'].sum():,.2f} DH")
        col2.metric("📦 إجمالي أنواع المواد", len(df_stock))
        
        low_stock_count = len(df_stock[df_stock['quantity'] <= df_stock['min_limit']])
        col3.metric("⚠️ مواد قريبة من النفاد", low_stock_count, delta_color="inverse")
        col4.metric("📈 متوسط ثمن الشراء", f"{df_stock['buy_price'].mean():,.2f} DH")
        
        st.write("---")
        
        if low_stock_count > 0:
            st.error("⚠️ **تنبيه: السلع التالية وصلت للحد الأدنى للمخزون:**")
            low_df = df_stock[df_stock['quantity'] <= df_stock['min_limit']]
            st.dataframe(low_df[['item_name', 'quantity', 'min_limit', 'unit']], use_container_width=True)
            st.write("---")
            
        st.subheader("📋 جدول المخزون الحالي")
        display_df = df_stock.rename(columns={
            'item_name': 'المادة',
            'quantity': 'الكمية الحالية',
            'min_limit': 'الحد الأدنى',
            'unit': 'الوحدة',
            'buy_price': 'سعر الشراء (DH)',
            'sell_price': 'سعر البيع/الاحتساب (DH)',
            'total_value': 'إجمالي القيمة (DH)'
        })
        st.dataframe(display_df.drop(columns=['id']), use_container_width=True)
    else:
        st.info("لا توجد مواد مسجلة حتى الآن في النظام.")

# ---------------------------------------------------------
# 2. ENTRÉE / RÉCEPTION
# ---------------------------------------------------------
elif choice == "📥 تسجيل دخول (Réception)":
    st.subheader("📥 تسجيل دخول سلعة (من المورد)")
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
                qty_in = st.number_input("الكمية المضافة:", min_value=0.1, value=1.0)
                supplier = st.text_input("اسم المورد (Fournisseur):")
            with col2:
                ref_num = st.text_input("رقم الفاتورة /
