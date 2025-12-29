# Tasks: Leasing Yönetim Sistemi

**Input**: Design documents from `.specify/memory/`
**Prerequisites**: plan.md ✅, specify.md ✅, constitution.md ✅

**Tests**: Tests are included per constitution requirement (>80% coverage target)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Django app structure**: `leasing_core/` at repository root
- **Apps**: `accounts/`, `customers/`, `orders/`, `documents/`, `tasks/`, `proposals/`, `core/`
- **Templates**: `templates/[app_name]/`
- **Static**: `static/`

---

## User Stories (from spec.md)

| ID | Story | Priority |
|----|-------|----------|
| US1 | Satış elemanı: müşteri aşaması ve günlük öncelikler görünümü | P1 |
| US2 | Müşteri: belge yükleme ve sipariş durumu takibi | P2 |
| US3 | Admin: departman performansı ve sistem kullanımı görünümü | P3 |
| US4 | Satış elemanı: ses/metin ile hızlı teklif oluşturma | P4 |
| US5 | Sistem: eksik/hatalı belge otomatik tespiti (AI) | P5 |

---

## Phase 1: Setup (Proje Altyapısı)

**Purpose**: Django projesi kurulumu ve temel yapı oluşturma

- [x] T001 Create Django project with `django-admin startproject leasing_core .`
- [x] T002 Create virtual environment and requirements.txt in project root
- [x] T003 [P] Create .env.example with required environment variables
- [x] T004 [P] Create .gitignore for Python/Django projects
- [x] T005 Configure settings.py with dev/prod separation in leasing_core/settings/
- [x] T006 [P] Install and configure Tailwind CSS in static/css/
- [x] T007 Create base.html template in templates/base.html
- [x] T008 [P] Configure static files and media settings in leasing_core/settings/base.py
- [x] T009 Create README.md with setup instructions

**Checkpoint**: Django project runs with `python manage.py runserver`

---

## Phase 2: Foundational (Temel Altyapı)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Authentication & User Management

- [x] T010 Create `accounts` app with `python manage.py startapp accounts`
- [x] T011 Implement CustomUser model (AbstractUser) in accounts/models.py
- [x] T012 [P] Create Department model in accounts/models.py
- [x] T013 Create user type choices (Admin, Salesperson, Customer) in accounts/models.py
- [x] T014 Configure AUTH_USER_MODEL in leasing_core/settings/base.py
- [x] T015 Create initial migrations for accounts app
- [x] T016 [P] Implement login view in accounts/views.py
- [x] T017 [P] Implement logout view in accounts/views.py
- [x] T018 [P] Implement password reset views in accounts/views.py
- [x] T019 Create login.html template in templates/accounts/login.html
- [x] T020 [P] Create password_reset.html templates in templates/accounts/
- [x] T021 Configure Django admin for CustomUser in accounts/admin.py
- [x] T022 Create admin user seeding command in accounts/management/commands/seed_admin.py

### Base Templates & Navigation

- [x] T023 Create navigation component in templates/components/navbar.html
- [x] T024 [P] Create sidebar component in templates/components/sidebar.html
- [x] T025 [P] Create footer component in templates/components/footer.html
- [ ] T026 Create role-based routing middleware in core/middleware.py
- [x] T027 [P] Create toast notifications component in templates/components/toast.html
- [x] T028 Create loading spinner component in templates/components/spinner.html

### Core App & Utilities

- [x] T029 Create `core` app with `python manage.py startapp core`
- [x] T030 Create base service class in core/services/base.py
- [x] T031 [P] Create logging utility in core/utils/logging.py
- [x] T032 [P] Create email utility in core/utils/email.py
- [x] T033 Create audit trail mixin in core/mixins.py
- [x] T034 [P] Create permission decorators in core/decorators.py

### AI Service Foundation

- [x] T035 Create `ai_services` app with `python manage.py startapp ai_services`
- [x] T036 Create ClaudeService base class in ai_services/services/claude.py
- [x] T037 [P] Create AI response models in ai_services/models.py
- [x] T038 Create retry logic and error handling in ai_services/utils.py
- [x] T039 [P] Create AI service configuration in ai_services/config.py

**Checkpoint**: Foundation ready - users can login, base templates render, AI service configured

---

## Phase 3: User Story 1 - Satış Dashboard ve Günlük Öncelikler (Priority: P1) 🎯 MVP

**Goal**: Satış elemanı müşteri aşamalarını ve günlük yapılacakları görebilmeli

**Independent Test**: Login as salesperson → see customer list with stages → see today's priorities widget

### Tests for User Story 1

- [ ] T040 [P] [US1] Unit test for Customer model in accounts/tests/test_models.py
- [ ] T041 [P] [US1] Unit test for Task model in tasks/tests/test_models.py
- [ ] T042 [P] [US1] Unit test for TaskPrioritizer service in tasks/tests/test_services.py
- [ ] T043 [US1] Integration test for sales dashboard in accounts/tests/test_views.py

### Implementation for User Story 1

#### Customer Management

- [ ] T044 Create `customers` app with `python manage.py startapp customers`
- [ ] T045 [P] [US1] Create Customer model (extends CustomUser) in customers/models.py
- [ ] T046 [P] [US1] Create CustomerStatus choices in customers/models.py
- [ ] T047 [US1] Create Customer-Salesperson relationship in customers/models.py
- [ ] T048 [US1] Create migrations for customers app
- [ ] T049 [US1] Create CustomerService in customers/services.py
- [ ] T050 [P] [US1] Create CustomerListView in customers/views.py
- [ ] T051 [P] [US1] Create CustomerDetailView in customers/views.py
- [ ] T052 [US1] Create customer_list.html template in templates/customers/customer_list.html
- [ ] T053 [P] [US1] Create customer_detail.html template in templates/customers/customer_detail.html
- [ ] T054 [US1] Create customer card component in templates/customers/components/customer_card.html

#### Task Management

- [ ] T055 Create `tasks` app with `python manage.py startapp tasks`
- [ ] T056 [P] [US1] Create Task model in tasks/models.py
- [ ] T057 [P] [US1] Create TaskStatus choices in tasks/models.py
- [ ] T058 [P] [US1] Create TaskPriority model in tasks/models.py
- [ ] T059 [US1] Create Task-Customer-Order relationships in tasks/models.py
- [ ] T060 [US1] Create migrations for tasks app
- [ ] T061 [US1] Create TaskPrioritizer AI service in tasks/services/prioritizer.py
- [ ] T062 [US1] Implement priority scoring logic in tasks/services/prioritizer.py
- [ ] T063 [US1] Create TaskListView in tasks/views.py
- [ ] T064 [P] [US1] Create TaskDetailView in tasks/views.py
- [ ] T065 [US1] Create task_list.html template in templates/tasks/task_list.html
- [ ] T066 [P] [US1] Create task_detail.html template in templates/tasks/task_detail.html

#### Sales Dashboard

- [ ] T067 [US1] Create SalesDashboardView in accounts/views.py
- [ ] T068 [US1] Create "Bugünün Önemlileri" widget in templates/dashboard/widgets/today_priorities.html
- [ ] T069 [US1] Create customer stage summary widget in templates/dashboard/widgets/customer_stages.html
- [ ] T070 [US1] Create sales_dashboard.html template in templates/dashboard/sales_dashboard.html
- [ ] T071 [US1] Integrate AI prioritization into dashboard view
- [ ] T072 [US1] Add quick action buttons to task cards

#### Notifications

- [ ] T073 [P] [US1] Create Notification model in core/models.py
- [ ] T074 [US1] Create notification dropdown component in templates/components/notifications.html
- [ ] T075 [US1] Create NotificationService in core/services/notifications.py
- [ ] T076 [US1] Add notification badge to navbar

**Checkpoint**: Salesperson can login, see customers with stages, see AI-prioritized daily tasks

---

## Phase 4: User Story 2 - Müşteri Belge Yükleme ve Sipariş Takibi (Priority: P2)

**Goal**: Müşteri istenen belgeleri yükleyebilmeli ve sipariş durumunu takip edebilmeli

**Independent Test**: Login as customer → create order → upload documents → track status

### Tests for User Story 2

- [ ] T077 [P] [US2] Unit test for Order model in orders/tests/test_models.py
- [ ] T078 [P] [US2] Unit test for UploadedDocument model in documents/tests/test_models.py
- [ ] T079 [P] [US2] Unit test for file validation in documents/tests/test_validators.py
- [ ] T080 [US2] Integration test for order creation flow in orders/tests/test_views.py

### Implementation for User Story 2

#### KVKK System

- [ ] T081 Create `documents` app with `python manage.py startapp documents`
- [ ] T082 [P] [US2] Create KVKKDocument model in documents/models.py
- [ ] T083 [P] [US2] Create KVKKComment model in documents/models.py
- [ ] T084 [US2] Create migrations for documents app
- [ ] T085 [US2] Create KVKKDocumentView in documents/views.py
- [ ] T086 [US2] Create kvkk_document.html template in templates/documents/kvkk_document.html
- [ ] T087 [US2] Create KVKK comment UI component in templates/documents/components/kvkk_comment.html
- [ ] T088 [US2] Implement signed document upload in documents/views.py

#### Order Management

- [ ] T089 Create `orders` app with `python manage.py startapp orders`
- [ ] T090 [P] [US2] Create Order model in orders/models.py
- [ ] T091 [P] [US2] Create OrderStatus choices in orders/models.py
- [ ] T092 [P] [US2] Create OrderNote model (timeline) in orders/models.py
- [ ] T093 [US2] Create Customer-Order relationship in orders/models.py
- [ ] T094 [US2] Create migrations for orders app
- [ ] T095 [US2] Create OrderService in orders/services.py

#### Order Wizard

- [ ] T096 [US2] Create order wizard base view in orders/views.py
- [ ] T097 [US2] Create wizard step 1: equipment selection in orders/views.py
- [ ] T098 [US2] Create wizard step 2: document upload in orders/views.py
- [ ] T099 [US2] Create order_wizard.html template in templates/orders/order_wizard.html
- [ ] T100 [P] [US2] Create equipment_selection.html in templates/orders/steps/equipment_selection.html
- [ ] T101 [P] [US2] Create document_upload.html in templates/orders/steps/document_upload.html
- [ ] T102 [US2] Create progress indicator component in templates/orders/components/progress_indicator.html
- [ ] T103 [US2] Implement session-based wizard state management in orders/utils.py

#### Document Upload

- [ ] T104 [P] [US2] Create DocumentTemplate model in documents/models.py
- [ ] T105 [P] [US2] Create UploadedDocument model in documents/models.py
- [ ] T106 [US2] Create file upload view in documents/views.py
- [ ] T107 [US2] Create drag-and-drop upload component in templates/documents/components/file_upload.html
- [ ] T108 [US2] Implement file type validation (PDF, Word, Images) in documents/validators.py
- [ ] T109 [US2] Implement file size validation (max 10MB) in documents/validators.py
- [ ] T110 [US2] Create upload progress indicator in templates/documents/components/upload_progress.html

#### Order Status Tracking

- [ ] T111 [US2] Create OrderListView for customer in orders/views.py
- [ ] T112 [US2] Create OrderDetailView for customer in orders/views.py
- [ ] T113 [US2] Create order_list.html template in templates/orders/order_list.html
- [ ] T114 [US2] Create order_detail.html template in templates/orders/order_detail.html
- [ ] T115 [US2] Create timeline component in templates/orders/components/timeline.html
- [ ] T116 [US2] Implement status change notifications in orders/signals.py

#### Customer Dashboard

- [ ] T117 [US2] Create CustomerDashboardView in accounts/views.py
- [ ] T118 [US2] Create customer_dashboard.html template in templates/dashboard/customer_dashboard.html
- [ ] T119 [US2] Create active orders widget in templates/dashboard/widgets/active_orders.html
- [ ] T120 [US2] Create pending forms widget in templates/dashboard/widgets/pending_forms.html

**Checkpoint**: Customer can create order, upload documents, and track status

---

## Phase 5: User Story 3 - Admin Dashboard ve Departman Performansı (Priority: P3)

**Goal**: Admin tüm departmanların performansını ve sistem kullanımını görebilmeli

**Independent Test**: Login as admin → see all department stats → see user activities → see system health

### Tests for User Story 3

- [ ] T121 [P] [US3] Unit test for dashboard statistics in accounts/tests/test_services.py
- [ ] T122 [P] [US3] Unit test for activity log in core/tests/test_models.py
- [ ] T123 [US3] Integration test for admin dashboard in accounts/tests/test_views.py

### Implementation for User Story 3

#### Admin Dashboard

- [ ] T124 [US3] Create AdminDashboardView in accounts/views.py
- [ ] T125 [US3] Create admin_dashboard.html template in templates/dashboard/admin_dashboard.html
- [ ] T126 [US3] Create DashboardStatisticsService in accounts/services.py

#### Statistics Widgets

- [ ] T127 [P] [US3] Create department stats widget in templates/dashboard/widgets/department_stats.html
- [ ] T128 [P] [US3] Create active orders widget in templates/dashboard/widgets/admin_active_orders.html
- [ ] T129 [P] [US3] Create pending approvals widget in templates/dashboard/widgets/pending_approvals.html
- [ ] T130 [P] [US3] Create user activity widget in templates/dashboard/widgets/user_activity.html

#### Charts & Graphs

- [ ] T131 [US3] Integrate Chart.js in static/js/charts.js
- [ ] T132 [US3] Create orders chart component in templates/dashboard/components/orders_chart.html
- [ ] T133 [P] [US3] Create user stats chart component in templates/dashboard/components/user_stats_chart.html
- [ ] T134 [US3] Create API endpoint for chart data in accounts/api.py

#### Activity Logging

- [ ] T135 [US3] Create ActivityLog model in core/models.py
- [ ] T136 [US3] Create activity log signals in core/signals.py
- [ ] T137 [US3] Create recent activity feed in templates/dashboard/widgets/recent_activity.html

#### System Health

- [ ] T138 [P] [US3] Create system health metrics view in core/views.py
- [ ] T139 [US3] Create health metrics widget in templates/dashboard/widgets/system_health.html
- [ ] T140 [US3] Create AI service status indicator in templates/dashboard/widgets/ai_status.html

**Checkpoint**: Admin can see all department metrics, user activities, and system health

---

## Phase 6: User Story 4 - AI Teklif Oluşturma (Priority: P4)

**Goal**: Satış elemanı metin ile hızlıca profesyonel teklif oluşturabilmeli

**Independent Test**: Login as salesperson → create proposal from text → generate PDF → send email

### Tests for User Story 4

- [ ] T141 [P] [US4] Unit test for Proposal model in proposals/tests/test_models.py
- [ ] T142 [P] [US4] Unit test for ProposalGenerator service in proposals/tests/test_services.py
- [ ] T143 [P] [US4] Unit test for PDF generation in proposals/tests/test_pdf.py
- [ ] T144 [US4] Integration test for proposal flow in proposals/tests/test_views.py

### Implementation for User Story 4

#### Proposal Models

- [ ] T145 Create `proposals` app with `python manage.py startapp proposals`
- [ ] T146 [P] [US4] Create Proposal model in proposals/models.py
- [ ] T147 [P] [US4] Create ProposalSection model in proposals/models.py
- [ ] T148 [US4] Create migrations for proposals app

#### AI Proposal Generation

- [ ] T149 [US4] Create ProposalGenerator AI service in proposals/services/generator.py
- [ ] T150 [US4] Implement requirement parsing in proposals/services/generator.py
- [ ] T151 [US4] Implement equipment identification in proposals/services/generator.py
- [ ] T152 [US4] Implement content generation in proposals/services/generator.py
- [ ] T153 [US4] Create proposal structure JSON schema in proposals/schemas.py

#### Proposal UI

- [ ] T154 [US4] Create ProposalCreateView in proposals/views.py
- [ ] T155 [US4] Create proposal_create.html template in templates/proposals/proposal_create.html
- [ ] T156 [US4] Create text input interface in templates/proposals/components/text_input.html
- [ ] T157 [P] [US4] Create structured form interface in templates/proposals/components/structured_form.html
- [ ] T158 [US4] Create proposal preview component in templates/proposals/components/preview.html

#### PDF Generation

- [ ] T159 [US4] Create PDF template design in templates/proposals/pdf/proposal_template.html
- [ ] T160 [US4] Implement PDFGenerator service in proposals/services/pdf_generator.py
- [ ] T161 [US4] Add company branding to PDF template
- [ ] T162 [US4] Create PDF download endpoint in proposals/views.py

#### Email Sending

- [ ] T163 [US4] Create ProposalEmailView in proposals/views.py
- [ ] T164 [US4] Create AI email composition in proposals/services/email_composer.py
- [ ] T165 [US4] Create email template for proposals in templates/emails/proposal_email.html
- [ ] T166 [US4] Create sent tracking in proposals/models.py

#### Proposal Management

- [ ] T167 [US4] Create ProposalListView in proposals/views.py
- [ ] T168 [US4] Create ProposalDetailView in proposals/views.py
- [ ] T169 [US4] Create proposal_list.html template in templates/proposals/proposal_list.html
- [ ] T170 [US4] Create proposal_detail.html template in templates/proposals/proposal_detail.html
- [ ] T171 [US4] Implement edit/regenerate functionality in proposals/views.py

**Checkpoint**: Salesperson can create AI-generated proposals, generate PDFs, and send via email

---

## Phase 7: User Story 5 - AI Belge Validasyonu (Priority: P5)

**Goal**: Sistem eksik veya hatalı belgeleri otomatik tespit edebilmeli

**Independent Test**: Upload document → AI analyzes → shows validation results → indicates missing fields

### Tests for User Story 5

- [ ] T172 [P] [US5] Unit test for DocumentValidator service in ai_services/tests/test_document_validator.py
- [ ] T173 [P] [US5] Unit test for text extraction in documents/tests/test_extraction.py
- [ ] T174 [P] [US5] Unit test for signature detection in ai_services/tests/test_signature.py
- [ ] T175 [US5] Integration test for validation flow in documents/tests/test_views.py

### Implementation for User Story 5

#### Text Extraction

- [ ] T176 [P] [US5] Implement PDF text extraction (PyPDF2) in documents/services/extraction.py
- [ ] T177 [P] [US5] Implement Word text extraction (python-docx) in documents/services/extraction.py
- [ ] T178 [US5] Implement image handling for documents in documents/services/extraction.py

#### AI Validation Service

- [ ] T179 [US5] Create DocumentValidator AI service in ai_services/services/document_validator.py
- [ ] T180 [US5] Implement field matching logic in ai_services/services/document_validator.py
- [ ] T181 [US5] Implement signature/paraf visual detection in ai_services/services/signature_validator.py
- [ ] T182 [US5] Create validation result JSON schema in ai_services/schemas.py
- [ ] T183 [US5] Implement confidence scoring in ai_services/services/document_validator.py

#### Validation Feedback UI

- [ ] T184 [US5] Create validation results component in templates/documents/components/validation_results.html
- [ ] T185 [US5] Create field checklist with status icons in templates/documents/components/field_checklist.html
- [ ] T186 [US5] Create error/warning messages display in templates/documents/components/validation_messages.html
- [ ] T187 [US5] Create re-upload button component in templates/documents/components/reupload.html
- [ ] T188 [US5] Create overall completion percentage in templates/documents/components/completion_bar.html

#### Real-time Validation

- [ ] T189 [US5] Create async validation endpoint in documents/api.py
- [ ] T190 [US5] Implement real-time feedback JavaScript in static/js/validation.js
- [ ] T191 [US5] Create validation status polling in static/js/validation.js
- [ ] T192 [US5] Add validation status to document list view

#### Salesperson Review

- [ ] T193 [US5] Create pending orders queue for salesperson in orders/views.py
- [ ] T194 [US5] Create order review view for salesperson in orders/views.py
- [ ] T195 [US5] Create AI validation results display for salesperson in templates/orders/review.html
- [ ] T196 [US5] Create approve/reject actions in orders/views.py
- [ ] T197 [US5] Create request correction functionality in orders/views.py
- [ ] T198 [US5] Implement department forwarding logic in orders/services.py

**Checkpoint**: System automatically validates uploaded documents and provides AI-powered feedback

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Security & KVKK Compliance

- [ ] T199 [P] Implement HTTPS enforcement in leasing_core/settings/production.py
- [ ] T200 [P] Add CSRF protection verification across all forms
- [ ] T201 [P] Implement rate limiting in core/middleware.py
- [ ] T202 Add sensitive data encryption in core/utils/encryption.py
- [ ] T203 Create audit trail report generation in core/reports.py

### Performance Optimization

- [ ] T204 [P] Add database indexes for frequently queried fields
- [ ] T205 Fix N+1 queries with select_related/prefetch_related
- [ ] T206 [P] Implement query caching for dashboard statistics
- [ ] T207 Minify CSS/JS for production in static/

### UI/UX Polish

- [ ] T208 [P] Add loading indicators to all async operations
- [ ] T209 [P] Improve error messages (Turkish, user-friendly)
- [ ] T210 [P] Add mobile responsive fixes
- [ ] T211 Polish toast notifications styling

### Documentation

- [ ] T212 [P] Update README.md with complete setup instructions
- [ ] T213 [P] Create user manual (Turkish) in docs/user_manual.md
- [ ] T214 [P] Create admin guide in docs/admin_guide.md
- [ ] T215 Create deployment guide in docs/deployment.md

### Final Testing

- [ ] T216 Run full E2E test suite for all user journeys
- [ ] T217 [P] Performance testing with 100 concurrent users
- [ ] T218 Security audit and vulnerability scan
- [ ] T219 Cross-browser testing (Chrome, Firefox, Safari, Edge)
- [ ] T220 Mobile responsiveness testing

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories can then proceed in priority order (P1 → P2 → P3 → P4 → P5)
  - US1 and US3 can be developed in parallel (different apps)
  - US2 and US5 have shared document components
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

| Story | Depends On | Can Parallel With |
|-------|------------|-------------------|
| US1 (Sales Dashboard) | Foundational only | US3 |
| US2 (Customer Portal) | Foundational only | US4 |
| US3 (Admin Dashboard) | Foundational, benefits from US1 data | US1 |
| US4 (Proposals) | Foundational, benefits from US1 customers | US2 |
| US5 (AI Validation) | US2 (document upload) | - |

### Within Each User Story

- Tests should be written alongside implementation
- Models before services
- Services before views
- Views before templates
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Models within a story marked [P] can run in parallel
- Templates marked [P] for different pages can run in parallel
- US1 and US3 can be developed simultaneously by different developers
- US2 and US4 can be developed simultaneously by different developers

---

## Parallel Example: Phase 2 Foundational

```bash
# Launch all parallel foundational tasks together:
T012: Create Department model in accounts/models.py
T016: Implement login view in accounts/views.py
T017: Implement logout view in accounts/views.py
T018: Implement password reset views in accounts/views.py
T020: Create password_reset.html templates in templates/accounts/
T024: Create sidebar component in templates/components/sidebar.html
T025: Create footer component in templates/components/footer.html
T27: Create toast notifications component in templates/components/toast.html
T031: Create logging utility in core/utils/logging.py
T032: Create email utility in core/utils/email.py
T034: Create permission decorators in core/decorators.py
T037: Create AI response models in ai_services/models.py
T039: Create AI service configuration in ai_services/config.py
```

---

## Parallel Example: User Story 1

```bash
# Launch all parallel US1 model tasks:
T045: Create Customer model (extends CustomUser) in customers/models.py
T046: Create CustomerStatus choices in customers/models.py
T056: Create Task model in tasks/models.py
T057: Create TaskStatus choices in tasks/models.py
T058: Create TaskPriority model in tasks/models.py

# Launch all parallel US1 view tasks:
T050: Create CustomerListView in customers/views.py
T051: Create CustomerDetailView in customers/views.py
T064: Create TaskDetailView in tasks/views.py

# Launch all parallel US1 template tasks:
T053: Create customer_detail.html template
T066: Create task_detail.html template
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (~2 days)
2. Complete Phase 2: Foundational (~5 days)
3. Complete Phase 3: User Story 1 (~5 days)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready - Salesperson can see customers and daily priorities

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (Week 1-2)
2. Add User Story 1 → Test → Deploy/Demo (MVP!) (Week 2)
3. Add User Story 2 → Test → Deploy/Demo (Week 3-4)
4. Add User Story 3 → Test → Deploy/Demo (Week 5)
5. Add User Story 4 → Test → Deploy/Demo (Week 6-7)
6. Add User Story 5 → Test → Deploy/Demo (Week 8)
7. Polish phase → Final deployment (Week 9-10)

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Sales Dashboard)
   - Developer B: User Story 2 (Customer Portal)
   - Developer C: User Story 3 (Admin Dashboard)
3. After US1/US2/US3:
   - Developer A: User Story 4 (Proposals)
   - Developer B: User Story 5 (AI Validation)
   - Developer C: Polish tasks
4. Stories complete and integrate independently

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 220 |
| **Phase 1 (Setup)** | 9 tasks |
| **Phase 2 (Foundational)** | 30 tasks |
| **US1 (Sales Dashboard)** | 37 tasks |
| **US2 (Customer Portal)** | 44 tasks |
| **US3 (Admin Dashboard)** | 20 tasks |
| **US4 (Proposals)** | 27 tasks |
| **US5 (AI Validation)** | 27 tasks |
| **Phase 8 (Polish)** | 22 tasks |
| **Parallel Opportunities** | ~80 tasks marked [P] |
| **MVP Scope** | Phase 1 + 2 + US1 (76 tasks) |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Follow Django best practices per constitution.md
- All UI in Turkish per constitution requirements
- AI services must have fallback mechanisms per constitution

