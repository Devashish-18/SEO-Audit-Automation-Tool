# 🔧 SEO Audit Tool - Error Codes & Solutions

## **Common Errors & How to Fix Them**

### **❌ Error 403 - Forbidden**
**Cause:** Website is blocking automated access (crawlers)

**Solution:** 
- Try a different website (some sites like ChatGPT actively block scrapers)
- The tool works with most public websites
- Try: Wikipedia, GitHub, Medium, Dev.to, etc.

---

### **❌ Error 401 - Unauthorized**
**Cause:** Website requires login

**Solution:**
- Use a public page that doesn't require authentication
- Try the homepage or public blog posts

---

### **❌ Error 429 - Too Many Requests**
**Cause:** Website rate-limited us

**Solution:**
- Wait a few moments and try again
- The API now rotates User-Agents to avoid this

---

### **❌ Error 503 - Service Unavailable**
**Cause:** Website is down or overloaded

**Solution:**
- Website is temporarily unavailable
- Try again in a few moments
- Check if the website is up on isitdownrightnow.com

---

### **❌ Cannot Connect to Website**
**Cause:** Website URL is wrong or site is offline

**Solution:**
- Check the URL spelling (e.g., https://example.com)
- Make sure the website is actually online
- Try a different website

---

### **❌ Request Timeout**
**Cause:** Website took more than 10 seconds to respond

**Solution:**
- Try a faster website
- Check your internet connection
- Try again later

---

### **❌ Cannot Connect to API Server**
**Cause:** Backend API is not running

**Solution:**
1. Open a new terminal
2. Run: `python api.py`
3. You should see: `Listening on: http://127.0.0.1:5000`
4. Go back to browser and try again

---

## **✅ Websites That Work Great**

These are tested and work reliably:

- **Wikipedia** - https://www.wikipedia.org/
- **GitHub** - https://github.com/
- **Medium** - https://medium.com/
- **Dev.to** - https://dev.to/
- **Stack Overflow** - https://stackoverflow.com/
- **Product Hunt** - https://www.producthunt.com/
- **Hacker News** - https://news.ycombinator.com/
- **BBC** - https://www.bbc.com/
- **CNN** - https://www.cnn.com/
- **TechCrunch** - https://techcrunch.com/

---

## **❌ Websites That Block Crawlers**

These actively block or require special headers:

- ChatGPT (chatgpt.com) - Requires special headers
- LinkedIn - Requires login
- Facebook - Heavily protected
- Instagram - Protected
- Twitter/X - Protected
- Patreon - Protected
- Stripe - Protected

---

## **🔍 Why Some Sites Block Crawlers**

1. **Security** - Prevent automated attacks
2. **Rate Limiting** - Control server load
3. **Terms of Service** - Many sites prohibit scraping
4. **Copyright Protection** - Prevent content copying
5. **Privacy** - Protect user data

---

## **💡 Tips for Best Results**

1. ✅ Test with public, open-source websites first
2. ✅ If one site fails, try another
3. ✅ Keep the 10-second timeout in mind (very large pages may timeout)
4. ✅ Check console (F12) for detailed error messages
5. ✅ Make sure your internet connection is stable

---

## **🚀 Want to Analyze a Specific Site?**

Try these steps:
1. **Visit the site directly** in your browser
2. **Check if it's public** (doesn't require login)
3. **Test with the tool**
4. **If it fails**, it's probably protected against crawlers

This is normal - many production sites have security measures!

---

## **📞 Support**

If you need help:
1. Check the error message in the red box
2. Look up the error code in this guide
3. Try a different website
4. Check that the API is running (see "Cannot Connect to API Server")
