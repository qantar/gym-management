export interface Member {
  id: number; member_id: string; branch_id: number
  first_name: string; last_name: string; email: string | null; phone: string
  status: "active" | "expired" | "frozen" | "suspended" | "cancelled"
  total_checkins: number; lifetime_value: number; qr_code: string | null; created_at: string
}
export interface PaginatedResponse<T> {
  items: T[]; total: number; page: number; page_size: number; pages: number
}
