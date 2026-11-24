<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <RouterView />
</template>

<style>
:root {
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
    'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  color: #172b43;
  background: #f4f7fa;
  --brand: #2563eb;
  --brand-dark: #1d4ed8;
  --ink: #172b43;
  --muted: #61758c;
  --line: #d9e2ec;
  --surface: #ffffff;
  --danger: #b42318;
  --danger-bg: #fef3f2;
  --success: #067647;
  --success-bg: #ecfdf3;
  --shadow: 0 24px 60px -32px rgb(23 43 67 / 35%);
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-height: 100vh;
  overflow-x: hidden;
  background:
    radial-gradient(circle at 15% 0%, rgb(37 99 235 / 10%), transparent 40%),
    radial-gradient(circle at 90% 10%, rgb(14 165 233 / 9%), transparent 35%),
    #f4f7fa;
}

button,
input {
  font: inherit;
}

a {
  color: var(--brand);
  font-weight: 600;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

/* 认证页 */

.auth-shell {
  position: relative;
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 32px 20px;
}

.auth-card {
  position: relative;
  z-index: 1;
  width: min(100%, 430px);
  padding: 36px;
  background: var(--surface);
  border: 1px solid rgb(23 43 67 / 6%);
  border-radius: 18px;
  box-shadow: var(--shadow);
}

.auth-watermark {
  position: absolute;
  z-index: 0;
  max-width: none;
  pointer-events: none;
  user-select: none;
}

.auth-watermark--top-left {
  top: 7%;
  left: 3%;
  width: min(24vw, 320px);
  opacity: 0.13;
  filter: blur(1.5px);
  transform: rotate(-10deg);
}

.auth-watermark--top-right {
  top: 6%;
  right: 4%;
  width: min(22vw, 280px);
  opacity: 0.11;
  filter: blur(1.5px);
  transform: rotate(11deg);
}

.auth-watermark--bottom-left {
  bottom: 6%;
  left: 5%;
  width: min(28vw, 360px);
  opacity: 0.11;
  filter: blur(2px);
  transform: rotate(7deg);
}

.auth-watermark--side {
  top: 52%;
  right: -20px;
  width: min(36vw, 460px);
  opacity: 0.13;
  filter: blur(2px);
  transform: translateY(-50%) rotate(-8deg);
}

.auth-header {
  margin-bottom: 28px;
}

.brand {
  margin: 0 0 14px;
  color: var(--brand);
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.brand-logo {
  display: block;
  width: 150px;
  height: auto;
}

.form {
  display: grid;
  gap: 18px;
}

.field {
  display: grid;
  gap: 7px;
}

.field label {
  font-size: 0.88rem;
  font-weight: 600;
}

.field input {
  width: 100%;
  padding: 11px 13px;
  color: var(--ink);
  background: #fbfdff;
  border: 1px solid var(--line);
  border-radius: 10px;
  outline: none;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.field input:focus {
  border-color: var(--brand);
  box-shadow: 0 0 0 3px rgb(37 99 235 / 14%);
}

.field input[aria-invalid='true'] {
  border-color: var(--danger);
}

.field-hint {
  margin: 0;
  color: var(--muted);
  font-size: 0.78rem;
}

.field-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.password-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.76rem;
  font-weight: 600;
}

.password-status svg {
  width: 16px;
  height: 16px;
}

.password-status.is-valid {
  color: var(--success);
}

.password-status.is-invalid {
  color: var(--danger);
}

.password-control {
  position: relative;
}

.password-control input {
  padding-right: 46px;
}

.password-toggle {
  position: absolute;
  top: 50%;
  right: 6px;
  display: grid;
  width: 32px;
  height: 32px;
  padding: 0;
  color: var(--muted);
  background: transparent;
  border: 0;
  border-radius: 8px;
  cursor: pointer;
  place-items: center;
  transform: translateY(-50%);
}

.password-toggle:hover {
  color: var(--ink);
  background: #eef4fb;
}

.password-toggle:focus-visible {
  outline: 2px solid var(--brand);
  outline-offset: 2px;
}

.password-toggle svg {
  width: 18px;
  height: 18px;
}

.field-error {
  margin: 0;
  color: var(--danger);
  font-size: 0.8rem;
}

.alert {
  margin: 0;
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 0.86rem;
  line-height: 1.5;
}

.alert-error {
  color: var(--danger);
  background: var(--danger-bg);
  border: 1px solid rgb(180 35 24 / 14%);
}

.alert-success {
  margin-bottom: 18px;
  color: var(--success);
  background: var(--success-bg);
  border: 1px solid rgb(6 118 71 / 14%);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition:
    background-color 0.15s ease,
    transform 0.1s ease,
    opacity 0.15s ease;
}

.btn:active:not(:disabled) {
  transform: translateY(1px);
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.btn-primary {
  padding: 12px 16px;
  color: #fff;
  background: var(--brand);
}

.btn-primary:hover:not(:disabled) {
  background: var(--brand-dark);
}

.btn-ghost {
  padding: 7px 12px;
  color: var(--ink);
  background: #fff;
  border: 1px solid var(--line);
}

.btn-ghost:hover {
  background: #f2f6fb;
}

.auth-switch {
  margin: 22px 0 0;
  color: var(--muted);
  font-size: 0.88rem;
  text-align: center;
}

/* 业务后台布局 */

.app-shell {
  min-height: 100vh;
  padding-left: 248px;
}

.app-sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 20;
  display: flex;
  width: 248px;
  flex-direction: column;
  gap: 26px;
  padding: 30px 18px 22px;
  background: var(--surface);
  border-right: 1px solid rgb(23 43 67 / 8%);
  box-shadow: 18px 0 50px -44px rgb(23 43 67 / 35%);
}

.sidebar-brand {
  display: block;
  padding: 0 10px;
  color: var(--brand);
  font-size: 1.05rem;
  font-weight: 700;
  line-height: 1.35;
  text-decoration: none;
}

.sidebar-section-label {
  margin: 0 0 10px;
  padding: 0 10px;
  color: var(--muted);
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.1em;
}

.sidebar-nav {
  display: grid;
  gap: 4px;
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  color: var(--ink);
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 600;
  text-decoration: none;
  transition:
    color 0.15s ease,
    background-color 0.15s ease;
}

.sidebar-link:hover {
  background: #f2f6fb;
}

.sidebar-link.is-active {
  color: var(--brand-dark);
  background: rgb(37 99 235 / 10%);
}

.sidebar-link svg {
  width: 18px;
  height: 18px;
  flex: none;
}

.sidebar-spacer {
  flex: 1;
}

.sidebar-user {
  display: grid;
  gap: 12px;
  padding-top: 18px;
  border-top: 1px solid rgb(23 43 67 / 8%);
}

.sidebar-user-row {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 10px;
  padding: 0 6px;
}

.sidebar-avatar {
  display: grid;
  width: 36px;
  height: 36px;
  flex: none;
  color: var(--brand-dark);
  background: rgb(37 99 235 / 12%);
  border-radius: 50%;
  font-size: 0.9rem;
  font-weight: 700;
  place-items: center;
}

.sidebar-user-meta {
  display: grid;
  min-width: 0;
  gap: 2px;
}

.sidebar-user-meta strong,
.sidebar-user-meta span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-user-meta strong {
  font-size: 0.88rem;
}

.sidebar-user-meta span {
  color: var(--muted);
  font-size: 0.76rem;
}

.sidebar-logout {
  width: 100%;
  justify-content: center;
}

.page {
  max-width: 62rem;
  margin-inline: auto;
  padding: 40px 24px 64px;
  display: grid;
  gap: 20px;
}

.hero-card,
.placeholder-card {
  padding: 32px;
  background: var(--surface);
  border: 1px solid rgb(23 43 67 / 6%);
  border-radius: 18px;
  box-shadow: 0 18px 50px -38px rgb(23 43 67 / 40%);
}

.eyebrow {
  margin: 0 0 8px;
  color: var(--brand);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.1em;
}

.hero-title {
  margin: 0;
  font-size: clamp(1.8rem, 4vw, 2.5rem);
  line-height: 1.15;
}

.muted {
  margin: 8px 0 0;
  color: var(--muted);
  line-height: 1.65;
}

.account-grid {
  margin: 28px 0 0;
  padding-top: 22px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr));
  gap: 16px;
  border-top: 1px solid rgb(23 43 67 / 8%);
}

.account-grid dt {
  color: var(--muted);
  font-size: 0.76rem;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.account-grid dd {
  margin: 4px 0 0;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.placeholder-card h2 {
  margin: 0;
  font-size: 1.15rem;
}

/* 业务页面通用组件 */

.panel {
  padding: 24px;
  background: var(--surface);
  border: 1px solid rgb(23 43 67 / 6%);
  border-radius: 18px;
  box-shadow: 0 18px 50px -38px rgb(23 43 67 / 40%);
}

.loading-state {
  padding: 32px 16px;
  color: var(--muted);
  text-align: center;
}

.empty-state {
  display: grid;
  justify-items: center;
  gap: 8px;
  padding: 36px 20px;
  text-align: center;
}

.empty-title {
  margin: 0;
  color: var(--ink);
  font-size: 1rem;
  font-weight: 600;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 9px;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 600;
  white-space: nowrap;
}

.status-badge.is-draft {
  color: #475467;
  background: #f2f4f7;
}

.status-badge.is-in_review {
  color: #b54708;
  background: #fffaeb;
}

.status-badge.is-approved {
  color: var(--success);
  background: var(--success-bg);
}

.status-badge.is-rejected {
  color: var(--danger);
  background: var(--danger-bg);
}

.btn-danger {
  padding: 10px 16px;
  color: #fff;
  background: var(--danger);
}

.btn-danger:hover:not(:disabled) {
  background: #912018;
}

.control {
  width: 100%;
  min-height: 40px;
  padding: 9px 11px;
  color: var(--ink);
  background: #fbfdff;
  border: 1px solid var(--line);
  border-radius: 10px;
  outline: none;
}

.control:focus {
  border-color: var(--brand);
  box-shadow: 0 0 0 3px rgb(37 99 235 / 12%);
}

textarea.control {
  min-height: 12rem;
  resize: vertical;
}

@media (max-width: 720px) {
  .auth-watermark--top-left,
  .auth-watermark--top-right,
  .auth-watermark--bottom-left {
    display: none;
  }

  .auth-watermark--side {
    right: -180px;
    width: 440px;
    opacity: 0.055;
  }
}

@media (max-width: 540px) {
  .app-shell {
    padding-top: 70px;
  }

  .app-sidebar {
    gap: 8px;
    padding: 10px 12px;
  }

  .sidebar-brand {
    display: none;
  }

  .sidebar-nav {
    gap: 0;
  }

  .sidebar-link {
    padding: 7px 8px;
    font-size: 0.78rem;
  }

  .sidebar-link svg {
    display: none;
  }

  .sidebar-user-meta strong {
    max-width: 4rem;
  }

  .sidebar-logout {
    padding: 6px 8px;
  }

  .auth-card {
    padding: 26px 22px;
  }

  .hero-card,
  .placeholder-card {
    padding: 24px 20px;
  }

  .app-shell {
    padding-left: 0;
    padding-top: 78px;
  }

  .app-sidebar {
    inset: 0 0 auto;
    width: 100%;
    height: auto;
    flex-direction: row;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-right: 0;
    border-bottom: 1px solid rgb(23 43 67 / 8%);
    box-shadow: 0 10px 30px -26px rgb(23 43 67 / 35%);
  }

  .sidebar-brand {
    padding: 0;
    font-size: 0.92rem;
    white-space: nowrap;
  }

  .sidebar-section-label,
  .sidebar-spacer,
  .sidebar-user-meta span {
    display: none;
  }

  .sidebar-nav-block {
    display: contents;
  }

  .sidebar-nav {
    display: flex;
    gap: 2px;
  }

  .sidebar-link {
    gap: 6px;
    padding: 8px 9px;
    font-size: 0.82rem;
  }

  .sidebar-link svg {
    width: 16px;
    height: 16px;
  }

  .sidebar-user {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-left: auto;
    padding: 0;
    border-top: 0;
  }

  .sidebar-user-row {
    padding: 0;
  }

  .sidebar-avatar {
    width: 28px;
    height: 28px;
    font-size: 0.78rem;
  }

  .sidebar-user-meta strong {
    max-width: 5.5rem;
    font-size: 0.8rem;
  }

  .sidebar-logout {
    width: auto;
    padding: 6px 9px;
    font-size: 0.8rem;
  }
}
</style>
