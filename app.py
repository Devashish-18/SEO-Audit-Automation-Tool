import streamlit as st
from seo_audit import crawl_page, extract_metrics, calculate_score, generate_suggestions

st.title("SEO Audit Automation Tool")

url = st.text_input("Enter URL to audit:")

if st.button("Audit"):
    if url:
        with st.spinner("Crawling the page..."):
            html_content = crawl_page(url)
        if html_content.startswith("Error"):
            st.error(html_content)
        else:
            st.success("Page crawled successfully!")
            metrics = extract_metrics(html_content, url)
            score = calculate_score(metrics)
            
            st.header("SEO Metrics Dashboard")
            
            # Display overall score prominently
            st.metric("Overall SEO Score", f"{score}/100")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Basic Info")
                st.write(f"**Title:** {metrics.get('title', 'Not found')}")
                st.write(f"**Meta Description:** {metrics.get('meta_description', 'Not found')}")
                st.write(f"**H1 Count:** {metrics['h1_count']}")
                st.write(f"**Images without Alt:** {metrics['images_without_alt']}")
            
            with col2:
                st.subheader("Links")
                st.write(f"**Internal Links:** {metrics['internal_links']}")
                st.write(f"**External Links:** {metrics['external_links']}")
                st.write(f"**Has Viewport Meta:** {'Yes' if metrics['has_viewport'] else 'No'}")
            
            if metrics['h1_texts']:
                st.subheader("H1 Tags")
                for h1 in metrics['h1_texts']:
                    st.write(f"- {h1}")
            
            # Generate and display suggestions
            suggestions = generate_suggestions(metrics)
            if suggestions:
                st.header("SEO Improvement Suggestions")
                for suggestion in suggestions:
                    st.write(f"• {suggestion}")
            
            # Report export
            st.header("Export Report")
            report_text = f"SEO Audit Report for {url}\n\n"
            report_text += f"Overall SEO Score: {score}/100\n\n"
            report_text += "Metrics:\n"
            report_text += f"- Title: {metrics.get('title', 'Not found')}\n"
            report_text += f"- Meta Description: {metrics.get('meta_description', 'Not found')}\n"
            report_text += f"- H1 Count: {metrics['h1_count']}\n"
            report_text += f"- Images without Alt: {metrics['images_without_alt']}\n"
            report_text += f"- Internal Links: {metrics['internal_links']}\n"
            report_text += f"- External Links: {metrics['external_links']}\n"
            report_text += f"- Has Viewport Meta: {'Yes' if metrics['has_viewport'] else 'No'}\n\n"
            if suggestions:
                report_text += "Suggestions:\n"
                for suggestion in suggestions:
                    report_text += f"- {suggestion}\n"
            
            st.download_button(
                label="Download Report as Text File",
                data=report_text,
                file_name=f"seo_audit_report_{url.replace('http://', '').replace('https://', '').replace('/', '_')}.txt",
                mime="text/plain"
            )
    else:
        st.warning("Please enter a URL.")
