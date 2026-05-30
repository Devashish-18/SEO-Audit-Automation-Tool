# Bulk Metadata Generator

A beginner-friendly web tool for education marketers to generate SEO metadata in bulk from CSV input.

## **Quick Start**

1. Open `index.html` in your browser.
2. Click **Download Sample CSV** to get a ready-made template.
3. Paste your course data in the CSV editor.
4. Click **Parse CSV**.
5. Click **Generate Metadata**.
6. Download the finished CSV.

---

## **How It Works**

1. Paste a CSV with these headers:
   - `URL`
   - `Program Name`
   - `University Name`
   - `Primary Keyword`
   - `Secondary Keyword`
2. Click **Parse CSV** to validate the rows.
3. Click **Generate Metadata** to create:
   - Page Title
   - Meta Description
   - Alternate Description
4. Click **Download CSV** to export your results.

---

## **Features**

✅ Bulk metadata generation for course pages

✅ Built for education brands with 50–200 course pages

✅ Works entirely in the browser with no backend needed

✅ Sample CSV template included

✅ Export is ready for upload to CMS or SEO tools

---

## **File Structure**

```
Bulk Metadata Generator/
├── index.html          # Main UI
├── styles.css          # Styling
├── script.js           # Frontend logic
├── README.md           # Usage guide
```

---

## **Deployment**

This tool can be deployed as a static website, including GitHub Pages. Just publish the repository and use `index.html` as the landing page.

---

## **Requirements**

- Python 3.8+
- Modern web browser
- Internet connection (to crawl websites)

---

## **Troubleshooting**

### **Error: "Cannot connect to API server"**
- Make sure `python api.py` is running in a separate terminal
- Check that port 5000 is not in use

### **Website blocked error**
- Some websites block automated crawlers
- Try with publicly accessible sites like Wikipedia or GitHub

### **Timeout error**
- The website took too long to respond
- Try again or use a faster internet connection

---

## **Development Options**

### **Option 1: HTML/JS + Python API (Recommended)**
```bash
# Terminal 1
python api.py

# Terminal 2 (optional - for serving files)
python -m http.server 8000

# Then open index.html in browser
```

### **Option 2: Streamlit Version**
```bash
streamlit run app.py
```

---

## **License**

MIT License - Feel free to use and modify!

---

## **Support**

For issues or suggestions, please check the error messages in the browser console (F12 > Console tab).
