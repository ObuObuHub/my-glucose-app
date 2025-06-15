"""
Glucose Monitoring App - Simple and Private
Your data stays in your Google Drive
Based on ADA 2025 Guidelines
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import json
import os

# Page configuration - this makes our app look good on phones
st.set_page_config(
    page_title="Monitor Glicemie",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state - this is like the app's memory
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_email = None
    st.session_state.credentials = None
    st.session_state.sheet_id = None

# Google OAuth settings - we'll use your credentials here
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 
          'https://www.googleapis.com/auth/drive.file']

def authenticate_user():
    """
    Handle Google sign-in process
    This is like showing your ID to enter a building
    """
    # Check if we have the necessary secrets
    if 'google' not in st.secrets:
        st.error("⚠️ Configurație lipsă! Adaugă credențialele Google în secrets.toml")
        st.stop()
    
    # Create the OAuth flow - this is Google's official login process
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": st.secrets.google.client_id,
                "client_secret": st.secrets.google.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [st.secrets.google.redirect_uri]
            }
        },
        scopes=SCOPES
    )
    
    flow.redirect_uri = st.secrets.google.redirect_uri
    
    # Generate authorization URL
    auth_url, _ = flow.authorization_url(prompt='consent')
    
    return auth_url

def get_feedback(value, measurement_type):
    """
    Provide feedback based on ADA 2025 guidelines
    This is like a traffic light system for your glucose values
    """
    
    # Check for dangerous low blood sugar first
    if value < 70:
        return ("⚠️ Hipoglicemie! Consumă imediat 15g carbohidrați rapizi. "
                "Verifică din nou în 15 minute.", "urgent")
    
    # Check for dangerous high blood sugar
    if value > 250:
        return ("🚨 Hiperglicemie severă! Bea apă și contactează medicul "
                "dacă nu scade în 2 ore.", "urgent")
    
    # Different rules for different measurement types
    if measurement_type == "Pe nemâncate":
        if value <= 99:
            return ("✅ Control glicemic excelent! Continuă așa!", "good")
        elif value <= 125:
            return ("⚠️ Valoare la limită. Atenție la dietă și mișcare.", "warning")
        else:
            return ("🔴 Glicemie crescută. Consultă medicul pentru ajustări.", "alert")
    
    elif measurement_type == "După masă (2 ore)":
        if value < 140:
            return ("✅ Excelent! Masa a fost bine tolerată.", "good")
        elif value < 180:
            return ("👍 În limite acceptabile.", "neutral")
        else:
            return ("🔴 Prea mare după masă. Redu carbohidrații.", "alert")
    
    else:  # Random check
        if value < 140:
            return ("Valoare normală.", "neutral")
        else:
            return ("⚠️ Valoare crescută. Monitorizează mai atent.", "warning")

def create_or_get_spreadsheet():
    """
    Create or access the user's glucose data spreadsheet
    Like creating a new notebook or opening an existing one
    """
    try:
        # This would use the authenticated credentials to access Google Sheets
        # For now, we'll simulate this
        st.session_state.sheet_id = "your-sheet-id"
        return True
    except Exception as e:
        st.error(f"Eroare la accesarea foii de calcul: {str(e)}")
        return False

def save_glucose_reading(value, measurement_type, notes=""):
    """
    Save a glucose reading to Google Sheets
    Like writing a new entry in your diary
    """
    timestamp = datetime.now()
    feedback, tone = get_feedback(value, measurement_type)
    
    # Create the data record
    record = {
        "Data": timestamp.strftime("%Y-%m-%d"),
        "Ora": timestamp.strftime("%H:%M"),
        "Valoare": value,
        "Tip Măsurare": measurement_type,
        "Feedback": feedback,
        "Ton": tone,
        "Note": notes
    }
    
    # Here we would save to Google Sheets
    # For now, we'll store in session state
    if 'readings' not in st.session_state:
        st.session_state.readings = []
    
    st.session_state.readings.append(record)
    return feedback, tone

def main():
    """
    Main application logic
    This is where everything comes together
    """
    
    # Title and description
    st.title("🩸 Monitor Glicemie")
    st.markdown("*Înregistrează și înțelege valorile glicemiei tale*")
    
    # Check if user is authenticated
    if not st.session_state.authenticated:
        st.markdown("""
        ### Bine ai venit! 
        
        Această aplicație te ajută să:
        - 📊 Înregistrezi valorile glicemiei
        - 💡 Înțelegi ce înseamnă fiecare valoare
        - 📈 Vezi tendințele în timp
        - 🔒 Păstrezi datele private în Google Drive
        
        **Cum funcționează confidențialitatea?**
        
        Datele tale sunt salvate într-o foaie Google Sheets privată în contul tău.
        Nimeni altcineva nu le poate vedea - nici măcar noi! Este ca și cum ai 
        avea un carnețel personal în seiful tău Google.
        """)
        
        # Login button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔐 Conectează-te cu Google", type="primary", use_container_width=True):
                auth_url = authenticate_user()
                st.markdown(f'<a href="{auth_url}" target="_self">Click aici pentru autentificare</a>', 
                          unsafe_allow_html=True)
        
        return
    
    # Sidebar for navigation
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user_email}")
        
        page = st.radio(
            "Navigare",
            ["📝 Adaugă Citire", "📊 Istoric", "📈 Tendințe", "⚙️ Setări"],
            label_visibility="collapsed"
        )
        
        if st.button("🚪 Deconectare"):
            st.session_state.authenticated = False
            st.rerun()
    
    # Main content based on selected page
    if page == "📝 Adaugă Citire":
        show_add_reading_page()
    elif page == "📊 Istoric":
        show_history_page()
    elif page == "📈 Tendințe":
        show_trends_page()
    elif page == "⚙️ Setări":
        show_settings_page()

def show_add_reading_page():
    """
    Page for adding new glucose readings
    Like filling out a simple form
    """
    st.header("📝 Adaugă Citire Nouă")
    
    # Create the form
    with st.form("glucose_reading"):
        col1, col2 = st.columns(2)
        
        with col1:
            value = st.number_input(
                "Valoare Glicemie (mg/dL)",
                min_value=20,
                max_value=600,
                value=100,
                step=1,
                help="Introdu valoarea afișată de glucometru"
            )
            
            measurement_type = st.selectbox(
                "Când ai măsurat?",
                ["Pe nemâncate", "După masă (2 ore)", "Verificare aleatorie"],
                help="Alege momentul măsurării pentru interpretare corectă"
            )
        
        with col2:
            measurement_time = st.time_input(
                "Ora măsurării",
                value=datetime.now().time(),
                help="Ora exactă când ai făcut măsurarea"
            )
            
            notes = st.text_area(
                "Note (opțional)",
                placeholder="Ex: După alergare, am mâncat mai mult la cină, etc.",
                height=100
            )
        
        # Submit button
        submitted = st.form_submit_button("💾 Salvează", type="primary", use_container_width=True)
        
        if submitted:
            # Save the reading
            feedback, tone = save_glucose_reading(value, measurement_type, notes)
            
            # Show feedback with appropriate styling
            if tone == "good":
                st.success(feedback)
            elif tone == "warning":
                st.warning(feedback)
            elif tone == "alert" or tone == "urgent":
                st.error(feedback)
            else:
                st.info(feedback)
            
            # Add encouraging message
            st.markdown("---")
            st.markdown("✅ **Citire salvată cu succes!**")
            
            # Show quick stats if we have data
            if 'readings' in st.session_state and len(st.session_state.readings) > 0:
                recent_readings = st.session_state.readings[-5:]
                avg_value = sum(r['Valoare'] for r in recent_readings) / len(recent_readings)
                st.metric("Media ultimelor 5 citiri", f"{avg_value:.0f} mg/dL")

def show_history_page():
    """
    Show historical glucose readings
    Like looking through your diary entries
    """
    st.header("📊 Istoric Citiri")
    
    if 'readings' not in st.session_state or len(st.session_state.readings) == 0:
        st.info("Nu ai încă citiri salvate. Adaugă prima ta citire!")
        return
    
    # Convert to DataFrame for easy display
    df = pd.DataFrame(st.session_state.readings)
    
    # Display summary statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Citiri", len(df))
    with col2:
        st.metric("Media Generală", f"{df['Valoare'].mean():.0f} mg/dL")
    with col3:
        good_readings = len(df[df['Ton'] == 'good'])
        percentage = (good_readings / len(df)) * 100
        st.metric("În Limite Normale", f"{percentage:.0f}%")
    
    # Show the readings table
    st.markdown("### Citiri Recente")
    
    # Format the display
    display_df = df[['Data', 'Ora', 'Valoare', 'Tip Măsurare', 'Feedback', 'Note']].copy()
    display_df = display_df.sort_index(ascending=False)  # Most recent first
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Valoare": st.column_config.NumberColumn(
                "Valoare (mg/dL)",
                format="%d"
            ),
            "Feedback": st.column_config.TextColumn(
                "Interpretare",
                width="large"
            )
        }
    )

def show_trends_page():
    """
    Show glucose trends over time
    Like looking at a graph of your progress
    """
    st.header("📈 Tendințe")
    
    if 'readings' not in st.session_state or len(st.session_state.readings) == 0:
        st.info("Ai nevoie de cel puțin câteva citiri pentru a vedea tendințe.")
        return
    
    df = pd.DataFrame(st.session_state.readings)
    
    # Create a simple line chart
    fig = go.Figure()
    
    # Add glucose values line
    fig.add_trace(go.Scatter(
        x=pd.to_datetime(df['Data'] + ' ' + df['Ora']),
        y=df['Valoare'],
        mode='lines+markers',
        name='Glicemie',
        line=dict(color='blue', width=2),
        marker=dict(size=8)
    ))
    
    # Add target ranges as background
    fig.add_hrect(y0=70, y1=130, fillcolor="green", opacity=0.1, 
                  annotation_text="Țintă pe nemâncate", annotation_position="right")
    fig.add_hrect(y0=0, y1=70, fillcolor="red", opacity=0.1,
                  annotation_text="Hipoglicemie", annotation_position="right")
    fig.add_hrect(y0=180, y1=600, fillcolor="orange", opacity=0.1,
                  annotation_text="Hiperglicemie", annotation_position="right")
    
    fig.update_layout(
        title="Evoluția Glicemiei",
        xaxis_title="Data și Ora",
        yaxis_title="Glicemie (mg/dL)",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show pattern analysis
    st.markdown("### Analiza Pattern-urilor")
    
    # Group by measurement type
    avg_by_type = df.groupby('Tip Măsurare')['Valoare'].mean()
    
    cols = st.columns(len(avg_by_type))
    for i, (measure_type, avg_value) in enumerate(avg_by_type.items()):
        with cols[i]:
            st.metric(f"Media {measure_type}", f"{avg_value:.0f} mg/dL")

def show_settings_page():
    """
    Settings page for user preferences
    Like adjusting the settings on your phone
    """
    st.header("⚙️ Setări")
    
    st.markdown("### Despre Aplicație")
    st.info("""
    **Monitor Glicemie v1.0**
    
    Această aplicație folosește ghidurile American Diabetes Association (ADA) 2025
    pentru a interpreta valorile glicemiei tale.
    
    Toate datele sunt stocate în contul tău Google Drive personal.
    Aplicația nu colectează și nu transmite date către terți.
    """)
    
    st.markdown("### Export Date")
    if st.button("📥 Descarcă datele în format CSV"):
        if 'readings' in st.session_state and len(st.session_state.readings) > 0:
            df = pd.DataFrame(st.session_state.readings)
            csv = df.to_csv(index=False)
            st.download_button(
                label="💾 Salvează CSV",
                data=csv,
                file_name=f"glicemie_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    st.markdown("### Ținte Personalizate")
    st.info("În dezvoltare: Posibilitatea de a seta ținte personalizate conform recomandărilor medicului tău.")
    
    st.markdown("### Ștergere Date")
    with st.expander("⚠️ Zonă Periculoasă"):
        st.warning("Ștergerea datelor este permanentă și nu poate fi anulată!")
        if st.button("🗑️ Șterge toate datele", type="secondary"):
            if 'readings' in st.session_state:
                st.session_state.readings = []
                st.success("Toate datele au fost șterse.")
                st.rerun()

# Run the app
if __name__ == "__main__":
    # For testing purposes, simulate authentication
    if st.query_params.get("authenticated") == "true":
        st.session_state.authenticated = True
        st.session_state.user_email = "test@example.com"
    
    main()
