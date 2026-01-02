# Firebase SSO Integration Guide
## For AWS WAF Scanner Streamlit Application

---

## 📚 **Table of Contents**

1. [Quick Start](#quick-start)
2. [Firebase Setup](#firebase-setup)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Integration](#integration)
6. [User Management](#user-management)
7. [Role-Based Access Control](#rbac)
8. [Troubleshooting](#troubleshooting)

---

## 🚀 **Quick Start (15 Minutes)**

### **Prerequisites**
- Firebase account (free tier works)
- Python 3.8+
- Existing AWS WAF Scanner project

### **Quick Setup**
```bash
# 1. Install Firebase packages
pip install firebase-admin pyrebase4 python-dotenv

# 2. Download service account key from Firebase Console
#    (see Firebase Setup section below)

# 3. Create first admin user
python create_first_admin.py

# 4. Update streamlit_app.py (see Integration section)

# 5. Run your app
streamlit run streamlit_app.py
```

---

## 🔥 **Firebase Setup (Step-by-Step)**

### **Step 1: Create Firebase Project**

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Click **"Add project"** (or use existing)
3. Enter project name: **"aws-waf-scanner"**
4. Disable Google Analytics (optional)
5. Click **"Create project"**

### **Step 2: Enable Authentication**

1. In left sidebar, click **"Build"** → **"Authentication"**
2. Click **"Get Started"**
3. Go to **"Sign-in method"** tab
4. Enable **"Email/Password"**:
   - Click on "Email/Password"
   - Toggle **"Enable"** switch
   - Click **"Save"**

### **Step 3: Create Firestore Database**

1. In left sidebar, click **"Build"** → **"Firestore Database"**
2. Click **"Create database"**
3. Select **"Start in production mode"**
4. Choose location: **"us-central"** (or closest to you)
5. Click **"Enable"**

### **Step 4: Download Service Account Key**

1. Click ⚙️ (gear icon) → **"Project settings"**
2. Go to **"Service accounts"** tab
3. Click **"Generate new private key"**
4. Click **"Generate key"** to download JSON file
5. Save as **`firebase_config.json`** in your project root
6. ⚠️ **Never commit this file to Git!**

### **Step 5: Get Web API Key**

1. In **Project settings** → **"General"** tab
2. Scroll to **"Your apps"** section
3. Click **Web icon (</>)** if no web app exists
4. Register app with nickname: **"WAF Scanner Web"**
5. Copy the **`firebaseConfig`** object
6. Note down the **`apiKey`** value

---

## 📦 **Installation**

### **Install Required Packages**

```bash
pip install firebase-admin pyrebase4 python-dotenv requests
```

### **Update requirements.txt**

Add to your `requirements.txt`:
```txt
firebase-admin>=6.2.0
pyrebase4>=4.7.0
python-dotenv>=1.0.0
requests>=2.31.0
```

### **Project Structure**

```
your-project/
├── streamlit_app.py              # Main app (updated with auth)
├── firebase_auth_streamlit.py    # Auth module ✨ NEW
├── create_first_admin.py          # Admin creation script ✨ NEW
├── waf_scanner_integrated.py     # Existing WAF scanner
├── waf_scanner_ai_enhanced.py    # Existing AI enhancement
├── firebase_config.json          # Service account key ⚠️ SECRET!
├── .env                          # Environment variables ⚠️ SECRET!
├── .gitignore                    # Git ignore file
└── requirements.txt              # Python dependencies
```

---

## ⚙️ **Configuration**

### **Option 1: Using .env File (Recommended for Development)**

Create `.env` file:
```bash
# Firebase Web API Key
FIREBASE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX

# Firebase Project Config
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
FIREBASE_STORAGE_BUCKET=your-project.appspot.com

# Optional: Firebase Admin SDK (alternative to service account file)
FIREBASE_SERVICE_ACCOUNT_KEY=./firebase_config.json
```

### **Option 2: Using Streamlit Secrets (Recommended for Production)**

Create `.streamlit/secrets.toml`:
```toml
[firebase]
api_key = "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX"

[firebase.service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "abc123..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."

[firebase.web_config]
apiKey = "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX"
authDomain = "your-project.firebaseapp.com"
projectId = "your-project-id"
storageBucket = "your-project.appspot.com"
messagingSenderId = "123456789"
appId = "1:123456789:web:abc123"
```

### **Update .gitignore**

Add these lines to `.gitignore`:
```
# Firebase secrets
firebase_config.json
.env
.streamlit/secrets.toml

# Python
__pycache__/
*.py[cod]
*$py.class
```

---

## 🔌 **Integration with Existing App**

### **Minimal Integration (Existing streamlit_app.py)**

Add these lines at the **very top** of your `streamlit_app.py`:

```python
import streamlit as st
from firebase_auth_streamlit import (
    firebase_manager, 
    render_login_page, 
    render_user_menu,
    check_session_timeout,
    UserRole,
    require_permission
)
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config (must be first Streamlit command)
st.set_page_config(
    page_title="AWS WAF Scanner",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Firebase (only once)
if 'firebase_initialized' not in st.session_state:
    # Try to load from secrets.toml first
    if hasattr(st, 'secrets') and 'firebase' in st.secrets:
        config = {
            'service_account_dict': dict(st.secrets['firebase']['service_account']),
            'api_key': st.secrets['firebase']['api_key'],
            'web_config': dict(st.secrets['firebase'].get('web_config', {}))
        }
    # Fallback to environment variables and firebase_config.json
    else:
        config = {
            'service_account_key': os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY', 'firebase_config.json'),
            'api_key': os.getenv('FIREBASE_API_KEY')
        }
    
    success, message = firebase_manager.initialize_firebase(config)
    if success:
        st.session_state.firebase_initialized = True
    else:
        st.error(f"Firebase initialization failed: {message}")
        st.stop()

# Check session timeout
check_session_timeout()

# AUTHENTICATION CHECK - This protects your entire app
if not st.session_state.get('authenticated'):
    render_login_page()
    st.stop()  # Stop execution here if not authenticated

# Show user menu in sidebar
render_user_menu()

# ==========================================
# YOUR EXISTING APP CODE STARTS HERE
# ==========================================

st.title("AWS Well-Architected Framework Scanner")

# ... rest of your existing code ...
```

### **Advanced Integration with RBAC**

For role-based access control:

```python
# In your existing code, wrap features with permission checks

# Example: Restrict multi-account scanning to admins and users only
if require_permission('multi_account_scan'):
    st.markdown("## Multi-Account Scanner")
    # Your multi-account scanner code here
else:
    st.info("🔒 Multi-account scanning requires User or Admin role")

# Example: Admin-only user management
if st.session_state.get('user_role') == UserRole.ADMIN:
    if st.sidebar.button("👥 Manage Users"):
        # Show user management interface
        from firebase_auth_streamlit import render_admin_user_management
        render_admin_user_management()
```

---

## 👥 **User Management**

### **Create First Admin User**

```bash
python create_first_admin.py
```

Follow the prompts:
```
Admin Email: admin@yourcompany.com
Display Name: Admin User
Password: ********
Confirm Password: ********
```

### **Create Additional Users (via Admin Panel)**

1. Login as admin
2. Navigate to **User Management** (add to your sidebar)
3. Click **"Create User"** tab
4. Fill in:
   - Email
   - Display Name
   - Role (Admin/User/Viewer)
   - Password
5. Click **"Create User"**

### **User Roles & Permissions**

| Permission | Admin | User | Viewer |
|------------|-------|------|--------|
| Create Users | ✅ | ❌ | ❌ |
| Delete Users | ✅ | ❌ | ❌ |
| Run AWS Scans | ✅ | ✅ | ❌ |
| Export Data | ✅ | ✅ | ✅ |
| Generate PDFs | ✅ | ✅ | ❌ |
| Multi-Account Scan | ✅ | ✅ | ❌ |
| Manage Settings | ✅ | ❌ | ❌ |

### **Programmatic User Creation**

```python
from firebase_auth_streamlit import firebase_manager, UserRole

success, message, user_data = firebase_manager.create_user(
    email="newuser@company.com",
    password="SecurePass123!",
    display_name="New User",
    role=UserRole.USER
)

if success:
    print(f"✅ User created: {user_data['email']}")
else:
    print(f"❌ Error: {message}")
```

---

## 🔒 **Role-Based Access Control (RBAC)**

### **Check Permissions in Code**

```python
from firebase_auth_streamlit import require_permission, UserRole

# Method 1: Check permission and show/hide feature
if require_permission('run_aws_scans'):
    st.button("🚀 Run Scan")
else:
    st.info("Scanning requires User role or higher")

# Method 2: Get user role
user_role = st.session_state.get('user_role', UserRole.VIEWER)

if user_role == UserRole.ADMIN:
    # Admin-only code
    pass
elif user_role == UserRole.USER:
    # User code
    pass
else:
    # Viewer code
    pass

# Method 3: Check specific permission
from firebase_auth_streamlit import UserRole

permissions = UserRole.get_permissions(st.session_state.get('user_role'))
if permissions.get('generate_pdfs'):
    # Generate PDF
    pass
```

### **Protect Entire Pages**

```python
from firebase_auth_streamlit import require_admin

def admin_settings_page():
    require_admin()  # This will show error and stop if not admin
    
    st.title("Admin Settings")
    # Admin-only settings here
```

---

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Issue 1: "Firebase not initialized"**
```
❌ Firebase not initialized. Please configure Firebase in settings.
```

**Solution:**
- Check `firebase_config.json` exists in project root
- Verify service account JSON is valid
- Check file permissions (should be readable)

#### **Issue 2: "Firebase API key not configured"**
```
❌ Firebase API key not configured
```

**Solution:**
- Add `FIREBASE_API_KEY` to `.env` file
- Or add `api_key` to `.streamlit/secrets.toml`
- Get API key from Firebase Console → Project Settings

#### **Issue 3: "Invalid email or password"**
```
❌ Invalid email or password
```

**Solution:**
- Verify email and password are correct
- Check if user exists in Firebase Console → Authentication
- Reset password using "Forgot Password" button

#### **Issue 4: "User account is disabled"**
```
❌ User account is disabled
```

**Solution:**
- Admin needs to enable the account
- Or run: `firebase_manager.enable_user(uid)`

#### **Issue 5: Session timeout after 24 hours**
```
Session expired. Please login again.
```

**Solution:**
- This is by design for security
- Login again
- To change timeout, edit `check_session_timeout()` in `firebase_auth_streamlit.py`:
```python
if datetime.now() - login_time > timedelta(hours=8):  # Change from 24 to 8
```

### **Debug Mode**

Add to your code for debugging:
```python
# Show session state (for debugging)
if st.sidebar.checkbox("Show Debug Info"):
    st.sidebar.json({
        'authenticated': st.session_state.get('authenticated'),
        'user_email': st.session_state.get('user_email'),
        'user_role': st.session_state.get('user_role'),
        'firebase_initialized': st.session_state.get('firebase_initialized')
    })
```

---

## 🧪 **Testing Your Setup**

### **Test 1: Firebase Initialization**
```python
python -c "from firebase_auth_streamlit import firebase_manager; print('✅ Import OK')"
```

### **Test 2: Create Test User**
```python
python create_first_admin.py
```

### **Test 3: Login Flow**
```bash
streamlit run streamlit_app.py
# Try logging in with created credentials
```

### **Test 4: Permissions**
```python
# In Streamlit app, add:
st.write("Your permissions:")
from firebase_auth_streamlit import UserRole
perms = UserRole.get_permissions(st.session_state.get('user_role'))
st.json(perms)
```

---

## 📖 **Additional Resources**

### **Firebase Documentation**
- [Firebase Authentication](https://firebase.google.com/docs/auth)
- [Firestore Database](https://firebase.google.com/docs/firestore)
- [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)

### **Security Best Practices**
1. ✅ Never commit `firebase_config.json` to Git
2. ✅ Use environment variables or secrets.toml in production
3. ✅ Enable HTTPS (Streamlit Cloud does this automatically)
4. ✅ Regularly review user list and disable inactive accounts
5. ✅ Use strong passwords (min 12 characters)
6. ✅ Enable email verification for production

### **Streamlit Cloud Deployment**
When deploying to Streamlit Cloud:
1. Go to App Settings → Secrets
2. Paste your `.streamlit/secrets.toml` content
3. Don't include `firebase_config.json` in your repo
4. All secrets will be encrypted and secure

---

## ✅ **Checklist**

Before going to production:

- [ ] Firebase project created
- [ ] Authentication enabled (Email/Password)
- [ ] Firestore database created
- [ ] Service account key downloaded
- [ ] API key obtained
- [ ] `firebase-admin` and `pyrebase4` installed
- [ ] First admin user created
- [ ] `.gitignore` updated
- [ ] Secrets configured (`.env` or `secrets.toml`)
- [ ] Login page tested
- [ ] User creation tested
- [ ] Role permissions tested
- [ ] Session timeout tested
- [ ] Password reset tested
- [ ] Deployed to production

---

**🎉 You're ready to go! Your AWS WAF Scanner now has enterprise-grade authentication with Firebase SSO!**
