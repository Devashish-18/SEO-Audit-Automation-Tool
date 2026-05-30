// Tabbed SEO Interface JavaScript

const API_BASE_URL = window.location.protocol === 'file:'
    ? 'http://127.0.0.1:8000'
    : window.location.origin;

const API_ROUTES = {
    metadata: `${API_BASE_URL}/api/generate/metadata`,
    headers: `${API_BASE_URL}/api/generate/headers`,
    faqs: `${API_BASE_URL}/api/generate/faqs`,
    audit: `${API_BASE_URL}/api/audit`
};

function setActiveTab(tabName) {
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.toggle('active', button.dataset.tab === tabName);
    });

    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === tabName);
    });
}

function getActiveTabId() {
    const activeSection = document.querySelector('.tab-content.active');
    return activeSection ? activeSection.id : 'metadata';
}

function showMessage(tabId, message, type = 'info') {
    const messageElement = document.getElementById(`${tabId}Message`);
    if (!messageElement) return;
    messageElement.textContent = message;
    messageElement.className = `message ${type}`;
    messageElement.style.display = 'block';
}

function hideMessage(tabId) {
    const messageElement = document.getElementById(`${tabId}Message`);
    if (!messageElement) return;
    messageElement.style.display = 'none';
    messageElement.textContent = '';
    messageElement.className = 'message';
}

function copyText(text, label) {
    if (!text || !String(text).trim()) {
        alert('Nothing to copy');
        return;
    }
    navigator.clipboard.writeText(text).then(() => {
        showMessage(getActiveTabId(), `${label} copied!`, 'success');
    }).catch(() => {
        showMessage(getActiveTabId(), 'Copy failed. Try again.', 'error');
    });
}

function updateCharCount(value, badgeId, maxLength) {
    const badge = document.getElementById(badgeId);
    if (!badge) return;
    const count = String(value || '').length;
    badge.textContent = `${count}/${maxLength}`;
    badge.classList.toggle('over-limit', count > maxLength);
}

function clearContainer(containerId) {
    const container = document.getElementById(containerId);
    if (container) container.innerHTML = '';
}

async function postJson(url, payload) {
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    const json = await response.json().catch(() => ({}));
    return { ok: response.ok, json };
}

function renderHeadersResponse(data) {
    document.getElementById('h1Output').textContent = data.h1 || '';
    clearContainer('h2Container');
    clearContainer('h3Container');

    (data.h2 || []).forEach(item => {
        const card = document.createElement('div');
        card.className = 'output-card';
        card.innerHTML = `
            <div class="output-text">${item}</div>
            <button type="button" class="copy-btn">📋 Copy</button>
        `;
        card.querySelector('button').addEventListener('click', () => copyText(item, 'H2'));
        document.getElementById('h2Container').appendChild(card);
    });

    (data.h3 || []).forEach(item => {
        const card = document.createElement('div');
        card.className = 'output-card';
        card.innerHTML = `
            <div class="output-text">${item}</div>
            <button type="button" class="copy-btn">📋 Copy</button>
        `;
        card.querySelector('button').addEventListener('click', () => copyText(item, 'H3'));
        document.getElementById('h3Container').appendChild(card);
    });
}

function renderFaqsResponse(data) {
    const container = document.getElementById('faqsContainer');
    if (!container) return;
    container.innerHTML = '';

    (data.faqs || []).forEach(faq => {
        const card = document.createElement('div');
        card.className = 'output-card';
        card.innerHTML = `
            <div class="output-label">${faq.question}</div>
            <div class="output-text">${faq.answer}</div>
            <button type="button" class="copy-btn">📋 Copy</button>
        `;
        card.querySelector('button').addEventListener('click', () => copyText(`${faq.question}\n${faq.answer}`, 'FAQ'));
        container.appendChild(card);
    });
}

function renderAuditResponse(data) {
    const container = document.getElementById('auditResults');
    if (!container) return;
    container.innerHTML = '';

    function appendCard(title, html) {
        const card = document.createElement('div');
        card.className = 'output-card';
        card.innerHTML = `
            <div class="output-label">${title}</div>
            <div class="output-text">${html}</div>
        `;
        container.appendChild(card);
    }

    if (typeof data.score === 'number') {
        const scoreBadgeColor = data.score >= 80 ? '#4CAF50' : data.score >= 60 ? '#FF9800' : '#FF0000';
        appendCard('Overall SEO Score', `<span style="font-size: 24px; font-weight: bold; color: ${scoreBadgeColor};">${data.score}/100</span>`);
    }

    if (Array.isArray(data.issues) && data.issues.length) {
        const problemsList = data.issues.map((item, idx) => `<div style="margin-bottom: 8px; padding: 8px; background: #fff; border-left: 3px solid #FF0000; border-radius: 4px;"><strong>${idx + 1}.</strong> ${item}</div>`).join('');
        appendCard('⚠️ Problems Found', problemsList);
    } else {
        appendCard('✅ Great!', '<div>No major issues detected. Your website SEO looks good!</div>');
    }

    if (data.header_hierarchy && data.header_hierarchy.issues && data.header_hierarchy.issues.length) {
        const headerIssues = data.header_hierarchy.issues.map(issue => `<div style="margin-bottom: 6px;">• ${issue}</div>`).join('');
        appendCard('Header Hierarchy Issues', headerIssues);
    }

    if (data.image_analysis && (data.image_analysis.missing_alt > 0 || data.image_analysis.missing_title > 0)) {
        const imgIssues = [];
        if (data.image_analysis.missing_alt > 0) imgIssues.push(`${data.image_analysis.missing_alt} image(s) missing alt text`);
        if (data.image_analysis.missing_title > 0) imgIssues.push(`${data.image_analysis.missing_title} image(s) missing title attribute`);
        const detailList = imgIssues.map(issue => `<div style="margin-bottom: 6px;">• ${issue}</div>`).join('');
        appendCard('Image Attribute Issues', detailList);
    }

    if (data.metadata_analysis && data.metadata_analysis.issues && data.metadata_analysis.issues.length) {
        const metaIssues = data.metadata_analysis.issues.map(issue => `<div style="margin-bottom: 6px;">• ${issue}</div>`).join('');
        appendCard('Metadata Issues', metaIssues);
    }

    if (data.keyword_analysis && data.keyword_analysis.issues && data.keyword_analysis.issues.length) {
        const keywordIssues = data.keyword_analysis.issues.map(issue => `<div style="margin-bottom: 6px;">• ${issue}</div>`).join('');
        appendCard('Keyword Issues', keywordIssues);
    }

    if (Array.isArray(data.schema_blocks) && data.schema_blocks.length) {
        const schemaList = data.schema_blocks.map(block => `<div style="margin-bottom: 12px;"><strong>Type:</strong> ${block.type || 'Unknown'}<pre style="white-space: pre-wrap; word-break: break-word; background:#fff; padding:8px; border:1px solid #ddd; border-radius:8px; margin-top:8px; font-size:12px;">${JSON.stringify(block.raw, null, 2)}</pre></div>`).join('');
        appendCard('Schema Markup Found', schemaList);
    } else {
        appendCard('Schema Markup', '<div>No schema JSON-LD markup detected. Consider adding schema.org markup for better search visibility.</div>');
    }

    if (Array.isArray(data.recommendations) && data.recommendations.length) {
        const recsList = data.recommendations.map((item, idx) => `<div style="margin-bottom: 8px; padding: 8px; background: #E8F5E9; border-left: 3px solid #4CAF50; border-radius: 4px;"><strong>${idx + 1}.</strong> ${item}</div>`).join('');
        appendCard('Recommendations', recsList);
    }
}

function initForms() {
    const metadataForm = document.getElementById('metadataForm');
    if (metadataForm) {
        metadataForm.addEventListener('submit', async event => {
            event.preventDefault();
            hideMessage('metadata');

            const payload = {
                pageType: document.getElementById('pageType')?.value || '',
                courseName: document.getElementById('courseName')?.value || '',
                primaryKeyword: document.getElementById('primaryKeyword')?.value || '',
                brand: document.getElementById('brand')?.value || '',
                highlights: document.getElementById('highlights')?.value || ''
            };

            showMessage('metadata', 'Generating metadata...', 'info');
            const { ok, json } = await postJson(API_ROUTES.metadata, payload);
            if (ok) {
                document.getElementById('titleOutput').textContent = json.title || '';
                document.getElementById('metaOutput').textContent = json.metaDescription || '';
                updateCharCount(json.title || '', 'titleBadge', 60);
                updateCharCount(json.metaDescription || '', 'metaBadge', 160);
                document.getElementById('metadataOutput').style.display = 'block';
                showMessage('metadata', 'Metadata generated successfully!', 'success');
            } else {
                showMessage('metadata', json.detail || json.error || 'Failed to generate metadata.', 'error');
            }
        });
    }

    const headersForm = document.getElementById('headersForm');
    if (headersForm) {
        headersForm.addEventListener('submit', async event => {
            event.preventDefault();
            hideMessage('headers');
            document.getElementById('h1Output').textContent = '';
            clearContainer('h2Container');
            clearContainer('h3Container');

            const payload = {
                count: Number(document.getElementById('headersCount')?.value || 5),
                pageType: document.getElementById('headersPageType')?.value || '',
                courseName: document.getElementById('headersCourseName')?.value || '',
                primaryKeyword: document.getElementById('headersPrimaryKeyword')?.value || '',
                brand: document.getElementById('headersBrand')?.value || '',
                highlights: document.getElementById('headersHighlights')?.value || ''
            };

            showMessage('headers', 'Generating headers...', 'info');
            const { ok, json } = await postJson(API_ROUTES.headers, payload);
            if (ok) {
                renderHeadersResponse(json);
                document.getElementById('headersOutput').style.display = 'block';
                showMessage('headers', 'Headers generated successfully!', 'success');
            } else {
                showMessage('headers', json.detail || json.error || 'Failed to generate headers.', 'error');
            }
        });
    }

    const faqsForm = document.getElementById('faqsForm');
    if (faqsForm) {
        faqsForm.addEventListener('submit', async event => {
            event.preventDefault();
            hideMessage('faqs');
            clearContainer('faqsContainer');

            const payload = {
                count: Number(document.getElementById('faqsCount')?.value || 5),
                pageType: document.getElementById('faqsPageType')?.value || '',
                courseName: document.getElementById('faqsCourseName')?.value || '',
                primaryKeyword: document.getElementById('faqsPrimaryKeyword')?.value || '',
                brand: document.getElementById('faqsBrand')?.value || '',
                highlights: document.getElementById('faqsHighlights')?.value || ''
            };

            showMessage('faqs', 'Generating FAQs...', 'info');
            const { ok, json } = await postJson(API_ROUTES.faqs, payload);
            if (ok) {
                renderFaqsResponse(json);
                document.getElementById('faqsOutput').style.display = 'block';
                showMessage('faqs', 'FAQs generated successfully!', 'success');
            } else {
                showMessage('faqs', json.detail || json.error || 'Failed to generate FAQs.', 'error');
            }
        });
    }

    const auditForm = document.getElementById('auditForm');
    if (auditForm) {
        auditForm.addEventListener('submit', async event => {
            event.preventDefault();
            hideMessage('audit');
            clearContainer('auditResults');

            const payload = {
                content: document.getElementById('auditContent')?.value || ''
            };

            showMessage('audit', 'Running SEO audit...', 'info');
            const { ok, json } = await postJson(API_ROUTES.audit, payload);
            if (ok) {
                renderAuditResponse(json);
                document.getElementById('auditOutput').style.display = 'block';
                showMessage('audit', 'SEO audit completed!', 'success');
            } else {
                showMessage('audit', json.detail || json.error || 'Failed to run audit.', 'error');
            }
        });
    }
}

function initTabs() {
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => setActiveTab(button.dataset.tab));
    });
}

function initPage() {
    initTabs();
    initForms();
    document.querySelectorAll('.output-section').forEach(section => {
        section.style.display = 'none';
    });
    setActiveTab('metadata');
}

window.addEventListener('DOMContentLoaded', initPage);

