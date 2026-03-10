import streamlit as st
import pandas as pd
import google.generativeai as genai
import urllib.parse
import json
import os
from datetime import date, datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import time

st.set_page_config(page_title="Cash Flow Chaser Pro", layout="wide")

# ==========================================
# 1. SECURITY & LOGIN VAULT
# ==========================================
try:
    SECURE_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ Secrets file not found! Please set up .streamlit/secrets.toml")
    st.stop()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("## 🔐 Welcome to Cash Flow Chaser")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        if submit_button:
            if username ==st.secret["ADMIN_USERNAME"] and password ==st.secret["ADMIN_PASSWORD"]:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ Invalid Username or Password")
    st.stop()

# ==========================================
# 2. DATABASE SETUP (Permanent Storage Engine)
# ==========================================
DB_FILE = "master_database.csv"

# Function to auto-generate Client IDs
def generate_new_client_id(df):
    if df.empty or 'Client_ID' not in df.columns:
        return "C-101"
    existing_ids = df['Client_ID'].astype(str).str.extract(r'C-(\d+)').dropna()[0].astype(int)
    if existing_ids.empty:
        return "C-101"
    return f"C-{existing_ids.max() + 1}"

# Function to load data from hard drive
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    else:
        # if no previous records
        return pd.DataFrame(columns=[
            "Client_ID", "Client Name", "Phone Number", "Client Email ID", "Amount Due (₹)", 
            "Due Date", "Next Action Date", "Payment Status", "Date Added", 
            "Relationship Status", "Previous Context", "Preferred Language"
        ])

# Function to save data to hard drive
def save_data(df):
    df.to_csv(DB_FILE, index=False)

if "db" not in st.session_state:
    st.session_state.db = load_data()

# --- SELF-HEALING ENGINE (Schema Migration) ---
required_columns = ["Client_ID", "Client Name", "Phone Number", "Client Email ID", "Amount Due (₹)", "Due Date", "Next Action Date", "Payment Status", "Date Added", "Relationship Status", "Previous Context", "Preferred Language"]

# Check if Client_ID is missing (legacy DB fix)
if "Client_ID" not in st.session_state.db.columns and not st.session_state.db.empty:
    st.session_state.db.insert(0, "Client_ID", [f"C-{101+i}" for i in range(len(st.session_state.db))])
    save_data(st.session_state.db)

for col in required_columns:
    if col not in st.session_state.db.columns:
        st.session_state.db[col] = "" 
        save_data(st.session_state.db)

st.title("💸 Tone-Adjusting Cash Flow Chaser")

# ==========================================
# EMAIL AUTOMATION ENGINE (The Postman)
# ==========================================
def send_daily_alert(gm_email, pending_count, total_amount):
    try:
        sender_email = st.secrets["SENDER_EMAIL"]
        email_password = st.secrets["EMAIL_PASSWORD"]
        
        msg = MIMEMultipart()
        msg['From'] = f"Cash Flow AI <{sender_email}>"
        msg['To'] = gm_email
        msg['Subject'] = f"🔔 Daily Alert: {pending_count} pending follow-ups today!"
        
        body = f"""
        Hello,
        
        This is your automated Cash Flow Chaser update.
        
        🚨 Action Required Today:
        - Clients to Contact: {pending_count}
        - Total Capital at Stake: Rs. {total_amount:,.0f}
        
        Please log in to your dashboard to send the AI-generated WhatsApp reminders with one click.
        
        Regards,
        Your AI Assistant
        """
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, email_password)
        text = msg.as_string()
        server.sendmail(sender_email, gm_email, text)
        server.quit()
        return "Success"
    except Exception as e:
        return str(e)

# --- SIDEBAR (Admin Controls) ---
with st.sidebar:
    st.markdown("### 🛠️ Admin Automation")
    st.write("Simulate the 9:00 AM daily alert.")
    
    today_date = date.today()
    pending_only = st.session_state.db[st.session_state.db["Payment Status"] == "Pending"]
    total_stuck = pd.to_numeric(pending_only["Amount Due (₹)"], errors='coerce').sum()
    
    test_gm_email = st.text_input("Send Alert To (Your Email):", placeholder="xyz@gmail.com")
    
    if st.button("📩 Send Daily Alert Now", type="primary"):
        if not test_gm_email:
            st.warning("Please enter your email above.")
        else:
            with st.spinner("Sending email via secure server..."):
                result = send_daily_alert(test_gm_email, len(pending_only), total_stuck)
                if result == "Success":
                    st.success("✅ Email Sent! Check your inbox.")
                    st.balloons()
                else:
                    st.error(f"❌ Failed to send: {result}")
    
    st.divider()
    st.markdown("### 🔒 Account")
    if st.button("🚪 Logout", type="secondary"):
        st.session_state.logged_in = False
        st.rerun()

# ==========================================
# 3. TABBED INTERFACE
# ==========================================
tab1, tab2, tab3 = st.tabs(["📨 Daily Action Queue", "⚙️ Manage Database", "🧠 AI Chat Analyzer"])

#--------------------------------------------------
# --- TAB 1: DAILY ACTION QUEUE ---
#---------------------------------------------------
with tab1:
    st.subheader("📋 Today's Action List")
    
    pending_only = st.session_state.db[st.session_state.db["Payment Status"] == "Pending"]
    total_pending = pd.to_numeric(pending_only["Amount Due (₹)"], errors='coerce').sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric(label="💰 Total Capital Stuck", value=f"₹ {total_pending:,.0f}")
    m2.metric(label="👥 Active Defaulters", value=f"{len(pending_only)} Clients")
    m3.metric(label="✅ Success Rate", value="AI Active", delta="Optimizing...")
    st.divider()

    today_date = date.today()
    
    def is_actionable(row):
        snooze_val = row["Next Action Date"]
        if pd.notna(snooze_val) and str(snooze_val).strip() != "":
            try:
                snooze_date = datetime.strptime(str(snooze_val).strip(), "%Y-%m-%d").date()
                if snooze_date > today_date:
                    return False
            except:
                pass
        return True
        
    action_queue = pending_only[pending_only.apply(is_actionable, axis=1)]

    if action_queue.empty:
        st.success("🎉 All clear! No pending task!!")
    else:
        if "queue_msgs" not in st.session_state:
            st.session_state.queue_msgs = {}
            
        missing_msgs = [idx for idx in action_queue.index if idx not in st.session_state.queue_msgs]
        
        if missing_msgs:
            st.warning(f"🔔 You have {len(missing_msgs)} clients in today's queue.")
            
            if st.button("🚀 Auto-Generate All Messages", type="primary", use_container_width=True):
                st.markdown("### 🤖 AI is working its magic...")
                progress_bar = st.progress(0)
                status_text = st.empty()
                tip_box = st.empty() 
                
                engagement_texts = [
                    "🧠 Analyzing past payment behavior...",
                    "✍️ Adjusting tone based on relationship status...",
                    "📊 Calculating exact overdue penalties...",
                    "💡 Pro Tip: 80% of unpaid invoices are paid after just 2 polite reminders.",
                    "🌐 Translating nuances into their preferred language...",
                    "💸 Consistent follow-ups improve cash flow by 30%.",
                    "⏳ Just a little more time... quality takes a few seconds!"
                ]
                
                genai.configure(api_key=SECURE_API_KEY)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                for i, idx in enumerate(missing_msgs):
                    client_data = action_queue.loc[idx]
                    status_text.markdown(f"**Drafting custom message for {client_data['Client Name']} ({i+1}/{len(missing_msgs)})...**")
                    tip_box.info(random.choice(engagement_texts))
                    
                    try:
                        due_date_obj = datetime.strptime(str(client_data["Due Date"]), "%Y-%m-%d").date()
                        overdue_days = max(0, (today_date - due_date_obj).days)
                    except:
                        overdue_days = 0
                        
                    if overdue_days > 20 or client_data['Relationship Status'] in ['Difficult', 'Tense']:
                        tone = "Strict"
                    elif overdue_days < 7:
                        tone = "Friendly"
                    else:
                        tone = "Firm"
                        
                    prompt = f"""
                    Write a payment reminder for:
                    - Name: {client_data['Client Name']}
                    - Amount: ₹{client_data['Amount Due (₹)']}
                    - Overdue: {overdue_days} days
                    - Relationship: {client_data['Relationship Status']}
                    - Context: {client_data['Previous Context']}
                    
                    Write EXACTLY in this language: {client_data['Preferred Language']}.
                    If Overdue > 20 days, be strict. If < 7 days, be friendly.
                    Output ONLY the message text.
                    """
                    try:
                        response = model.generate_content(prompt)
                        st.session_state.queue_msgs[idx] = {"text": response.text, "tone": tone}
                    except Exception as e:
                        st.session_state.queue_msgs[idx] = {"text": f"Error: {e}", "tone": "Error"}
                    
                    time.sleep(3) 
                    progress_bar.progress((i + 1) / len(missing_msgs))
                    
                tip_box.empty() 
                status_text.success("✅ All messages generated successfully! Loading your dashboard...")
                time.sleep(1.5) 
                st.rerun()
        else:
            st.success("✨ All messages are drafted and ready to send!")
            
            # Headers including Client ID context
            h1, h2, h3, h4, h5, h6, h7 = st.columns([1.5, 1.2, 0.8, 0.8, 1.2, 1.2, 1.5])
            h1.markdown("**1. Client (ID)**")
            h2.markdown("**2. AI Tone**")
            h3.markdown("**3. Email**")
            h4.markdown("**4. Whatsapp**")
            h5.markdown("**5. Snooze**")
            h6.markdown("**6. Resolve**")
            h7.markdown("**7. Dues**")
            st.divider()
            
            for idx, client_data in action_queue.iterrows():
                c1, c2, c3, c4, c5, c6, c7 = st.columns([1.5, 1.2, 1.0, 1.2, 1.2, 1.2, 1.5])
                client_id = client_data['Client_ID']
                
                try:
                    due_date_obj = datetime.strptime(str(client_data["Due Date"]), "%Y-%m-%d").date()
                    overdue_days = max(0, (today_date - due_date_obj).days)
                except:
                    overdue_days = 0
                    
                msg_data = st.session_state.queue_msgs[idx]
                
                # Col 1: Name & ID
                c1.write(f"**{client_data['Client Name']}**\n\n`{client_id}`")
                
                # Col 2: Tone Button
                with c2:
                    with st.popover(f"🎭 {msg_data['tone']}"):
                        st.markdown("**AI Generated Message:**")
                        edited_msg = st.text_area("Edit", msg_data['text'], height=150, key=f"txt_{idx}", label_visibility="collapsed")
                        st.session_state.queue_msgs[idx]["text"] = edited_msg

                encoded_message = urllib.parse.quote(st.session_state.queue_msgs[idx]["text"])
                
                # Col 3: Email
                with c3:
                    email_url = f"mailto:{str(client_data['Client Email ID']).strip()}?subject=Payment Reminder&body={encoded_message}"
                    st.link_button("📧", email_url, help="Send via Email")
                    
                # Col 4: WhatsApp
                with c4:
                    wa_url = f"https://wa.me/{str(client_data['Phone Number']).strip()}?text={encoded_message}"
                    st.link_button("📲", wa_url, help="Send via WhatsApp")
                    
                # Col 5: Snooze (Strictly using Client_ID)
                with c5:
                    with st.popover("💤 Snooze"):
                        snz_days = st.number_input("Days", 1, value=2, key=f"snz_{idx}")
                        if st.button("Confirm", key=f"snz_btn_{idx}"):
                            new_date = str(today_date + timedelta(days=snz_days))
                            st.session_state.db.loc[st.session_state.db['Client_ID'] == client_id, "Next Action Date"] = new_date
                            save_data(st.session_state.db)
                            del st.session_state.queue_msgs[idx] 
                            st.rerun()
                            
                # Col 6: Paid (Strictly using Client_ID)
                with c6:
                    if st.button("✅ Paid", key=f"paid_{idx}"):
                        st.session_state.db.loc[st.session_state.db['Client_ID'] == client_id, "Payment Status"] = "Paid"
                        save_data(st.session_state.db)
                        del st.session_state.queue_msgs[idx] 
                        st.rerun()
                        
                # Col 7: Amount
                with c7:
                    st.write(f"₹{client_data['Amount Due (₹)']} \n *({overdue_days} days)*")
                    
                st.markdown("---")

#------------------------------------
# --- TAB 2: MANAGE DATABASE ---
#------------------------------------
with tab2:
    st.subheader("⚙️ Master Database")
    st.write("Ab aap safely yahan data edit, upload aur delete kar sakte hain.")
    
    edited_df = st.data_editor(st.session_state.db, num_rows="dynamic", use_container_width=True, key="editor")
    
    if st.button("💾 Save All Changes", type="primary"):
        # Ensure any newly added rows through the UI get a Client_ID
        for index, row in edited_df.iterrows():
            if pd.isna(row['Client_ID']) or str(row['Client_ID']).strip() == "":
                edited_df.at[index, 'Client_ID'] = generate_new_client_id(edited_df)
                
        st.session_state.db = edited_df
        save_data(st.session_state.db) 
        st.success("✅ Database permanently updated!")
        st.rerun()
        
    st.divider()
    
    # --- BULK IMPORT ---
    uploaded_csv = st.file_uploader("Upload Tally/Excel Data (.csv)", type=["csv"])
    if uploaded_csv is not None:
        if st.button("📥 Import CSV Data"):
            new_data = pd.read_csv(uploaded_csv)
            # Ensure new imported data gets Client IDs
            if "Client_ID" not in new_data.columns:
                new_data.insert(0, "Client_ID", "")
            for i in range(len(new_data)):
                if pd.isna(new_data.at[i, "Client_ID"]) or str(new_data.at[i, "Client_ID"]).strip() == "":
                    temp_combined = pd.concat([st.session_state.db, new_data.iloc[:i]], ignore_index=True)
                    new_data.at[i, "Client_ID"] = generate_new_client_id(temp_combined)
                    
            st.session_state.db = pd.concat([st.session_state.db, new_data], ignore_index=True)
            save_data(st.session_state.db) 
            st.success("✅ Bulk Data Added with unique Client IDs!")
            st.rerun()

    st.divider()
    
    col_export, col_danger = st.columns(2)
    with col_export:
        st.markdown("##### 📤 Export Data")
        csv_export = st.session_state.db.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Updated CSV", data=csv_export, file_name=f"CashFlow_{date.today()}.csv", mime="text/csv")
        
    with col_danger:
        st.markdown("##### ⚠️ Danger Zone")
        if st.button("🗑️ Wipe Entire Database"):
            st.session_state.db = pd.DataFrame(columns=st.session_state.db.columns)
            save_data(st.session_state.db)
            st.success("🧹 Database has been wiped clean!")
            st.rerun()

#----------------------------------------------------
# --- TAB 3: AI CHAT ANALYZER (With Update Logic) ---
#----------------------------------------------------
with tab3:
    st.subheader("🕵️‍♂️ Paste Raw Chat for AI Extraction")
    uploaded_file = st.file_uploader("Upload WhatsApp Export (.txt)", type=["txt"])
    raw_chat = uploaded_file.read().decode("utf-8") if uploaded_file else st.text_area("Or Paste Raw Chat here:", height=150)
    
    if "temp_extracted" not in st.session_state:
        st.session_state.temp_extracted = None

    if st.button("Extract Data", type="primary"):
        if not raw_chat:
            st.error("⚠️ Please paste data!")
        else:
            with st.spinner("AI is analyzing text..."):
                genai.configure(api_key=SECURE_API_KEY)
                model = genai.GenerativeModel('gemini-2.5-flash')
                prompt = f"""
                Analyze this rough chat note and extract business details into STRICT JSON.
                Raw Text: {raw_chat}
                Output ONLY valid JSON.
                {{
                    "Client Name": "Extract the CLIENT'S name. If the text addresses the owner, do NOT use it. Else 'Unknown'",
                    "Phone Number": "Extract number with 91. If not found, strictly write ''",
                    "Client Email ID": "Extract email if present, else ''",
                    "Amount Due (₹)": Extract only the integer amount,
                    "Due Date": "If no old debt date, strictly set to today: {date.today()}",
                    "Next Action Date": "If promise to pay in future calculate date. Else ''",
                    "Payment Status": "Strictly write 'Pending'",
                    "Relationship Status": "Choose: Regular, VIP, Difficult, or Tense",
                    "Previous Context": "Write a 1-line summary EXACTLY in the raw text's language. NO English translation.",
                    "Preferred Language": "Choose: Hindi, English, or Hinglish"
                }}
                """
                try:
                    response = model.generate_content(prompt)
                    cleaned = response.text.replace("```json", "").replace("```", "").strip()
                    data = json.loads(cleaned)
                    data["Date Added"] = str(date.today())
                    st.session_state.temp_extracted = pd.DataFrame([data])
                except Exception as e:
                    st.error(f"Error parsing data: {e}")

    # --- THE REVIEW & UPDATE ZONE ---
    if st.session_state.temp_extracted is not None:
        st.divider()
        st.markdown("### 🛑 Action Zone: Append or Update")
        
        # --- SMART MATCH FILTER ---
        extracted_name = str(st.session_state.temp_extracted["Client Name"].iloc[0]).strip()
        extracted_phone = str(st.session_state.temp_extracted["Phone Number"].iloc[0]).strip()
        
        client_options = ["-- Create New Client --"]
        
        if not st.session_state.db.empty:
            db = st.session_state.db
            
            # Condition 1: Exact phone number match
            phone_match = db['Phone Number'].astype(str).str.contains(extracted_phone, na=False) if extracted_phone else False
            
            # Condition 2: Partial name match (case-insensitive)
            name_match = False
            if extracted_name and extracted_name.lower() != "unknown":
                name_match = db['Client Name'].astype(str).str.lower().str.contains(extracted_name.lower(), na=False)
                
            # Filter the database to only show overlapping clients
            matched_clients = db[phone_match | name_match]
            
            if not matched_clients.empty:
                client_options += list(matched_clients["Client_ID"].astype(str) + " - " + matched_clients["Client Name"].astype(str))
                
        selected_target = st.selectbox("Where should this data go? (Filtered by Smart Match)", client_options)
        
        st.write("Edit extracted details below if AI missed anything:")
        edited_temp = st.data_editor(st.session_state.temp_extracted, use_container_width=True, key="temp_editor")
        
        col_cancel, col_save = st.columns([1, 4])
        
        if col_cancel.button("❌ Cancel"):
            st.session_state.temp_extracted = None
            st.rerun()
            
        if col_save.button("✅ Confirm Action", type="primary"):
            if selected_target == "-- Create New Client --":
                # Create a completely new entry
                if edited_temp["Phone Number"].iloc[0] == "" or edited_temp["Phone Number"].iloc[0] == "910000000000":
                    st.error("⚠️ Phone number is required for new clients!")
                else:
                    new_id = generate_new_client_id(st.session_state.db)
                    edited_temp.insert(0, "Client_ID", new_id)
                    st.session_state.db = pd.concat([st.session_state.db, edited_temp], ignore_index=True)
                    save_data(st.session_state.db)
                    st.session_state.temp_extracted = None
                    st.success(f"🔥 Successfully created new client: {new_id}")
                    st.rerun()
            else:
                # Update existing client (Schema fix implementation)
                target_id = selected_target.split(" - ")[0]
                
                # Only update columns that have non-empty data extracted by AI
                update_cols = edited_temp.columns
                for col in update_cols:
                    val = edited_temp[col].iloc[0]
                    if pd.notna(val) and str(val).strip() != "" and col != "Date Added":
                        st.session_state.db.loc[st.session_state.db["Client_ID"] == target_id, col] = val
                        
                save_data(st.session_state.db)
                st.session_state.temp_extracted = None
                st.success(f"🔄 Successfully updated existing client: {target_id}")

                st.rerun()
