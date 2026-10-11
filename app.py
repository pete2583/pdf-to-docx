import streamlit as st
import os

# Modern Adobe PDF Services SDK v4+ imports
from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
from adobe.pdfservices.operation.pdf_services import PDFServices
from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_params import ExportPDFParams
from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_target_format import ExportPDFTargetFormat
from adobe.pdfservices.operation.pdfjobs.jobs.export_pdf_job import ExportPDFJob
from adobe.pdfservices.operation.pdfjobs.result.export_pdf_result import ExportPDFResult

st.set_page_config(page_title="Unofficial Adobe PDF to DOCX", layout="centered")

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
    st.title("📄 PDF to DOCX (Adobe Engine)")
    st.markdown("Batch convert PDFs to Word using the official Adobe PDF Services API.")

    # File uploader (Accepts multiple files)
    uploaded_files = st.file_uploader("Select PDF files", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        if not CLIENT_ID or not CLIENT_SECRET:
            st.error("⚠️ Adobe credentials are missing. Please add ADOBE_CLIENT_ID and ADOBE_CLIENT_SECRET in Portainer.")
        else:
            file_count = len(uploaded_files)
            st.info(f"{file_count} file(s) ready for processing.")
            
            if st.button(f"Process {file_count} File(s) (Costs {file_count} Adobe Transactions)"):
                
                # Clear any previously converted files from memory
                st.session_state["converted_files"] = []
                
                # UI Elements for progress
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Loop through all uploaded files
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Processing {uploaded_file.name} ({i+1}/{file_count})...")
                    
                    try:
                        # 1. Setup Adobe API Credentials
                        credentials = ServicePrincipalCredentials(
                            client_id=CLIENT_ID,
                            client_secret=CLIENT_SECRET
                        )
                        pdf_services = PDFServices(credentials=credentials)

                        # 2. Upload the PDF
                        input_stream = uploaded_file.getvalue()
                        input_asset = pdf_services.upload(
                            input_stream=input_stream, 
                            mime_type=PDFServicesMediaType.PDF
                        )

                        # 3. Configure the export job
                        export_pdf_params = ExportPDFParams(target_format=ExportPDFTargetFormat.DOCX)
                        export_pdf_job = ExportPDFJob(
                            input_asset=input_asset, 
                            export_pdf_params=export_pdf_params
                        )

                        # 4. Submit the job and wait
                        location = pdf_services.submit(export_pdf_job)
                        pdf_services_response = pdf_services.get_job_result(location, ExportPDFResult)

                        # 5. Fetch the converted DOCX file
                        result_asset = pdf_services_response.get_result().get_asset()
                        stream_asset = pdf_services.get_content(result_asset)
                        docx_bytes = stream_asset.get_input_stream()
                        
                        # Save the bytes and filename to session state so it survives page reloads
                        out_name = f"{uploaded_file.name.replace('.pdf', '')}.docx"
                        st.session_state["converted_files"].append((out_name, docx_bytes))
                        
                    except Exception as e:
                        st.error(f"Error processing {uploaded_file.name}: {e}")
                        
                    # Update progress bar
                    progress_bar.progress((i + 1) / file_count)
                
                status_text.text("All processing complete!")
                st.success(f"Successfully converted {len(st.session_state['converted_files'])} file(s)!")

    # --- DOWNLOAD SECTION ---
    # We display this outside the button loop so downloads survive page refreshes
    if "converted_files" in st.session_state and st.session_state["converted_files"]:
        st.markdown("### 📥 Download Converted Files")
        
        # Display individual download buttons for every file
        for file_name, file_bytes in st.session_state["converted_files"]:
            st.download_button(
                label=f"Download {file_name}",
                data=file_bytes,
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=file_name # Unique key required when generating buttons in a loop
            )
