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
st.sidebar.title("BTP Stock Pro")
st.sidebar.markdown("---")

menu = [
    "لوحة التحكم", 
    "تسجيل دخول سلعة", 
    "تسجيل خروج سلعة للورش", 
    "إضافة مادة جديدة",
    "إدارة وتعديل المواد (محمي بالرمز)",
    "السجل والتقارير",
    "النسخ الاحتياطي"
]
choice = st.sidebar.selectbox("القائمة الرئيسية", menu)

# ---------------------------------------------------------
# 1. DASHBOARD
# ---------------------------------------------------------
if choice == "لوحة التحكم":
    st.title("لوحة القيادة والمؤشرات الرئيسية")
    
    conn = get_connection()
    df_stock = pd.read_sql_query("SELECT * FROM inventory", conn)
    conn.close()
    
    if not df_stock.empty:
        df_stock['total_value'] = df_stock['quantity'] * df_stock['buy_price']
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("قيمة المخزون الإجمالية", f"{df_stock['total_value'].sum():,.2f} DH")
        col2.metric("إجمالي أنواع المواد", len(df_stock))
        
        low_stock_count = len(df_stock[df_stock['quantity'] <= df_stock['min_limit']])
        col3.metric("مواد قريبة من النفاد", low_stock_count, delta_color="inverse")
        col4.metric("متوسط ثمن الشراء", f"{df_stock['buy_price'].mean():,.2f} DH")
        
        st.write("---")
        
        if low_stock_count > 0:
            st.error("تنبيه: السلع التالية وصلت للحد الأدنى للمخزون:")
            low_df = df_stock[df_stock['quantity'] <= df_stock['min_limit']]
            st.dataframe(low_df[['item_name', 'quantity', 'min_limit', 'unit']], use_container_width=True)
            st.write("---")
            
        st.subheader("جدول المخزون الحالي")
        display_df = df_stock.rename(columns={
            'item_name': 'المادة',
            'quantity': 'الكمية الحالية',
            'min_limit': 'الحد الأدنى',
            'unit': 'الوحدة',
            'buy_price': 'سعر الشراء (DH)',
            'sell_price': 'سعر البيع (DH)',
            'total_value': 'إجمالي القيمة (DH)'
        })
        st.dataframe(display_df.drop(columns=['id']), use_container_width=True)
    else:
        st.info("لا توجد مواد مسجلة حتى الآن في النظام.")

# ---------------------------------------------------------
# 2. ENTRÉE / RÉCEPTION
# ---------------------------------------------------------
elif choice == "تسجيل دخول سلعة":
    st.subheader("تسجيل دخول سلعة من المورد")
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
                supplier = st.text_input("اسم المورد:")
            with col2:
                ref_num = st.text_input("رقم الفاتورة أو البون:")
                notes = st.text_input("ملاحظات إضافية:")
            
            if st.form_submit_button("تأكيد تسجيل الدخول"):
                conn = get_connection()
                c = conn.cursor()
                buy_price = df_items[df_items["item_name"] == selected_item]["buy_price"].values[0]
                c.execute("UPDATE inventory SET quantity = quantity + ? WHERE item_name = ?", (qty_in, selected_item))
                c.execute("""
                    INSERT INTO transactions (item_name, type, quantity, total_price, date, entity, ref_num, notes) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (selected_item, "دخول", qty_in, qty_in * buy_price, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), supplier, ref_num, notes))
                conn.commit()
                conn.close()
                st.success(f"تمت إضافة الكمية بنجاح!")

# ---------------------------------------------------------
# 3. SORTIE / CHANTIER
# ---------------------------------------------------------
elif choice == "تسجيل خروج سلعة للورش":
    st.subheader("تسجيل خروج سلعة إلى ورش البناء")
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
                item_data = df_inv[df_inv["item_name"] == selected_item].iloc[0]
                st.info(f"المتوفر حالياً: {item_data['quantity']} {item_data['unit']}")
                qty_out = st.number_input("الكمية الخارجة:", min_value=0.1, value=1.0)
            with col2:
                chantier = st.text_input("اسم الورش:")
                ref_num = st.text_input("رقم إذن الخروج:")
                notes = st.text_input("ملاحظات:")
            
            if st.form_submit_button("تأكيد الخروج"):
                if item_data['quantity'] >= qty_out:
                    total_amt = qty_out * item_data['sell_price']
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("UPDATE inventory SET quantity = quantity - ? WHERE item_name = ?", (qty_out, selected_item))
                    c.execute("""
                        INSERT INTO transactions (item_name, type, quantity, total_price, date, entity, ref_num, notes) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (selected_item, "خروج", qty_out, total_amt, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), chantier, ref_num, notes))
                    conn.commit()
                    conn.close()
                    st.success("تم تسجيل الخروج بنجاح!")
                    st.rerun()
                else:
                    st.error("الكمية المطلوبة أكبر من المتوفر في السطوك!")

# ---------------------------------------------------------
# 4. ADD ITEM
# ---------------------------------------------------------
elif choice == "إضافة مادة جديدة":
    st.subheader("إضافة مادة بناء جديدة للقائمة")
    with st.form("add_item_form"):
        col1, col2 = st.columns(2)
        with col1:
            item_name = st.text_input("اسم المادة:")
            unit = st.selectbox("وحدة القياس", ["Sac", "Kg", "Tonne", "Unité", "m³", "Mètre"])
            initial_qty = st.number_input("الكمية الأولية", min_value=0.0, value=0.0)
        with col2:
            min_limit = st.number_input("حد التنبيه الأدنى", min_value=0.0, value=10.0)
            buy_price = st.number_input("سعر الشراء", min_value=0.0, value=0.0)
            sell_price = st.number_input("سعر البيع", min_value=0.0, value=0.0)

        if st.form_submit_button("إضافة المادة"):
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
                            (item_name.strip(), "دخول", initial_qty, initial_qty * buy_price, 
                             datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "مخزون أولي"))
                    conn.commit()
                    st.success("تمت إضافة المادة بنجاح!")
                except sqlite3.IntegrityError:
                    st.error("هذه المادة توجد بالفعل!")
                finally:
                    conn.close()

# ---------------------------------------------------------
# 5. EDIT / DELETE ITEMS (PROTECTED BY PASSWORD)
# ---------------------------------------------------------
elif choice == "إدارة وتعديل المواد (محمي بالرمز)":
    st.subheader("صفحة محمية: تعديل أو حذف المواد")
    
    ADMIN_PASSWORD = "admin123"
    password_input = st.text_input("أدخل كلمة سر المسؤول:", type="password")
    
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
                    new_min = st.number_input("تعديل حد التنبيه:", min_value=0.0, value=float(item_row['min_limit']))
                    new_buy = st.number_input("تعديل ثمن الشراء:", min_value=0.0, value=float(item_row['buy_price']))
                with col2:
                    new_sell = st.number_input("تعديل ثمن البيع:", min_value=0.0, value=float(item_row['sell_price']))
                    new_unit = st.selectbox("تعديل الوحدة:", ["Sac", "Kg", "Tonne", "Unité", "m³", "Mètre"])
                
                if st.form_submit_button("تحديث البيانات"):
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
            if st.button(f"حذف المادة '{selected_item}' نهائياً"):
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
        st.error("خطأ في كلمة السر!")

# ---------------------------------------------------------
# 6. HISTORIQUE & EXCEL
# ---------------------------------------------------------
elif choice == "السجل والتقارير":
    st.subheader("تاريخ كافة الحركات")
    conn = get_connection()
    df_trans = pd.read_sql_query("""
        SELECT date AS 'التاريخ', item_name AS 'المادة', type AS 'الحركة', 
               quantity AS 'الكمية', total_price AS 'المبلغ الإجمالي', 
               entity AS 'الجهة', ref_num AS 'المرجع', notes AS 'ملاحظات' 
        FROM transactions ORDER BY id DESC""", conn)
    conn.close()
    
    if not df_trans.empty:
        st.dataframe(df_trans, use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_trans.to_excel(writer, index=False, sheet_name='Historique_Stock')
        
        st.download_button(
            label="تحميل السجل بصيغة Excel",
            data=buffer.getvalue(),
            file_name=f"rapport_stock_{datetime.now().strftime('%Y_%m_%d')}.xlsx",
            mime="application/vnd.ms-excel"
        )
    else:
        st.info("لا توجد أي حركات مسجلة حتى الآن.")

# ---------------------------------------------------------
# 7. BACKUP DATABASE
# ---------------------------------------------------------
elif choice == "النسخ الاحتياطي":
    st.subheader("حفظ نسخة احتياطية من قاعدة البيانات")
    try:
        with open("stock_materiux.db", "rb") as fp:
            st.download_button(
                label="تحميل ملف قاعدة البيانات",
                data=fp,
                file_name=f"stock_materiux_backup_{datetime.now().strftime('%Y_%m_%d')}.db",
                mime="application/x-sqlite3"
            )
    except FileNotFoundError:
        st.error("لم يتم العثور على قاعدة البيانات بعد.")
