/**
 * ==============================================================================
 * Project Kanban App Engine (with Built-in i18n)
 * 核心驱动：Pele (SVG 渲染) + 纯原生内置 i18n 引擎 (0 外部运行时依赖)
 * ==============================================================================
 */

import { render, enableZoom } from 'https://esm.sh/pele';

// 1. 内置多语言字典
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
    lang_btn: 'EN',
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
    lang_btn: '中文',
  },
};

/**
 * 获取当前语言 (优先级: localStorage > navigator.language > 默认 zh)
 */
export function getCurrentLang() {
  const saved = localStorage.getItem('kanban_lang');
  if (saved && (saved === 'zh' || saved === 'en')) {
    return saved;
  }
  const navLang = (navigator.language || navigator.userLanguage || '').toLowerCase();
  return navLang.startsWith('zh') ? 'zh' : 'en';
}

/**
 * 切换语言
 */
export function toggleLang() {
  const current = getCurrentLang();
  const next = current === 'zh' ? 'en' : 'zh';
  localStorage.setItem('kanban_lang', next);
  applyI18n(next);
}

/**
 * 应用并更新界面所有文字
 */
export function applyI18n(lang = getCurrentLang()) {
  const t = I18N_LOCALES[lang] || I18N_LOCALES.zh;

  // 更新网页 Title 与品牌标题
  document.title = t.title;
  const brandEl = document.getElementById('brand-title');
  if (brandEl) brandEl.textContent = t.title;

  // 更新语言切换按钮文案
  const langToggleBtn = document.getElementById('btn-lang-toggle');
  if (langToggleBtn) langToggleBtn.textContent = t.lang_btn;

  // 重新渲染看板 (将泳道标题映射为对应语言)
  initKanban({ lang });
}

/**
 * 智能本地化 Mermaid Kanban 泳道标题
 */
function localizeMermaid(source, lang) {
  const lanes = (I18N_LOCALES[lang] || I18N_LOCALES.zh).lanes;
  
  let result = source;
  // 匹配并替换 4 大标准泳道的展示标签
  result = result.replace(/backlog\[[^\]]+\]/g, `backlog[${lanes.backlog}]`);
  result = result.replace(/todo\[[^\]]+\]/g, `todo[${lanes.todo}]`);
  result = result.replace(/in_progress\[[^\]]+\]/g, `in_progress[${lanes.in_progress}]`);
  result = result.replace(/ready_for_review\[[^\]]+\]/g, `ready_for_review[${lanes.ready_for_review}]`);
  
  return result;
}

/**
 * 初始化并渲染项目看板
 */
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
    mountEl.innerHTML = `
      <div style="display:flex;flex-direction:column;align-items:center;padding:3rem;color:var(--text-muted);">
        <p style="margin:0;font-size:0.875rem;">${t.empty}</p>
      </div>
    `;
    return;
  }

  try {
    // 1. 将 Mermaid 源码中的泳道标签动态匹配为当前语言
    const localizedMermaid = localizeMermaid(rawMermaid, lang);

    // 2. 调用 Pele 将 Mermaid Kanban 渲染为高质感 SVG
    const result = render(localizedMermaid);
    mountEl.innerHTML = result.svg;

    // 3. 启用画板拖拽与平滑缩放
    enableZoom(mountEl, {
      controls: true,
      maxScale: 3,
    });
  } catch (error) {
    console.error('[Kanban] 渲染失败:', error);
    mountEl.innerHTML = `
      <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.25);color:#fca5a5;padding:1rem 1.25rem;border-radius:8px;font-size:0.875rem;margin:1rem;">
        <strong style="display:block;margin-bottom:0.25rem;">${t.render_failed}</strong>
        <span style="font-family:var(--pele-font-mono);font-size:0.8125rem;">${error.message || error}</span>
      </div>
    `;
  }
}

// 自动执行启动并挂载切换事件
if (typeof window !== 'undefined') {
  window.addEventListener('DOMContentLoaded', () => {
    // 绑定语言切换按钮
    const btn = document.getElementById('btn-lang-toggle');
    if (btn) {
      btn.addEventListener('click', toggleLang);
    }
    applyI18n();
  });

  // 支持 Vite HMR 热重载
  if (import.meta && import.meta.hot) {
    import.meta.hot.accept(() => {
      applyI18n();
    });
  }
}
