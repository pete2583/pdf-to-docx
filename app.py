import streamlit as st
import os

# Modern Adobe PDF Services SDK v4+ imports
from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
from adobe.pdfservices.operation.pdf_services import PDFServices
from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType

# Export PDF imports
from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_params import ExportPDFParams
from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_target_format import ExportPDFTargetFormat
from adobe.pdfservices.operation.pdfjobs.jobs.export_pdf_job import ExportPDFJob
from adobe.pdfservices.operation.pdfjobs.result.export_pdf_result import ExportPDFResult

# Combine PDF imports (NEW)
from adobe.pdfservices.operation.pdfjobs.params.combine_pdf.combine_pdf_params import CombinePDFParams
from adobe.pdfservices.operation.pdfjobs.jobs.combine_pdf_job import CombinePDFJob
from adobe.pdfservices.operation.pdfjobs.result.combine_pdf_result import CombinePDFResult

st.set_page_config(page_title="Official Adobe PDF Toolkit", layout="centered")

# --- FETCH SECRETS FROM ENVIRONMENT VARIABLES ---
CLIENT_ID = os.environ.get("ADOBE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("ADOBE_CLIENT_SECRET")
APP_PASSWORD = os.environ.get("APP_PASSWORD")

# --- PASSWORD PROTECTION LOGIC ---
def check_password():
    if not APP_PASSWORD:
        st.error("⚠️ Server configuration error: APP_PASSWORD is not set in environment variables.")
        return False

    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔒 Access Restricted")
        st.markdown("Please enter the password to use this tool.")
        
        with st.form("login_form"):
            pwd = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if pwd == APP_PASSWORD:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("Incorrect password. Please try again.")
        return False
        
    return True

# --- MAIN APP ---
if check_password():
    st.title("📄 Adobe PDF Toolkit")
    st.markdown("Batch convert PDFs to Word or combine multiple PDFs using the official Adobe PDF Services API.")

    # NEW: Let the user choose the tool
    operation = st.radio("What would you like to do?", ["Convert to DOCX", "Combine into a single PDF"], horizontal=True)

    # File uploader (Accepts multiple files)
    uploaded_files = st.file_uploader("Select PDF files", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        if not CLIENT_ID or not CLIENT_SECRET:
            st.error("⚠️ Adobe credentials are missing. Please add ADOBE_CLIENT_ID and ADOBE_CLIENT_SECRET in Portainer.")
        else:
            file_count = len(uploaded_files)
            
            # ------------------------------------
            # MODE 1: CONVERT TO DOCX
            # ------------------------------------
            if operation == "Convert to DOCX":
                st.info(f"{file_count} file(s) ready for conversion.")
                
                if st.button(f"Convert {file_count} File(s) (Costs {file_count} Adobe Transactions)"):
                    st.session_state["converted_files"] = []
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    for i, uploaded_file in enumerate(uploaded_files):
                        status_text.text(f"Converting {uploaded_file.name} ({i+1}/{file_count})...")
                        try:
                            credentials = ServicePrincipalCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
                            pdf_services = PDFServices(credentials=credentials)

                            input_asset = pdf_services.upload(input_stream=uploaded_file.getvalue(), mime_type=PDFServicesMediaType.PDF)
                            export_job = ExportPDFJob(input_asset=input_asset, export_pdf_params=ExportPDFParams(target_format=ExportPDFTargetFormat.DOCX))
                            
                            location = pdf_services.submit(export_job)
                            pdf_services_response = pdf_services.get_job_result(location, ExportPDFResult)
                            
                            stream_asset = pdf_services.get_content(pdf_services_response.get_result().get_asset())
                            out_name = f"{uploaded_file.name.replace('.pdf', '')}.docx"
                            st.session_state["converted_files"].append((out_name, stream_asset.get_input_stream()))
                            
                        except Exception as e:
                            st.error(f"Error processing {uploaded_file.name}: {e}")
                            
                        progress_bar.progress((i + 1) / file_count)
                    
                    status_text.text("All conversions complete!")
                    st.success(f"Successfully converted {len(st.session_state['converted_files'])} file(s)!")

            # ------------------------------------
            # MODE 2: COMBINE INTO SINGLE PDF
            # ------------------------------------
            elif operation == "Combine into a single PDF":
                if file_count < 2:
                    st.warning("Please upload at least 2 PDF files to combine them.")
                else:
                    st.info(f"{file_count} files ready to be combined into one document.")
                    
                    if st.button(f"Combine {file_count} Files (Costs 1 Adobe Transaction)"):
                        st.session_state["combined_file"] = None
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        try:
                            credentials = ServicePrincipalCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
                            pdf_services = PDFServices(credentials=credentials)
                            
                            combine_params = CombinePDFParams()
                            
                            # Upload all files sequentially to Adobe and add to combine params
                            for i, uploaded_file in enumerate(uploaded_files):
                                status_text.text(f"Uploading {uploaded_file.name} to Adobe ({i+1}/{file_count})...")
                                input_asset = pdf_services.upload(input_stream=uploaded_file.getvalue(), mime_type=PDFServicesMediaType.PDF)
                                combine_params.add_asset(input_asset)
                                progress_bar.progress((i + 1) / (file_count + 1)) # Leave some progress for the actual combine job
                                
                            status_text.text("Merging files on Adobe's servers (this may take a moment)...")
                            
                            combine_job = CombinePDFJob(combine_pdf_params=combine_params)
                            location = pdf_services.submit(combine_job)
                            
                            pdf_services_response = pdf_services.get_job_result(location, CombinePDFResult)
                            stream_asset = pdf_services.get_content(pdf_services_response.get_result().get_asset())
                            
                            st.session_state["combined_file"] = stream_asset.get_input_stream()
                            
                            progress_bar.progress(1.0)
                            status_text.text("Combine complete!")
                            st.success("Successfully merged your files!")
                            
                        except Exception as e:
                            st.error(f"Error combining files: {e}")

    # --- DOWNLOAD SECTION ---
    
    # 1. Download Buttons for DOCX Mode
    if operation == "Convert to DOCX" and st.session_state.get("converted_files"):
        st.markdown("### 📥 Download Converted Files")
        for file_name, file_bytes in st.session_state["converted_files"]:
            st.download_button(
                label=f"Download {file_name}",
                data=file_bytes,
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=file_name
            )

    # 2. Download Button for Combine Mode
    elif operation == "Combine into a single PDF" and st.session_state.get("combined_file"):
        st.markdown("### 📥 Download Merged PDF")
        st.download_button(
            label="Download Combined.pdf",
            data=st.session_state["combined_file"],
            file_name="Combined.pdf",
            mime="application/pdf",
            type="primary" # Makes this button stand out in red/blue
        )
        
