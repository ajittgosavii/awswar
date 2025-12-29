"""
Azure AD SSO Authentication - FIXED BUTTON VERSION
Works with personal Microsoft accounts
Session persistence via JWT tokens in browser local storage
"""

import streamlit as st
from typing import Optional, Dict, List, Callable
from functools import wraps
import jwt
import hashlib
from datetime import datetime, timedelta
import json

# ============================================================================
# SESSION PERSISTENCE CONFIGURATION
# ============================================================================

# Secret key for JWT signing (in production, use st.secrets)
def get_jwt_secret():
    """Get JWT secret from secrets or generate a stable one"""
    try:
        return st.secrets.get("jwt_secret", "waf-scanner-session-key-2024")
    except:
        return "waf-scanner-session-key-2024"

SESSION_EXPIRY_DAYS = 7  # Session valid for 7 days

# ============================================================================
# JWT SESSION HELPERS
# ============================================================================

def create_session_token(user_info: Dict) -> str:
    """Create a JWT session token for the user"""
    payload = {
        'user_id': user_info.get('id', ''),
        'email': user_info.get('email', ''),
        'name': user_info.get('name', ''),
        'role': user_info.get('role', 'viewer'),
        'exp': datetime.utcnow() + timedelta(days=SESSION_EXPIRY_DAYS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm='HS256')


def verify_session_token(token: str) -> Optional[Dict]:
    """Verify and decode a JWT session token"""
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def inject_session_storage_script():
    """Inject JavaScript to handle session storage"""
    st.markdown("""
    <script>
    // Session storage helper functions
    window.saveSessionToken = function(token) {
        try {
            localStorage.setItem('waf_session_token', token);
            return true;
        } catch(e) {
            console.error('Failed to save session:', e);
            return false;
        }
    };
    
    window.getSessionToken = function() {
        try {
            return localStorage.getItem('waf_session_token');
        } catch(e) {
            return null;
        }
    };
    
    window.clearSessionToken = function() {
        try {
            localStorage.removeItem('waf_session_token');
            return true;
        } catch(e) {
            return false;
        }
    };
    </script>
    """, unsafe_allow_html=True)


def save_session_to_browser(token: str):
    """Save session token to browser local storage"""
    st.markdown(f"""
    <script>
    (function() {{
        try {{
            localStorage.setItem('waf_session_token', '{token}');
            console.log('Session saved successfully');
        }} catch(e) {{
            console.error('Failed to save session:', e);
        }}
    }})();
    </script>
    """, unsafe_allow_html=True)


def clear_session_from_browser():
    """Clear session token from browser local storage"""
    st.markdown("""
    <script>
    (function() {
        try {
            localStorage.removeItem('waf_session_token');
            console.log('Session cleared');
        } catch(e) {
            console.error('Failed to clear session:', e);
        }
    })();
    </script>
    """, unsafe_allow_html=True)


def check_and_restore_session():
    """
    Check for existing session token in query params and restore session.
    Returns True if session was restored, False otherwise.
    """
    # Check if already authenticated
    if st.session_state.get('authenticated', False):
        return True
    
    # Check for session token in query params (passed from JavaScript)
    query_params = st.query_params
    
    if 'session_token' in query_params:
        token = query_params.get('session_token')
        
        # Verify the token
        payload = verify_session_token(token)
        
        if payload:
            # Token is valid - restore session
            user_info = {
                'id': payload.get('user_id', ''),
                'email': payload.get('email', ''),
                'name': payload.get('name', ''),
                'role': payload.get('role', 'viewer'),
                'given_name': payload.get('name', '').split()[0] if payload.get('name') else '',
            }
            
            # Set session state
            st.session_state.authenticated = True
            st.session_state.user_id = user_info['id']
            st.session_state.user_info = user_info
            st.session_state.user_manager = SimpleUserManager()
            
            # Clear the token from URL (for cleaner URLs)
            st.query_params.clear()
            
            return True
        else:
            # Token expired or invalid - clear it
            st.query_params.clear()
    
    return False


def render_session_restore_script():
    """Render JavaScript that checks for stored session and restores it"""
    st.markdown("""
    <script>
    (function() {
        // Only run if not already authenticated (check URL for auth indicators)
        const urlParams = new URLSearchParams(window.location.search);
        
        // Skip if already processing OAuth callback
        if (urlParams.has('code') || urlParams.has('session_token')) {
            return;
        }
        
        // Check for stored session token
        const token = localStorage.getItem('waf_session_token');
        
        if (token) {
            // Redirect with session token to restore session
            const currentUrl = new URL(window.location.href);
            currentUrl.searchParams.set('session_token', token);
            window.location.href = currentUrl.toString();
        }
    })();
    </script>
    """, unsafe_allow_html=True)


# ============================================================================
# ROLE-BASED ACCESS CONTROL
# ============================================================================

class RoleManager:
    """Manages role-based permissions"""
    
    ROLES = {
        'admin': {
            'description': 'Full system access',
            'permissions': ['*']
        },
        'architect': {
            'description': 'Design and provision infrastructure',
            'permissions': [
                'view_dashboard', 'view_resources', 'provision_resources',
                'design_architecture', 'use_devex', 'view_costs', 'manage_policies'
            ]
        },
        'developer': {
            'description': 'Deploy and manage applications',
            'permissions': ['view_dashboard', 'view_resources', 'deploy_applications', 'use_devex']
        },
        'finops': {
            'description': 'Financial operations and cost management',
            'permissions': ['view_dashboard', 'view_costs']
        },
        'security': {
            'description': 'Security and compliance management',
            'permissions': ['view_dashboard', 'view_security']
        },
        'viewer': {
            'description': 'Read-only access',
            'permissions': ['view_dashboard', 'view_resources', 'view_costs']
        }
    }
    
    @staticmethod
    def has_permission(user_role: str, required_permission: str) -> bool:
        if not user_role or user_role not in RoleManager.ROLES:
            return False
        role_permissions = RoleManager.ROLES[user_role]['permissions']
        if '*' in role_permissions:
            return True
        return required_permission in role_permissions
    
    @staticmethod
    def get_user_permissions(user_role: str) -> List[str]:
        if not user_role or user_role not in RoleManager.ROLES:
            return []
        permissions = RoleManager.ROLES[user_role]['permissions']
        if '*' in permissions:
            all_permissions = set()
            for role_data in RoleManager.ROLES.values():
                all_permissions.update(role_data['permissions'])
            all_permissions.discard('*')
            return list(all_permissions)
        return permissions


def require_permission(permission: str) -> Callable:
    """Decorator to require specific permission for a function"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_manager = st.session_state.get('user_manager')
            if not user_manager:
                st.error("❌ Authentication required")
                return
            
            current_user = user_manager.get_current_user()
            if not current_user or not isinstance(current_user, dict):
                st.error("❌ User session not found")
                st.info("Please logout and login again")
                return
            
            user_role = current_user.get('role', 'viewer')
            
            if not RoleManager.has_permission(user_role, permission):
                st.error("❌ You don't have permission to access this feature")
                st.info(f"**Required:** `{permission}` | **Your role:** `{user_role}`")
                return
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


class SimpleUserManager:
    """Simple user manager for session"""
    
    def get_current_user(self):
        return st.session_state.get('user_info')
    
    def is_authenticated(self):
        return st.session_state.get('authenticated', False)


# ============================================================================
# AZURE AD AUTHENTICATION - FIXED BUTTON VERSION
# ============================================================================

def exchange_code_for_token(code: str, client_id: str, client_secret: str, 
                           redirect_uri: str, tenant_id: str = "common") -> Optional[Dict]:
    """Exchange authorization code for access token"""
    import requests
    
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    token_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
        'scope': 'openid profile email https://graph.microsoft.com/User.Read'
    }
    
    try:
        response = requests.post(token_url, data=token_data, timeout=10)
        
        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            error_desc = error_data.get('error_description', f'HTTP {response.status_code}')
            
            st.error(f"❌ Authentication Failed")
            
            with st.expander("🔍 View Error Details", expanded=True):
                st.code(error_desc)
                
                # Provide specific fixes based on error type
                if 'redirect_uri' in error_desc.lower():
                    st.warning(f"""
                    **Redirect URI Mismatch**
                    
                    The redirect_uri must match EXACTLY in Azure AD.
                    
                    Current redirect_uri: `{redirect_uri}`
                    """)
                
                elif 'unauthorized_client' in error_desc.lower():
                    st.warning("""
                    **Unauthorized Client**
                    
                    This usually means:
                    1. Personal Microsoft accounts not enabled in Azure AD
                    2. Or the app is not configured for the account type being used
                    
                    **Fix:**
                    - Go to Azure Portal → App registrations → Your App
                    - Change "Supported account types" to include personal Microsoft accounts
                    """)
                
                elif 'client_secret' in error_desc.lower() or 'invalid_client' in error_desc.lower():
                    st.warning("""
                    **Invalid Client Secret**
                    
                    **Steps to fix:**
                    1. Go to Azure Portal → App Registrations → Your App
                    2. Go to Certificates & secrets
                    3. Create a new client secret
                    4. Update the secret in Streamlit secrets
                    """)
            
            return None
        
        return response.json()
        
    except requests.exceptions.Timeout:
        st.error("❌ Connection timeout - please try again")
        return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Network connection error - please check your internet connection")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return None


def get_user_info(access_token: str) -> Optional[Dict]:
    """Get user information from Microsoft Graph"""
    import requests
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get('https://graph.microsoft.com/v1.0/me', 
                              headers=headers, 
                              timeout=10)
        response.raise_for_status()
        
        user_data = response.json()
        
        return {
            'id': user_data.get('id'),
            'email': user_data.get('mail') or user_data.get('userPrincipalName'),
            'name': user_data.get('displayName'),
            'given_name': user_data.get('givenName'),
            'family_name': user_data.get('surname')
        }
    except Exception as e:
        st.error(f"❌ Failed to get user info: {str(e)}")
        return None


def render_login():
    """Render login UI with WORKING button and session persistence"""
    
    # STEP 1: Try to restore session from browser storage
    if check_and_restore_session():
        # Session restored successfully - no need to show login
        return
    
    # STEP 2: Inject session restore script for browser refresh handling
    render_session_restore_script()
    
    # Get Azure AD config
    try:
        client_id = st.secrets.azure_ad.client_id
        client_secret = st.secrets.azure_ad.client_secret
        tenant_id = st.secrets.azure_ad.get('tenant_id', 'common')
        
        # Get redirect URI and clean it
        redirect_uri_config = st.secrets.azure_ad.get('redirect_uri', '')
        
        # Clean the redirect_uri
        redirect_uri = redirect_uri_config.rstrip('/')
        
        # Validate configuration
        if not all([client_id, client_secret, redirect_uri]):
            raise ValueError("Missing required configuration")
            
    except Exception as e:
        st.error("❌ Azure AD Configuration Error")
        st.info("""
        **Required Streamlit Secrets:**
        
        ```toml
        [azure_ad]
        client_id = "your-client-id-from-azure"
        client_secret = "your-client-secret-from-azure"
        tenant_id = "common"  # For both work and personal accounts
        redirect_uri = "https://hyperscaler.streamlit.app"
        ```
        """)
        st.stop()
    
    # Check for OAuth callback
    query_params = st.query_params
    
    if 'code' in query_params:
        # User returned from Microsoft with authorization code
        with st.spinner("🔐 Completing sign-in..."):
            code = query_params['code']
            
            # Exchange code for token
            token_response = exchange_code_for_token(
                code=code,
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                tenant_id=tenant_id
            )
            
            if token_response and 'access_token' in token_response:
                # Get user info from Microsoft Graph
                user_info = get_user_info(token_response['access_token'])
                
                if user_info:
                    # Register/update user in Firebase
                    try:
                        from auth_database_firebase import get_database_manager
                        db_manager = get_database_manager()
                        
                        if db_manager:
                            user_id = user_info['id']
                            
                            # Check if user exists
                            try:
                                existing_user = db_manager.get_user(user_id)
                                is_new_user = not (existing_user and isinstance(existing_user, dict))
                            except:
                                is_new_user = True
                            
                            if is_new_user:
                                # New user - set defaults
                                user_info['role'] = 'viewer'
                                user_info['is_active'] = True
                                db_manager.create_or_update_user(user_info)
                                final_user_info = user_info
                            else:
                                # Existing user - update info but preserve role
                                update_data = {
                                    'id': user_info['id'],
                                    'email': user_info['email'],
                                    'name': user_info.get('name', ''),
                                    'given_name': user_info.get('given_name', ''),
                                    'family_name': user_info.get('family_name', '')
                                }
                                db_manager.create_or_update_user(update_data)
                                
                                # Load from Firebase to get actual role
                                try:
                                    final_user_info = db_manager.get_user(user_id)
                                    if not final_user_info:
                                        final_user_info = user_info
                                except:
                                    final_user_info = user_info
                            
                            # Set session state
                            st.session_state.authenticated = True
                            st.session_state.user_id = final_user_info['id']
                            st.session_state.user_info = final_user_info
                            st.session_state.user_manager = SimpleUserManager()
                            
                            # Create and save session token for persistence
                            session_token = create_session_token(final_user_info)
                            save_session_to_browser(session_token)
                            
                            # Clear query params and redirect to app
                            st.query_params.clear()
                            st.success("✅ Login successful!")
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"❌ Database error: {str(e)}")
                        st.info("Please try logging in again")
                        if st.button("🔄 Try Again"):
                            st.query_params.clear()
                            st.rerun()
                else:
                    st.error("❌ Could not retrieve user information")
                    if st.button("🔄 Try Again"):
                        st.query_params.clear()
                        st.rerun()
            else:
                # Token exchange failed - error already displayed
                if st.button("🔄 Try Again"):
                    st.query_params.clear()
                    st.rerun()
    
    elif 'error' in query_params:
        # User cancelled or error occurred at Microsoft
        error = query_params.get('error', ['unknown'])[0]
        error_desc = query_params.get('error_description', ['No description'])[0]
        
        st.error("❌ Authentication Error")
        st.warning(f"**Error:** {error}")
        st.info(error_desc)
        
        if st.button("🔄 Try Again"):
            st.query_params.clear()
            st.rerun()
    
    else:
        # Professional login page with centered link
        from urllib.parse import quote
        
        # Build OAuth authorization URL
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        scopes = "openid profile email https://graph.microsoft.com/User.Read"
        
        auth_url = (
            f"{authority}/oauth2/v2.0/authorize?"
            f"client_id={client_id}&"
            f"response_type=code&"
            f"redirect_uri={quote(redirect_uri, safe='')}&"
            f"response_mode=query&"
            f"scope={quote(scopes)}&"
            f"prompt=select_account"
        )
        
        # Professional login page with Infosys branding
        st.markdown(f"""
        <style>
        .login-container {{
            max-width: 460px;
            margin: 60px auto;
            padding: 50px 45px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.06);
            text-align: center;
            border: 1px solid #E5E9EC;
        }}
        .infosys-logo {{
            font-size: 38px;
            font-weight: 700;
            color: #007CC3;
            margin-bottom: 35px;
            letter-spacing: -0.5px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }}
        .logo-bar {{
            width: 4px;
            height: 32px;
            background: #007CC3;
            border-radius: 2px;
        }}
        .divider {{
            width: 50px;
            height: 2px;
            background: #007CC3;
            margin: 0 auto 25px auto;
            border-radius: 1px;
        }}
        .app-title {{
            font-size: 22px;
            font-weight: 600;
            color: #1A1A1A;
            margin-bottom: 6px;
            line-height: 1.3;
        }}
        .app-subtitle {{
            font-size: 14px;
            color: #666;
            margin-bottom: 40px;
            font-weight: 400;
        }}
        .signin-link {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 12px 32px;
            color: white;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            border: none;
            border-radius: 6px;
            transition: all 0.2s ease;
            background: #0078D4;
            min-width: 240px;
        }}
        .signin-link:hover {{
            background: #106EBE;
            color: white;
            text-decoration: none;
            box-shadow: 0 2px 8px rgba(0,120,212,0.25);
        }}
        .ms-icon {{
            width: 18px;
            height: 18px;
        }}
        .footer-text {{
            margin-top: 40px;
            font-size: 11px;
            color: #999;
            letter-spacing: 0.5px;
        }}
        </style>
        
        <div class="login-container">
            <div class="infosys-logo">
                <div class="logo-bar"></div>
                Infosys
            </div>
            <div class="divider"></div>
            <div class="app-title">AWS Well-Architected Framework Advisor</div>
            <div class="app-subtitle">AI-Powered Architecture Assessment & Scanning</div>
            <a href="{auth_url}" class="signin-link">
                <svg class="ms-icon" viewBox="0 0 21 21" fill="none">
                    <rect width="10" height="10" fill="#F25022"/>
                    <rect x="11" width="10" height="10" fill="#7FBA00"/>
                    <rect y="11" width="10" height="10" fill="#00A4EF"/>
                    <rect x="11" y="11" width="10" height="10" fill="#FFB900"/>
                </svg>
                Sign in with Microsoft
            </a>
            <div class="footer-text">ENTERPRISE CLOUD SOLUTIONS</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.stop()


def perform_logout():
    """Perform complete logout - clear session state and browser token"""
    # Clear session state
    st.session_state.authenticated = False
    st.session_state.user_info = None
    st.session_state.user_id = None
    st.session_state.user_manager = None
    
    # Clear browser session token
    clear_session_from_browser()


__all__ = [
    'RoleManager', 
    'require_permission', 
    'SimpleUserManager', 
    'render_login',
    'perform_logout',
    'clear_session_from_browser',
    'check_and_restore_session',
    'create_session_token',
    'verify_session_token'
]
