import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

st.set_page_config(
    page_title="تطبيق إدارة مخزون مواد البناء",
    page_icon="🏗️",
    layout="wide"
)

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
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_connection():
    return sqlite3.connect("stock_materiux.db")

st.title("🏗️ نظام إدارة ومراقبة مخزون مواد البناء")

menu = [
    "📊 المخزون والتنبيهات", 
    "📥 تسجيل دخول (Entrée)", 
    "📤 تسجيل خروج (Sortie)", 
    "➕ إضافة مادة جديدة", 
    "📜 السجل والتقارير"
]
choice = st.sidebar.selectbox("القائمة الرئيسية", menu)

if choice == "➕ إضافة مادة جديدة":
    st.subheader("➕ إضافة مادة بناء جديدة")
    with st.form("add_item_form"):
        col1, col2 = st.columns(2)
        with col1:
            item_name = st.text_input("اسم المادة (مثلاً: Ciment, Fer 12, Brique)")
            unit = st.selectbox("وحدة القياس", ["Sac", "Kg", "Tonne", "Unité", "m³"])
            initial_qty = st.number_input("الكمية الأولية", min_value=0.0, value=0.0)
        with col2:
            min_limit = st.number_input("حد التنبيه الأدنى (Min Stock)", min_value=0.0, value=10.0)
            buy_price = st.number_input("سعر الشراء (درهم)", min_value=0.0, value=0.0)
            sell_price = st.number_input("سعر البيع (درهم)", min_value=0.0, value=0.0)

        submitted = st.form_submit_button("إضافة المادة")
        if submitted:
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
                            INSERT INTO transactions (item_name, type, quantity, total_price, date, notes) 
                            VALUES (?, ?, ?, ?, ?, ?)""",
                            (item_name.strip(), "دخل", initial_qty, initial_qty * buy_price, 
                             datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "مخزون أولي"))
                    conn.commit()
                    st.success(f"تمت إضافة المادة '{item_name}' بنجاح!")
                except sqlite3.IntegrityError:
                    st.error("هذه المادة موجودة بالفعل!")
                finally:
                    conn.close()

elif choice == "📥 تسجيل دخول (Entrée)":
    st.subheader("📥 تسجيل دخول سلعة إلى السطوك")
    conn = get_connection()
    df_items = pd.read_sql_query("SELECT item_name, buy_price FROM inventory", conn)
    conn.close()
    
    if df_items.empty:
        st.warning("المرجو إضافة مواد أولاً.")
    else:
        with st.form("in_form"):
            selected_item = st.selectbox("المادة:", df_items["item_name"].tolist())
            qty_in = st.number_input("الكمية التي دخلت:", min_value=0.1, value=1.0)
            notes = st.text_input("ملاحظات (المورد / رقم الفاتورة):")
            
            if st.form_submit_button("تأكيد الدخول"):
                conn = get_connection()
                c = conn.cursor()
                buy_price = df_items[df_items["item_name"] == selected_item]["buy_price"].values[0]
                c.execute("UPDATE inventory SET quantity = quantity + ? WHERE item_name = ?", (qty_in, selected_item))
                c.execute("""
                    INSERT INTO transactions (item_name, type, quantity, total_price, date, notes) 
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (selected_item, "دخل", qty_in, qty_in * buy_price, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), notes))
                conn.commit()
                conn.close()
                st.success("تم التحديث بنجاح!")

elif choice == "📤 تسجيل خروج (Sortie)":
    st.subheader("📤 تسجيل بيع / خروج سلعة")
    conn = get_connection()
    df_inv = pd.read_sql_query("SELECT item_name, quantity, sell_price, unit FROM inventory", conn)
    conn.close()
    
    if df_inv.empty:
        st.warning("لا توجد مواد.")
    else:
        with st.form("out_form"):
            selected_item = st.selectbox("المادة:", df_inv["item_name"].tolist())
            item_data = df_inv[df_inv["item_name"] == selected_item].iloc[0]
            
            st.info(f"المتوفر: {item_data['quantity']} {item_data['unit']} | ثمن البيع: {item_data['sell_price']} DH")
            
            qty_out = st.number_input("الكمية الخارجة:", min_value=0.1, value=1.0)
            notes = st.text_input("اسم الزبون / المشروع:")
            
            if st.form_submit_button("تأكيد الخروج"):
                if item_data['quantity'] >= qty_out:
                    total_amt = qty_out * item_data['sell_price']
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("UPDATE inventory SET quantity = quantity - ? WHERE item_name = ?", (qty_out, selected_item))
                    c.execute("""
                        INSERT INTO transactions (item_name, type, quantity, total_price, date, notes) 
                        VALUES (?, ?, ?, ?, ?, ?)""",
                        (selected_item, "خرج", qty_out, total_amt, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), notes))
                    conn.commit()
                    conn.close()
                    st.success(f"تم التسجيل! المجموع: {total_amt:.2f} درهم")
                    st.rerun()
                else:
                    st.error("الكمية غير كافية في السطوك!")

elif choice == "📊 المخزون والتنبيهات":
    st.subheader("📊 حالة المخزون التفاعلية")
    conn = get_connection()
    df_stock = pd.read_sql_query("""
        SELECT item_name AS 'المادة', quantity AS 'الكمية', min_limit AS 'الحد الأدنى', 
               unit AS 'الوحدة', buy_price AS 'سعر الشراء', sell_price AS 'سعر البيع' 
        FROM inventory""", conn)
    conn.close()
    
    if not df_stock.empty:
        df_stock['قيمة السطوك (DH)'] = df_stock['الكمية'] * df_stock['سعر الشراء']
        total_val = df_stock['قيمة السطوك (DH)'].sum()
        
        st.metric("💰 القيمة المالية الإجمالية للسطوك الحالي", f"{total_val:,.2f} DH")
        st.write("---")
        
        low_stock = df_stock[df_stock['الكمية'] <= df_stock['الحد الأدنى']]
        if not low_stock.empty:
            st.error("⚠️ **تنبيه: المواد التالية على وشك النفاد!**")
            for _, row in low_stock.iterrows():
                st.write(f"- **{row['المادة']}**: الباقي {row['الكمية']} {row['الوحدة']} (الحد الأدنى هو {row['الحد الأدنى']})")
            st.write("---")

        st.dataframe(df_stock, use_container_width=True)
    else:
        st.info("لا توجد بيانات.")

elif choice == "📜 السجل والتقارير":
    st.subheader("📜 تاريخ العمليات مع إمكانية التحميل")
    conn = get_connection()
    df_trans = pd.read_sql_query("""
        SELECT date AS 'التاريخ', item_name AS 'المادة', type AS 'النوع', 
               quantity AS 'الكمية', total_price AS 'المبلغ الإجمالي (DH)', notes AS 'ملاحظات' 
        FROM transactions ORDER BY id DESC""", conn)
    conn.close()
    
    if not df_trans.empty:
        st.dataframe(df_trans, use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_trans.to_excel(writer, index=False, sheet_name='Historique')
        
        st.download_button(
            label="📥 تحميل السجل بصيغة Excel",
            data=buffer.getvalue(),
            file_name=f"rapport_stock_{datetime.now().strftime('%Y_%m_%d')}.xlsx",
            mime="application/vnd.ms-excel"
        )
    else:
        st.info("لا توجد عمليات.")
