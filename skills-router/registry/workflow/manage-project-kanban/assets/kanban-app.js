/**
 * ==============================================================================
 * Project Kanban App Engine
 * 驱动核心：Pele (Mermaid 渲染) + Halfmoon v2 (交互组件)
 * 可直接通过 CDN (jsDelivr / esm.sh) 引入，亦可本地使用
 * ==============================================================================
 */

import { render, enableZoom } from 'https://esm.sh/pele';

/**
 * 初始化项目看板
 * @param {Object} options 配置项
 * @param {string} options.sourceId 存放 Mermaid 源码的元素 ID (默认 'kanban-source')
 * @param {string} options.mountId 挂载渲染 SVG 的容器 ID (默认 'kanban-mount')
 */
export function initKanban(options = {}) {
  const sourceId = options.sourceId || 'kanban-source';
  const mountId = options.mountId || 'kanban-mount';

  const sourceEl = document.getElementById(sourceId);
  const mountEl = document.getElementById(mountId);

  if (!sourceEl || !mountEl) {
    console.warn(`[Kanban] 未找到容器元素: #${sourceId} 或 #${mountId}`);
    return;
  }

  const rawMermaid = sourceEl.textContent.trim();
  if (!rawMermaid) {
    mountEl.innerHTML = `
      <div class="kanban-empty">
        <i class="bi bi-inbox fs-1 mb-2"></i>
        <p class="mb-0">当前看板尚无任务数据</p>
      </div>
    `;
    return;
  }

  try {
    // 1. 调用 Pele 将 Mermaid Kanban 解析并渲染为高质量 SVG
    const result = render(rawMermaid);
    mountEl.innerHTML = result.svg;

    // 2. 启用画板拖拽与滚轮缩放控制
    enableZoom(mountEl, {
      controls: true,
      maxScale: 3,
    });

    console.log('[Kanban] 画板渲染完成');
  } catch (error) {
    console.error('[Kanban] 渲染失败:', error);
    mountEl.innerHTML = `
      <div class="alert alert-danger m-3" role="alert">
        <h5 class="alert-heading"><i class="bi bi-exclamation-triangle-fill me-2"></i>看板语法解析失败</h5>
        <p class="mb-0 font-monospace small">${error.message || error}</p>
      </div>
    `;
  }
}

/**
 * 弹出 Halfmoon 风格 Toast 浮动提示
 * @param {string} message 提示文案
 * @param {string} type 类型 ('success' | 'info' | 'warning' | 'danger')
 */
export function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toastEl = document.createElement('div');
  toastEl.className = `toast align-items-center text-bg-${type} border-0 show mb-2`;
  toastEl.setAttribute('role', 'alert');
  toastEl.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">
        <i class="bi bi-info-circle me-2"></i>${message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  `;

  container.appendChild(toastEl);
  setTimeout(() => {
    toastEl.classList.remove('show');
    setTimeout(() => toastEl.remove(), 300);
  }, 3500);
}

// 自动执行启动
if (typeof window !== 'undefined') {
  window.addEventListener('DOMContentLoaded', () => {
    initKanban();
  });

  // 如果是在 Vite 环境下，支持热重载自刷新
  if (import.meta && import.meta.hot) {
    import.meta.hot.accept(() => {
      initKanban();
    });
  }
}
