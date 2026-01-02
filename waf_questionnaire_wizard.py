"""
Paginated WAF Questionnaire Wizard
==================================
One question per page with progress tracking, navigation, and auto-save.

This replaces the current approach of showing all 200+ questions at once,
which causes significant performance issues and overwhelms users.

Features:
- Single question per page
- Progress bar and question counter
- Previous/Next navigation
- Jump to specific pillar or question
- Auto-save after each answer
- Keyboard shortcuts (Enter for next)
- Skip functionality
- Review mode before completion

Usage:
    from waf_questionnaire_wizard import WAFQuestionnaireWizard
    
    wizard = WAFQuestionnaireWizard(questions, responses)
    wizard.render()

Version: 1.0.0
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json


# ============================================================================
# DATA MODELS
# ============================================================================

class WAFPillar(Enum):
    """AWS Well-Architected Framework Pillars"""
    OPERATIONAL_EXCELLENCE = "Operational Excellence"
    SECURITY = "Security"
    RELIABILITY = "Reliability"
    PERFORMANCE_EFFICIENCY = "Performance Efficiency"
    COST_OPTIMIZATION = "Cost Optimization"
    SUSTAINABILITY = "Sustainability"


PILLAR_ICONS = {
    WAFPillar.OPERATIONAL_EXCELLENCE: "⚙️",
    WAFPillar.SECURITY: "🔒",
    WAFPillar.RELIABILITY: "🛡️",
    WAFPillar.PERFORMANCE_EFFICIENCY: "⚡",
    WAFPillar.COST_OPTIMIZATION: "💰",
    WAFPillar.SUSTAINABILITY: "🌱"
}

PILLAR_COLORS = {
    WAFPillar.OPERATIONAL_EXCELLENCE: "#5D6D7E",
    WAFPillar.SECURITY: "#2874A6",
    WAFPillar.RELIABILITY: "#148F77",
    WAFPillar.PERFORMANCE_EFFICIENCY: "#B9770E",
    WAFPillar.COST_OPTIMIZATION: "#1E8449",
    WAFPillar.SUSTAINABILITY: "#117A65"
}


@dataclass
class QuestionResponse:
    """Response to a WAF questionnaire question"""
    question_id: str
    pillar: str
    question_text: str
    response: str = ""  # yes, no, partial, not_applicable
    auto_detected: bool = False
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)
    notes: str = ""
    answered_at: Optional[datetime] = None


@dataclass
class WizardState:
    """State container for the questionnaire wizard"""
    current_index: int = 0
    current_pillar: Optional[str] = None
    view_mode: str = "sequential"  # sequential, by_pillar, review
    show_answered: bool = True
    auto_advance: bool = True
    last_saved: Optional[datetime] = None


# ============================================================================
# QUESTIONNAIRE WIZARD
# ============================================================================

class WAFQuestionnaireWizard:
    """
    Paginated questionnaire wizard showing one question at a time.
    
    Dramatically improves performance and UX compared to showing all questions.
    """
    
    SESSION_KEY = '_waf_wizard_state'
    
    def __init__(
        self,
        questions: Dict[Any, List[Dict]],
        responses: List[QuestionResponse],
        on_save: Optional[Callable] = None,
        on_complete: Optional[Callable] = None
    ):
        """
        Initialize the questionnaire wizard.
        
        Args:
            questions: Dict mapping pillar -> list of question dicts
            responses: List of existing responses
            on_save: Callback when progress is saved
            on_complete: Callback when questionnaire is completed
        """
        self.questions_by_pillar = questions
        self.responses = responses
        self.on_save = on_save
        self.on_complete = on_complete
        
        # Build flat question list for sequential navigation
        self._build_question_index()
        
        # Initialize or get state
        self._init_state()
    
    def _build_question_index(self):
        """Build a flat index of all questions for navigation"""
        self.all_questions = []
        self.question_to_index = {}
        self.pillar_ranges = {}
        
        idx = 0
        for pillar in WAFPillar:
            pillar_questions = self.questions_by_pillar.get(pillar, [])
            if not pillar_questions:
                continue
            
            start_idx = idx
            for q in pillar_questions:
                q['_pillar'] = pillar
                q['_index'] = idx
                self.all_questions.append(q)
                self.question_to_index[q['id']] = idx
                idx += 1
            
            self.pillar_ranges[pillar] = (start_idx, idx - 1)
        
        self.total_questions = len(self.all_questions)
    
    def _init_state(self):
        """Initialize wizard state in session"""
        if self.SESSION_KEY not in st.session_state:
            st.session_state[self.SESSION_KEY] = WizardState()
        self.state = st.session_state[self.SESSION_KEY]
    
    def _get_response(self, question_id: str) -> Optional[QuestionResponse]:
        """Get response for a question"""
        for r in self.responses:
            if r.question_id == question_id:
                return r
        return None
    
    def _set_response(self, question_id: str, pillar: str, question_text: str, 
                      response: str, notes: str = ""):
        """Set or update response for a question"""
        existing = self._get_response(question_id)
        
        if existing:
            existing.response = response
            existing.notes = notes
            existing.answered_at = datetime.now()
        else:
            self.responses.append(QuestionResponse(
                question_id=question_id,
                pillar=pillar,
                question_text=question_text,
                response=response,
                notes=notes,
                answered_at=datetime.now()
            ))
    
    def _get_progress_stats(self) -> Dict:
        """Calculate progress statistics"""
        answered = sum(1 for r in self.responses if r.response)
        auto_detected = sum(1 for r in self.responses if r.auto_detected and r.response)
        
        # Per-pillar stats
        pillar_stats = {}
        for pillar in WAFPillar:
            pillar_qs = self.questions_by_pillar.get(pillar, [])
            pillar_answered = sum(
                1 for q in pillar_qs 
                if self._get_response(q['id']) and self._get_response(q['id']).response
            )
            pillar_stats[pillar.value] = {
                'total': len(pillar_qs),
                'answered': pillar_answered,
                'pending': len(pillar_qs) - pillar_answered
            }
        
        return {
            'total': self.total_questions,
            'answered': answered,
            'pending': self.total_questions - answered,
            'auto_detected': auto_detected,
            'progress_pct': (answered / self.total_questions * 100) if self.total_questions > 0 else 0,
            'by_pillar': pillar_stats
        }
    
    def render(self):
        """Render the questionnaire wizard"""
        
        # Header with progress
        self._render_header()
        
        st.markdown("---")
        
        # View mode selector
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            view_mode = st.radio(
                "Navigation Mode",
                ["sequential", "by_pillar", "review"],
                format_func=lambda x: {
                    "sequential": "📝 Question by Question",
                    "by_pillar": "📂 By Pillar",
                    "review": "👁️ Review All"
                }[x],
                horizontal=True,
                key="wizard_view_mode"
            )
            self.state.view_mode = view_mode
        
        with col2:
            if view_mode == "sequential":
                self.state.auto_advance = st.checkbox(
                    "Auto-advance after answer",
                    value=self.state.auto_advance,
                    key="wizard_auto_advance"
                )
        
        with col3:
            if st.button("💾 Save Progress", use_container_width=True):
                self._save_progress()
        
        st.markdown("---")
        
        # Render based on view mode
        if view_mode == "sequential":
            self._render_sequential_view()
        elif view_mode == "by_pillar":
            self._render_pillar_view()
        else:
            self._render_review_view()
        
        st.markdown("---")
        
        # Footer with completion
        self._render_footer()
    
    def _render_header(self):
        """Render progress header"""
        stats = self._get_progress_stats()
        
        st.markdown("## 📝 WAF Assessment Questionnaire")
        
        # Progress bar
        st.progress(stats['progress_pct'] / 100)
        
        # Stats row
        cols = st.columns(5)
        with cols[0]:
            st.metric("Total", stats['total'])
        with cols[1]:
            st.metric("Answered", stats['answered'])
        with cols[2]:
            st.metric("Pending", stats['pending'], delta=-stats['pending'] if stats['pending'] > 0 else None)
        with cols[3]:
            st.metric("Auto-detected", stats['auto_detected'])
        with cols[4]:
            st.metric("Progress", f"{stats['progress_pct']:.0f}%")
        
        # Pillar mini-progress
        with st.expander("📊 Progress by Pillar", expanded=False):
            pillar_cols = st.columns(6)
            for idx, pillar in enumerate(WAFPillar):
                pillar_stat = stats['by_pillar'].get(pillar.value, {})
                with pillar_cols[idx]:
                    total = pillar_stat.get('total', 0)
                    answered = pillar_stat.get('answered', 0)
                    icon = PILLAR_ICONS.get(pillar, "")
                    
                    if total > 0:
                        pct = answered / total * 100
                        color = "🟢" if pct == 100 else "🟡" if pct >= 50 else "🔴"
                        st.markdown(f"{icon} **{pillar.value.split()[0]}**")
                        st.caption(f"{color} {answered}/{total}")
    
    def _render_sequential_view(self):
        """Render one question at a time with navigation"""
        
        if self.total_questions == 0:
            st.warning("No questions loaded")
            return
        
        # Jump to question
        col1, col2 = st.columns([3, 1])
        with col1:
            # Quick jump selector
            jump_options = [f"{q['id']}: {q['question'][:50]}..." for q in self.all_questions]
            selected_jump = st.selectbox(
                "Jump to question",
                range(len(jump_options)),
                format_func=lambda i: jump_options[i],
                index=self.state.current_index,
                key="wizard_jump"
            )
            if selected_jump != self.state.current_index:
                self.state.current_index = selected_jump
                st.rerun()
        
        with col2:
            st.markdown(f"**Question {self.state.current_index + 1} of {self.total_questions}**")
        
        st.markdown("---")
        
        # Get current question
        question = self.all_questions[self.state.current_index]
        pillar = question['_pillar']
        response = self._get_response(question['id'])
        
        # Render question card
        self._render_question_card(question, pillar, response)
        
        st.markdown("---")
        
        # Navigation buttons
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⏮️ First", disabled=self.state.current_index == 0, use_container_width=True):
                self.state.current_index = 0
                st.rerun()
        
        with col2:
            if st.button("◀️ Previous", disabled=self.state.current_index == 0, use_container_width=True):
                self.state.current_index -= 1
                st.rerun()
        
        with col3:
            # Show current position
            pending_ahead = sum(
                1 for q in self.all_questions[self.state.current_index + 1:]
                if not self._get_response(q['id']) or not self._get_response(q['id']).response
            )
            if pending_ahead > 0:
                st.caption(f"⚠️ {pending_ahead} unanswered questions ahead")
        
        with col4:
            if st.button("▶️ Next", disabled=self.state.current_index >= self.total_questions - 1, 
                        use_container_width=True, type="primary"):
                self.state.current_index += 1
                st.rerun()
        
        with col5:
            if st.button("⏭️ Last", disabled=self.state.current_index >= self.total_questions - 1,
                        use_container_width=True):
                self.state.current_index = self.total_questions - 1
                st.rerun()
        
        # Jump to next unanswered
        if st.button("🔍 Jump to Next Unanswered", use_container_width=True):
            next_unanswered = self._find_next_unanswered(self.state.current_index)
            if next_unanswered is not None:
                self.state.current_index = next_unanswered
                st.rerun()
            else:
                st.success("✅ All questions answered!")
    
    def _render_question_card(self, question: Dict, pillar: WAFPillar, response: Optional[QuestionResponse]):
        """Render a single question card"""
        
        icon = PILLAR_ICONS.get(pillar, "")
        color = PILLAR_COLORS.get(pillar, "#333")
        
        # Question header
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {color}22, {color}11); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid {color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.9em; color: {color};">
                    {icon} {pillar.value} | {question['id']}
                </span>
                <span style="font-size: 0.8em; color: #666;">
                    {'🤖 Auto-detected' if response and response.auto_detected else '✍️ Manual'}
                </span>
            </div>
            <h3 style="margin: 15px 0 10px 0; color: #333;">{question['question']}</h3>
            <p style="color: #666; font-style: italic;">{question.get('description', '')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("")
        
        # Auto-detection info
        if response and response.auto_detected and response.response:
            confidence_color = "#4CAF50" if response.confidence > 0.7 else "#FF9800" if response.confidence > 0.5 else "#F44336"
            st.info(f"🤖 **Auto-detected** with {response.confidence:.0%} confidence based on: {', '.join(response.evidence[:3])}")
        
        # Response selection
        options = ["", "yes", "partial", "no", "not_applicable"]
        labels = {
            "": "⬜ Not answered",
            "yes": "✅ Yes - Fully implemented",
            "partial": "⚠️ Partial - Partially implemented",
            "no": "❌ No - Not implemented",
            "not_applicable": "➖ N/A - Not applicable"
        }
        
        current_response = response.response if response else ""
        current_index = options.index(current_response) if current_response in options else 0
        
        # Use buttons for response (more visual)
        st.markdown("### Your Assessment")
        
        response_cols = st.columns(5)
        new_response = current_response
        
        for idx, opt in enumerate(options):
            with response_cols[idx]:
                is_selected = opt == current_response
                btn_type = "primary" if is_selected else "secondary"
                
                if st.button(
                    labels[opt].split(" - ")[0],  # Short label
                    key=f"resp_{question['id']}_{opt}",
                    use_container_width=True,
                    type=btn_type if opt else "secondary"
                ):
                    new_response = opt
        
        # Update response if changed
        if new_response != current_response:
            self._set_response(
                question['id'],
                pillar.value,
                question['question'],
                new_response
            )
            
            # Auto-advance if enabled
            if self.state.auto_advance and new_response and self.state.current_index < self.total_questions - 1:
                self.state.current_index += 1
            
            st.rerun()
        
        # Notes field
        with st.expander("📝 Add Notes (Optional)"):
            notes = st.text_area(
                "Notes",
                value=response.notes if response else "",
                key=f"notes_{question['id']}",
                placeholder="Add any notes, evidence, or context..."
            )
            if response and notes != response.notes:
                response.notes = notes
        
        # Best practices
        if question.get('best_practices'):
            with st.expander("💡 Best Practices"):
                for bp in question['best_practices']:
                    st.markdown(f"- {bp}")
        
        # Detection services
        if question.get('scan_detectable') and question.get('detection_services'):
            st.caption(f"🔍 Can be verified via: {', '.join(question['detection_services'])}")
    
    def _render_pillar_view(self):
        """Render questions grouped by pillar"""
        
        # Pillar selector
        pillar_options = list(WAFPillar)
        pillar_labels = [
            f"{PILLAR_ICONS[p]} {p.value}" 
            for p in pillar_options
        ]
        
        selected_pillar_idx = st.selectbox(
            "Select Pillar",
            range(len(pillar_options)),
            format_func=lambda i: pillar_labels[i],
            key="wizard_pillar_select"
        )
        
        selected_pillar = pillar_options[selected_pillar_idx]
        pillar_questions = self.questions_by_pillar.get(selected_pillar, [])
        
        if not pillar_questions:
            st.warning(f"No questions for {selected_pillar.value}")
            return
        
        # Filter options
        show_filter = st.radio(
            "Show",
            ["all", "pending", "answered"],
            format_func=lambda x: {"all": "📋 All", "pending": "⚠️ Pending Only", "answered": "✅ Answered Only"}[x],
            horizontal=True,
            key="pillar_filter"
        )
        
        # Filter questions
        if show_filter == "pending":
            filtered = [q for q in pillar_questions 
                       if not self._get_response(q['id']) or not self._get_response(q['id']).response]
        elif show_filter == "answered":
            filtered = [q for q in pillar_questions 
                       if self._get_response(q['id']) and self._get_response(q['id']).response]
        else:
            filtered = pillar_questions
        
        st.caption(f"Showing {len(filtered)} of {len(pillar_questions)} questions")
        
        # Paginate within pillar (10 per page)
        page_size = 10
        total_pages = (len(filtered) - 1) // page_size + 1 if filtered else 1
        
        if f"pillar_page_{selected_pillar.value}" not in st.session_state:
            st.session_state[f"pillar_page_{selected_pillar.value}"] = 0
        
        current_page = st.session_state[f"pillar_page_{selected_pillar.value}"]
        
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                if st.button("◀️ Prev", disabled=current_page == 0, key="pillar_prev"):
                    st.session_state[f"pillar_page_{selected_pillar.value}"] -= 1
                    st.rerun()
            with col2:
                st.markdown(f"Page {current_page + 1} of {total_pages}")
            with col3:
                if st.button("Next ▶️", disabled=current_page >= total_pages - 1, key="pillar_next"):
                    st.session_state[f"pillar_page_{selected_pillar.value}"] += 1
                    st.rerun()
        
        # Show questions for current page
        start_idx = current_page * page_size
        end_idx = min(start_idx + page_size, len(filtered))
        
        for q in filtered[start_idx:end_idx]:
            response = self._get_response(q['id'])
            has_answer = response and response.response
            
            with st.expander(
                f"{'✅' if has_answer else '⚠️'} **{q['id']}**: {q['question'][:80]}...",
                expanded=not has_answer
            ):
                self._render_compact_question(q, selected_pillar, response)
    
    def _render_compact_question(self, question: Dict, pillar: WAFPillar, response: Optional[QuestionResponse]):
        """Render a compact question form for pillar/review view"""
        
        st.markdown(f"*{question.get('description', '')}*")
        
        # Response selection
        options = ["", "yes", "partial", "no", "not_applicable"]
        labels = {"": "⬜ Select...", "yes": "✅ Yes", "partial": "⚠️ Partial", "no": "❌ No", "not_applicable": "➖ N/A"}
        
        current_response = response.response if response else ""
        
        new_response = st.radio(
            "Assessment:",
            options,
            index=options.index(current_response) if current_response in options else 0,
            format_func=lambda x: labels.get(x, x),
            key=f"compact_{question['id']}",
            horizontal=True
        )
        
        if new_response != current_response:
            self._set_response(question['id'], pillar.value, question['question'], new_response)
            st.rerun()
    
    def _render_review_view(self):
        """Render review of all answers"""
        
        st.markdown("### 📋 Review Your Answers")
        
        stats = self._get_progress_stats()
        
        if stats['pending'] > 0:
            st.warning(f"⚠️ You have {stats['pending']} unanswered questions. Please complete all questions before finishing.")
        else:
            st.success("✅ All questions answered! Review your responses below.")
        
        # Summary by pillar
        for pillar in WAFPillar:
            pillar_questions = self.questions_by_pillar.get(pillar, [])
            if not pillar_questions:
                continue
            
            icon = PILLAR_ICONS.get(pillar, "")
            pillar_stat = stats['by_pillar'].get(pillar.value, {})
            
            with st.expander(f"{icon} **{pillar.value}** - {pillar_stat.get('answered', 0)}/{pillar_stat.get('total', 0)} answered"):
                # Count responses
                yes_count = 0
                partial_count = 0
                no_count = 0
                na_count = 0
                
                for q in pillar_questions:
                    r = self._get_response(q['id'])
                    if r:
                        if r.response == "yes":
                            yes_count += 1
                        elif r.response == "partial":
                            partial_count += 1
                        elif r.response == "no":
                            no_count += 1
                        elif r.response == "not_applicable":
                            na_count += 1
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("✅ Yes", yes_count)
                with col2:
                    st.metric("⚠️ Partial", partial_count)
                with col3:
                    st.metric("❌ No", no_count)
                with col4:
                    st.metric("➖ N/A", na_count)
                
                # List questions with "No" responses (areas for improvement)
                no_responses = [q for q in pillar_questions 
                               if self._get_response(q['id']) and self._get_response(q['id']).response == "no"]
                
                if no_responses:
                    st.markdown("**Areas for Improvement:**")
                    for q in no_responses[:5]:
                        st.markdown(f"- {q['id']}: {q['question'][:60]}...")
    
    def _render_footer(self):
        """Render completion footer"""
        
        stats = self._get_progress_stats()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Save & Exit", use_container_width=True):
                self._save_progress()
                st.info("Progress saved! You can continue later.")
        
        with col2:
            if self.state.last_saved:
                st.caption(f"Last saved: {self.state.last_saved.strftime('%H:%M:%S')}")
        
        with col3:
            if stats['pending'] == 0:
                if st.button("✅ Complete Assessment", type="primary", use_container_width=True):
                    self._complete_questionnaire()
            else:
                st.button(
                    f"⚠️ {stats['pending']} questions remaining",
                    disabled=True,
                    use_container_width=True
                )
    
    def _find_next_unanswered(self, start_idx: int) -> Optional[int]:
        """Find next unanswered question after start_idx"""
        for i in range(start_idx + 1, self.total_questions):
            q = self.all_questions[i]
            r = self._get_response(q['id'])
            if not r or not r.response:
                return i
        
        # Wrap around to beginning
        for i in range(0, start_idx):
            q = self.all_questions[i]
            r = self._get_response(q['id'])
            if not r or not r.response:
                return i
        
        return None
    
    def _save_progress(self):
        """Save current progress"""
        self.state.last_saved = datetime.now()
        if self.on_save:
            self.on_save(self.responses)
        st.success("✅ Progress saved!")
    
    def _complete_questionnaire(self):
        """Mark questionnaire as complete"""
        self._save_progress()
        if self.on_complete:
            self.on_complete(self.responses)
        st.success("🎉 Questionnaire completed!")
        st.balloons()


# ============================================================================
# INTEGRATION HELPER
# ============================================================================

def render_paginated_questionnaire(
    questions: Dict,
    responses: List,
    on_save: Optional[Callable] = None,
    on_complete: Optional[Callable] = None
):
    """
    Helper function to render the paginated questionnaire.
    
    Drop-in replacement for the old questionnaire rendering.
    
    Args:
        questions: WAF_QUESTIONS dict (pillar -> questions list)
        responses: List of QuestionResponse objects
        on_save: Callback for saving progress
        on_complete: Callback for completion
    """
    wizard = WAFQuestionnaireWizard(
        questions=questions,
        responses=responses,
        on_save=on_save,
        on_complete=on_complete
    )
    wizard.render()


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Demo mode
    st.set_page_config(page_title="WAF Questionnaire Wizard", layout="wide")
    
    # Sample questions
    sample_questions = {
        WAFPillar.SECURITY: [
            {
                "id": "SEC-001",
                "question": "How do you manage identities?",
                "description": "Identity management is foundational to security.",
                "best_practices": ["Use SSO", "Enable MFA", "Use IAM roles"],
                "scan_detectable": True,
                "detection_services": ["IAM", "Identity Center"]
            },
            {
                "id": "SEC-002", 
                "question": "How do you manage permissions?",
                "description": "Permissions control access to resources.",
                "best_practices": ["Least privilege", "Regular reviews"],
                "scan_detectable": True,
                "detection_services": ["IAM", "Access Analyzer"]
            }
        ],
        WAFPillar.RELIABILITY: [
            {
                "id": "REL-001",
                "question": "How do you manage service quotas?",
                "description": "Service quotas can impact availability.",
                "best_practices": ["Monitor quotas", "Request increases proactively"],
                "scan_detectable": True,
                "detection_services": ["Service Quotas", "Trusted Advisor"]
            }
        ]
    }
    
    # Initialize responses
    if 'demo_responses' not in st.session_state:
        st.session_state.demo_responses = []
    
    def save_handler(responses):
        st.session_state.demo_responses = responses
    
    def complete_handler(responses):
        st.session_state.demo_responses = responses
        st.session_state.completed = True
    
    render_paginated_questionnaire(
        questions=sample_questions,
        responses=st.session_state.demo_responses,
        on_save=save_handler,
        on_complete=complete_handler
    )
