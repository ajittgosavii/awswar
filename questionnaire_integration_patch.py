"""
Integration Patch: Paginated Questionnaire
==========================================

This file shows how to integrate the new paginated WAF questionnaire wizard
into the existing waf_review_comprehensive.py file.

Apply these changes to replace the "all questions at once" approach with
the new "one question per page" wizard.
"""

# ============================================================================
# STEP 1: Add import at the top of waf_review_comprehensive.py
# ============================================================================

# Add this import near the top of the file (around line 25-45):
"""
# Import paginated questionnaire wizard
try:
    from waf_questionnaire_wizard import (
        WAFQuestionnaireWizard,
        render_paginated_questionnaire,
        QuestionResponse as WizardQuestionResponse
    )
    WIZARD_AVAILABLE = True
except ImportError:
    WIZARD_AVAILABLE = False
    print("Paginated questionnaire wizard not available")
"""


# ============================================================================
# STEP 2: Replace _render_questionnaire_phase method
# ============================================================================

# Find the method at around line 1649 and replace it with this:

def _render_questionnaire_phase_NEW(self):
    """
    Render WAF questionnaire phase - PAGINATED VERSION
    
    Uses the new wizard component for one-question-per-page experience.
    Falls back to old method if wizard not available.
    """
    
    # Check if wizard is available
    if not WIZARD_AVAILABLE:
        # Fall back to original method
        self._render_questionnaire_phase_legacy()
        return
    
    st.markdown("## 📝 Step 3: WAF Questionnaire")
    st.markdown("""
    Answer questions about your workload to complete the assessment.
    Questions that can be auto-detected from scan results are pre-filled.
    """)
    
    # Check for saved progress
    has_saved, saved_info = self.has_saved_progress()
    if has_saved and not self.session.responses:
        st.info(f"📂 **Saved progress found!** {saved_info}")
        col_restore, col_new = st.columns(2)
        with col_restore:
            if st.button("📥 Restore Saved Progress", type="primary", use_container_width=True):
                if self.load_progress():
                    st.success("✅ Progress restored!")
                    st.rerun()
                else:
                    st.error("❌ Could not restore progress")
        with col_new:
            if st.button("🆕 Start Fresh", use_container_width=True):
                self.clear_saved_progress()
                self._auto_detect_answers()
                st.rerun()
        st.markdown("---")
    
    # Auto-detect answers from findings (if no responses yet)
    if not self.session.responses:
        self._auto_detect_answers()
    
    # Convert WAF_QUESTIONS to wizard format
    # WAF_QUESTIONS uses WAFPillar enum as keys
    questions_for_wizard = {}
    for pillar in WAFPillar:
        questions_for_wizard[pillar] = WAF_QUESTIONS.get(pillar, [])
    
    # Define callbacks
    def on_save(responses):
        """Called when user saves progress"""
        # Convert wizard responses back to our format if needed
        self.session.responses = responses
        self.save_progress()
    
    def on_complete(responses):
        """Called when questionnaire is completed"""
        self.session.responses = responses
        self.session.questionnaire_completed = True
        self.session.current_phase = ReviewPhase.SCORING
        self.session.updated_at = datetime.now()
        self.save_progress()
        st.rerun()
    
    # Render the paginated wizard
    render_paginated_questionnaire(
        questions=questions_for_wizard,
        responses=self.session.responses,
        on_save=on_save,
        on_complete=on_complete
    )
    
    # Navigation (only show "Back" - Next is handled by wizard)
    st.markdown("---")
    if st.button("⬅️ Back to Scan Results", use_container_width=False):
        self.session.current_phase = ReviewPhase.SCANNING
        st.rerun()


# ============================================================================
# STEP 3: Rename original method as legacy fallback
# ============================================================================

# Rename the original _render_questionnaire_phase to:
# _render_questionnaire_phase_legacy

# The original method (lines 1649-1777) becomes the fallback


# ============================================================================
# STEP 4: Add toggle for questionnaire mode
# ============================================================================

# Add this to the class __init__ or session initialization:

"""
# In session state initialization, add:
if 'use_paginated_questionnaire' not in st.session_state:
    st.session_state.use_paginated_questionnaire = True  # New default
"""

# Add toggle in the UI (optional - in sidebar or settings):
"""
# In sidebar or settings section:
st.session_state.use_paginated_questionnaire = st.toggle(
    "Use Paginated Questionnaire",
    value=st.session_state.get('use_paginated_questionnaire', True),
    help="Show one question per page instead of all questions at once"
)
"""


# ============================================================================
# STEP 5: Update the phase router to use new method
# ============================================================================

# In the render() method where phases are routed (around line 1004):
# Change:
#     self._render_questionnaire_phase()
# To:
#     self._render_questionnaire_phase_NEW()


# ============================================================================
# COMPLETE REPLACEMENT CODE
# ============================================================================

# Here's the complete replacement for _render_questionnaire_phase:

REPLACEMENT_CODE = '''
    def _render_questionnaire_phase(self):
        """
        Render WAF questionnaire phase
        Uses paginated wizard for better UX with 200+ questions
        """
        
        # Try to use paginated wizard
        try:
            from waf_questionnaire_wizard import render_paginated_questionnaire
            wizard_available = True
        except ImportError:
            wizard_available = False
        
        st.markdown("## 📝 Step 3: WAF Questionnaire")
        
        # Mode toggle
        use_wizard = st.session_state.get('use_paginated_questionnaire', True)
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if wizard_available:
                new_mode = st.toggle(
                    "Paginated Mode",
                    value=use_wizard,
                    help="One question per page (recommended for 200+ questions)"
                )
                if new_mode != use_wizard:
                    st.session_state.use_paginated_questionnaire = new_mode
                    st.rerun()
        
        st.markdown("""
        Answer questions about your workload to complete the assessment.
        Questions that can be auto-detected from scan results are pre-filled.
        """)
        
        # Check for saved progress
        has_saved, saved_info = self.has_saved_progress()
        if has_saved and not self.session.responses:
            st.info(f"📂 **Saved progress found!** {saved_info}")
            col_restore, col_new = st.columns(2)
            with col_restore:
                if st.button("📥 Restore Saved Progress", type="primary", use_container_width=True):
                    if self.load_progress():
                        st.success("✅ Progress restored!")
                        st.rerun()
            with col_new:
                if st.button("🆕 Start Fresh", use_container_width=True):
                    self.clear_saved_progress()
                    self._auto_detect_answers()
                    st.rerun()
            st.markdown("---")
        
        # Auto-detect answers
        if not self.session.responses:
            self._auto_detect_answers()
        
        # Render based on mode
        if wizard_available and use_wizard:
            self._render_questionnaire_wizard()
        else:
            self._render_questionnaire_legacy()
    
    def _render_questionnaire_wizard(self):
        """Render paginated questionnaire wizard"""
        from waf_questionnaire_wizard import render_paginated_questionnaire
        
        # Convert questions to wizard format
        questions_for_wizard = {}
        for pillar in WAFPillar:
            questions_for_wizard[pillar] = WAF_QUESTIONS.get(pillar, [])
        
        def on_save(responses):
            self.session.responses = responses
            self.save_progress()
        
        def on_complete(responses):
            self.session.responses = responses
            self.session.questionnaire_completed = True
            self.session.current_phase = ReviewPhase.SCORING
            self.save_progress()
            st.rerun()
        
        render_paginated_questionnaire(
            questions=questions_for_wizard,
            responses=self.session.responses,
            on_save=on_save,
            on_complete=on_complete
        )
        
        st.markdown("---")
        if st.button("⬅️ Back to Scan Results"):
            self.session.current_phase = ReviewPhase.SCANNING
            st.rerun()
    
    def _render_questionnaire_legacy(self):
        """Render legacy all-questions-at-once view"""
        # ... original _render_questionnaire_phase code goes here ...
        # (the code from lines 1681-1777 of the original file)
        pass  # Replace with original implementation
'''

print("Integration patch created successfully!")
print("See MODULAR_FILE_STRUCTURE.md for complete restructuring guide")
