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

st.set_page_config(page_title="Official Adobe PDF to DOCX", layout="centered")

# --- FETCH SECRETS FROM ENVIRONMENT VARIABLES ---
CLIENT_ID = os.environ.get("ADOBE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("ADOBE_CLIENT_SECRET")
APP_PASSWORD = os.environ.get("APP_PASSWORD")

# --- PASSWORD PROTECTION LOGIC ---
def check_password():
    # Fail-safe just in case the variable isn't set in Portainer
    if not APP_PASSWORD:
        st.error("⚠️ Server configuration error: APP_PASSWORD is not set in environment variables.")
        return False

    # Initialize the session state so it remembers if you are logged in
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    # If not logged in, show the login screen
    if not st.session_state["password_correct"]:
        st.title("🔒 Access Restricted")
        st.markdown("Please enter the password to use this tool.")
        
        # We use a form so the user can just press 'Enter' on their keyboard
        with st.form("login_form"):
            pwd = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if pwd == APP_PASSWORD:
                    st.session_state["password_correct"] = True
                    st.rerun()  # Instantly reloads the page to show the app
                else:
                    st.error("Incorrect password. Please try again.")
        return False
        
    return True

# --- MAIN APP (Only runs if password is correct) ---
if check_password():
    st.title("📄 PDF to DOCX (Adobe Engine)")
    st.markdown("This uses the official Adobe PDF Services API for flawless reconstruction.")

    # File uploader
    uploaded_file = st.file_uploader("Select a PDF file", type=["pdf"])

    if uploaded_file is not None:
        if not CLIENT_ID or not CLIENT_SECRET:
            st.error("⚠️ Adobe credentials are missing. Please add ADOBE_CLIENT_ID and ADOBE_CLIENT_SECRET as environment variables in Portainer.")
        else:
            st.info("File uploaded successfully. Click below to process using Adobe's servers.")
            
            if st.button("Process File (Costs 1 Adobe Transaction)"):
                with st.spinner("Uploading and processing on Adobe's servers..."):
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
                        
                        st.success("Conversion Complete!")
                        
                        # 6. Provide the download button
                        st.download_button(
                            label="Download DOCX",
                            data=docx_bytes,
                            file_name=f"{uploaded_file.name.replace('.pdf', '')}_converted.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                        
                    except Exception as e:
                        st.error(f"An error occurred during Adobe processing: {e}")
