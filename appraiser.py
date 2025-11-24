"""
Appraiser Integration Module - Streamlit Page
Handles inspection assignment, photo uploads, and damage assessment
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Appraiser Integration",
    page_icon="🔧",
    layout="wide"
)

# Initialize session state
if 'inspection_queue' not in st.session_state:
    st.session_state.inspection_queue = []
if 'completed_inspections' not in st.session_state:
    st.session_state.completed_inspections = []

st.title("🔧 Appraiser Integration Portal")
st.markdown("### Vehicle Inspection & Damage Assessment Workflow")

# Navigation tabs
tab1, tab2, tab3 = st.tabs(["📋 Inspection Queue", "📷 Photo Upload & Assessment", "✅ Completed Inspections"])

# =======================
# TAB 1: Inspection Queue
# =======================
with tab1:
    st.header("Pending Inspections")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("""
        Claims requiring physical inspection are automatically assigned here.
        Appraisers can view details and mark inspections as scheduled.
        """)
    
    with col2:
        if st.button("➕ Add Test Inspection"):
            st.session_state.inspection_queue.append({
                'claim_number': f"CLM-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'claimant': "Test Claimant",
                'vehicle': "2020 Honda Accord",
                'damage_type': "Collision",
                'priority': "High",
                'assigned_date': datetime.now(),
                'status': "Pending Assignment"
            })
            st.rerun()
    
    if not st.session_state.inspection_queue:
        st.info("📭 No pending inspections. Queue is empty.")
    else:
        for idx, inspection in enumerate(st.session_state.inspection_queue):
            with st.expander(f"**{inspection['claim_number']}** - {inspection['claimant']} ({inspection['priority']} Priority)"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Vehicle:** {inspection['vehicle']}")
                    st.write(f"**Damage Type:** {inspection['damage_type']}")
                
                with col2:
                    st.write(f"**Priority:** {inspection['priority']}")
                    st.write(f"**Status:** {inspection['status']}")
                
                with col3:
                    st.write(f"**Assigned:** {inspection['assigned_date'].strftime('%Y-%m-%d')}")
                
                # Assignment actions
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    appraiser = st.selectbox(
                        "Assign to Appraiser",
                        ["Unassigned", "John Smith", "Sarah Johnson", "Mike Chen"],
                        key=f"appraiser_{idx}"
                    )
                
                with col2:
                    inspection_date = st.date_input(
                        "Schedule Inspection",
                        key=f"date_{idx}"
                    )
                
                with col3:
                    if st.button("✅ Assign & Schedule", key=f"assign_{idx}"):
                        inspection['assigned_appraiser'] = appraiser
                        inspection['scheduled_date'] = inspection_date
                        inspection['status'] = "Scheduled"
                        st.success(f"Assigned to {appraiser} for {inspection_date}")

# =======================
# TAB 2: Photo Upload & Assessment
# =======================
with tab2:
    st.header("Damage Assessment Workflow")
    
    # Select inspection
    if not st.session_state.inspection_queue:
        st.warning("⚠️ No inspections available. Add test inspection from Queue tab.")
    else:
        selected_idx = st.selectbox(
            "Select Inspection",
            range(len(st.session_state.inspection_queue)),
            format_func=lambda x: f"{st.session_state.inspection_queue[x]['claim_number']} - {st.session_state.inspection_queue[x]['claimant']}"
        )
        
        inspection = st.session_state.inspection_queue[selected_idx]
        
        st.subheader(f"Assessment for: {inspection['claim_number']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Vehicle Information:**")
            st.write(f"Vehicle: {inspection['vehicle']}")
            st.write(f"Claimant: {inspection['claimant']}")
            st.write(f"Damage Type: {inspection['damage_type']}")
        
        with col2:
            st.markdown("**Inspection Details:**")
            st.write(f"Priority: {inspection['priority']}")
            st.write(f"Status: {inspection['status']}")
            if 'assigned_appraiser' in inspection:
                st.write(f"Appraiser: {inspection['assigned_appraiser']}")
        
        st.markdown("---")
        
        # Photo upload section
        st.subheader("📷 Upload Damage Photos")
        
        uploaded_photos = st.file_uploader(
            "Upload vehicle damage photos",
            type=['jpg', 'jpeg', 'png'],
            accept_multiple_files=True,
            help="Upload photos showing all damaged areas"
        )
        
        if uploaded_photos:
            st.success(f"✅ {len(uploaded_photos)} photo(s) uploaded")
            
            # Display thumbnails
            cols = st.columns(min(len(uploaded_photos), 4))
            for idx, photo in enumerate(uploaded_photos[:4]):
                with cols[idx % 4]:
                    st.image(photo, caption=photo.name, use_container_width=True)
            
            if len(uploaded_photos) > 4:
                st.caption(f"+ {len(uploaded_photos) - 4} more photo(s)")
        
        st.markdown("---")
        
        # Damage assessment form
        st.subheader("🔍 Damage Assessment")
        
        col1, col2 = st.columns(2)
        
        with col1:
            damage_areas = st.multiselect(
                "Damaged Areas",
                ["Front Bumper", "Rear Bumper", "Front Driver Door", "Front Passenger Door",
                 "Rear Driver Door", "Rear Passenger Door", "Hood", "Trunk", "Roof",
                 "Driver Fender", "Passenger Fender", "Windshield", "Headlights", "Taillights"],
                default=["Front Bumper"]
            )
            
            repair_complexity = st.select_slider(
                "Repair Complexity",
                options=["Minor", "Moderate", "Extensive", "Total Loss"],
                value="Moderate"
            )
        
        with col2:
            estimated_repair_cost = st.number_input(
                "Estimated Repair Cost ($)",
                min_value=0.0,
                value=5000.0,
                step=500.0
            )
            
            pre_existing_damage = st.checkbox("Pre-existing damage detected")
            
            additional_parts_needed = st.text_area(
                "Additional Parts Needed",
                placeholder="List any OEM parts required for repair..."
            )
        
        # Repair vs Total Loss recommendation
        st.markdown("---")
        st.subheader("💡 Recommendation")
        
        # Simple logic for demo
        vehicle_value = 15000.0  # Mock value
        total_loss_threshold = vehicle_value * 0.75
        
        if estimated_repair_cost >= total_loss_threshold:
            st.error(f"⚠️ **Total Loss Recommended** - Repair cost (${estimated_repair_cost:,.2f}) exceeds 75% of vehicle value (${vehicle_value:,.2f})")
            recommendation = "Total Loss"
        else:
            st.success(f"✅ **Repairable** - Repair cost (${estimated_repair_cost:,.2f}) is below threshold (${total_loss_threshold:,.2f})")
            recommendation = "Repair"
        
        # Final notes
        appraiser_notes = st.text_area(
            "Appraiser Notes",
            placeholder="Additional observations, concerns, or recommendations..."
        )
        
        # Submit assessment
        if st.button("📤 Submit Assessment", type="primary"):
            if not uploaded_photos:
                st.warning("Please upload at least one photo")
            elif not damage_areas:
                st.warning("Please select damaged areas")
            else:
                # Create assessment record
                assessment = {
                    'claim_number': inspection['claim_number'],
                    'claimant': inspection['claimant'],
                    'vehicle': inspection['vehicle'],
                    'damage_areas': damage_areas,
                    'repair_complexity': repair_complexity,
                    'estimated_cost': estimated_repair_cost,
                    'recommendation': recommendation,
                    'pre_existing': pre_existing_damage,
                    'parts_needed': additional_parts_needed,
                    'notes': appraiser_notes,
                    'photo_count': len(uploaded_photos),
                    'completed_date': datetime.now(),
                    'appraiser': inspection.get('assigned_appraiser', 'Current User')
                }
                
                # Move to completed
                st.session_state.completed_inspections.append(assessment)
                st.session_state.inspection_queue.pop(selected_idx)
                
                st.success("✅ Assessment submitted successfully!")
                st.balloons()
                st.rerun()

# =======================
# TAB 3: Completed Inspections
# =======================
with tab3:
    st.header("Completed Assessments")
    
    if not st.session_state.completed_inspections:
        st.info("📊 No completed inspections yet. Complete assessments from the Photo Upload tab.")
    else:
        # Summary metrics
        total = len(st.session_state.completed_inspections)
        total_loss_count = sum(1 for a in st.session_state.completed_inspections if a['recommendation'] == "Total Loss")
        avg_cost = sum(a['estimated_cost'] for a in st.session_state.completed_inspections) / total
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Inspections", total)
        with col2:
            st.metric("Total Loss Rate", f"{(total_loss_count/total*100):.1f}%")
        with col3:
            st.metric("Avg Repair Cost", f"${avg_cost:,.2f}")
        
        st.markdown("---")
        
        # List completed assessments
        for assessment in reversed(st.session_state.completed_inspections):
            with st.expander(f"**{assessment['claim_number']}** - {assessment['vehicle']} | {assessment['recommendation']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Claimant:** {assessment['claimant']}")
                    st.write(f"**Appraiser:** {assessment['appraiser']}")
                    st.write(f"**Completed:** {assessment['completed_date'].strftime('%Y-%m-%d %H:%M')}")
                
                with col2:
                    st.write(f"**Damaged Areas:** {len(assessment['damage_areas'])}")
                    st.write(f"**Complexity:** {assessment['repair_complexity']}")
                    st.write(f"**Photos:** {assessment['photo_count']}")
                
                with col3:
                    st.write(f"**Estimated Cost:** ${assessment['estimated_cost']:,.2f}")
                    st.write(f"**Recommendation:** {assessment['recommendation']}")
                    st.write(f"**Pre-existing:** {'Yes' if assessment['pre_existing'] else 'No'}")
                
                if assessment['notes']:
                    st.markdown(f"**Notes:** {assessment['notes']}")

# Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### Appraiser Tools")
st.sidebar.markdown("- 📸 Photo upload support")
st.sidebar.markdown("- 🔍 Damage area mapping")
st.sidebar.markdown("- 💰 Cost estimation")
st.sidebar.markdown("- 📊 Repair vs Total Loss logic")
st.sidebar.markdown("---")
st.sidebar.caption("Ema Agentic Claims v1.0")
