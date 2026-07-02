import streamlit as st
import os
from group_analyzer import run_dynamic_analysis

st.set_page_config(page_title="GroupDNA Analyzer", page_icon="📊", layout="centered")

st.title("📊 Universal WhatsApp GroupDNA Analyzer")
st.write("Upload any exported WhatsApp chat log (`.txt`) to generate a pixel-perfect, high-resolution image infographic report instantly.")

# File Uploader Widget
uploaded_files = st.file_uploader("Drop your WhatsApp chat files here", type=["txt"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.subheader(f"Processing: {uploaded_file.name}")
        
        # Save uploaded file to a temporary location safely
        temp_path = os.path.join("temp_uploads", uploaded_file.name)
        os.makedirs("temp_uploads", exist_ok=True)
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        try:
            # Run parsing engine
            with st.spinner("Analyzing log patterns and formatting charts..."):
                generated_img = run_dynamic_analysis(temp_path)
            
            # Render report straight onto web interface page
            if generated_img and os.path.exists(generated_img):
                st.image(generated_img, caption="Generated Report Card", use_container_width=True)
                
                # Check actual file size on disk to display to user
                file_size_mb = os.path.getsize(generated_img) / (1024 * 1024)
                
                # Provide instant download functionality
                with open(generated_img, "rb") as file:
                    st.download_button(
                        label=f"💾 Download Report PNG ({file_size_mb:.2f} MB)",
                        data=file,
                        file_name=generated_img,
                        mime="image/png"
                    )
                st.success(f"Successfully compiled {uploaded_file.name}!")
            else:
                st.error("Engine processed data but image generation framework layout failed.")
                
        except Exception as e:
            st.error(f"Could not parse this log file format layout. Error: {e}")
        finally:
            # Clean up temporary storage footprint
            if os.path.exists(temp_path):
                os.remove(temp_path)
