import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
export const cn = (...i: ClassValue[]) => twMerge(clsx(i))
export const formatCurrency = (v: number | string) => `SAR ${Number(v).toLocaleString("en-SA", { minimumFractionDigits: 2 })}`
export const formatDate = (d: string | Date) => new Date(d).toLocaleDateString("en-SA", { year: "numeric", month: "short", day: "numeric" })
