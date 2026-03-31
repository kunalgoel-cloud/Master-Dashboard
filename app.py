# --- CUSTOM CSS FOR STYLING ---
st.markdown("""
    <style>
    /* Card Container Styling */
    [data-testid="stVerticalBlockBorderWrapper"] {
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1) !important;
        border-color: #ff4b4b !important;
    }
    /* Metric Styling */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #ff4b4b;
    }
    </style>
    """, unsafe_allow_html=True)

# --- TAB 1: THE HUB (UI OVERHAUL) ---
with tabs[0]:
    # 1. HERO SECTION
    st.markdown("""
        <div style="background-color: #f0f2f6; padding: 2rem; border-radius: 15px; margin-bottom: 2rem;">
            <h1 style="margin: 0;">Main Dashboard Hub 🏢</h1>
            <p style="color: #555; font-size: 1.1rem;">Centralized access to all enterprise analytics tools.</p>
        </div>
    """, unsafe_allow_html=True)

    # 2. QUICK METRICS
    categories = run_query("SELECT * FROM categories ORDER BY name ASC")
    total_apps = run_query("SELECT COUNT(*) as count FROM dashboards WHERE is_active = True")[0]['count']
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Departments", len(categories))
    m2.metric("Active Dashboards", total_apps)
    m3.metric("System Status", "Healthy 🟢")
    
    st.divider()

    # 3. DYNAMIC CATEGORY GRID
    if not categories:
        st.info("No departments defined yet. Go to Configuration to add some!")
    
    for cat in categories:
        apps = run_query(
            "SELECT * FROM dashboards WHERE category_id = %s AND is_active = True", 
            (cat['id'],)
        )
        
        # Heading for the Department
        st.subheader(f"📂 {cat['name']}")
        
        if not apps:
            st.caption("No dashboards in this department yet.")
        else:
            # Create rows of 3
            cols = st.columns(3)
            for idx, app in enumerate(apps):
                with cols[idx % 3]:
                    # The Card Content
                    with st.container(border=True):
                        st.markdown(f"### {app['title']}")
                        
                        # Add a "Tag" for the department
                        st.markdown(f"**{cat['name']}**", help="Department")
                        
                        # Description with fixed height for alignment
                        st.write(app['description'] if app['description'] else "No description provided.")
                        
                        # Big primary button for the URL
                        st.link_button(
                            "Launch Dashboard 🚀", 
                            app['url'], 
                            use_container_width=True,
                            type="primary"
                        )
        st.markdown("<br>", unsafe_allow_html=True) # Spacer between departments
