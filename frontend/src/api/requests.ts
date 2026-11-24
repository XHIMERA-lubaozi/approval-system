import { apiRequest } from './client'

export type RequestStatus = 'draft' | 'in_review' | 'approved' | 'rejected'

export interface UserSummary {
  id: number
  username: string
  display_name: string
}

export interface ApprovalRequest {
  id: number
  title: string
  content: string
  status: RequestStatus
  applicant: UserSummary
  first_approver: UserSummary
  second_approver: UserSummary
  current_step: number | null
  current_approver: UserSummary | null
  created_at: string
  updated_at: string
  submitted_at: string | null
}

export interface OperationHistory {
  id: number
  request_id: number
  operator: UserSummary
  action: 'submit' | 'approve' | 'reject'
  step: number | null
  comment: string | null
  before_status: RequestStatus
  before_step: number | null
  after_status: RequestStatus
  after_step: number | null
  operated_at: string
}

export interface ApprovalRequestDetail extends ApprovalRequest {
  history: OperationHistory[]
}

export interface RequestPage {
  count: number
  page: number
  page_size: number
  results: ApprovalRequest[]
}

export interface DraftInput {
  title: string
  content: string
  first_approver_id: number
  second_approver_id: number
}

export interface ListRequestParams {
  scope?: 'mine'
  page?: number
  pageSize?: number
  status?: RequestStatus
  keyword?: string
}

export function listUsers(): Promise<UserSummary[]> {
  return apiRequest<UserSummary[]>('/api/users')
}

export function listRequests(
  params: ListRequestParams = {},
): Promise<RequestPage> {
  const query = new URLSearchParams()
  query.set('scope', params.scope ?? 'mine')
  if (params.page !== undefined) query.set('page', String(params.page))
  if (params.pageSize !== undefined) {
    query.set('pageSize', String(params.pageSize))
  }
  if (params.status) query.set('status', params.status)
  if (params.keyword?.trim()) query.set('keyword', params.keyword.trim())

  return apiRequest<RequestPage>(`/api/requests?${query.toString()}`)
}

export function getRequest(id: number): Promise<ApprovalRequestDetail> {
  return apiRequest<ApprovalRequestDetail>(`/api/requests/${id}`)
}

export function createDraft(payload: DraftInput): Promise<ApprovalRequest> {
  return apiRequest<ApprovalRequest>('/api/requests', {
    method: 'POST',
    body: payload,
  })
}

export function updateDraft(
  id: number,
  payload: DraftInput,
): Promise<ApprovalRequest> {
  return apiRequest<ApprovalRequest>(`/api/requests/${id}`, {
    method: 'PUT',
    body: payload,
  })
}

export function deleteDraft(id: number): Promise<void> {
  return apiRequest<void>(`/api/requests/${id}`, { method: 'DELETE' })
}
