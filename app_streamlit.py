import streamlit as st
import pandas as pd
import os
import requests
import folium
from streamlit_folium import st_folium
import base64

# ==========================================
# 1. FILE-BASED STORAGE SETUP (إعداد حفظ البيانات في ملف)
# ==========================================
# We store the reports in a local CSV file instead of SQLite.
# This makes it easier to inspect, backup, and deploy without DB drivers.
DATA_FILE = "reports.csv"
IMAGE_DIR = "uploaded_images"

# Ensure directories exist
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# Check if the CSV file exists. If not, initialize it with the required column headers.
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["id", "type", "region", "latitude", "longitude", "temperature", "description", "image_path"])
    df.to_csv(DATA_FILE, index=False)

# Predefined Beirut neighborhoods and their coordinates in English for auto-fill support
BEIRUT_REGIONS = {
    # Central Beirut
    "Downtown": (33.8958, 35.5052),
    "Saifi": (33.8954, 35.5106),
    "Zaitunay Bay": (33.9030, 35.5015),

    # West Beirut
    "Hamra": (33.8962, 35.4815),
    "Ras Beirut": (33.9028, 35.4765),
    "Manara": (33.9010, 35.4742),
    "Raouche": (33.8900, 35.4715),
    "Ain El Tineh": (33.8938, 35.4878),
    "Verdun": (33.8890, 35.4855),
    "Clemenceau": (33.8925, 35.4925),
    "Kantari": (33.8920, 35.4940),
    "Mazraa": (33.8825, 35.4928),
    "Tallet El Khayat": (33.8842, 35.4895),
    "Mousseitbeh": (33.8848, 35.4938),
    "Msaitbeh": (33.8845, 35.4940),
    "Sanayeh": (33.8930, 35.4920),
    "UNESCO": (33.8820, 35.4868),
    "Tariq El Jdideh": (33.8785, 35.4862),
    "Corniche Mazraa": (33.8780, 35.4945),
    "Ouzaai": (33.8525, 35.4845),
    "Jnah": (33.8698, 35.4812),
    "Ramlet El Baida": (33.8785, 35.4748),

    # East Beirut
    "Achrafieh": (33.8872, 35.5222),
    "Gemmayze": (33.8958, 35.5158),
    "Mar Mikhael": (33.8978, 35.5240),
    "Geitawi": (33.8968, 35.5202),
    "Rmeil": (33.8980, 35.5190),
    "Sursock": (33.8915, 35.5208),
    "Sioufi": (33.8855, 35.5215),
    "Furn El Hayek": (33.8840, 35.5198),
    "Badaro": (33.8785, 35.5140),
    "Sodeco": (33.8865, 35.5112),
    "Adlieh": (33.8788, 35.5195),
    "Furn El Chebbak": (33.8758, 35.5338),
    "Sin El Fil": (33.8812, 35.5412),
    "Hazmieh": (33.8658, 35.5428),

    # Southern Beirut
    "Chiyah": (33.8675, 35.5178),
    "Ghobeiry": (33.8635, 35.5125),
    "Haret Hreik": (33.8565, 35.5148),
    "Bir Hassan": (33.8685, 35.4952),
    "Bir Abed": (33.8568, 35.5055),
    "Laylake": (33.8528, 35.5198),
    "Tahwitat El Ghadir": (33.8468, 35.5095),

    # Northern Beirut
    "Karantina": (33.9048, 35.5288),
    "Bourj Hammoud": (33.8988, 35.5442),
    "Nabaa": (33.8932, 35.5470),
    "Medawar": (33.9015, 35.5220),

    # Popular / Lower-income areas
    "Basta": (33.8870, 35.5015),
    "Basta El Tahta": (33.8858, 35.5032),
    "Basta El Fouqa": (33.8888, 35.5018),
    "Bachoura": (33.8898, 35.5058),
    "Khandaq El Ghamiq": (33.8860, 35.5095),
    "Nweiri": (33.8835, 35.5015),
    "Zarif": (33.8908, 35.4872),
    "Sabra": (33.8678, 35.4865),
    "Shatila": (33.8660, 35.4895),
    "Burj El Barajneh": (33.8505, 35.4965),

    # Business / Commercial
    "Beirut Port": (33.9045, 35.5185),
    "Airport Area": (33.8209, 35.4884),

    # Custom
    "Custom Location": (33.8938, 35.5018)
}

def load_data():
    """Load the environmental reports from the CSV file as a Pandas DataFrame."""
    try:
        df = pd.read_csv(DATA_FILE)
        # Ensure region and image_path columns exist for backward compatibility with older CSVs
        if "region" not in df.columns:
            df["region"] = ""
        if "image_path" not in df.columns:
            df["image_path"] = ""
        # Force column types to ensure consistency during calculations and map rendering
        df["id"] = df["id"].astype(int)
        df["type"] = df["type"].astype(str)
        df["region"] = df["region"].fillna("").astype(str)
        df["latitude"] = df["latitude"].astype(float)
        df["longitude"] = df["longitude"].astype(float)
        df["temperature"] = pd.to_numeric(df["temperature"], errors='coerce')
        df["description"] = df["description"].fillna("").astype(str)
        df["image_path"] = df["image_path"].fillna("").astype(str)
        return df
    except Exception:
        # Return an empty DataFrame with the correct schema if reading fails
        return pd.DataFrame(columns=["id", "type", "region", "latitude", "longitude", "temperature", "description", "image_path"])

def save_data(df):
    """Save the environmental reports back to the CSV file."""
    df.to_csv(DATA_FILE, index=False)

def get_image_base64(filepath):
    """Read a local file and return its base64 encoded string."""
    try:
        if os.path.exists(filepath):
            with open(filepath, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception:
        pass
    return None

# ==========================================
# 2. APP CONFIGURATION (إعدادات التطبيق)
# ==========================================
st.set_page_config(page_title="Beirut Green Pulse - Streamlit", page_icon="🌿", layout="centered")

# ==========================================
# 3. SIDEBAR NAVIGATION (شريط التنقل الجانبي)
# ==========================================
st.sidebar.title("🌿 Navigation")
page = st.sidebar.radio("Go to:", ["🌍 Climate Map", "📝 Submit Form", "📊 Climate Analytics", "🗑️ Admin Control"])

# ==========================================
# VIEW 1: CLIMATE MAP (خريطة المناخ)
# ==========================================
if page == "🌍 Climate Map":
    st.title("🌍 Beirut Environmental Map")
    st.write("Click on any marker to view report details.")
    st.write("---")

    # Load reports from the local CSV file
    df = load_data()

    if not df.empty:
        # Filter dropdowns
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            map_filter = st.selectbox("Filter Map Pins by Type:", ["Show All", "Heat Stress Reports Only 🌡️", "Tree Planting Proposals Only 🌱"])
        with col_f2:
            # Extract unique regions present in database to build filter options dynamically
            unique_regions = sorted(list(df["region"].unique()))
            unique_regions = [r for r in unique_regions if r != ""]
            region_options = ["Show All Regions"] + unique_regions
            selected_region_filter = st.selectbox("Filter Map Pins by Region:", region_options)
        
        filtered_df = df.copy()
        
        # Apply type filter
        if map_filter == "Heat Stress Reports Only 🌡️":
            filtered_df = filtered_df[filtered_df["type"] == "heat"]
        elif map_filter == "Tree Planting Proposals Only 🌱":
            filtered_df = filtered_df[filtered_df["type"] == "tree"]
            
        # Apply region filter
        if selected_region_filter != "Show All Regions":
            filtered_df = filtered_df[filtered_df["region"] == selected_region_filter]

        # Center map on Beirut
        beirut_map = folium.Map(location=[33.8938, 35.5018], zoom_start=13, tiles="OpenStreetMap")

        # Add custom emoji markers
        for idx, row in filtered_df.iterrows():
            emoji = "🌡️" if row["type"] == "heat" else "🌱"
            title_text = "Heat Stress Report" if row["type"] == "heat" else "Tree Proposal"
            temp_text = f"<br><b>Temperature:</b> {row['temperature']}°C" if row["type"] == "heat" else ""
            region_text = f"<br><b>Region:</b> {row['region']}" if "region" in row and row['region'] != "" else ""
            
            # Embed image in base64 inside Folium popup if available
            img_html = ""
            if "image_path" in row and row["image_path"] != "" and os.path.exists(str(row["image_path"])):
                img_b64 = get_image_base64(str(row["image_path"]))
                if img_b64:
                    img_html = f'<br><img src="data:image/jpeg;base64,{img_b64}" style="width:100%; max-width:200px; border-radius:5px; margin-top:5px;">'
            
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; font-size: 13px; line-height: 1.4;">
                <h4 style="margin: 0 0 5px; color: #1a7c4f;">{emoji} {title_text}</h4>
                <b>Coords:</b> {row['latitude']:.4f}, {row['longitude']:.4f}{region_text}{temp_text}<br>
                <b>Description:</b> {row['description']}{img_html}
            </div>
            """
            
            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{emoji} {title_text}",
                icon=folium.DivIcon(
                    html=f'<div style="font-size: 26px; transform: translate(-10px, -15px);">{emoji}</div>'
                )
            ).add_to(beirut_map)

        # Render Folium map in Streamlit
        st_folium(beirut_map, width=700, height=450, returned_objects=[])
        
        # Display data table
        st.subheader("📋 Data Table")
        st.dataframe(filtered_df)
    else:
        st.info("No reports or proposals submitted yet. Use the sidebar to submit data!")

# ==========================================
# VIEW 2: SUBMIT FORM (إرسال البيانات)
# ==========================================
elif page == "📝 Submit Form":
    st.title("📝 Submit New Environmental Data")
    st.write("Report local heat anomalies or propose new tree planting locations.")
    st.write("---")

    report_type = st.selectbox("Select Submission Type:", [
        "Heat Stress Report 🌡️", 
        "Tree Planting Proposal 🌱"
    ])

    st.subheader("📍 Region Selection")
    selected_region = st.selectbox(
        "Select Beirut Neighborhood:", 
        list(BEIRUT_REGIONS.keys())
    )
    
    # Auto-fill coordinates based on selected region
    default_lat, default_lon = BEIRUT_REGIONS[selected_region]

    with st.form("submission_form"):
        st.caption("Coordinates auto-filled below based on selected region. You can adjust them manually if needed.")
        lat = st.number_input("Location Latitude", value=default_lat, format="%.6f")
        lon = st.number_input("Location Longitude", value=default_lon, format="%.6f")
        
        temp = None
        if report_type == "Heat Stress Report 🌡️":
            temp = st.slider("Reported Temperature °C", min_value=0.0, max_value=45.0, value=30.0, step=0.5)
            
        desc = st.text_area("Description / Comments", placeholder="E.g., barren concrete plaza in need of shade." if report_type == "Tree Planting Proposal 🌱" else "E.g., high heat index, no tree cover.")
        
        # Image Upload field (optional)
        uploaded_image = st.file_uploader("Upload Image (Optional):", type=["jpg", "jpeg", "png"])
        
        submit_button = st.form_submit_button("Submit Form")

    if submit_button:
        db_type = "heat" if report_type == "Heat Stress Report 🌡️" else "tree"
        
        # Load current records from the CSV file
        df = load_data()
        
        # Generate the next auto-increment ID
        next_id = int(df["id"].max() + 1) if not df.empty else 1
        
        # Save uploaded image to disk if provided
        image_path = ""
        if uploaded_image is not None:
            file_extension = os.path.splitext(uploaded_image.name)[1]
            if not file_extension:
                file_extension = ".jpg"
            filename = f"{db_type}_{next_id}{file_extension}"
            image_path = os.path.join(IMAGE_DIR, filename)
            with open(image_path, "wb") as f:
                f.write(uploaded_image.getbuffer())
        
        # Construct the new report record
        new_row = pd.DataFrame([{
            "id": next_id,
            "type": db_type,
            "region": selected_region,
            "latitude": lat,
            "longitude": lon,
            "temperature": temp,
            "description": desc,
            "image_path": image_path
        }])
        
        # Append and save the updated data to the CSV file
        df = pd.concat([df, new_row], ignore_index=True)
        save_data(df)
        
        st.success(f"✅ {report_type} saved to file successfully!")

# ==========================================
# VIEW 3: CLIMATE ANALYTICS (الإحصائيات)
# ==========================================
elif page == "📊 Climate Analytics":
    st.title("📊 Environmental Analytics & Insights")
    st.write("Summary analysis and environmental recommendations based on crowdsourced data.")
    st.write("---")

    # Load reports from CSV for environmental analytics
    df = load_data()

    if not df.empty:
        heat_df = df[df["type"] == "heat"]
        tree_df = df[df["type"] == "tree"]
        heat_count = len(heat_df)
        tree_count = len(tree_df)

        # 1. METRICS SUMMARY ROW
        col1, col2, col3 = st.columns(3)
        col1.metric("Heat Stress Reports 🌡️", heat_count)
        col2.metric("Tree Planting Proposals 🌱", tree_count)
        
        if not heat_df.empty and not heat_df["temperature"].isna().all():
            avg_temp = round(heat_df['temperature'].mean(), 1)
            col3.metric("Average Reported Temp", f"{avg_temp} °C")
        else:
            col3.metric("Average Reported Temp", "N/A")

        st.write("---")

        # 2. CHARTS SECTION (SIDE-BY-SIDE)
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.subheader("📈 Submission Distribution")
            chart_data = pd.DataFrame({
                "Count": [heat_count, tree_count]
            }, index=["Heat Stress Reports", "Tree Planting Proposals"])
            st.bar_chart(chart_data)
            
        with col_c2:
            st.subheader("📍 Submissions by Neighborhood")
            # Count submissions per region
            if "region" in df.columns and not df[df["region"] != ""].empty:
                region_counts = df[df["region"] != ""]["region"].value_counts()
                st.bar_chart(region_counts)
            else:
                st.info("No region details available to show neighborhood distribution.")

        # 3. ADVANCED ANALYTICS: NEIGHBORHOOD TEMPERATURE ANOMALIES
        st.write("---")
        st.subheader("🌡️ Neighborhood Temperature Analysis")
        
        if not heat_df.empty and "region" in heat_df.columns:
            # Calculate average temperature per neighborhood
            heat_by_region = heat_df[heat_df["region"] != ""].groupby("region")["temperature"].mean().round(1)
            
            if not heat_by_region.empty:
                col_chart, col_table = st.columns([2, 1])
                with col_chart:
                    st.bar_chart(heat_by_region)
                with col_table:
                    # Render a clean table of temperatures per neighborhood
                    st.dataframe(pd.DataFrame({
                        "Average Temp (°C)": heat_by_region
                    }))
                    
                # Identify the hottest neighborhood anomaly
                hottest_neighborhood = heat_by_region.idxmax()
                hottest_temp = heat_by_region.max()
                
                st.info(f"💡 **Key Insight:** **{hottest_neighborhood}** is currently reporting the highest average temperature anomaly at **{hottest_temp}°C**. This area should be prioritized for immediate urban greening and tree shading interventions.")
            else:
                st.info("Submit heat reports with region details to see temperature analysis by neighborhood.")
        else:
            st.info("No temperature data available for neighborhood analysis.")

        # 4. ACTIONABLE REPORT
        st.write("---")
        st.subheader("📋 Urban Greening Recommendations")
        
        st.markdown(f"""
        Based on the crowdsourced dataset, the following interventions are recommended for Beirut:
        * **Target Hotspots**: Allocate urban forestry budgets to regions reporting high heat indices.
        * **Community Synergy**: Align tree proposals in areas where heat anomalies overlap (compare **{heat_count}** heat reports against **{tree_count}** tree proposals).
        * **Sustainable Choice**: Focus on planting native, drought-resistant trees that survive with minimal watering in urban soils.
        """)
    else:
        st.info("No data available yet. Analytics and reports will show here once reports are submitted.")

# ==========================================
# VIEW 4: ADMIN CONTROL (إدارة وحذف البيانات)
# ==========================================
elif page == "🗑️ Admin Control":
    st.title("🗑️ Admin File Control")
    st.write("View all entries and delete incorrect submissions from the CSV file.")
    st.write("---")

    # Load reports from CSV for management
    df = load_data()

    if not df.empty:
        st.subheader("📋 Manage Submissions")
        for idx, row in df.iterrows():
            col1, col2 = st.columns([5, 1])
            
            # Formulate title string based on report type
            emoji = "🌡️" if row['type'] == 'heat' else "🌱"
            temp_info = f" ({row['temperature']}°C)" if row['type'] == 'heat' and not pd.isna(row['temperature']) else ""
            region_info = f" in {row['region']}" if "region" in row and row['region'] != "" else ""
            summary_text = f"**ID: {int(row['id'])}** | {emoji} {row['type'].upper()}{temp_info}{region_info} at ({row['latitude']:.4f}, {row['longitude']:.4f})"
            
            col1.write(summary_text)
            col1.caption(f"Description: {row['description']}")
            # Show image preview in admin panel if it exists
            if "image_path" in row and row["image_path"] != "" and os.path.exists(str(row["image_path"])):
                col1.image(str(row["image_path"]), width=150)
            
            # Action button to trigger delete
            if col2.button("Delete ❌", key=f"del_{int(row['id'])}"):
                # Delete image file if it exists
                if "image_path" in row and row["image_path"] != "":
                    if os.path.exists(str(row["image_path"])):
                        try:
                            os.remove(str(row["image_path"]))
                        except Exception:
                            pass
                # Filter out the record from the DataFrame
                df = df[df["id"] != row['id']]
                save_data(df)
                st.success(f"Successfully deleted entry ID {int(row['id'])}!")
                st.rerun()
            
            st.write("---")
            
        # Danger zone button to wipe file records
        st.subheader("🚨 Danger Zone")
        if st.button("Delete All Data ☠️"):
            # Delete all uploaded images
            if os.path.exists(IMAGE_DIR):
                for img_file in os.listdir(IMAGE_DIR):
                    try:
                        os.remove(os.path.join(IMAGE_DIR, img_file))
                    except Exception:
                        pass
            # Empty DataFrame with headers
            df = pd.DataFrame(columns=["id", "type", "region", "latitude", "longitude", "temperature", "description", "image_path"])
            save_data(df)
            st.warning("All records and uploaded images have been cleared!")
            st.rerun()
    else:
        st.info("The data file is currently empty. No entries to manage.")
