import { create } from 'zustand'

export type ToastVariant = 'success' | 'error' | 'warning' | 'info'
export type ModalName = 'search' | null

export interface Toast {
  id: string
  message: string
  variant: ToastVariant
  duration?: number
}

export interface UIState {
  theme: 'dark' | 'light'
  sidebarOpen: boolean
  toastQueue: Toast[]
  activeModal: ModalName

  setTheme: (theme: 'dark' | 'light') => void
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  addToast: (message: string, variant: ToastVariant, duration?: number) => void
  removeToast: (id: string) => void
  openModal: (modal: ModalName) => void
  closeModal: () => void
}

let toastCounter = 0

export const useUIStore = create<UIState>()((set, get) => ({
  theme: 'dark',
  sidebarOpen: false,
  toastQueue: [],
  activeModal: null,

  setTheme: (theme) => set({ theme }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  addToast: (message, variant, duration = 5000) => {
    const id = `toast-${++toastCounter}`
    set((s) => ({ toastQueue: [...s.toastQueue, { id, message, variant, duration }] }))
    if (duration > 0) {
      setTimeout(() => get().removeToast(id), duration)
    }
  },

  removeToast: (id) => set((s) => ({ toastQueue: s.toastQueue.filter((t) => t.id !== id) })),

  openModal: (modal) => set({ activeModal: modal }),
  closeModal: () => set({ activeModal: null }),
}))