import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor

# --- DATABASE CONNECTION ---
def init_connection():
    return psycopg2.connect(st.secrets["postgres"]["url"])

conn = init_connection()

def run_query(query, params=None, commit=False):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params)
        if commit:
            conn.commit()
            return None
        return cur.fetchall()

# --- APP UI ---
st.set_page_config(page_title="Master Dashboard Hub", layout="wide")
st.title("🚀 Enterprise Dashboard Portal")

tabs = st.tabs(["🏠 Hub", "⚙️ Configuration"])

# --- TAB 1: THE HUB (VIEWING) ---
with tabs[0]:
    categories = run_query("SELECT * FROM categories")
    
    for cat in categories:
        with st.expander(f"## {cat['name']} Dashboards", expanded=True):
            # Fetch apps for this category
            apps = run_query(
                "SELECT * FROM dashboards WHERE category_id = %s AND is_active = True", 
                (cat['id'],)
            )
            
            if not apps:
                st.info("No dashboards added yet.")
            else:
                # Create a grid layout for apps
                cols = st.columns(3)
                for idx, app in enumerate(apps):
                    with cols[idx % 3]:
                        st.markdown(f"### {app['title']}")
                        st.caption(app['description'])
                        st.link_button("Open Dashboard", app['url'], use_container_width=True)

# --- TAB 2: CONFIGURATION (ADMIN) ---
with tabs[1]:
    st.header("Manage Dashboards")
    
    with st.form("add_new_dashboard"):
        st.subheader("Add New App")
        new_title = st.text_input("App Name")
        new_url = st.text_input("URL")
        new_desc = st.text_area("Short Description")
        
        # Get category options for dropdown
        cat_options = {c['name']: c['id'] for c in categories}
        selected_cat = st.selectbox("Department", options=list(cat_options.keys()))
        
        if st.form_submit_button("Save Dashboard"):
            run_query(
                "INSERT INTO dashboards (category_id, title, url, description) VALUES (%s, %s, %s, %s)",
                (cat_options[selected_cat], new_title, new_url, new_desc),
                commit=True
            )
            st.success(f"Added {new_title} to {selected_cat}!")
            st.rerun()

    st.divider()
    
    # Simple Table View for Editing/Deleting
    st.subheader("Existing Links")
    all_data = run_query("""
        SELECT d.id, d.title, d.url, c.name as category 
        FROM dashboards d 
        JOIN categories c ON d.category_id = c.id
    """)
    st.table(all_data)
