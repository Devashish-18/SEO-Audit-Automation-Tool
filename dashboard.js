// ============================================================================
// SEO AUDIT DASHBOARD JAVASCRIPT
// ============================================================================

const dashboardState = {
    currentModule: 'siteAudit'
};

window.addEventListener('DOMContentLoaded', () => {
    initializeDashboardNavigation();
    initializeForms();
    switchModule(dashboardState.currentModule);
});

function initializeDashboardNavigation() {
    document.querySelectorAll('.nav-item[data-module]').forEach(item => {
        item.addEventListener('click', event => {
            event.preventDefault();
            switchModule(item.dataset.module);
        });
    });
}

function initializeNavigation() {
    initializeDashboardNavigation();
}

function switchModule(moduleName) {
    dashboardState.currentModule = moduleName;

    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.module === moduleName);
    });

    document.querySelectorAll('.module-content').forEach(content => {
        const isActive = content.id === moduleName;
        content.classList.toggle('active', isActive);
        content.classList.toggle('hidden', !isActive);
    });

    const titleMap = {
        siteAudit: 'Site Audit',
        headerHierarchy: 'Generate Headers',
        imageSEO: 'Image SEO Audit',
        metadata: 'Generate Metadata',
        schema: 'Schema Markup Audit',
        keywordAnalysis: 'Keyword Analysis',
        keywordResearch: 'Keyword Research',
        rankTracker: 'Rank Tracker Setup',
        contentGaps: 'Content Gap Analysis',
        competitor: 'Competitor Analysis',
        backlinks: 'Backlink Analysis',
        mentions: 'Generate FAQs',
        marketing: 'Generate Blog Post',
        report: 'Generate Comprehensive Report'
    };

    const subtitleMap = {
        siteAudit: 'Perform comprehensive technical SEO analysis',
        headerHierarchy: 'Create strong header structure for your page',
        imageSEO: 'Audit image tags, alt text, and load performance',
        metadata: 'Generate powerful page titles and meta descriptions',
        schema: 'Check for schema markup and structured data',
        keywordAnalysis: 'Analyze keyword relevance and usage',
        keywordResearch: 'Discover keyword opportunities',
        rankTracker: 'Set up keyword tracking for your domain',
        contentGaps: 'Identify gaps in your content against competitors',
        competitor: 'Compare your site with competitor sites',
        backlinks: 'Review backlink quality and authority',
        mentions: 'Create FAQs tailored to your page',
        marketing: 'Generate blog content from your inputs',
        report: 'Build a deep SEO report for your domain'
    };

    const pageTitle = document.getElementById('pageTitle');
    const pageSubtitle = document.getElementById('pageSubtitle');
    if (pageTitle) {
        pageTitle.textContent = titleMap[moduleName] || 'SEO Dashboard';
    }
    if (pageSubtitle) {
        pageSubtitle.textContent = subtitleMap[moduleName] || 'Manage your SEO tools and reports';
    }
}

function initializeForms() {
    const formActions = [
        ['siteAuditForm', performSiteAudit],
        ['headerHierarchyForm', generateHeaders],
        ['imageSeoForm', auditImageSEO],
        ['metadataAuditForm', generateMetadata],
        ['schemaForm', auditSchema],
        ['keywordAnalysisForm', analyzeKeywords],
        ['keywordResearchForm', performKeywordResearch],
        ['rankTrackerForm', setupRankTracker],
        ['contentGapForm', analyzeContentGaps],
        ['competitorForm', analyzeCompetitor],
        ['backlinksForm', auditBacklinks],
        ['brandMentionsForm', generateFAQs],
        ['marketingPlanForm', generateBlog],
        ['reportForm', generateReport]
    ];

    formActions.forEach(([id, handler]) => {
        const form = document.getElementById(id);
        if (form) {
            form.addEventListener('submit', async event => {
                event.preventDefault();
                await handler(event);
            });
        }
    });
}

function showMessage(elementId, message, type = 'info') {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.textContent = message;
    el.className = `message show ${type}`;
    if (type === 'success') {
        setTimeout(() => el.classList.remove('show'), 4000);
    }
}

function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value;
    return div.innerHTML;
}

function getTextAreaLines(id) {
    const element = document.getElementById(id);
    if (!element) return [];
    return element.value
        .split(/\r?\n/)
        .map(line => line.trim())
        .filter(line => line.length > 0);
}

function generateProgressBadge(value) {
    if (value >= 80) return '<span class="badge success">Excellent</span>';
    if (value >= 60) return '<span class="badge warning">Fair</span>';
    return '<span class="badge error">Poor</span>';
}

// ---------------------------------------------------------------------------
// MODULE 1: Site Audit
// ---------------------------------------------------------------------------

async function performSiteAudit() {
    const url = document.getElementById('auditUrl').value.trim();
    const scope = document.getElementById('crawlScope').value;
    const pages = parseInt(document.getElementById('pagesToCrawl').value, 10) || 0;

    if (!url) {
        showMessage('siteAuditMessage', 'Please enter a URL for the audit.', 'error');
        return;
    }

    showMessage('siteAuditMessage', '🔄 Running site audit...', 'info');
    await new Promise(resolve => setTimeout(resolve, 800));

    const results = generateSiteAuditData(url, scope, pages);
    displaySiteAuditResults(results);
    showMessage('siteAuditMessage', '✅ Site audit completed.', 'success');
}

function generateSiteAuditData(url, scope, pages) {
    const issues = [
        { type: 'critical', title: 'Missing H1 tag', count: 12, description: 'Important pages have no H1 heading.' },
        { type: 'critical', title: 'Duplicate meta descriptions', count: 8, description: 'Multiple pages use identical meta descriptions.' },
        { type: 'warning', title: 'Images missing alt text', count: 18, description: 'Several images lack accessible alt text.' },
        { type: 'warning', title: 'Slow page load', count: 14, description: 'Pages with rendering speed more than 3 seconds.' },
        { type: 'notice', title: 'Missing canonical links', count: 21, description: 'Canonical tags are absent on pages.' }
    ];
    const criticalCount = issues.filter(i => i.type === 'critical').length;
    const warningCount = issues.filter(i => i.type === 'warning').length;
    const noticeCount = issues.filter(i => i.type === 'notice').length;
    const score = Math.max(25, 100 - (criticalCount * 15 + warningCount * 8 + noticeCount * 3));

    return {
        url,
        scope,
        pagesScanned: pages || 50,
        score,
        criticalCount,
        warningCount,
        noticeCount,
        issues,
        date: new Date().toLocaleDateString()
    };
}

function displaySiteAuditResults(data) {
    const target = document.getElementById('siteAuditResults');
    if (!target) return;

    const scoreColor = data.score >= 80 ? '#4CAF50' : data.score >= 60 ? '#FF9800' : '#FF0000';
    const scoreLabel = data.score >= 80 ? 'Excellent' : data.score >= 60 ? 'Fair' : 'Poor';

    let html = `
        <div class="stats-grid">
            <div class="stat-card" style="border-left-color: ${scoreColor};">
                <div class="stat-value" style="color: ${scoreColor};">${data.score}</div>
                <div class="stat-label">Site Health</div>
                <div style="font-size: 12px; color: #777; margin-top: 8px;">${scoreLabel}</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${data.pagesScanned}</div>
                <div class="stat-label">Pages Scanned</div>
            </div>
            <div class="stat-card" style="border-left-color: #FF0000;">
                <div class="stat-value" style="color: #FF0000;">${data.criticalCount}</div>
                <div class="stat-label">Critical Issues</div>
            </div>
            <div class="stat-card" style="border-left-color: #FF9800;">
                <div class="stat-value" style="color: #FF9800;">${data.warningCount}</div>
                <div class="stat-label">Warnings</div>
            </div>
        </div>
    `;

    html += `
        <div class="card">
            <div class="card-title">Issue Breakdown</div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Severity</th>
                            <th>Issue</th>
                            <th>Pages</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
    `;

    data.issues.forEach(issue => {
        const badgeColor = issue.type === 'critical' ? '#FF0000' : issue.type === 'warning' ? '#FF9800' : '#0096FF';
        html += `
            <tr>
                <td><span class="badge" style="background: ${badgeColor}20; color: ${badgeColor}; border: 1px solid ${badgeColor};">${issue.type.toUpperCase()}</span></td>
                <td>${escapeHtml(issue.title)}</td>
                <td>${issue.count}</td>
                <td>${escapeHtml(issue.description)}</td>
            </tr>
        `;
    });

    html += `</tbody></table></div></div>`;
    target.innerHTML = html;
}

// ---------------------------------------------------------------------------
// MODULE 2: Header Hierarchy
// ---------------------------------------------------------------------------

async function analyzeHeaderHierarchy() {
    const url = document.getElementById('headerUrl').value.trim();
    if (!url) {
        showMessage('headerMessage', 'Please enter a URL to analyze.', 'error');
        return;
    }

    showMessage('headerMessage', '🔄 Analyzing header hierarchy...', 'info');
    await new Promise(resolve => setTimeout(resolve, 700));

    const data = {
        headers: {
            h1: ['Professional SEO Audit Services'],
            h2: ['Technical SEO', 'Content Strategy', 'Backlink Monitoring'],
            h3: ['Page Speed Suggestions', 'Schema Validation', 'Keyword Placement']
        },
        issues: [
            { severity: 'warning', message: 'Multiple H1 tags found on internal pages.' },
            { severity: 'notice', message: 'Some H2 tags are identical across pages.' }
        ]
    };

    displayHeaderResults(data);
    showMessage('headerMessage', '✅ Header structure reviewed.', 'success');
}

function displayHeaderResults(data) {
    const target = document.getElementById('headerResults');
    if (!target) return;

    let html = `<div class="card"><div class="card-title">Header Overview</div><div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px;">`;

    ['h1', 'h2', 'h3'].forEach(level => {
        html += `<div style="background: #F8FAFF; padding: 15px; border-radius: 12px;"><strong>${level.toUpperCase()} Tags</strong><ul style="margin-top: 12px; font-size: 13px; line-height: 1.6;">`;
        data.headers[level].forEach(text => {
            html += `<li>${escapeHtml(text)}</li>`;
        });
        html += `</ul></div>`;
    });

    html += `</div></div>`;
    if (data.issues.length) {
        html += `<div class="card"><div class="card-title">Header Issues</div>`;
        data.issues.forEach(issue => {
            const color = issue.severity === 'warning' ? '#FF9800' : '#0096FF';
            html += `<div style="padding: 12px; margin-top: 12px; border-left: 4px solid ${color}; background: #FFF;">${escapeHtml(issue.message)}</div>`;
        });
        html += `</div>`;
    }

    target.innerHTML = html;
}

// ---------------------------------------------------------------------------
// MODULE 3: Image SEO
// ---------------------------------------------------------------------------

async function auditImageSEO() {
    const url = document.getElementById('imageUrl').value.trim();
    if (!url) {
        showMessage('imageMessage', 'Please enter a URL to audit images.', 'error');
        return;
    }

    showMessage('imageMessage', '🔄 Auditing image SEO...', 'info');
    await new Promise(resolve => setTimeout(resolve, 800));

    const images = [
        { src: 'hero.jpg', alt: 'Landing page hero image', status: 'Optimized', size: '240KB' },
        { src: 'feature.png', alt: '', status: 'Missing Alt', size: '180KB' },
        { src: 'team.jpg', alt: 'Company team photo', status: 'Optimized', size: '420KB' }
    ];

    displayImageResults(images);
    showMessage('imageMessage', '✅ Image SEO audit complete.', 'success');
}

function displayImageResults(images) {
    const target = document.getElementById('imageResults');
    if (!target) return;

    const total = images.length;
    const missingAlt = images.filter(img => !img.alt).length;
    const optimized = images.filter(img => img.status === 'Optimized').length;

    let html = `
        <div class="stats-grid">
            <div class="stat-card"><div class="stat-value">${total}</div><div class="stat-label">Images</div></div>
            <div class="stat-card" style="border-left-color: #4CAF50;"><div class="stat-value" style="color: #4CAF50;">${optimized}</div><div class="stat-label">Optimized</div></div>
            <div class="stat-card" style="border-left-color: #FF0000;"><div class="stat-value" style="color: #FF0000;">${missingAlt}</div><div class="stat-label">Missing Alt</div></div>
        </div>
        <div class="card"><div class="card-title">Image Details</div><div class="table-container"><table><thead><tr><th>Image</th><th>Alt Text</th><th>Status</th><th>Size</th></tr></thead><tbody>`;

    images.forEach(img => {
        const badgeColor = img.status === 'Optimized' ? '#4CAF50' : '#FF0000';
        html += `<tr><td><code style="font-size: 11px;">${escapeHtml(img.src)}</code></td><td>${escapeHtml(img.alt || 'Missing')}</td><td><span class="badge" style="background: ${badgeColor}20; color: ${badgeColor}; border: 1px solid ${badgeColor};">${img.status}</span></td><td>${img.size}</td></tr>`;
    });

    html += '</tbody></table></div></div>';
    target.innerHTML = html;
}

// ---------------------------------------------------------------------------
// MODULE 4: Metadata Audit
// ---------------------------------------------------------------------------

async function auditMetadata() {
    const url = document.getElementById('metadataUrl').value.trim();
    if (!url) {
        showMessage('metadataMessage', 'Please enter a URL for metadata audit.', 'error');
        return;
    }

    showMessage('metadataMessage', '🔄 Auditing metadata...', 'info');
    await new Promise(resolve => setTimeout(resolve, 800));

    const metadata = {
        title: 'Professional SEO Services | Example Company',
        description: 'Custom SEO audits and optimization for businesses that want measurable traffic growth.',
        canonical: 'https://example.com',
        openGraph: true,
        twitterCard: true,
        robots: 'index, follow'
    };

    displayMetadataResults(metadata);
    showMessage('metadataMessage', '✅ Metadata audit complete.', 'success');
}

function displayMetadataResults(metadata) {
    const target = document.getElementById('metadataResults');
    if (!target) return;

    let html = `<div class="card"><div class="card-title">Metadata Summary</div><div style="margin-top: 18px;">`;
    html += buildMetadataRow('Title Tag', metadata.title, metadata.title.length, metadata.title.length >= 50 && metadata.title.length <= 60);
    html += buildMetadataRow('Meta Description', metadata.description, metadata.description.length, metadata.description.length >= 140 && metadata.description.length <= 160);
    html += buildMetadataRow('Canonical URL', metadata.canonical, null, Boolean(metadata.canonical));
    html += buildMetadataRow('Open Graph', metadata.openGraph ? 'Present' : 'Missing', null, metadata.openGraph);
    html += buildMetadataRow('Twitter Card', metadata.twitterCard ? 'Present' : 'Missing', null, metadata.twitterCard);
    html += buildMetadataRow('Robots Tag', metadata.robots, null, Boolean(metadata.robots));
    html += '</div></div>';

    target.innerHTML = html;
}

function buildMetadataRow(label, value, length, ok) {
    return `<div style="padding: 12px; margin-top: 12px; background: #F8FAFF; border-left: 4px solid ${ok ? '#4CAF50' : '#FF9800'}; border-radius: 10px;">
        <div style="font-weight: 600;">${label}</div>
        <div style="font-size: 13px; color: #444; margin-top: 6px;">${escapeHtml(String(value))}</div>
        ${length !== null ? `<div style="font-size: 12px; color: #777; margin-top: 6px;">Length: ${length} chars</div>` : ''}
    </div>`;
}

// ---------------------------------------------------------------------------
// MODULE 5: Schema Markup
// ---------------------------------------------------------------------------

async function auditSchema() {
    const url = document.getElementById('schemaUrl').value.trim();
    if (!url) {
        showMessage('schemaMessage', 'Please enter a URL for schema audit.', 'error');
        return;
    }

    showMessage('schemaMessage', '🔄 Auditing schema markup...', 'info');
    await new Promise(resolve => setTimeout(resolve, 900));

    const schema = {
        count: 2,
        items: [
            { type: 'BreadcrumbList', valid: true },
            { type: 'Organization', valid: true }
        ]
    };

    displaySchemaResults(schema);
    showMessage('schemaMessage', '✅ Schema audit complete.', 'success');
}

function displaySchemaResults(schema) {
    const target = document.getElementById('schemaResults');
    if (!target) return;

    let html = `<div class="card"><div class="card-title">Schema Markup Found</div><div style="margin-top: 18px;">`;
    schema.items.forEach(item => {
        html += `<div style="padding: 12px; margin-top: 12px; background: #F8FAFF; border-left: 4px solid ${item.valid ? '#4CAF50' : '#FF0000'}; border-radius: 10px;">`;
        html += `<div style="font-weight: 600;">${item.type}</div>`;
        html += `<div style="font-size: 13px; color: #555; margin-top: 6px;">Status: ${item.valid ? 'Valid' : 'Needs Review'}</div>`;
        html += '</div>';
    });
    html += '</div></div>';
    target.innerHTML = html;
}

// ---------------------------------------------------------------------------
// MODULE 6: Keyword Analysis
// ---------------------------------------------------------------------------

async function analyzeKeywords() {
    const url = document.getElementById('keywordAnalysisUrl').value.trim();
    const keyword = document.getElementById('primaryKeywordInput').value.trim();

    if (!url || !keyword) {
        showMessage('keywordAnalysisMessage', 'Please enter URL and keyword.', 'error');
        return;
    }

    showMessage('keywordAnalysisMessage', '🔄 Analyzing keyword placement...', 'info');
    await new Promise(resolve => setTimeout(resolve, 900));

    const analysis = {
        keyword,
        density: (Math.random() * 2 + 0.7).toFixed(2),
        placements: ['Title', 'H1', 'Body', 'Meta Description'],
        occurrences: Math.floor(Math.random() * 8) + 3
    };

    displayKeywordAnalysis(analysis);
    showMessage('keywordAnalysisMessage', '✅ Keyword analysis complete.', 'success');
}

function displayKeywordAnalysis(data) {
    const target = document.getElementById('keywordAnalysisResults');
    if (!target) return;

    let html = `<div class="stats-grid">
        <div class="stat-card"><div class="stat-value">${data.density}%</div><div class="stat-label">Keyword Density</div></div>
        <div class="stat-card"><div class="stat-value">${data.occurrences}</div><div class="stat-label">Occurrences</div></div>
    </div>
    <div class="card"><div class="card-title">Keyword Placement</div><ul style="margin-top: 12px; font-size: 13px; line-height: 1.7;">`;
    data.placements.forEach(place => {
        html += `<li>${escapeHtml(place)}</li>`;
    });
    html += '</ul></div>';
    target.innerHTML = html;
}

// ---------------------------------------------------------------------------
// MODULE 7: Keyword Research
// ---------------------------------------------------------------------------

async function performKeywordResearch() {
    const seed = document.getElementById('seedKeyword').value.trim();
    if (!seed) {
        showMessage('keywordResearchMessage', 'Please enter a seed keyword.', 'error');
        return;
    }

    showMessage('keywordResearchMessage', '🔄 Generating keyword ideas...', 'info');
    await new Promise(resolve => setTimeout(resolve, 1000));

    const results = generateKeywordSuggestions(seed);
    displayKeywordResearch(results);
    showMessage('keywordResearchMessage', '✅ Keyword research complete.', 'success');
}

function generateKeywordSuggestions(seed) {
    const intents = ['Informational', 'Transactional', 'Commercial'];
    return [
        `${seed} best practices`,
        `how to ${seed}`,
        `${seed} services`,
        `top ${seed} tips`,
        `${seed} strategy`
    ].map((keyword, index) => ({
        keyword,
        volume: Math.floor(Math.random() * 9000) + 500,
        difficulty: Math.floor(Math.random() * 80) + 10,
        intent: intents[index % intents.length]
    }));
}

function displayKeywordResearch(items) {
    const target = document.getElementById('keywordResearchResults');
    if (!target) return;

    let html = `<div class="card"><div class="card-title">Keyword Suggestions</div><div class="table-container"><table><thead><tr><th>Keyword</th><th>Volume</th><th>Difficulty</th><th>Intent</th></tr></thead><tbody>`;
    items.forEach(item => {
        const color = item.difficulty < 40 ? '#4CAF50' : item.difficulty < 65 ? '#FF9800' : '#FF0000';
        html += `<tr><td>${escapeHtml(item.keyword)}</td><td>${item.volume.toLocaleString()}</td><td><span class="badge" style="background: ${color}20; color: ${color}; border: 1px solid ${color};">${item.difficulty}</span></td><td>${escapeHtml(item.intent)}</td></tr>`;
    });
    html += '</tbody></table></div></div>';
    target.innerHTML = html;
}

// ---------------------------------------------------------------------------
// MODULE 8: Rank Tracker
// ---------------------------------------------------------------------------

async function setupRankTracker() {
    const domain = document.getElementById('trackerDomain').value.trim();
    const keywords = getTextAreaLines('trackingKeywords');

    if (!domain || keywords.length === 0) {
        showMessage('rankTrackerMessage', 'Please enter domain and keywords.', 'error');
        return;
    }

    showMessage('rankTrackerMessage', '🔄 Generating rank tracking data...', 'info');
    await new Promise(resolve => setTimeout(resolve, 1000));

    const data = keywords.map(keyword => ({
        keyword,
        currentRank: Math.floor(Math.random() * 40) + 1,
        trend: Math.random() > 0.5 ? 'up' : 'down'
    }));

    displayRankTracker(data, domain);
    showMessage('rankTrackerMessage', '✅ Rank tracker is ready.', 'success');
}

function displayRankTracker(rows, domain) {
    const target = document.getElementById('rankTrackerResults');
    if (!target) return;

    let html = `<div class="card"><div class="card-title">Ranking Overview for ${escapeHtml(domain)}</div><div class="table-container"><table><thead><tr><th>Keyword</th><th>Current Rank</th><th>Trend</th></tr></thead><tbody>`;
    rows.forEach(row => {
        const trendColor = row.trend === 'up' ? '#4CAF50' : '#FF0000';
        html += `<tr><td>${escapeHtml(row.keyword)}</td><td>#${row.currentRank}</td><td><span class="badge" style="background: ${trendColor}20; color: ${trendColor}; border: 1px solid ${trendColor};">${row.trend.toUpperCase()}</span></td></tr>`;
    });
    html += '</tbody></table></div></div>';
    target.innerHTML = html;
}

// ---------------------------------------------------------------------------
// MODULE 9: Content Gap Analysis
// ---------------------------------------------------------------------------

async function analyzeContentGaps() {
    const domain = document.getElementById('gapDomain').value.trim();
    const competitors = getTextAreaLines('competitorDomains');

    if (!domain || competitors.length === 0) {
        showMessage('contentGapMessage', 'Enter your domain and at least one competitor domain.', 'error');
        return;
    }

    showMessage('contentGapMessage', '🔄 Identifying content gaps...', 'info');
    await new Promise(resolve => setTimeout(resolve, 1000));

    const gaps = [
        { keyword: 'SEO optimization strategy', volume: 1700, priority: 'High' },
        { keyword: 'website performance checklist', volume: 1200, priority: 'Medium' },
        { keyword: 'content gap analysis tool', volume: 900, priority: 'High' }
    ];

    displayContentGaps(gaps);
    showMessage('contentGapMessage', '✅ Content gap analysis complete.', 'success');
}

function displayContentGaps(gaps) {
    const target = document.getElementById('contentGapResults');
    if (!target) return;

    let html = `<div class="stats-grid"><div class="stat-card"><div class="stat-value">${gaps.length}</div><div class="stat-label">Opportunities</div></div><div class="stat-card" style="border-left-color: #FF9800;"><div class="stat-value" style="color: #FF9800;">${gaps.filter(g => g.priority === 'High').length}</div><div class="stat-label">High Priority</div></div></div>`;
    html += `<div class="card"><div class="card-title">Gap Opportunities</div><div class="table-container"><table><thead><tr><th>Keyword</th><th>Volume</th><th>Priority</th></tr></thead><tbody>`;
    gaps.forEach(gap => {
        const color = gap.priority === 'High' ? '#FF0000' : '#FF9800';
        html += `<tr><td>${escapeHtml(gap.keyword)}</td><td>${gap.volume.toLocaleString()}</td><td><span class="badge" style="background: ${color}20; color: ${color}; border: 1px solid ${color};">${gap.priority}</span></td></tr>`;
    });
    html += '</tbody></table></div></div>';
    target.innerHTML = html;
}

// ---------------------------------------------------------------------------
// MODULE 10: Competitor Analysis
// ---------------------------------------------------------------------------

async function analyzeCompetitor() {
    const url = document.getElementById('competitorUrl').value.trim();
    if (!url) {
        showMessage('competitorMessage', 'Please enter a competitor URL.', 'error');
        return;
    }

    showMessage('competitorMessage', '🔄 Analyzing competitor...', 'info');
    await new Promise(resolve => setTimeout(resolve, 900));

    const data = {
        domain: url,
        traffic: Math.floor(Math.random() * 180000) + 25000,
        topKeywords: 26,
        backlinks: Math.floor(Math.random() * 4800) + 1200,
        keywordList: [
            { keyword: 'seo audit tools', rank: 3 },
            { keyword: 'technical seo checklist', rank: 5 },
            { keyword: 'content optimization services', rank: 8 }
        ]
    };

    displayCompetitorAnalysis(data);
    showMessage('competitorMessage', '✅ Competitor analysis complete.', 'success');
}

function displayCompetitorAnalysis(data) {
    const target = document.getElementById('competitorResults');
    if (!target) return;

    let html = `<div class="stats-grid"><div class="stat-card"><div class="stat-value">${Math.round(data.traffic / 1000)}K</div><div class="stat-label">Estimated Traffic</div></div><div class="stat-card"><div class="stat-value">${data.topKeywords}</div><div class="stat-label">Ranked Keywords</div></div><div class="stat-card"><div class="stat-value">${data.backlinks}</div><div class="stat-label">Backlinks</div></div></div>`;
    html += `<div class="card"><div class="card-title">Top Competitor Keywords</div><div class="table-container"><table><thead><tr><th>Keyword</th><th>Rank</th></tr></thead><tbody>`;
    data.keywordList.forEach(item => {
        html += `<tr><td>${escapeHtml(item.keyword)}</td><td>#${item.rank}</td></tr>`;
    });
    html += '</tbody></table></div></div>';
    target.innerHTML = html;
}

// ---------------------------------------------------------------------------
// MODULE 11: Backlinks Monitor
// ---------------------------------------------------------------------------

async function auditBacklinks() {
    const url = document.getElementById('backlinksUrl').value.trim();
    if (!url) {
        showMessage('backlinksMessage', 'Please enter a domain.', 'error');
        return;
    }

    showMessage('backlinksMessage', '🔄 Auditing backlinks...', 'info');
    await new Promise(resolve => setTimeout(resolve, 900));

    const backlinks = [
        { source: 'blog.example.com', anchor: 'SEO audit', type: 'Dofollow', da: 54, date: '2024-05-02' },
        { source: 'news.example.com', anchor: 'website optimization', type: 'Nofollow', da: 38, date: '2024-04-28' },
        { source: 'community.example.com', anchor: 'organic traffic', type: 'Dofollow', da: 45, date: '2024-04-20' }
    ];

    displayBacklinkResults(backlinks);
    showMessage('backlinksMessage', '✅ Backlink audit complete.', 'success');
}

function displayBacklinkResults(backlinks) {
    const target = document.getElementById('backlinksResults');
    if (!target) return;

    let html = `<div class="card"><div class="card-title">Backlinks Summary</div><div class="table-container"><table><thead><tr><th>Source</th><th>Anchor</th><th>Type</th><th>DA</th><th>Date</th></tr></thead><tbody>`;
    backlinks.forEach(link => {
        const color = link.type === 'Dofollow' ? '#4CAF50' : '#FF9800';
        html += `<tr><td><code style="font-size: 11px;">${escapeHtml(link.source)}</code></td><td>${escapeHtml(link.anchor)}</td><td><span class="badge" style="background: ${color}20; color: ${color}; border: 1px solid ${color};">${link.type}</span></td><td>${link.da}</td><td>${link.date}</td></tr>`;
    });
    html += '</tbody></table></div></div>';
    target.innerHTML = html;
}

// ---------------------------------------------------------------------------
// MODULE 12: Brand Mentions
// ---------------------------------------------------------------------------

async function monitorBrandMentions() {
    const brand = document.getElementById('brandName').value.trim();
    if (!brand) {
        showMessage('brandMentionsMessage', 'Please enter the brand name.', 'error');
        return;
    }

    showMessage('brandMentionsMessage', '🔄 Scanning brand mentions...', 'info');
    await new Promise(resolve => setTimeout(resolve, 900));

    const mentions = [
        { source: 'twitter.com', excerpt: 'Great SEO audit experience!', sentiment: 'positive', date: '2024-05-10' },
        { source: 'linkedin.com', excerpt: 'Helpful audit report for our website', sentiment: 'neutral', date: '2024-05-08' },
        { source: 'forum.example.com', excerpt: 'Site needs better content strategy', sentiment: 'negative', date: '2024-05-05' }
    ];

    displayBrandMentionResults(brand, mentions);
    showMessage('brandMentionsMessage', '✅ Brand mention monitoring complete.', 'success');
}

function displayBrandMentionResults(brand, mentions) {
    const target = document.getElementById('brandMentionsResults');
    if (!target) return;

    const positive = mentions.filter(m => m.sentiment === 'positive').length;
    const neutral = mentions.filter(m => m.sentiment === 'neutral').length;
    const negative = mentions.filter(m => m.sentiment === 'negative').length;

    let html = `<div class="stats-grid"><div class="stat-card"><div class="stat-value">${mentions.length}</div><div class="stat-label">Mentions for ${escapeHtml(brand)}</div></div><div class="stat-card" style="border-left-color: #4CAF50;"><div class="stat-value" style="color: #4CAF50;">${positive}</div><div class="stat-label">Positive</div></div><div class="stat-card" style="border-left-color: #FF9800;"><div class="stat-value" style="color: #FF9800;">${neutral}</div><div class="stat-label">Neutral</div></div><div class="stat-card" style="border-left-color: #FF0000;"><div class="stat-value" style="color: #FF0000;">${negative}</div><div class="stat-label">Negative</div></div></div>`;
    html += `<div class="card"><div class="card-title">Mention Details</div><div class="table-container"><table><thead><tr><th>Source</th><th>Excerpt</th><th>Sentiment</th><th>Date</th></tr></thead><tbody>`;
    mentions.forEach(mention => {
        const color = mention.sentiment === 'positive' ? '#4CAF50' : mention.sentiment === 'negative' ? '#FF0000' : '#FF9800';
        html += `<tr><td><code style="font-size: 11px;">${escapeHtml(mention.source)}</code></td><td>${escapeHtml(mention.excerpt)}</td><td><span class="badge" style="background: ${color}20; color: ${color}; border: 1px solid ${color};">${mention.sentiment}</span></td><td>${mention.date}</td></tr>`;
    });
    html += '</tbody></table></div></div>';
    target.innerHTML = html;
}

// ---------------------------------------------------------------------------
// MODULE 13: Marketing Plan
// ---------------------------------------------------------------------------

async function generateMarketingPlan() {
    const domain = document.getElementById('planDomain').value.trim();
    const duration = document.getElementById('planDuration').value;
    if (!domain) {
        showMessage('marketingPlanMessage', 'Please enter your domain.', 'error');
        return;
    }

    showMessage('marketingPlanMessage', '🔄 Building marketing plan...', 'info');
    await new Promise(resolve => setTimeout(resolve, 900));

    const plan = [
        { task: 'Improve page speed across the site', due: 'Week 1', category: 'Technical' },
        { task: 'Create 5 new keyword-focused blog posts', due: 'Week 2', category: 'Content' },
        { task: 'Build 10 high-quality backlinks', due: 'Week 4', category: 'Link Building' }
    ];

    displayMarketingPlan(domain, duration, plan);
    showMessage('marketingPlanMessage', '✅ Marketing plan generated.', 'success');
}

function displayMarketingPlan(domain, duration, plan) {
    const target = document.getElementById('marketingPlanResults');
    if (!target) return;

    let html = `<div class="card"><div class="card-title">${escapeHtml(domain)} - ${duration} Month Plan</div><div style="margin-top: 18px;">`;
    plan.forEach(item => {
        html += `<div style="padding: 14px; margin-top: 12px; background: #F8FAFF; border-left: 4px solid #0096FF; border-radius: 10px;"><strong>${escapeHtml(item.task)}</strong><div style="font-size: 12px; color: #555; margin-top: 6px;">Due: ${escapeHtml(item.due)} • ${escapeHtml(item.category)}</div></div>`;
    });
    html += '</div></div>';
    target.innerHTML = html;
}

// ---------------------------------------------------------------------------
// MODULE 14: Report Builder
// ---------------------------------------------------------------------------

async function generateReport() {
    const domain = document.getElementById('reportDomain').value.trim();
    if (!domain) {
        showMessage('reportMessage', 'Please enter a domain for the report.', 'error');
        return;
    }

    showMessage('reportMessage', '🔄 Generating report...', 'info');
    await new Promise(resolve => setTimeout(resolve, 1000));

    const report = {
        domain,
        date: new Date().toLocaleDateString(),
        siteScore: Math.floor(Math.random() * 25) + 75,
        findings: 14,
        actionItems: 7
    };

    displayReport(report);
    showMessage('reportMessage', '✅ Report generated.', 'success');
}

function displayReport(report) {
    const target = document.getElementById('reportResults');
    if (!target) return;

    const html = `<div class="card"><div class="card-title">${escapeHtml(report.domain)} Audit Report</div><div style="padding: 18px; line-height: 1.7;">` +
        `<div><strong>Date:</strong> ${escapeHtml(report.date)}</div>` +
        `<div><strong>Overall Score:</strong> ${report.siteScore}/100</div>` +
        `<div><strong>Key Findings:</strong> ${report.findings}</div>` +
        `<div><strong>Action Items:</strong> ${report.actionItems}</div>` +
        `<div style="margin-top: 18px;"><button class="btn-primary" onclick="alert('Download support coming soon')">📥 Download PDF</button></div>` +
        '</div></div>';

    target.innerHTML = html;
}

// ============================================================================
// CONTENT GENERATION FUNCTIONS - Metadata, Headers, FAQs, Blog
// ============================================================================

// Generate dynamic metadata based on input
async function generateMetadata(event) {
    event.preventDefault();
    
    const pageType = document.getElementById('metadataPageType').value;
    const courseName = document.getElementById('metadataCourseName').value.trim();
    const keyword = document.getElementById('metadataKeyword').value.trim();
    const brand = document.getElementById('metadataBrand').value.trim();
    const highlights = document.getElementById('metadataHighlights').value.trim();

    if (!pageType || !courseName || !keyword || !highlights) {
        showMessage('metadataMessage', 'Please fill all required fields.', 'error');
        return;
    }

    showMessage('metadataMessage', '🔄 Generating metadata...', 'info');
    await new Promise(resolve => setTimeout(resolve, 800));

    // Generate page title (50-60 chars optimal)
    let pageTitle = '';
    if (brand) {
        pageTitle = `${courseName} | ${keyword} | ${brand}`;
    } else {
        pageTitle = `${courseName} | Best ${keyword}`;
    }
    
    // Keep title within 60 chars
    if (pageTitle.length > 60) {
        pageTitle = pageTitle.substring(0, 57) + '...';
    }

    // Generate meta description (140-160 chars optimal)
    const highlightsList = highlights.split('\n').filter(h => h.trim());
    let description = `Discover ${courseName} - ${keyword}. `;
    if (brand) {
        description += `${brand} offers flexible, industry-recognized learning. `;
    }
    description += highlightsList.slice(0, 2).join('. ') + '. Enroll today!';
    
    if (description.length > 160) {
        description = description.substring(0, 157) + '...';
    }

    displayMetadataGeneratedResults({
        title: pageTitle,
        description: description,
        keyword: keyword,
        pageType: pageType,
        courseName: courseName
    });

    showMessage('metadataMessage', '✅ Metadata generated successfully!', 'success');
}

function displayMetadataGeneratedResults(data) {
    const target = document.getElementById('metadataResults');
    if (!target) return;

    let html = `<div class="card"><div class="card-title">Generated Metadata</div><div style="margin-top: 18px;">`;
    
    html += `<div style="padding: 14px; margin-bottom: 12px; background: #F0F7FF; border-left: 4px solid #0096FF; border-radius: 8px;">
        <div style="font-weight: 600; color: #0078CC;">Page Title (${data.title.length} chars)</div>
        <div style="font-size: 13px; color: #333; margin-top: 6px; font-family: monospace;">${escapeHtml(data.title)}</div>
        <div style="font-size: 12px; color: #777; margin-top: 4px;">Optimal: 50-60 characters</div>
    </div>`;

    html += `<div style="padding: 14px; margin-bottom: 12px; background: #F0F7FF; border-left: 4px solid #0096FF; border-radius: 8px;">
        <div style="font-weight: 600; color: #0078CC;">Meta Description (${data.description.length} chars)</div>
        <div style="font-size: 13px; color: #333; margin-top: 6px; font-family: monospace;">${escapeHtml(data.description)}</div>
        <div style="font-size: 12px; color: #777; margin-top: 4px;">Optimal: 140-160 characters</div>
    </div>`;

    html += `<div style="padding: 14px; background: #F5F5F5; border-radius: 8px;">
        <div style="font-weight: 600; color: #333; margin-bottom: 8px;">Additional Info:</div>
        <div style="font-size: 13px; color: #666; line-height: 1.6;">
            <div>📌 <strong>Page Type:</strong> ${data.pageType}</div>
            <div>🎯 <strong>Focus Keyword:</strong> ${escapeHtml(data.keyword)}</div>
            <div>📚 <strong>Course/Service:</strong> ${escapeHtml(data.courseName)}</div>
        </div>
    </div>`;

    html += '</div></div>';
    target.innerHTML = html;
}

// Generate dynamic headers
async function generateHeaders(event) {
    event.preventDefault();
    
    const count = parseInt(document.getElementById('headerCount').value, 10);
    const pageType = document.getElementById('headerPageType').value;
    const courseName = document.getElementById('headerCourseName').value.trim();
    const keyword = document.getElementById('headerKeyword').value.trim();
    const highlights = document.getElementById('headerHighlights').value.trim();

    if (!pageType || !courseName || !keyword || !highlights || count < 1) {
        showMessage('headerMessage', 'Please fill all required fields.', 'error');
        return;
    }

    showMessage('headerMessage', `🔄 Generating ${count} headers...`, 'info');
    await new Promise(resolve => setTimeout(resolve, 1000));

    const headers = [];
    const templates = {
        course: [
            `${courseName}: Everything You Need to Know`,
            `Why ${keyword} Matters in Today's Career`,
            `How to Succeed with ${courseName}`,
            `The Complete Guide to ${keyword}`,
            `${courseName} vs Traditional Education`,
            `Key Features of ${courseName}`,
            `Success Stories: ${courseName} Impact`,
            `Getting Started with ${courseName}`,
            `Advanced Skills in ${keyword}`,
            `Career Outcomes from ${courseName}`
        ],
        service: [
            `Professional ${courseName} Services`,
            `Transform Your Business with ${courseName}`,
            `Why Choose Our ${courseName}?`,
            `The Benefits of ${keyword} Solutions`,
            `How We Deliver ${courseName}`,
            `Our ${courseName} Process Explained`,
            `Industry Standards in ${keyword}`,
            `Results You Can Expect`,
            `Client Success with ${courseName}`,
            `Getting Started Today`
        ],
        blog: [
            `Understanding ${keyword}: A Comprehensive Guide`,
            `The Evolution of ${courseName}`,
            `Why ${keyword} Matters Now More Than Ever`,
            `Expert Tips for ${courseName}`,
            `Common Mistakes in ${keyword}`,
            `Best Practices for ${courseName}`,
            `The Future of ${keyword}`,
            `Real-World Applications`,
            `FAQ: Common Questions About ${courseName}`,
            `Taking Your ${keyword} to the Next Level`
        ]
    };

    const selectedTemplates = templates[pageType] || templates.blog;
    
    for (let i = 0; i < Math.min(count, selectedTemplates.length); i++) {
        headers.push({
            level: i === 0 ? 'H1' : 'H2',
            text: selectedTemplates[i]
        });
    }

    displayGeneratedHeaders(headers, courseName);
    showMessage('headerMessage', `✅ ${count} headers generated successfully!`, 'success');
}

function displayGeneratedHeaders(headers, courseName) {
    const target = document.getElementById('headerResults');
    if (!target) return;

    let html = `<div class="card"><div class="card-title">Generated Headers</div><div style="margin-top: 18px;">`;
    
    headers.forEach((header, index) => {
        const bgColor = header.level === 'H1' ? '#FFF3CD' : '#E7F3FF';
        const borderColor = header.level === 'H1' ? '#FF9800' : '#0096FF';
        
        html += `<div style="padding: 12px 14px; margin-bottom: 10px; background: ${bgColor}; border-left: 4px solid ${borderColor}; border-radius: 8px;">
            <div style="font-weight: 600; color: #333; font-size: 14px;">${header.level}</div>
            <div style="font-size: 14px; color: #555; margin-top: 6px; font-family: monospace;">${escapeHtml(header.text)}</div>
        </div>`;
    });

    html += '</div></div>';
    target.innerHTML = html;
}

// Generate dynamic FAQs
async function generateFAQs(event) {
    event.preventDefault();
    
    const count = parseInt(document.getElementById('faqCount').value, 10);
    const pageType = document.getElementById('faqPageType').value;
    const courseName = document.getElementById('faqCourseName').value.trim();
    const keyword = document.getElementById('faqKeyword').value.trim();
    const highlights = document.getElementById('faqHighlights').value.trim();

    if (!pageType || !courseName || !keyword || !highlights || count < 1) {
        showMessage('brandMentionsMessage', 'Please fill all required fields.', 'error');
        return;
    }

    showMessage('brandMentionsMessage', `🔄 Generating ${count} FAQs...`, 'info');
    await new Promise(resolve => setTimeout(resolve, 1000));

    const faqTemplates = {
        course: [
            { q: `What is ${courseName}?`, a: `${courseName} is a comprehensive program designed to teach you ${keyword}. It combines theoretical knowledge with practical skills.` },
            { q: `Who should take ${courseName}?`, a: `Perfect for professionals looking to advance in ${keyword}, career changers, and students seeking industry-recognized credentials.` },
            { q: `How long does ${courseName} take?`, a: `The program is flexible and can typically be completed in 3-6 months depending on your pace and prior experience.` },
            { q: `Is ${courseName} recognized by industry?`, a: `Yes, our certification in ${keyword} is recognized by leading companies and industry bodies worldwide.` },
            { q: `What support is available during ${courseName}?`, a: `We provide 24/7 student support, expert mentorship, peer learning groups, and dedicated career counseling.` },
            { q: `What are the job prospects after ${courseName}?`, a: `Graduates typically see ${keyword} roles with strong salary growth. We provide placement assistance and job guarantees.` },
            { q: `Can I access ${courseName} content anytime?`, a: `Yes, all course materials are available 24/7 with lifetime access. Learn at your own pace and schedule.` },
            { q: `What is the fee for ${courseName}?`, a: `Pricing varies based on the plan. We offer flexible payment options, scholarships, and money-back guarantees.` }
        ],
        service: [
            { q: `What is included in ${courseName}?`, a: `Our ${courseName} includes comprehensive consultation, implementation, training, and ongoing support for ${keyword}.` },
            { q: `How does ${courseName} work?`, a: `We follow a proven 5-step process: assessment, planning, execution, optimization, and continuous support.` },
            { q: `What results can I expect from ${courseName}?`, a: `Clients typically see 40-60% improvement in ${keyword} metrics within the first 90 days.` },
            { q: `How long does implementation take?`, a: `Most implementations are complete within 4-8 weeks, with ongoing optimization support after that.` },
            { q: `Is there a guarantee with ${courseName}?`, a: `Yes, we offer a satisfaction guarantee and are committed to delivering measurable results in ${keyword}.` },
            { q: `Can you customize ${courseName} for my needs?`, a: `Absolutely. We customize every ${courseName} solution to align with your specific ${keyword} goals.` },
            { q: `What support do you provide after implementation?`, a: `We provide dedicated support including regular reviews, optimization, training, and quarterly strategy sessions.` },
            { q: `How is ${courseName} priced?`, a: `Pricing is based on scope and scale. We offer transparent, flexible pricing with no hidden fees.` }
        ]
    };

    const templates = faqTemplates[pageType] || faqTemplates.course;
    const faqs = templates.slice(0, count);

    displayGeneratedFAQs(faqs);
    showMessage('brandMentionsMessage', `✅ ${count} FAQs generated successfully!`, 'success');
}

function displayGeneratedFAQs(faqs) {
    const target = document.getElementById('brandMentionsResults');
    if (!target) return;

    let html = `<div class="card"><div class="card-title">Generated FAQs</div><div style="margin-top: 18px;">`;
    
    faqs.forEach((faq, index) => {
        html += `<div style="padding: 14px; margin-bottom: 12px; background: #F8FAFF; border: 1px solid #E0E8FF; border-radius: 8px;">
            <div style="font-weight: 600; color: #0078CC; margin-bottom: 6px;">Q${index + 1}: ${escapeHtml(faq.q)}</div>
            <div style="font-size: 13px; color: #555; line-height: 1.6; padding-left: 20px;"><strong>A:</strong> ${escapeHtml(faq.a)}</div>
        </div>`;
    });

    html += '</div></div>';
    target.innerHTML = html;
}

// Generate blog post content
async function generateBlog(event) {
    event.preventDefault();
    
    const topic = document.getElementById('blogTopic').value.trim();
    const url = document.getElementById('blogUrl').value.trim();
    const primaryKw = document.getElementById('blogPrimaryKeywords').value.trim();
    const secondaryKw = document.getElementById('blogSecondaryKeywords').value.trim();
    const h1 = document.getElementById('blogH1').value.trim();
    const h2Topics = document.getElementById('blogH2Topics').value.trim();

    if (!topic || !url || !primaryKw || !h1 || !h2Topics) {
        showMessage('marketingPlanMessage', 'Please fill all required fields.', 'error');
        return;
    }

    showMessage('marketingPlanMessage', '🔄 Generating blog post...', 'info');
    await new Promise(resolve => setTimeout(resolve, 1500));

    // Store blog data for export
    window.currentBlogData = {
        topic, url, primaryKw, secondaryKw, h1, h2Topics,
        generatedAt: new Date().toLocaleDateString()
    };

    const blogContent = generateBlogContent(topic, h1, h2Topics, primaryKw);
    displayBlogResults(blogContent);
    
    showMessage('marketingPlanMessage', '✅ Blog post generated successfully! You can export it as DOCX below.', 'success');
}

function generateBlogContent(topic, h1, h2Topics, keywords) {
    const h2Array = h2Topics.split('\n').filter(h => h.trim());
    
    let content = `<h1>${escapeHtml(h1)}</h1>\n\n`;
    content += `<p>The landscape of ${topic.toLowerCase()} has undergone significant transformation in recent years. This comprehensive guide explores what you need to know.</p>\n\n`;

    h2Array.forEach(h2 => {
        content += `<h2>${escapeHtml(h2)}</h2>\n\n`;
        content += `<p>This section covers important aspects of ${h2.toLowerCase()}. In today's competitive environment, understanding ${keywords.split('\n')[0] || topic} is crucial for success.</p>\n\n`;
        content += `<ul style="margin-left: 20px;"><li>Key point related to the topic</li><li>Industry best practices</li><li>Actionable insights and strategies</li></ul>\n\n`;
    });

    return content;
}

function displayBlogResults(content) {
    const target = document.getElementById('marketingPlanResults');
    if (!target) return;

    let html = `<div class="card" style="background: #F9FBFF; padding: 20px;"><div class="card-title">Blog Post Preview</div>`;
    html += `<div style="margin-top: 16px; font-size: 13px; line-height: 1.8; color: #444; font-family: 'Georgia', serif;">`;
    html += content.replace(/\n\n/g, '</p><p>').replace(/^/, '<p>').replace(/$/, '</p>');
    html += `</div>`;
    html += `<div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #E0E8FF;">
        <button class="btn-primary" onclick="exportBlogToDOCX()" style="width: auto;">📥 Export as Word Document</button>
    </div>`;
    html += `</div>`;

    target.innerHTML = html;
}

// Export blog to DOCX format
function exportBlogToDOCX() {
    if (!window.currentBlogData) {
        alert('Please generate a blog post first');
        return;
    }

    const { topic, url, primaryKw, h1, generatedAt } = window.currentBlogData;
    
    // Create a simple Word document structure
    let docContent = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p><w:r><w:rPr><w:b/><w:sz w:val="48"/></w:rPr><w:t>${escapeHtml(h1)}</w:t></w:r></w:p>
        <w:p><w:r><w:rPr><w:i/></w:rPr><w:t>Blog Topic: ${escapeHtml(topic)}</w:t></w:r></w:p>
        <w:p><w:r><w:rPr><w:i/></w:rPr><w:t>Page URL: ${escapeHtml(url)}</w:t></w:r></w:p>
        <w:p><w:r><w:rPr><w:i/></w:rPr><w:t>Generated: ${generatedAt}</w:t></w:r></w:p>
        <w:p/>
        <w:p><w:r><w:t>Primary Keywords: ${escapeHtml(primaryKw.replace(/\n/g, ', '))}</w:t></w:r></w:p>
        <w:p/>
        <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Blog Content:</w:t></w:r></w:p>
        <w:p><w:r><w:t>This blog post has been generated based on your inputs. Please review and customize the content as needed before publishing.</w:t></w:r></w:p>
    </w:body>
</w:document>`;

    // Create a simple text file as fallback (since true DOCX requires more complex structure)
    const textContent = `
===============================================
${h1}
===============================================

Blog Topic: ${topic}
Page URL: ${url}
Generated: ${generatedAt}

PRIMARY KEYWORDS:
${window.currentBlogData.primaryKw}

SECONDARY KEYWORDS:
${window.currentBlogData.secondaryKw || 'None'}

H2 TOPICS:
${window.currentBlogData.h2Topics}

BLOG CONTENT:
[Your generated blog content here - customize and expand as needed]

This is a structured template for your blog post. Please review, customize, and add additional content before publishing.

===============================================
Generated by SEO Audit Dashboard
===============================================
`;

    // Create download link for text file (works better cross-browser)
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(textContent));
    element.setAttribute('download', `blog_${Date.now()}.txt`);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);

    showToast('Blog content exported! (Note: Exported as text - copy to Word for formatting)', 'success', 3000);
}

function showToast(message, type = 'info', duration = 3000) {
    const alert = document.createElement('div');
    alert.className = `message ${type} show`;
    alert.textContent = message;
    alert.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? '#4CAF50' : '#0096FF'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
    `;
    
    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), duration);
}
