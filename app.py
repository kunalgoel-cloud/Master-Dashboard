import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor

# --- DATABASE CONNECTION ---
def init_connection():
    return psycopg2.connect(st.secrets["postgres"]["url"])

conn = init_connection()

def run_query(query, params=None, commit=False):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        try:
            cur.execute(query, params)
            if commit:
                conn.commit()
                return None
            return cur.fetchall()
        except Exception as e:
            conn.rollback()
            st.error(f"Database Error: {e}")
            return []

# --- APP UI ---
st.set_page_config(page_title="Master Dashboard Hub", layout="wide")
st.title("🚀 Enterprise Dashboard Portal")

tabs = st.tabs(["🏠 Hub", "⚙️ Configuration"])

# --- TAB 1: THE HUB ---
with tabs[0]:
    categories = run_query("SELECT * FROM categories ORDER BY name ASC")
    
    if not categories:
        st.info("No departments defined yet. Go to Configuration to add some!")
    
    for cat in categories:
        apps = run_query(
            "SELECT * FROM dashboards WHERE category_id = %s AND is_active = True", 
            (cat['id'],)
        )
        
        # Only show the category if it has apps, or keep it visible if you prefer
        with st.expander(f"## {cat['name']} Dashboards", expanded=True):
            if not apps:
                st.caption("No dashboards in this department.")
            else:
                cols = st.columns(3)
                for idx, app in enumerate(apps):
                    with cols[idx % 3]:
                        st.container(border=True).markdown(f"**{app['title']}**\n\n{app['description']}")
                        st.link_button("Open App", app['url'], use_container_width=True)

# --- TAB 2: CONFIGURATION ---
with tabs[1]:
    col1, col2 = st.columns(2)

    # 1. DEPARTMENT MANAGEMENT
    with col1:
        st.subheader("🏢 Define Departments")
        with st.form("add_dept_form", clear_on_submit=True):
            new_dept = st.text_input("New Department Name (e.g., Marketing)")
            if st.form_submit_button("Add Department"):
                if new_dept:
                    run_query("INSERT INTO categories (name) VALUES (%s) ON CONFLICT DO NOTHING", (new_dept,), commit=True)
                    st.success(f"Department '{new_dept}' added!")
                    st.rerun()

        # List existing departments
        st.write("Current Departments:")
        for c in categories:
            st.text(f"• {c['name']}")

    # 2. DASHBOARD MANAGEMENT
    with col2:
        st.subheader("🔗 Add Dashboard Link")
        with st.form("add_app_form", clear_on_submit=True):
            app_name = st.text_input("App Name")
            app_url = st.text_input("URL")
            app_desc = st.text_area("Description")
            
            cat_map = {c['name']: c['id'] for c in categories}
            app_dept = st.selectbox("Assign to Department", options=list(cat_map.keys()))
            
            if st.form_submit_button("Save Dashboard"):
                if app_name and app_url:
                    run_query(
                        "INSERT INTO dashboards (category_id, title, url, description) VALUES (%s, %s, %s, %s)",
                        (cat_map[app_dept], app_name, app_url, app_desc),
                        commit=True
                    )
                    st.success(f"Linked {app_name} to {app_dept}!")
                    st.rerun()

    st.divider()
    
    # 3. EDIT/DELETE VIEW
    st.subheader("📋 Master List")
    all_apps = run_query("""
        SELECT d.id, d.title, c.name as department, d.url 
        FROM dashboards d 
        JOIN categories c ON d.category_id = c.id
    """)
    if all_apps:
        st.dataframe(all_apps, use_container_width=True)
