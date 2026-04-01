from netbox.plugins import PluginTemplateExtension


class SolomonThemeExtension(PluginTemplateExtension):
    """
    Injects the Solomon dark theme CSS and JS into every page.
    Registered for all models (models = None means global).
    """

    def head(self):
        return THEME_CSS

    def navbar(self):
        return ""


# ---------------------------------------------------------------------------
# Hardcoded Solomon dark theme (Material Design color palette)
#
# Colors from color-palette.txt:
#   Background:     #121212      Surface:        #1e1e1e
#   Surface alt:    #2c2c2c      Primary:        #03a9f4
#   Primary light:  #4fc3f7      Primary dark:   #0288d1
#   On surface:     #e0e0e0      On surface dim: #9e9e9e
#   Error:          #cf6679      Success:        #66bb6a
#   Warning:        #ffa726
# ---------------------------------------------------------------------------

THEME_CSS = """
<style>
/* ═══════════════════════════════════════════════════════════════════
   Solomon Theme - Hardcoded dark Material Design theme
   ═══════════════════════════════════════════════════════════════════ */

/*
 * 1) Override the Tabler gray scale that the dark theme is built on.
 *    Tabler uses --tblr-gray-{100..900} and then references them in
 *    [data-bs-theme=dark] for --tblr-body-bg, --tblr-bg-surface, etc.
 *    By redefining the grays we change everything derived from them.
 *
 * 2) Override the direct Tabler/Bootstrap variables for surfaces,
 *    text, primary colors, borders, navbar, etc.
 *
 * 3) Override NetBox-specific hardcoded colors (.page-header, sidebar
 *    gradient, nav-link colors) that don't use CSS variables.
 */

/* ── Force dark color-scheme on every element ── */
:root,
html,
html[data-bs-theme="light"],
html[data-bs-theme="dark"] {
  color-scheme: dark !important;
}

/* ── Tabler gray scale → Solomon Material palette ── */
:root,
[data-bs-theme="dark"] {
  --tblr-gray-50:   #2c2c2c;
  --tblr-gray-100:  #e0e0e0;
  --tblr-gray-200:  #e0e0e0;
  --tblr-gray-300:  #bdbdbd;
  --tblr-gray-400:  #9e9e9e;
  --tblr-gray-500:  #757575;
  --tblr-gray-600:  #616161;
  --tblr-gray-700:  #2c2c2c;
  --tblr-gray-800:  #1e1e1e;
  --tblr-gray-900:  #121212;
  --tblr-gray-900-rgb: 18, 18, 18;
}

/* ── Bootstrap / Tabler surface & color variable overrides ── */
[data-bs-theme="dark"] {
  /* Body */
  --tblr-body-bg:                 #121212 !important;
  --tblr-body-bg-rgb:             18, 18, 18;
  --tblr-body-color:              #e0e0e0 !important;
  --tblr-body-color-rgb:          224, 224, 224;

  /* Surfaces */
  --tblr-bg-surface:              #1e1e1e !important;
  --tblr-bg-surface-secondary:    #121212 !important;
  --tblr-bg-surface-tertiary:     #2c2c2c !important;
  --tblr-bg-surface-inverted:     #e0e0e0;
  --tblr-bg-forms:                #1e1e1e;
  --tblr-secondary-bg:            #1e1e1e;
  --tblr-tertiary-bg:             #2c2c2c;

  /* Bootstrap 5 uses --bs-tertiary-bg for bg-body-tertiary (default dark: #17212f).
     Override it to match our Surface alt color. */
  --bs-secondary-bg:              #1e1e1e;
  --bs-secondary-bg-rgb:          30, 30, 30;
  --bs-tertiary-bg:               #2c2c2c;
  --bs-tertiary-bg-rgb:           44, 44, 44;

  /* Text */
  --tblr-emphasis-color:          #ffffff;
  --tblr-secondary-color:         rgba(224, 224, 224, 0.75);
  --tblr-muted:                   #9e9e9e;
  --tblr-heading-color:           inherit;

  /* Primary */
  --tblr-primary:                 #03a9f4 !important;
  --tblr-primary-rgb:             3, 169, 244 !important;
  --tblr-primary-fg:              #121212;
  --tblr-btn-active-color:        #121212;

  /* Links */
  --tblr-link-color:              #4fc3f7 !important;
  --tblr-link-hover-color:        #03a9f4 !important;
  --tblr-link-color-rgb:          79, 195, 247;
  --tblr-link-hover-color-rgb:    3, 169, 244;

  /* Borders */
  --tblr-border-color:            #2c2c2c !important;
  --tblr-border-color-translucent: rgba(255, 255, 255, 0.08);
  --tblr-border-dark-color:       #383838;

  /* Cards */
  --tblr-card-bg:                 #1e1e1e;
  --tblr-card-cap-bg:             #2c2c2c;

  /* Status colors */
  --tblr-danger:                  #cf6679;
  --tblr-danger-rgb:              207, 102, 121;
  --tblr-success:                 #66bb6a;
  --tblr-success-rgb:             102, 187, 106;
  --tblr-warning:                 #ffa726;
  --tblr-warning-rgb:             255, 167, 38;
  --tblr-info:                    #4fc3f7;
  --tblr-info-rgb:                79, 195, 247;

  /* Navbar */
  --tblr-navbar-bg:               #1e1e1e;
  --tblr-navbar-active-bg:        rgba(3, 169, 244, 0.12);
  --tblr-navbar-active-border-color: #03a9f4;
  --tblr-navbar-border-color:     #2c2c2c;

  /* Active/hover bg */
  --tblr-active-bg:               #2c2c2c;

  /* Code */
  --tblr-code-color:              #4fc3f7;
  --tblr-highlight-bg:            rgba(3, 169, 244, 0.15);
}

/* ══════════════════════════════════════════════════════════════════
   Component-level overrides  (hardcoded NetBox values need !important)
   ══════════════════════════════════════════════════════════════════ */

/* ── Sidebar (vertical navbar) ──
   NetBox hardcodes: background: linear-gradient(...), #001423
*/
html[data-bs-theme=dark] .navbar-vertical.navbar-expand-lg {
  background: linear-gradient(
    180deg,
    rgba(3, 169, 244, 0.00) 0%,
    rgba(3, 169, 244, 0.07) 100%
  ), #1e1e1e !important;
}

html[data-bs-theme=dark] .navbar-vertical.navbar-expand-lg .nav-link-title,
html[data-bs-theme=dark] .navbar-vertical.navbar-expand-lg .nav-link-icon {
  color: #e0e0e0 !important;
}

html[data-bs-theme=dark] .navbar-vertical.navbar-expand-lg .text-secondary {
  color: #4fc3f7 !important;
}

html[data-bs-theme=dark] .navbar-vertical.navbar-expand-lg .nav-item.dropdown.active::after {
  border-color: #03a9f4 !important;
}

html[data-bs-theme=dark] .navbar-vertical.navbar-expand-lg .dropdown-item a {
  color: #e0e0e0 !important;
}

html[data-bs-theme=dark] .navbar-vertical.navbar-expand-lg .dropdown-item.active,
html[data-bs-theme=dark] .navbar-vertical.navbar-expand-lg .dropdown-item:hover {
  background-color: rgba(3, 169, 244, 0.10) !important;
}

/* Light theme sidebar - also override in case setmode hasn't fired yet */
html[data-bs-theme=light] .navbar-vertical.navbar-expand-lg {
  background: linear-gradient(
    180deg,
    rgba(3, 169, 244, 0.00) 0%,
    rgba(3, 169, 244, 0.07) 100%
  ), #1e1e1e !important;
}

html[data-bs-theme=light] .navbar-vertical.navbar-expand-lg .nav-link-title,
html[data-bs-theme=light] .navbar-vertical.navbar-expand-lg .nav-link-icon {
  color: #e0e0e0 !important;
}

html[data-bs-theme=light] .navbar-vertical.navbar-expand-lg .text-secondary {
  color: #4fc3f7 !important;
}

/* ── Page background ──
   NetBox sets .page { background-color: var(--tblr-bg-surface-secondary) }
   which we override via the variable above, but add explicit backup.
   Also override html[data-bs-theme=dark] { background-color: #001423 } on the root.
*/
html[data-bs-theme=dark],
html[data-bs-theme=dark] body,
html[data-bs-theme=light] body {
  background-color: #121212 !important;
}

html[data-bs-theme=dark] .page,
html[data-bs-theme=light] .page {
  background-color: #121212 !important;
}

/* ── Page header ──
   NetBox hardcodes: .page-header { background-color: #001423 }
*/
.page-header {
  background-color: #1e1e1e !important;
}

/* ── Top navbar / header bar ── */
.navbar {
  background: #1e1e1e !important;
}

/* ── Tables ── */
/* Fix: NetBox hardcodes #001423 for thead th background in dark mode */
html[data-bs-theme=dark] .table thead th,
html[data-bs-theme=dark] .markdown > table thead th {
  background-color: #1e1e1e !important;
}

/* Fix: object-list-tab (page-tabs nav) active link uses bg-surface-secondary (#081b2a) */
html[data-bs-theme=dark] .page-tabs .nav-tabs .nav-link.active,
html[data-bs-theme=dark] .page-tabs .nav-tabs .nav-link:active {
  background-color: #1e1e1e !important;
}

html[data-bs-theme=dark] .table > thead {
  background-color: #1e1e1e;
}

html[data-bs-theme=dark] .table {
  --tblr-table-bg:           #1e1e1e;
  --tblr-table-striped-bg:   #242424;
  --tblr-table-hover-bg:     #2c2c2c;
  --tblr-table-border-color: #2c2c2c;
  color: #e0e0e0;
}

/* ── Cards ── */
/* NetBox compiled CSS: html[data-bs-theme=dark] .card { background: #001423 !important } */
html[data-bs-theme=dark] .card {
  background: #1e1e1e !important;
  background-color: #1e1e1e !important;
  border-color: #2c2c2c;
}

html[data-bs-theme=dark] .card-header {
  background-color: #2c2c2c;
  border-bottom-color: #2c2c2c;
}

/* ── Buttons (primary) ── */
html[data-bs-theme=dark] .btn-primary {
  --tblr-btn-bg: #03a9f4;
  --tblr-btn-border-color: #03a9f4;
  --tblr-btn-hover-bg: #0288d1;
  --tblr-btn-hover-border-color: #0288d1;
  --tblr-btn-active-bg: #0288d1;
  --tblr-btn-active-color: #121212;
  color: #121212 !important;
}

html[data-bs-theme=dark] .btn-outline-primary {
  --tblr-btn-color: #03a9f4;
  --tblr-btn-border-color: #03a9f4;
  --tblr-btn-hover-bg: #03a9f4;
  --tblr-btn-hover-border-color: #03a9f4;
  --tblr-btn-hover-color: #121212;
}

/* ── Primary-background text color overrides ──
   NetBox compiled CSS: html[data-bs-theme=dark] .text-bg-primary,
   .bg-primary .card-title/a/i { color: #001423 !important }
   We keep dark text on primary bg, but use #121212 (our dark background).
*/
html[data-bs-theme=dark] .text-bg-primary,
html[data-bs-theme=dark] .bg-primary .card-title,
html[data-bs-theme=dark] .bg-primary a,
html[data-bs-theme=dark] .bg-primary i {
  color: #121212 !important;
}

/* ── Badges ── */
html[data-bs-theme=dark] .badge.bg-primary {
  background-color: #03a9f4 !important;
  color: #121212 !important;
}
html[data-bs-theme=dark] .badge.bg-secondary {
  background-color: #424242 !important;
  color: #e0e0e0 !important;
  border: 1px solid #616161;
}
html[data-bs-theme=dark] .badge.bg-info {
  background-color: #006064 !important;
  color: #e0f7fa !important;
}

/* ── Form controls ── */
html[data-bs-theme=dark] .form-control,
html[data-bs-theme=dark] .form-select {
  background-color: #2c2c2c;
  border-color: rgba(255, 255, 255, 0.1);
  color: #e0e0e0;
}

html[data-bs-theme=dark] .form-control:focus,
html[data-bs-theme=dark] .form-select:focus {
  border-color: #03a9f4;
  box-shadow: 0 0 0 0.25rem rgba(3, 169, 244, 0.25);
}

/* ── Dropdown menus ── */
html[data-bs-theme=dark] .dropdown-menu {
  background-color: #1e1e1e;
  border-color: #2c2c2c;
}

html[data-bs-theme=dark] .dropdown-item:hover,
html[data-bs-theme=dark] .dropdown-item:focus {
  background-color: #2c2c2c;
  color: #e0e0e0;
}

/* ── Scrollbar (webkit) ── */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: #121212;
}
::-webkit-scrollbar-thumb {
  background: #2c2c2c;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #9e9e9e;
}

/* ── Alerts ── */
html[data-bs-theme=dark] .alert-danger {
  --tblr-alert-bg: rgba(207, 102, 121, 0.15);
  --tblr-alert-color: #cf6679;
  --tblr-alert-border-color: rgba(207, 102, 121, 0.3);
}
html[data-bs-theme=dark] .alert-success {
  --tblr-alert-bg: rgba(102, 187, 106, 0.15);
  --tblr-alert-color: #66bb6a;
  --tblr-alert-border-color: rgba(102, 187, 106, 0.3);
}
html[data-bs-theme=dark] .alert-warning {
  --tblr-alert-bg: rgba(255, 167, 38, 0.15);
  --tblr-alert-color: #ffa726;
  --tblr-alert-border-color: rgba(255, 167, 38, 0.3);
}

/* ── Modal dialogs ── */
html[data-bs-theme=dark] .modal-content {
  background-color: #1e1e1e;
  border-color: #2c2c2c;
}

/* ── List groups ── */
html[data-bs-theme=dark] .list-group-item {
  background-color: #1e1e1e;
  border-color: #2c2c2c;
  color: #e0e0e0;
}
html[data-bs-theme=dark] .list-group-item-action:hover,
html[data-bs-theme=dark] .list-group-item-action:focus {
  background-color: #2c2c2c !important;
  color: #4fc3f7 !important;
}

/* ── Color mode toggle: show it, we support both modes now ── */
/* .color-mode-toggle is visible (we removed the display:none) */

/* ── Login page ── */
html[data-bs-theme=dark] .page-center,
html[data-bs-theme=light] .page-center {
  background-color: #121212 !important;
}

html[data-bs-theme=dark] .page-center .card,
html[data-bs-theme=light] .page-center .card {
  background-color: #1e1e1e !important;
  border-color: #2c2c2c !important;
}

html[data-bs-theme=dark] .page-center .card .card-body,
html[data-bs-theme=light] .page-center .card .card-body {
  background-color: #1e1e1e !important;
}

html[data-bs-theme=dark] .page-center .card .hr-text::after,
html[data-bs-theme=light] .page-center .card .hr-text::after {
  color: #9e9e9e;
}

html[data-bs-theme=dark] .page-center .card .hr-text::before,
html[data-bs-theme=light] .page-center .card .hr-text::before {
  border-color: #2c2c2c;
}

/* ── Dashboard widget card headers (text-bg-* overrides) ── */
html[data-bs-theme=dark] .grid-stack-item .card .card-header {
  border-bottom-color: rgba(255, 255, 255, 0.08) !important;
}

html[data-bs-theme=dark] .grid-stack-item .card .card-body {
  background-color: #1e1e1e !important;
}

/* ── Bootstrap bg-light / bg-white in dark mode ── */
html[data-bs-theme=dark] .bg-light,
html[data-bs-theme=light] .bg-light {
  background-color: #2c2c2c !important;
}

html[data-bs-theme=dark] .bg-white,
html[data-bs-theme=light] .bg-white {
  background-color: #1e1e1e !important;
}

html[data-bs-theme=dark] .bg-body,
html[data-bs-theme=light] .bg-body {
  background-color: #121212 !important;
}

/* ── Bootstrap bg-body-tertiary (uses --bs-tertiary-bg, default dark: #17212f) ── */
html[data-bs-theme=dark] .bg-body-tertiary {
  background-color: #2c2c2c !important;
}

/* ── Bootstrap bg-body-secondary (uses --bs-secondary-bg) ── */
html[data-bs-theme=dark] .bg-body-secondary {
  background-color: #1e1e1e !important;
}

/* ── text-bg-light badge ── */
html[data-bs-theme=dark] .text-bg-light {
  background-color: #2c2c2c !important;
  color: #e0e0e0 !important;
}

/* ── Offcanvas / sidebar ── */
html[data-bs-theme=dark] .offcanvas {
  background-color: #1e1e1e !important;
}

/* ── Pagination ── */
html[data-bs-theme=dark] .page-link {
  background-color: #1e1e1e;
  border-color: #2c2c2c;
  color: #4fc3f7;
}
html[data-bs-theme=dark] .page-item.active .page-link,
html[data-bs-theme=dark] .page-link.active,
html[data-bs-theme=dark] .active > .page-link {
  background-color: #03a9f4;
  border-color: #03a9f4;
  color: #121212 !important;
}
html[data-bs-theme=dark] .page-item.disabled .page-link {
  background-color: #1e1e1e;
  border-color: #2c2c2c;
  color: #616161;
}

/* ── Tab content areas ── */
html[data-bs-theme=dark] .nav-tabs .nav-link.active {
  background-color: #1e1e1e;
  border-color: #2c2c2c #2c2c2c #1e1e1e;
  color: #e0e0e0;
}
html[data-bs-theme=dark] .nav-tabs .nav-link {
  color: #9e9e9e;
}
html[data-bs-theme=dark] .nav-tabs .nav-link:hover {
  border-color: #2c2c2c;
  color: #4fc3f7;
}

/* ── Breadcrumb ── */
html[data-bs-theme=dark] .breadcrumb-item a {
  color: #4fc3f7;
}
html[data-bs-theme=dark] .breadcrumb-item.active {
  color: #9e9e9e;
}

/* ── Object detail panels ── */
html[data-bs-theme=dark] .card-body .table {
  color: #e0e0e0;
}

/* ── Select2 / Tom-select dropdowns ── */
html[data-bs-theme=dark] .ts-dropdown {
  background-color: #1e1e1e;
  border-color: #2c2c2c;
}
html[data-bs-theme=dark] .ts-dropdown .active {
  background-color: rgba(3, 169, 244, 0.15);
  color: #4fc3f7;
}
html[data-bs-theme=dark] .ts-control {
  background-color: #2c2c2c;
  border-color: rgba(255, 255, 255, 0.1);
  color: #e0e0e0;
}

/* ══════════════════════════════════════════════════════════════════
   LIGHT MODE - full palette mirrored from dark, using light tones
   Triggered by [data-bs-theme="light"] which NetBox sets on toggle.
   ══════════════════════════════════════════════════════════════════ */

/*
 * Solomon Light Palette:
 *   Background:    #f5f5f5    Surface:       #ffffff
 *   Surface alt:   #eeeeee    Primary:       #0288d1
 *   Primary light: #03a9f4    Primary dark:  #01579b
 *   On surface:    #212121    On surface dim:#616161
 *   Error:         #c62828    Success:       #2e7d32
 *   Warning:       #e65100
 */

html[data-bs-theme="light"] {
  color-scheme: light !important;
}

[data-bs-theme="light"] {
  /* Tabler gray scale → light palette */
  --tblr-gray-50:   #eeeeee;
  --tblr-gray-100:  #212121;
  --tblr-gray-200:  #212121;
  --tblr-gray-300:  #424242;
  --tblr-gray-400:  #616161;
  --tblr-gray-500:  #757575;
  --tblr-gray-600:  #9e9e9e;
  --tblr-gray-700:  #eeeeee;
  --tblr-gray-800:  #ffffff;
  --tblr-gray-900:  #f5f5f5;
  --tblr-gray-900-rgb: 245, 245, 245;

  /* Body */
  --tblr-body-bg:                 #f5f5f5 !important;
  --tblr-body-bg-rgb:             245, 245, 245;
  --tblr-body-color:              #212121 !important;
  --tblr-body-color-rgb:          33, 33, 33;

  /* Surfaces */
  --tblr-bg-surface:              #ffffff !important;
  --tblr-bg-surface-secondary:    #f5f5f5 !important;
  --tblr-bg-surface-tertiary:     #eeeeee !important;
  --tblr-bg-surface-inverted:     #212121;
  --tblr-bg-forms:                #ffffff;
  --tblr-secondary-bg:            #ffffff;
  --tblr-tertiary-bg:             #eeeeee;

  /* Bootstrap 5 --bs-tertiary-bg for bg-body-tertiary */
  --bs-secondary-bg:              #f5f5f5;
  --bs-secondary-bg-rgb:          245, 245, 245;
  --bs-tertiary-bg:               #eeeeee;
  --bs-tertiary-bg-rgb:           238, 238, 238;

  /* Text */
  --tblr-emphasis-color:          #000000;
  --tblr-secondary-color:         rgba(33, 33, 33, 0.65);
  --tblr-muted:                   #757575;
  --tblr-heading-color:           inherit;

  /* Primary */
  --tblr-primary:                 #0288d1 !important;
  --tblr-primary-rgb:             2, 136, 209 !important;

  /* Links */
  --tblr-link-color:              #0288d1 !important;
  --tblr-link-hover-color:        #01579b !important;
  --tblr-link-color-rgb:          2, 136, 209;
  --tblr-link-hover-color-rgb:    1, 87, 155;

  /* Borders */
  --tblr-border-color:            #e0e0e0 !important;
  --tblr-border-color-translucent: rgba(0, 0, 0, 0.1);
  --tblr-border-dark-color:       #bdbdbd;

  /* Cards */
  --tblr-card-bg:                 #ffffff;
  --tblr-card-cap-bg:             #f5f5f5;

  /* Status */
  --tblr-danger:                  #c62828;
  --tblr-success:                 #2e7d32;
  --tblr-warning:                 #e65100;
  --tblr-info:                    #0288d1;

  /* Navbar */
  --tblr-navbar-bg:               #ffffff;
  --tblr-navbar-active-bg:        rgba(2, 136, 209, 0.10);
  --tblr-navbar-active-border-color: #0288d1;
  --tblr-navbar-border-color:     #e0e0e0;

  /* Active/hover bg */
  --tblr-active-bg:               #eeeeee;

  /* Code */
  --tblr-code-color:              #0288d1;
  --tblr-highlight-bg:            rgba(2, 136, 209, 0.12);
}

/* ── Light: body + page backgrounds ── */
html[data-bs-theme="light"] body,
html[data-bs-theme="light"] .page {
  background-color: #f5f5f5 !important;
}

/* ── Light: page-header + top navbar ── */
html[data-bs-theme="light"] .page-header {
  background-color: #ffffff !important;
}
html[data-bs-theme="light"] .navbar {
  background: #ffffff !important;
  border-bottom: 1px solid #e0e0e0 !important;
}

/* ── Light: sidebar ── */
html[data-bs-theme="light"] .navbar-vertical.navbar-expand-lg {
  background: linear-gradient(
    180deg,
    rgba(2, 136, 209, 0.00) 0%,
    rgba(2, 136, 209, 0.07) 100%
  ), #ffffff !important;
  border-right: 1px solid #e0e0e0 !important;
}
html[data-bs-theme="light"] .navbar-vertical.navbar-expand-lg .nav-link-title,
html[data-bs-theme="light"] .navbar-vertical.navbar-expand-lg .nav-link-icon {
  color: #212121 !important;
}
html[data-bs-theme="light"] .navbar-vertical.navbar-expand-lg .text-secondary {
  color: #0288d1 !important;
}
html[data-bs-theme="light"] .navbar-vertical.navbar-expand-lg .nav-item.dropdown.active::after {
  border-color: #0288d1 !important;
}
html[data-bs-theme="light"] .navbar-vertical.navbar-expand-lg .dropdown-item a {
  color: #212121 !important;
}
html[data-bs-theme="light"] .navbar-vertical.navbar-expand-lg .dropdown-item.active,
html[data-bs-theme="light"] .navbar-vertical.navbar-expand-lg .dropdown-item:hover {
  background-color: rgba(2, 136, 209, 0.08) !important;
}

/* ── Light: cards ── */
html[data-bs-theme="light"] .card {
  background-color: #ffffff;
  border-color: #e0e0e0;
}
html[data-bs-theme="light"] .card-header {
  background-color: #f5f5f5;
  border-bottom-color: #e0e0e0;
}

/* ── Light: tables ── */
html[data-bs-theme="light"] .table thead th,
html[data-bs-theme="light"] .markdown > table thead th {
  background-color: #eeeeee !important;
  color: #616161;
}
html[data-bs-theme="light"] .table {
  --tblr-table-bg:           #ffffff;
  --tblr-table-striped-bg:   #fafafa;
  --tblr-table-hover-bg:     #f5f5f5;
  --tblr-table-border-color: #e0e0e0;
  color: #212121;
}

/* ── Light: page-tabs ── */
html[data-bs-theme="light"] .page-tabs .nav-tabs .nav-link.active,
html[data-bs-theme="light"] .page-tabs .nav-tabs .nav-link:active {
  background-color: #ffffff !important;
}

/* ── Light: form controls ── */
html[data-bs-theme="light"] .form-control,
html[data-bs-theme="light"] .form-select {
  background-color: #ffffff;
  border-color: rgba(0, 0, 0, 0.2);
  color: #212121;
}
html[data-bs-theme="light"] .form-control:focus,
html[data-bs-theme="light"] .form-select:focus {
  border-color: #0288d1;
  box-shadow: 0 0 0 0.25rem rgba(2, 136, 209, 0.25);
}

/* ── Light: buttons ── */
html[data-bs-theme="light"] .btn-primary {
  --tblr-btn-bg: #0288d1;
  --tblr-btn-border-color: #0288d1;
  --tblr-btn-hover-bg: #01579b;
  --tblr-btn-hover-border-color: #01579b;
  color: #ffffff;
}
html[data-bs-theme="light"] .btn-outline-primary {
  --tblr-btn-color: #0288d1;
  --tblr-btn-border-color: #0288d1;
  --tblr-btn-hover-bg: #0288d1;
  --tblr-btn-hover-color: #ffffff;
}

/* ── Light: pagination ── */
html[data-bs-theme="light"] .page-link {
  background-color: #ffffff;
  border-color: #e0e0e0;
  color: #0288d1;
}
html[data-bs-theme="light"] .page-item.active .page-link {
  background-color: #0288d1;
  border-color: #0288d1;
  color: #ffffff;
}

/* ── Light: nav-tabs ── */
html[data-bs-theme="light"] .nav-tabs .nav-link.active {
  background-color: #ffffff;
  border-color: #e0e0e0 #e0e0e0 #ffffff;
  color: #212121;
}
html[data-bs-theme="light"] .nav-tabs .nav-link {
  color: #757575;
}
html[data-bs-theme="light"] .nav-tabs .nav-link:hover {
  color: #0288d1;
}

/* ── Light: dropdown menus ── */
html[data-bs-theme="light"] .dropdown-menu {
  background-color: #ffffff;
  border-color: #e0e0e0;
}
html[data-bs-theme="light"] .dropdown-item:hover,
html[data-bs-theme="light"] .dropdown-item:focus {
  background-color: #f5f5f5;
  color: #212121;
}

/* ── Light: list groups ── */
html[data-bs-theme="light"] .list-group-item {
  background-color: #ffffff;
  border-color: #e0e0e0;
  color: #212121;
}
html[data-bs-theme="light"] .list-group-item-action:hover,
html[data-bs-theme="light"] .list-group-item-action:focus {
  background-color: #e3f2fd !important;
  color: #0288d1 !important;
}

/* ── Light: badges ── */
html[data-bs-theme="light"] .badge.bg-primary {
  background-color: #0288d1 !important;
  color: #ffffff !important;
}
html[data-bs-theme="light"] .badge.bg-secondary {
  background-color: #e0e0e0 !important;
  color: #424242 !important;
}
html[data-bs-theme="light"] .badge.bg-info {
  background-color: #006064 !important;
  color: #e0f7fa !important;
}

/* ── Light: modals ── */
html[data-bs-theme="light"] .modal-content {
  background-color: #ffffff;
  border-color: #e0e0e0;
}

/* ── Light: tom-select ── */
html[data-bs-theme="light"] .ts-dropdown {
  background-color: #ffffff;
  border-color: #e0e0e0;
}
html[data-bs-theme="light"] .ts-dropdown .active {
  background-color: rgba(2, 136, 209, 0.10);
  color: #0288d1;
}
html[data-bs-theme="light"] .ts-control {
  background-color: #ffffff;
  border-color: rgba(0, 0, 0, 0.2);
  color: #212121;
}

/* ── Light: breadcrumbs ── */
html[data-bs-theme="light"] .breadcrumb-item a {
  color: #0288d1;
}
html[data-bs-theme="light"] .breadcrumb-item.active {
  color: #757575;
}

/* ── Light: alerts ── */
html[data-bs-theme="light"] .alert-danger {
  --tblr-alert-bg: rgba(198, 40, 40, 0.10);
  --tblr-alert-color: #c62828;
  --tblr-alert-border-color: rgba(198, 40, 40, 0.3);
}
html[data-bs-theme="light"] .alert-success {
  --tblr-alert-bg: rgba(46, 125, 50, 0.10);
  --tblr-alert-color: #2e7d32;
  --tblr-alert-border-color: rgba(46, 125, 50, 0.3);
}
html[data-bs-theme="light"] .alert-warning {
  --tblr-alert-bg: rgba(230, 81, 0, 0.10);
  --tblr-alert-color: #e65100;
  --tblr-alert-border-color: rgba(230, 81, 0, 0.3);
}

/* ── Light: offcanvas ── */
html[data-bs-theme="light"] .offcanvas {
  background-color: #ffffff !important;
}

/* ── Light: bg-light / bg-white utility overrides ── */
html[data-bs-theme="light"] .bg-light {
  background-color: #eeeeee !important;
}
html[data-bs-theme="light"] .bg-white {
  background-color: #ffffff !important;
}
html[data-bs-theme="light"] .bg-body {
  background-color: #f5f5f5 !important;
}

/* ── Light: login page ── */
html[data-bs-theme="light"] .page-center {
  background-color: #f5f5f5 !important;
}
html[data-bs-theme="light"] .page-center .card {
  background-color: #ffffff !important;
  border-color: #e0e0e0 !important;
}
html[data-bs-theme="light"] .page-center .card .card-body {
  background-color: #ffffff !important;
}

/* ── Light: scrollbar ── */
html[data-bs-theme="light"] ::-webkit-scrollbar-track {
  background: #f5f5f5;
}
html[data-bs-theme="light"] ::-webkit-scrollbar-thumb {
  background: #bdbdbd;
}
html[data-bs-theme="light"] ::-webkit-scrollbar-thumb:hover {
  background: #757575;
}

/* ── Footer links: hide commercial / cloud / community sections ── */
/* JS in DOMContentLoaded handles hiding individual links.
   CSS provides a safety net for known external link patterns. */
.footer a[href*="netboxlabs.com"],
.footer a[href*="netdev.chat"] {
  display: none !important;
}
/* Hide the <li> wrapping the hidden link */
.footer li:has(a[href*="netboxlabs.com"]),
.footer li:has(a[href*="netdev.chat"]),
.footer li:has(a[href*="github.com/netbox-community"]) {
  display: none !important;
}
/* Hide "Get Cloud / Get Enterprise" text in sidebar */
.navbar-collapse a[href*="netboxlabs.com/netbox-cloud"],
.navbar-collapse a[href*="netboxlabs.com/netbox-enterprise"] {
  display: none !important;
}

/* ── Logo alt-text: override NetBox alt to Solomon ── */
/* (Actual SVG files are replaced at the static root level by the entrypoint) */
</style>

<script>
/* Solomon theme init - runs early in <head> before paint.
 * Respects user preference stored in localStorage.
 * Default: dark mode.
 */
(function() {
  var stored = localStorage.getItem("netbox-color-mode");
  var mode = (stored === "light") ? "light" : "dark";
  if (!stored) {
    localStorage.setItem("netbox-color-mode", "dark");
  }
  document.documentElement.setAttribute("data-bs-theme", mode);
  document.documentElement.style.colorScheme = mode;
})();
</script>

<script>
/*
 * Solomon branding overrides.
 *
 * The logo SVG files are already replaced at the static-root level by the
 * Docker entrypoint (logo_netbox_*.svg → Solomon building icon). This script
 * handles text-level and DOM-attribute tweaks that can't be done server-side:
 *   - alt text on logo images
 *   - Edition label ("NetBox" → "Solomon")
 *   - Page title
 *   - Favicon <link> tag (point to SVG)
 *   - Hide duplicate light/dark logo
 *   - Hide commercial footer links
 */
document.addEventListener("DOMContentLoaded", function() {
  var LOGO_LOGIN = "/static/solomon_theme/img/logo_login.svg";
  var FAVICON    = "/static/solomon_theme/img/favicon.svg";

  /* Update alt text on all logo images */
  document.querySelectorAll("img.navbar-brand-image, img.logo").forEach(function(img) {
    img.alt = "Solomon";
  });

  /* On login page, swap to the brand-colored logo variant */
  document.querySelectorAll(".page-center .text-center img.logo").forEach(function(img) {
    img.src = LOGO_LOGIN;
  });

  /* Hide duplicate logos in navbar (light/dark pairs) - keep only the first */
  var navBrand = document.querySelector(".navbar-brand");
  if (navBrand) {
    var imgs = navBrand.querySelectorAll("img");
    for (var i = 1; i < imgs.length; i++) {
      imgs[i].style.display = "none";
    }
  }

  /* Hide duplicate logos on login page (light/dark pairs) - keep only the first */
  document.querySelectorAll(".page-center .text-center").forEach(function(container) {
    var imgs = container.querySelectorAll("img.logo, img.hide-theme-dark, img.hide-theme-light");
    for (var i = 1; i < imgs.length; i++) {
      imgs[i].style.display = "none";
    }
  });

  /* Replace "NetBox" edition text with "Solomon" */
  document.querySelectorAll(".netbox-edition").forEach(function(el) {
    el.textContent = "Solomon";
  });

  /* Replace favicon with SVG */
  var existingIcon = document.querySelector('link[rel="icon"]');
  if (existingIcon) {
    existingIcon.href = FAVICON;
    existingIcon.type = "image/svg+xml";
  }

  /* Replace apple-touch-icon */
  var touchIcon = document.querySelector('link[rel="apple-touch-icon"]');
  if (touchIcon) {
    touchIcon.href = FAVICON;
    touchIcon.type = "image/svg+xml";
  }

  /* Replace page title suffix */
  if (document.title.indexOf("NetBox") !== -1) {
    document.title = document.title.replace(/NetBox/g, "Solomon");
  }

  /* ── Hide commercial footer links ── */
  /* Hide all anchors in .footer pointing to NetBox commercial/community sites */
  var footerLinkHrefs = [
    "netboxlabs.com",
    "netbox.dev",
    "netdev.chat",
    "github.com/netbox-community",
    "mailto:support@netboxlabs.com",
  ];
  var footerLinks = document.querySelectorAll(".footer a");
  footerLinks.forEach(function(anchor) {
    var href = anchor.getAttribute("href") || "";
    var matched = footerLinkHrefs.some(function(pattern) {
      return href.indexOf(pattern) !== -1;
    });
    if (matched) {
      /* Walk up to <li> container and hide it */
      var li = anchor.closest("li");
      if (li) {
        li.style.display = "none";
      } else {
        anchor.style.display = "none";
      }
    }
  });

  /* ── Hide "Get Cloud | Get Enterprise" in the sidebar ── */
  /* This is in .collapse.navbar-collapse > div.text-muted.text-center */
  var sidebarLinks = document.querySelectorAll(".navbar-collapse .text-muted a");
  sidebarLinks.forEach(function(anchor) {
    var href = anchor.getAttribute("href") || "";
    if (href.indexOf("netboxlabs.com") !== -1) {
      /* Hide the entire parent div (contains both links + the pipe) */
      var parentDiv = anchor.closest("div");
      if (parentDiv) {
        parentDiv.style.display = "none";
      }
    }
  });
});
</script>
"""


# Register the extension so NetBox discovers it via registry
template_extensions = [SolomonThemeExtension]
