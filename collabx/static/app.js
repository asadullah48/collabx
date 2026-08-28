// CollabX Interactive Controller & Bilingual Localization

let currentLang = 'en';

const TRANSLATIONS = {
  en: {
    badgeTitle: "Editorial Team Agents",
    statusLive: "Editorial Desk Active (:8014)",
    heroTitle: "Orchestrated Multi-Agent Team for Publication-Ready Newsletters",
    heroSubtitle: "Coordinate Researcher, Writer, and Editor agents across a collaborative state graph to uncover industry breakthroughs, draft narrative arcs, and compile polished editorial editions.",
    metric1Label: "Publishing Velocity",
    metric1Sub: "From Idea to Publication",
    metric2Label: "Readability Rating",
    metric2Sub: "Flesch-Kincaid Verified",
    metric3Label: "Fact-Check Grounding",
    metric3Sub: "Peer-Audited Dossiers",
    metric4Label: "Output Formats",
    metric4Sub: "Instant Multi-Channel Sync",
    studioTitle: "Autonomous Editorial Desk Studio",
    studioDesc: "Submit an editorial topic, monitor multi-agent collaboration across the research and writing pipeline, and review the final publication edition in real time.",
    lblPresets: "Select Preset Editorial Topic:",
    lblTopic: "Newsletter Topic / Theme",
    lblAudience: "Target Audience",
    lblTone: "Tone of Voice",
    btnExecuteProduce: "🚀 Run Multi-Agent Team & Publish",
    titleEdition: "Published Newsletter Edition",
    lblFinalEdition: "Newsletter Preview & Markdown:",
    lblDossier: "Verified Research Signals:",
    lblCritique: "Editor Critique Notes:"
  },
  ar: {
    badgeTitle: "فريق التحرير الذكي",
    statusLive: "المكتب التحريري نشط (:8014)",
    heroTitle: "فريق متعدد الوكلاء لإنتاج النشرات والتقارير الإخبارية الجاهزة للنشر",
    heroSubtitle: "تنسيق جهود وكيل البحث ووكيل الكتابة ووكيل التحرير في مخطط تعاوني لاستكشاف الأخبار وصياغة المقالات وإصدار النشرات البريدية فورياً.",
    metric1Label: "سرعة النشر",
    metric1Sub: "من الفكرة إلى النشر",
    metric2Label: "مؤشر سهولة القراءة",
    metric2Sub: "تقييم Flesch-Kincaid",
    metric3Label: "تدقيق الحقائق",
    metric3Sub: "مراجع موثقة بالكامل",
    metric4Label: "صيغ التصدير",
    metric4Sub: "Markdown و HTML فورياً",
    studioTitle: "استوديو المكتب التحريري الذكي",
    studioDesc: "أرسل موضوع النشرة، وراقب تعاون الوكلاء في البحث والكتابة، واقرأ الإصدار النهائي المكتمل في الوقت الفعلي.",
    lblPresets: "اختر موضوعاً تحريرياً مسبقاً:",
    lblTopic: "موضوع / فكرة النشرة",
    lblAudience: "الجمهور المستهدف",
    lblTone: "نبرة الصوت والصياغة",
    btnExecuteProduce: "🚀 تشغيل فريق الوكلاء وإصدار النشرة",
    titleEdition: "الإصدار التحريري المنشور",
    lblFinalEdition: "معاينة النشرة البريدية وكود Markdown:",
    lblDossier: "المؤشرات والأدلة البحثية الموثقة:",
    lblCritique: "ملاحظات المحرر التحريرية:"
  }
};

const SCENARIOS = [
  {
    name: "🤖 The Rise of Autonomous Agent Swarms in Enterprise",
    topic: "The Rise of Autonomous Agent Swarms in Enterprise Automation",
    audience: "CTOs, Founders & Enterprise Architects",
    tone: "TECH_PIONEER"
  },
  {
    name: "🧬 Next-Gen CRISPR Therapeutics & AI Protein Design",
    topic: "Next-Gen CRISPR Therapeutics & AI-Driven Protein Design",
    audience: "Biotech Investors & Pharma Executives",
    tone: "DEEP_DIVE_ANALYST"
  },
  {
    name: "⚡ Nuclear SMRs & Clean Energy Powering Hyperscalers",
    topic: "Small Modular Reactors (SMRs) Powering Next-Gen AI Data Centers",
    audience: "Infrastructure Leaders & Clean Tech Strategists",
    tone: "EXECUTIVE_BRIEF"
  },
  {
    name: "💳 Tokenized Real-World Assets (RWA) & Settlement Rails",
    topic: "Institutional Real-World Asset (RWA) Tokenization & 24/7 Settlement",
    audience: "Asset Managers & Global Treasury Heads",
    tone: "EXECUTIVE_BRIEF"
  }
];

function init() {
  renderPresets();
  loadScenario(0);
}

function toggleLanguage() {
  currentLang = currentLang === 'en' ? 'ar' : 'en';
  document.documentElement.lang = currentLang;
  document.documentElement.dir = currentLang === 'ar' ? 'rtl' : 'ltr';
  document.getElementById('langLabel').innerText = currentLang === 'en' ? 'العربية' : 'English';

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (TRANSLATIONS[currentLang][key]) {
      el.innerText = TRANSLATIONS[currentLang][key];
    }
  });
}

function renderPresets() {
  const container = document.getElementById('scenarioButtons');
  container.innerHTML = '';
  SCENARIOS.forEach((sc, idx) => {
    const btn = document.createElement('button');
    btn.className = 'preset-btn';
    btn.innerText = sc.name;
    btn.onclick = () => loadScenario(idx);
    container.appendChild(btn);
  });
}

function loadScenario(idx) {
  const sc = SCENARIOS[idx];
  document.getElementById('topicInput').value = sc.topic;
  document.getElementById('audienceInput').value = sc.audience;
  document.getElementById('toneSelect').value = sc.tone;
}

async function runEditorialTask() {
  const btn = document.getElementById('produceBtn');
  const topic = document.getElementById('topicInput').value.trim();
  const audience = document.getElementById('audienceInput').value.trim();
  const tone = document.getElementById('toneSelect').value;

  btn.disabled = true;
  btn.innerText = "Orchestrating Researcher -> Writer -> Editor...";

  try {
    const res = await fetch('/api/v1/editorial/produce-newsletter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        brief_id: `BRIEF-${Date.now()}`,
        topic: topic,
        target_audience: audience,
        tone: tone,
        target_word_count: 650
      })
    });

    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`Gateway returned ${res.status}: ${detail.slice(0, 200)}`);
    }

    const data = await res.json();
    renderNewsletter(data);

  } catch (err) {
    document.getElementById('newsletterStream').innerText = `Error: ${err.message}`;
  } finally {
    btn.disabled = false;
    btn.innerText = TRANSLATIONS[currentLang].btnExecuteProduce;
  }
}

// Readability gate defined in SPEC.md section 3 (Flesch-Kincaid >= 80).
const READABILITY_THRESHOLD = 80.0;

function renderNewsletter(data) {
  const fb = data.feedback;

  // Report the verdict the Editor actually returned, not a fixed "APPROVED".
  const approved = fb.fact_check_passed
    && !fb.revision_required
    && fb.readability_score >= READABILITY_THRESHOLD;

  const badge = document.getElementById('qualityBadge');
  badge.className = 'badge ' + (approved ? 'badge-success' : 'badge-warning');
  badge.innerText = `READABILITY: ${fb.readability_score.toFixed(1)} / 100 `
    + `(${approved ? 'APPROVED' : 'REVISION REQUIRED'})`;

  // Pipeline Bar
  const bar = document.getElementById('pipelineBar');
  bar.innerHTML = '';
  const tags = [
    `Read Time: ${data.read_time_minutes} Min`,
    `Tone: ${Math.round(fb.tone_alignment_score * 100)}% Aligned`,
    `Fact-Check: ${fb.fact_check_passed ? 'PASSED' : 'FAILED'}`
  ];
  tags.forEach(text => {
    const span = document.createElement('span');
    span.className = 'pipe-tag';
    span.innerText = text;
    bar.appendChild(span);
  });

  // Newsletter Markdown
  document.getElementById('newsletterStream').innerText = data.final_markdown;

  // Editor critique notes
  const critique = document.getElementById('critiqueList');
  if (critique) {
    critique.innerHTML = '';
    fb.critique_notes.forEach(note => {
      const li = document.createElement('li');
      li.innerText = `• ${note}`;
      critique.appendChild(li);
    });
  }

  // Research Dossier List
  const list = document.getElementById('dossierList');
  list.innerHTML = '';
  data.research_dossier.findings.forEach(f => {
    const li = document.createElement('li');
    li.innerText = `• [Signal] ${f.headline} — "${f.verified_quote}" (${f.statistic})`;
    list.appendChild(li);
  });
}

window.addEventListener('DOMContentLoaded', init);
