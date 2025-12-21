"""
Scanner UI Components
=====================
Extracted UI components from streamlit_app.py for better maintainability.

This module contains reusable UI components for the WAF Scanner interface,
helping reduce the size of streamlit_app.py and avoid circular imports.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass


# ============================================================================
# UI CONFIGURATION
# ============================================================================

@dataclass
class UIConfig:
    """Configuration for UI components"""
    primary_color: str = "#007CC3"  # Infosys Blue
    success_color: str = "#28a745"
    warning_color: str = "#ffc107"
    danger_color: str = "#dc3545"
    info_color: str = "#17a2b8"


# ============================================================================
# PROGRESS COMPONENTS
# ============================================================================

class ScanProgressUI:
    """
    Manages scan progress display in Streamlit.
    
    Usage:
        progress = ScanProgressUI("Scanning AWS accounts...")
        progress.update(25, "Scanning account 1/4")
        progress.update(50, "Scanning account 2/4")
        progress.complete("Scan finished!")
    """
    
    def __init__(self, title: str = "Scanning..."):
        """Initialize progress UI"""
        self.container = st.container()
        with self.container:
            self.status_text = st.empty()
            self.progress_bar = st.progress(0)
            self.details = st.empty()
        
        self.status_text.text(title)
    
    def update(self, progress: float, status: str = None, details: str = None):
        """
        Update progress display.
        
        Args:
            progress: Progress percentage (0-100)
            status: Status text to display
            details: Additional details
        """
        self.progress_bar.progress(min(100, max(0, int(progress))))
        
        if status:
            self.status_text.text(status)
        
        if details:
            self.details.caption(details)
    
    def complete(self, message: str = "Complete!"):
        """Mark progress as complete"""
        self.progress_bar.progress(100)
        self.status_text.text(f"✅ {message}")
        self.details.empty()
    
    def error(self, message: str):
        """Display error state"""
        self.status_text.text(f"❌ {message}")
        self.progress_bar.empty()


# ============================================================================
# METRIC CARDS
# ============================================================================

def render_metric_card(
    title: str,
    value: Any,
    delta: Optional[Any] = None,
    delta_color: str = "normal"
):
    """
    Render a metric card with title, value, and optional delta.
    
    Args:
        title: Card title
        value: Main value to display
        delta: Change value (optional)
        delta_color: Color for delta ("normal", "inverse", "off")
    """
    st.metric(
        label=title,
        value=value,
        delta=delta,
        delta_color=delta_color
    )


def render_score_card(
    title: str,
    score: float,
    max_score: float = 100,
    thresholds: Dict[str, float] = None
):
    """
    Render a score card with color-coded progress.
    
    Args:
        title: Card title
        score: Current score
        max_score: Maximum possible score
        thresholds: Dict with 'good', 'warning' thresholds
    """
    thresholds = thresholds or {'good': 80, 'warning': 60}
    
    percentage = (score / max_score) * 100 if max_score > 0 else 0
    
    # Determine color
    if percentage >= thresholds['good']:
        color = "green"
        icon = "✅"
    elif percentage >= thresholds['warning']:
        color = "orange"
        icon = "⚠️"
    else:
        color = "red"
        icon = "❌"
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, {color} {percentage}%, #e0e0e0 {percentage}%);
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    ">
        <strong>{icon} {title}</strong>: {score:.1f}/{max_score} ({percentage:.1f}%)
    </div>
    """, unsafe_allow_html=True)


def render_pillar_scores(pillar_scores: Dict[str, float]):
    """
    Render WAF pillar scores in a grid layout.
    
    Args:
        pillar_scores: Dict mapping pillar name to score
    """
    pillar_icons = {
        'Operational Excellence': '⚙️',
        'Security': '🔒',
        'Reliability': '🛡️',
        'Performance Efficiency': '⚡',
        'Cost Optimization': '💰',
        'Sustainability': '🌱'
    }
    
    cols = st.columns(3)
    
    for idx, (pillar, score) in enumerate(pillar_scores.items()):
        with cols[idx % 3]:
            icon = pillar_icons.get(pillar, '📊')
            render_score_card(f"{icon} {pillar}", score)


# ============================================================================
# FINDINGS DISPLAY
# ============================================================================

def render_finding_card(
    finding: Dict[str, Any],
    show_details: bool = True
):
    """
    Render a single finding card.
    
    Args:
        finding: Finding dictionary
        show_details: Whether to show expandable details
    """
    severity = finding.get('severity', 'INFO')
    severity_colors = {
        'CRITICAL': '🔴',
        'HIGH': '🟠',
        'MEDIUM': '🟡',
        'LOW': '🟢',
        'INFO': '🔵'
    }
    
    icon = severity_colors.get(severity, '⚪')
    title = finding.get('title', 'Finding')
    resource = finding.get('resource', 'N/A')
    
    if show_details:
        with st.expander(f"{icon} [{severity}] {title}"):
            st.markdown(f"**Resource:** `{resource}`")
            
            if 'description' in finding:
                st.markdown(f"**Description:** {finding['description']}")
            
            if 'recommendation' in finding:
                st.info(f"💡 **Recommendation:** {finding['recommendation']}")
            
            if 'pillar' in finding:
                st.caption(f"WAF Pillar: {finding['pillar']}")
    else:
        st.markdown(f"{icon} [{severity}] {title} - `{resource}`")


def render_findings_summary(findings: List[Dict[str, Any]]):
    """
    Render a summary of findings by severity.
    
    Args:
        findings: List of finding dictionaries
    """
    # Count by severity
    severity_counts = {}
    for finding in findings:
        severity = finding.get('severity', 'INFO')
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    # Display counts
    cols = st.columns(5)
    severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
    colors = ['🔴', '🟠', '🟡', '🟢', '🔵']
    
    for col, severity, color in zip(cols, severities, colors):
        with col:
            count = severity_counts.get(severity, 0)
            st.metric(f"{color} {severity}", count)


def render_findings_table(
    findings: List[Dict[str, Any]],
    columns: List[str] = None
):
    """
    Render findings in a table format.
    
    Args:
        findings: List of finding dictionaries
        columns: Columns to display
    """
    import pandas as pd
    
    columns = columns or ['severity', 'title', 'resource', 'pillar']
    
    if not findings:
        st.info("No findings to display")
        return
    
    df = pd.DataFrame(findings)
    
    # Filter to available columns
    available_cols = [c for c in columns if c in df.columns]
    
    if available_cols:
        st.dataframe(
            df[available_cols],
            use_container_width=True,
            hide_index=True
        )


# ============================================================================
# ACCOUNT SELECTOR
# ============================================================================

def render_account_selector(
    accounts: List[Dict[str, Any]],
    multi_select: bool = True,
    key: str = "account_selector"
) -> List[Dict[str, Any]]:
    """
    Render an account selector component.
    
    Args:
        accounts: List of account dictionaries with 'id' and 'name'
        multi_select: Allow multiple selection
        key: Streamlit widget key
        
    Returns:
        List of selected accounts
    """
    if not accounts:
        st.warning("No accounts available")
        return []
    
    # Format options
    options = {f"{a['name']} ({a['id']})": a for a in accounts}
    
    if multi_select:
        selected = st.multiselect(
            "Select Accounts",
            options=list(options.keys()),
            key=key
        )
        return [options[s] for s in selected]
    else:
        selected = st.selectbox(
            "Select Account",
            options=list(options.keys()),
            key=key
        )
        return [options[selected]] if selected else []


def render_region_selector(
    regions: List[str] = None,
    multi_select: bool = True,
    key: str = "region_selector"
) -> List[str]:
    """
    Render a region selector component.
    
    Args:
        regions: List of region names (uses defaults if None)
        multi_select: Allow multiple selection
        key: Streamlit widget key
        
    Returns:
        List of selected regions
    """
    default_regions = [
        'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
        'eu-west-1', 'eu-west-2', 'eu-central-1',
        'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1'
    ]
    
    regions = regions or default_regions
    
    if multi_select:
        return st.multiselect(
            "Select Regions",
            options=regions,
            default=['us-east-1'],
            key=key
        )
    else:
        return [st.selectbox("Select Region", options=regions, key=key)]


def render_pillar_selector(
    key: str = "pillar_selector"
) -> List[str]:
    """
    Render a WAF pillar selector component.
    
    Args:
        key: Streamlit widget key
        
    Returns:
        List of selected pillars
    """
    pillars = [
        'Operational Excellence',
        'Security',
        'Reliability',
        'Performance Efficiency',
        'Cost Optimization',
        'Sustainability'
    ]
    
    return st.multiselect(
        "Select WAF Pillars",
        options=pillars,
        default=pillars,
        key=key
    )


# ============================================================================
# ACTION BUTTONS
# ============================================================================

def render_scan_button(
    label: str = "🔍 Start Scan",
    disabled: bool = False,
    key: str = "scan_button"
) -> bool:
    """
    Render a scan button.
    
    Args:
        label: Button label
        disabled: Whether button is disabled
        key: Streamlit widget key
        
    Returns:
        True if button was clicked
    """
    return st.button(
        label,
        type="primary",
        disabled=disabled,
        use_container_width=True,
        key=key
    )


def render_export_buttons(
    on_pdf: Callable = None,
    on_excel: Callable = None,
    on_json: Callable = None
):
    """
    Render export format buttons.
    
    Args:
        on_pdf: Callback for PDF export
        on_excel: Callback for Excel export
        on_json: Callback for JSON export
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export PDF", use_container_width=True):
            if on_pdf:
                on_pdf()
    
    with col2:
        if st.button("📊 Export Excel", use_container_width=True):
            if on_excel:
                on_excel()
    
    with col3:
        if st.button("📋 Export JSON", use_container_width=True):
            if on_json:
                on_json()


# ============================================================================
# STATUS MESSAGES
# ============================================================================

def show_connection_status(connected: bool, account_id: str = None):
    """
    Display AWS connection status.
    
    Args:
        connected: Whether connected to AWS
        account_id: Connected account ID (if connected)
    """
    if connected:
        st.success(f"✅ Connected to AWS Account: `{account_id}`")
    else:
        st.warning("⚠️ Not connected to AWS. Demo mode available.")


def show_scan_complete(
    total_findings: int,
    critical_count: int,
    scan_time: float
):
    """
    Display scan completion message.
    
    Args:
        total_findings: Total findings count
        critical_count: Critical findings count
        scan_time: Scan duration in seconds
    """
    if critical_count > 0:
        st.error(f"""
        🚨 **Scan Complete** - Found **{critical_count} critical** issues!
        
        Total findings: {total_findings} | Scan time: {scan_time:.1f}s
        """)
    else:
        st.success(f"""
        ✅ **Scan Complete**
        
        Total findings: {total_findings} | Scan time: {scan_time:.1f}s
        """)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'UIConfig',
    'ScanProgressUI',
    'render_metric_card',
    'render_score_card',
    'render_pillar_scores',
    'render_finding_card',
    'render_findings_summary',
    'render_findings_table',
    'render_account_selector',
    'render_region_selector',
    'render_pillar_selector',
    'render_scan_button',
    'render_export_buttons',
    'show_connection_status',
    'show_scan_complete',
]
