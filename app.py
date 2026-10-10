import streamlit as st

# Modern Adobe PDF Services SDK v4+ imports
from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
from adobe.pdfservices.operation.pdf_services import PDFServices
from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_params import ExportPDFParams
from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_target_format import ExportPDFTargetFormat
from adobe.pdfservices.operation.pdfjobs.jobs.export_pdf_job import ExportPDFJob
from adobe.pdfservices.operation.pdfjobs.result.export_pdf_result import ExportPDFResult

st.set_page_config(page_title="Official Adobe PDF to DOCX", layout="centered")

# --- SIDEBAR FOR CREDENTIALS ---
st.sidebar.title("🔑 Adobe API Credentials")
st.sidebar.markdown("Get these from the [Adobe Developer Console](https://developer.adobe.com/document-services/).")
client_id = st.sidebar.text_input("Client ID", type="password")
client_secret = st.sidebar.text_input("Client Secret", type="password")

# --- MAIN APP ---
st.title("📄 PDF to DOCX (Adobe Engine)")
st.markdown("This uses the official Adobe PDF Services API for flawless reconstruction.")

# File uploader
uploaded_file = st.file_uploader("Select a PDF file", type=["pdf"])

if uploaded_file is not None:
    
    if not client_id or not client_secret:
        st.warning("⚠️ Please enter your Adobe Client ID and Client Secret in the sidebar first.")
    else:
        st.info("File uploaded successfully. Click below to process using Adobe's servers.")
        
        if st.button("Process File (Costs 1 Adobe Transaction)"):
            with st.spinner("Uploading and processing on Adobe's servers..."):
                try:
                    # 1. Setup Adobe API Credentials
                    credentials = ServicePrincipalCredentials(
                        client_id=client_id,
                        client_secret=client_secret
                    )
                    pdf_services = PDFServices(credentials=credentials)

                    # 2. Upload the PDF from Streamlit's memory
                    input_stream = uploaded_file.getvalue()
                    input_asset = pdf_services.upload(
                        input_stream=input_stream, 
                        mime_type=PDFServicesMediaType.PDF
                    )

                    # 3. Configure the job to export to DOCX
                    export_pdf_params = ExportPDFParams(target_format=ExportPDFTargetFormat.DOCX)
                    export_pdf_job = ExportPDFJob(
                        input_asset=input_asset, 
                        export_pdf_params=export_pdf_params
                    )

                    # 4. Submit the job and wait for the result
                    location = pdf_services.submit(export_pdf_job)
                    pdf_services_response = pdf_services.get_job_result(location, ExportPDFResult)

                    # 5. Fetch the converted DOCX file from Adobe
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