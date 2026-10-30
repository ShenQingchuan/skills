/**
 * ==============================================================================
 * Project Kanban App Engine (Linear/Raycast Precision Edition)
 * 核心特性：明暗主题切换、双语 Icon 切换、Pele SVG 渲染、Linear 级任务抽屉
 * ==============================================================================
 */

import { render, enableZoom } from 'https://esm.sh/pele';

// 1. 多语言字典
export const I18N_LOCALES = {
  zh: {
    title: '项目看板',
    empty: '当前看板尚无任务数据',
    render_failed: '看板语法解析失败',
    lanes: {
      backlog: '需求池',
      todo: '待开发',
      in_progress: '进行中',
      ready_for_review: '待验收',
    },
    drawer: {
      priority: '优先级',
      assignee: '负责人',
      status: '当前状态',
      activity: '流转轨迹与活动日志',
      created: '需求录入并在看板创建',
      started: 'AI 认领任务并开始进入攻坚',
      ready: '已完成自测，提交进入待验收阶段',
      unassigned: '暂未分配',
    },
  },
  en: {
    title: 'Project Kanban',
    empty: 'No tasks on the board yet',
    render_failed: 'Kanban syntax parse error',
    lanes: {
      backlog: 'Backlog',
      todo: 'Todo',
      in_progress: 'In Progress',
      ready_for_review: 'Ready for Review',
    },
    drawer: {
      priority: 'Priority',
      assignee: 'Assignee',
      status: 'Status',
      activity: 'Activity & Timeline',
      created: 'Task created on board',
      started: 'AI claimed task and started execution',
      ready: 'Implemented & verified, ready for review',
      unassigned: 'Unassigned',
    },
  },
};

// ==============================================================================
// 语言状态管理
// ==============================================================================
export function getCurrentLang() {
  const saved = localStorage.getItem('kanban_lang');
  if (saved && (saved === 'zh' || saved === 'en')) return saved;
  const navLang = (navigator.language || '').toLowerCase();
  return navLang.startsWith('zh') ? 'zh' : 'en';
}

export function toggleLang() {
  const current = getCurrentLang();
  const next = current === 'zh' ? 'en' : 'zh';
  localStorage.setItem('kanban_lang', next);
  applyI18n(next);
}

// ==============================================================================
// 明暗主题状态管理
// ==============================================================================
export function getCurrentTheme() {
  const saved = localStorage.getItem('kanban_theme');
  if (saved && (saved === 'dark' || saved === 'light')) return saved;
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

export function toggleTheme() {
  const current = getCurrentTheme();
  const next = current === 'dark' ? 'light' : 'dark';
  localStorage.setItem('kanban_theme', next);
  applyTheme(next);
}

export function applyTheme(theme = getCurrentTheme()) {
  document.documentElement.setAttribute('data-theme', theme);
  document.body.setAttribute('data-theme', theme);
  updateThemeIcon(theme);
  initKanban();
}

function updateThemeIcon(theme) {
  const btn = document.getElementById('btn-theme-toggle');
  if (!btn) return;
  btn.innerHTML = theme === 'dark'
    ? `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>`
    : `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>`;
}

export function applyI18n(lang = getCurrentLang()) {
  const t = I18N_LOCALES[lang] || I18N_LOCALES.zh;
  document.title = t.title;
  const brandEl = document.getElementById('brand-title');
  if (brandEl) brandEl.textContent = t.title;
  initKanban({ lang });
}

// ==============================================================================
// 智能本地化 Mermaid 泳道标签
// ==============================================================================
function localizeMermaid(source, lang) {
  const lanes = (I18N_LOCALES[lang] || I18N_LOCALES.zh).lanes;
  let result = source;
  result = result.replace(/backlog\[[^\]]+\]/g, `backlog[${lanes.backlog}]`);
  result = result.replace(/todo\[[^\]]+\]/g, `todo[${lanes.todo}]`);
  result = result.replace(/in_progress\[[^\]]+\]/g, `in_progress[${lanes.in_progress}]`);
  result = result.replace(/ready_for_review\[[^\]]+\]/g, `ready_for_review[${lanes.ready_for_review}]`);
  return result;
}

// ==============================================================================
// 看板主渲染逻辑
// ==============================================================================
export function initKanban(options = {}) {
  const sourceId = options.sourceId || 'kanban-source';
  const mountId = options.mountId || 'kanban-mount';
  const lang = options.lang || getCurrentLang();
  const t = I18N_LOCALES[lang] || I18N_LOCALES.zh;

  const sourceEl = document.getElementById(sourceId);
  const mountEl = document.getElementById(mountId);
  if (!sourceEl || !mountEl) return;

  const rawMermaid = sourceEl.textContent.trim();
  if (!rawMermaid) {
    mountEl.innerHTML = `<div style="padding:3rem;color:var(--text-muted);font-size:0.875rem;">${t.empty}</div>`;
    return;
  }

  try {
    const localizedMermaid = localizeMermaid(rawMermaid, lang);
    const result = render(localizedMermaid, { fontSize: 13 });
    mountEl.innerHTML = result.svg;

    enableZoom(mountEl, {
      controls: true,
      maxScale: 3,
    });

    bindCardClickEvents(mountEl, rawMermaid, lang);
  } catch (error) {
    console.error('[Kanban] 渲染失败:', error);
    mountEl.innerHTML = `
      <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.25);color:#fca5a5;padding:1rem;border-radius:6px;font-size:0.8125rem;">
        <strong>${t.render_failed}:</strong> ${error.message || error}
      </div>
    `;
  }
}

// ==============================================================================
// Linear 风格任务详情抽屉逻辑
// ==============================================================================
function bindCardClickEvents(mountEl, rawMermaid, lang) {
  const cards = mountEl.querySelectorAll('.pele-card');
  cards.forEach(card => {
    card.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = card.getAttribute('data-id');
      const textNode = card.querySelector('text');
      const title = textNode ? textNode.textContent.trim() : id;
      openTaskDrawer(id, title, rawMermaid, lang);
    });
  });
}

function openTaskDrawer(cardId, cardTitle, rawMermaid, lang) {
  const backdrop = document.getElementById('drawer-backdrop');
  if (!backdrop) return;

  const t = I18N_LOCALES[lang] || I18N_LOCALES.zh;

  let priority = 'Normal';
  let assigned = t.drawer.unassigned;
  let lane = t.lanes.todo;

  const cardRegex = new RegExp(`${cardId}\\[[^\\]]+\\](?:@\\{([^\\}]+)\\})?`, 'i');
  const match = rawMermaid.match(cardRegex);
  if (match && match[1]) {
    const attrs = match[1];
    if (attrs.includes('priority: "High"')) priority = 'High';
    if (attrs.includes('priority: "Medium"')) priority = 'Medium';
    if (attrs.includes('priority: "Low"')) priority = 'Low';
    if (attrs.includes('assigned: "AI"')) assigned = 'AI Agent';
  }

  if (rawMermaid.indexOf(cardId) !== -1) {
    const index = rawMermaid.indexOf(cardId);
    const before = rawMermaid.slice(0, index);
    if (before.includes('ready_for_review')) lane = t.lanes.ready_for_review;
    else if (before.includes('in_progress')) lane = t.lanes.in_progress;
    else if (before.includes('todo')) lane = t.lanes.todo;
    else if (before.includes('backlog')) lane = t.lanes.backlog;
  }

  document.getElementById('drawer-badge-status').textContent = lane;
  document.getElementById('drawer-task-id-text').textContent = cardId.toUpperCase();
  document.getElementById('drawer-task-title-text').textContent = cardTitle;

  document.getElementById('drawer-prop-priority').textContent = priority;
  document.getElementById('drawer-prop-assignee').textContent = assigned;
  document.getElementById('drawer-prop-lane').textContent = lane;

  const timelineEl = document.getElementById('drawer-timeline');
  timelineEl.innerHTML = `
    <div class="timeline-event">
      <span class="timeline-dot"></span>
      <div class="timeline-event-header">
        <span class="timeline-event-title">${t.drawer.created}</span>
        <span class="timeline-event-time">2025-10-30</span>
      </div>
      <div class="timeline-event-desc">分配编号 ${cardId.toUpperCase()}，录入至 ${lane}</div>
    </div>
    ${lane === t.lanes.in_progress || lane === t.lanes.ready_for_review ? `
    <div class="timeline-event">
      <span class="timeline-dot"></span>
      <div class="timeline-event-header">
        <span class="timeline-event-title">${t.drawer.started}</span>
        <span class="timeline-event-time">进行中</span>
      </div>
      <div class="timeline-event-desc">负责人: ${assigned}</div>
    </div>` : ''}
    ${lane === t.lanes.ready_for_review ? `
    <div class="timeline-event">
      <span class="timeline-dot" style="border-color:#10b981;"></span>
      <div class="timeline-event-header">
        <span class="timeline-event-title" style="color:#10b981;">${t.drawer.ready}</span>
        <span class="timeline-event-time">待验收</span>
      </div>
      <div class="timeline-event-desc">完成实现与自动化验证，等待人类终审验收</div>
    </div>` : ''}
  `;

  backdrop.classList.add('active');
}

export function closeTaskDrawer() {
  const backdrop = document.getElementById('drawer-backdrop');
  if (backdrop) backdrop.classList.remove('active');
}

// ==============================================================================
// 启动与事件绑定
// ==============================================================================
if (typeof window !== 'undefined') {
  window.addEventListener('DOMContentLoaded', () => {
    const langBtn = document.getElementById('btn-lang-toggle');
    if (langBtn) langBtn.addEventListener('click', toggleLang);

    const themeBtn = document.getElementById('btn-theme-toggle');
    if (themeBtn) themeBtn.addEventListener('click', toggleTheme);

    const closeBtn = document.getElementById('btn-drawer-close');
    if (closeBtn) closeBtn.addEventListener('click', closeTaskDrawer);

    const backdrop = document.getElementById('drawer-backdrop');
    if (backdrop) {
      backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) closeTaskDrawer();
      });
    }

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeTaskDrawer();
    });

    applyTheme();
    applyI18n();
  });

  if (import.meta && import.meta.hot) {
    import.meta.hot.accept(() => {
      applyTheme();
      applyI18n();
    });
  }
}
