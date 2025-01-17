import streamlit as st
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

import firebase_setup  # Import Firebase setup to initialize the app only once
from firebase_admin import firestore

db = firestore.client()


# Gmail SMTP credentials
SMTP_EMAIL = "arif670@gmail.com"
SMTP_PASSWORD = "fnhv puid ukeq skhp"
APP_URL = "http://localhost:8501"

# App logo
LOGO_PATH = r"C:\Users\arif6\OneDrive\Desktop\STRIDGE\Misc_The Mark\LOGO-3.jpeg"

# Ensure default Admin user exists
def ensure_default_admin():
    admin_query = db.collection("Users").where("EmailID", "==", "Admin").stream()
    if not any(admin_query):
        db.collection("Users").add({
            "Name": "Admin",
            "EmailID": "Admin",
            "Role": "Admin",
            "Password": "Admin"
        })

ensure_default_admin()

# Helper functions
def authenticate_user(email, password):
    users = db.collection("Users").where("EmailID", "==", email).stream()
    for user in users:
        user_data = user.to_dict()
        if user_data.get("Password") == password:
            user_data["id"] = user.id
            return user_data
    return None

def send_email(recipient_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        st.error(f"Failed to send email. Error: {e}")

def add_new_user():
    st.subheader("Add New User")
    name = st.text_input("Name")
    email = st.text_input("Email ID")
    role = st.selectbox("Role", ["Requestee", "Checker", "Approver", "Admin"])
    if st.button("Add User"):
        temp_password = "Temp@123"
        db.collection("Users").add({"Name": name, "EmailID": email, "Role": role, "Password": temp_password})
        email_body = f"""
        <p>Hello {name},</p>
        <p>You have been added to the Material Requisition system.</p>
        <p>Login URL: <a href="{APP_URL}">{APP_URL}</a></p>
        <p>Your temporary password is: <b>{temp_password}</b></p>
        """
        send_email(email, "Welcome to Material Requisition System", email_body)
        st.success("User added and email sent!")

def modify_existing_user():
    st.subheader("Modify Existing User")
    users = db.collection("Users").stream()

    # Safely collect user data
    user_list = {}
    for user in users:
        user_data = user.to_dict()
        user_id = user.id
        name = user_data.get("Name", "Unnamed User")  # Default if 'Name' is missing
        user_list[user_id] = name

    if not user_list:
        st.warning("No users found.")
        return

    # Select user
    selected_user = st.selectbox("Select User", list(user_list.keys()), format_func=lambda x: user_list[x])
    if selected_user:
        user_data = db.collection("Users").document(selected_user).get().to_dict()
        st.write(f"Selected User: {user_data.get('Name', 'Unnamed User')}")
        new_email = st.text_input("Email ID", user_data.get("EmailID", ""))
        new_role = st.selectbox("Role", ["Requestee", "Checker", "Approver", "Admin"], 
                                index=["Requestee", "Checker", "Approver", "Admin"].index(user_data.get("Role", "Requestee")))
        if st.button("Update User"):
            db.collection("Users").document(selected_user).update({
                "EmailID": new_email,
                "Role": new_role,
            })
            st.success("User updated successfully!")

def authenticate_user(email, password):
    users = db.collection("Users").where("EmailID", "==", email).stream()
    for user in users:
        user_data = user.to_dict()
        if user_data.get("Password") == password:
            user_data["id"] = user.id
            user_data.setdefault("Name", "Unnamed User")  # Default for missing 'Name'
            return user_data
    return None


def submit_material_request(user_id):
    st.subheader("Submit Material Request")
    product_code = st.text_input("Product Code")
    description = st.text_input("Product Description")
    units = st.text_input("Units")
    quantity = st.number_input("Quantity", min_value=0)
    required_date = st.date_input("Required Date")
    remarks = st.text_area("Remarks")
    if st.button("Submit Request"):
        db.collection("MaterialRequests").add({
            "Product Code": product_code,
            "Description": description,
            "Units": units,
            "Quantity": quantity,
            "Required Date": required_date.strftime("%Y-%m-%d"),
            "Remarks": remarks,
            "Requestee": user_id,
            "Status": "Pending"
        })
        st.success("Material request submitted!")

def review_material_requests(role):
    st.subheader(f"Review Material Requests ({role})")
    requests = db.collection("MaterialRequests").where("Status", "==", "Pending").stream()
    request_list = {req.id: req.to_dict() for req in requests}
    selected_request = st.selectbox("Select Request", list(request_list.keys()), format_func=lambda x: request_list[x]["Product Code"])
    if selected_request:
        request_data = request_list[selected_request]
        st.write(request_data)
        action = st.selectbox("Action", ["Approve", "Reject", "Revise and Resubmit", "Hold"])
        remarks = st.text_area("Remarks") if action != "Approve" else None
        if st.button("Submit Action"):
            db.collection("MaterialRequests").document(selected_request).update({"Status": action, "Remarks": remarks})
            st.success(f"Request marked as {action}.")

def change_password(user_id):
    st.subheader("Change Password")
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    if st.button("Update Password"):
        if new_password == confirm_password:
            db.collection("Users").document(user_id).update({"Password": new_password})
            st.success("Password updated successfully!")
        else:
            st.error("Passwords do not match.")

# Main App Logic
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.image(LOGO_PATH, width=300)
    st.title("Material Requisition Portal")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = authenticate_user(email, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user = user
        else:
            st.error("Invalid email or password.")
else:
    st.sidebar.title("Navigation")
    role = st.session_state.user["Role"]
    if role == "Admin":
        with st.sidebar.expander("Admin Options", expanded=True):
            if st.button("Add New User"):
                st.session_state["current_tab"] = "add_user"
            if st.button("Modify Existing User"):
                st.session_state["current_tab"] = "modify_user"
    if role == "Requestee":
        if st.sidebar.button("Submit Material Request"):
            st.session_state["current_tab"] = "submit_request"
    if role in ["Checker", "Approver"]:
        if st.sidebar.button("Review Material Requests"):
            st.session_state["current_tab"] = "review_requests"
    if st.sidebar.button("Change Password"):
        st.session_state["current_tab"] = "change_password"
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.experimental_rerun()

    if "current_tab" not in st.session_state:
        st.session_state["current_tab"] = None

    if st.session_state["current_tab"] == "add_user":
        add_new_user()
    elif st.session_state["current_tab"] == "modify_user":
        modify_existing_user()
    elif st.session_state["current_tab"] == "submit_request":
        submit_material_request(st.session_state.user["id"])
    elif st.session_state["current_tab"] == "review_requests":
        review_material_requests(st.session_state.user["Role"])
    elif st.session_state["current_tab"] == "change_password":
        change_password(st.session_state.user["id"])
    else:
        st.write("Welcome to the Material Requisition Portal!")
