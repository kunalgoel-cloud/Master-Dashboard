import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor

# --- 1. DATABASE CONFIGURATION ---
def init_connection():
    """Establishes connection to Neon PostgreSQL."""
    return psycopg2.connect(st.secrets["postgres"]["url"])

def run_query(query, params=None, commit=False):
    """Helper to execute SQL queries safely."""
    conn = init_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        try:
            cur.execute(query, params)
            if commit:
                conn.commit()
                result = None
            else:
                result = cur.fetchall()
            return result
        except Exception as e:
            conn.rollback()
            st.error(f"Database Error: {e}")
            return []
        finally:
            conn.close()

# --- 2. PAGE CONFIG & STYLING ---
st.set_page_config(
    page_title="Enterprise Dashboard Hub", 
    page_icon="🚀", 
    layout="wide"
)

# Custom CSS for the "Brightened" Card UI
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Card Container Hover Effect */
    [data-testid="stVerticalBlockBorderWrapper"] {
        transition: all 0.3s ease-in-out;
        border-radius: 12px !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 16px rgba(0,0,0,0.1) !important;
        border-color: #FF4B4B !important;
    }
    
    /* Metric Styling */
    [data-testid="stMetricValue"] {
        color: #FF4B4B;
        font-weight: 800;
    }
    
    /* Title Styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1E1E1E;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. APP LOGIC ---
tabs = st.tabs(["🏠 Hub", "⚙️ Configuration"])

# Fetch categories once to use in both tabs
categories = run_query("SELECT * FROM categories ORDER BY name ASC")

# --- TAB 1: THE HUB ---
with tabs[0]:
    # Hero Section
    st.markdown('<h1 class="main-header">Master Dashboard Hub</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666;">Select a department below to launch your analytics workspace.</p>', unsafe_allow_html=True)
    
    # Quick Summary Metrics
    total_apps_res = run_query("SELECT COUNT(*) as count FROM dashboards WHERE is_active = True")
    total_apps = total_apps_res[0]['count'] if total_apps_res else 0
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Active Portals", total_apps)
    m2.metric("Departments", len(categories))
    m3.metric("System Integrity", "Verified ✅")
    
    st.divider()

    if not categories:
        st.warning("Welcome! Please head over to the **Configuration** tab to define your first Department.")
    else:
        for cat in categories:
            apps = run_query(
                "SELECT * FROM dashboards WHERE category_id = %s AND is_active = True", 
                (cat['id'],)
            )
            
            st.subheader(f"📂 {cat['name']}")
            
            if not apps:
                st.info(f"No apps linked to {cat['name']} yet.")
            else:
                # Create a grid: 3 columns per row
                cols = st.columns(3)
                for idx, app in enumerate(apps):
                    with cols[idx % 3]:
                        with st.container(border=True):
                            st.markdown(f"### {app['title']}")
                            st.caption(f"Category: {cat['name']}")
                            st.write(app['description'] if app['description'] else "No description provided for this dashboard.")
                            st.link_button(
                                "Launch Dashboard 🚀", 
                                app['url'], 
                                use_container_width=True,
                                type="primary"
                            )
            st.write("") # Extra spacer

# --- TAB 2: CONFIGURATION ---
with tabs[1]:
    st.header("Admin Controls")
    st.info("Manage your departments and dashboard links here. Changes reflect instantly on the Hub.")
    
    col_left, col_right = st.columns(2)

    # 1. Manage Departments
    with col_left:
        with st.container(border=True):
            st.subheader("🏢 Manage Departments")
            with st.form("dept_form", clear_on_submit=True):
                new_dept = st.text_input("New Department Name")
                if st.form_submit_button("Create Department"):
                    if new_dept:
                        run_query("INSERT INTO categories (name) VALUES (%s) ON CONFLICT DO NOTHING", (new_dept,), commit=True)
                        st.success(f"Added {new_dept}")
                        st.rerun()
            
            st.write("**Current Departments:**")
            for c in categories:
                st.text(f"• {c['name']}")

    # 2. Add Dashboards
    with col_right:
        with st.container(border=True):
            st.subheader("🔗 Add Dashboard Link")
            with st.form("app_form", clear_on_submit=True):
                app_name = st.text_input("App Display Name")
                app_url = st.text_input("URL (https://...)")
                app_desc = st.text_area("Brief Description", help="Tell users what this dashboard is for.")
                
                cat_map = {c['name']: c['id'] for c in categories}
                selected_cat = st.selectbox("Assign Department", options=list(cat_map.keys()))
                
                if st.form_submit_button("Save to Hub"):
                    if app_name and app_url:
                        run_query(
                            "INSERT INTO dashboards (category_id, title, url, description) VALUES (%s, %s, %s, %s)",
                            (cat_map[selected_cat], app_name, app_url, app_desc),
                            commit=True
                        )
                        st.success(f"Successfully linked {app_name}!")
                        st.rerun()
                    else:
                        st.error("Name and URL are required.")

    st.divider()
    
    # 3. Quick Table View
    st.subheader("📋 Active Link Manifest")
    manifest = run_query("""
        SELECT d.title, c.name as dept, d.url 
        FROM dashboards d 
        JOIN categories c ON d.category_id = c.id
    """)
    if manifest:
        st.dataframe(manifest, use_container_width=True)
