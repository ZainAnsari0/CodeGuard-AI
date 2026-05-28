import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useUIStore } from '../uiStore'

describe('UIStore', () => {
  beforeEach(() => {
    useUIStore.setState({
      theme: 'dark',
      sidebarOpen: false,
      toastQueue: [],
      activeModal: null,
    })
  })

  it('initializes with default values', () => {
    const state = useUIStore.getState()
    expect(state.theme).toBe('dark')
    expect(state.sidebarOpen).toBe(false)
    expect(state.toastQueue).toEqual([])
    expect(state.activeModal).toBeNull()
  })

  it('sets theme', () => {
    useUIStore.getState().setTheme('light')
    expect(useUIStore.getState().theme).toBe('light')
  })

  it('toggles sidebar', () => {
    expect(useUIStore.getState().sidebarOpen).toBe(false)
    useUIStore.getState().toggleSidebar()
    expect(useUIStore.getState().sidebarOpen).toBe(true)
    useUIStore.getState().toggleSidebar()
    expect(useUIStore.getState().sidebarOpen).toBe(false)
  })

  it('sets sidebar open', () => {
    useUIStore.getState().setSidebarOpen(true)
    expect(useUIStore.getState().sidebarOpen).toBe(true)
  })

  it('adds a toast', () => {
    useUIStore.getState().addToast('Test message', 'success')
    const queue = useUIStore.getState().toastQueue
    expect(queue).toHaveLength(1)
    expect(queue[0].message).toBe('Test message')
    expect(queue[0].variant).toBe('success')
  })

  it('adds multiple toasts', () => {
    useUIStore.getState().addToast('First', 'success')
    useUIStore.getState().addToast('Second', 'error')
    expect(useUIStore.getState().toastQueue).toHaveLength(2)
  })

  it('removes a toast', () => {
    useUIStore.getState().addToast('Test', 'info')
    const toastId = useUIStore.getState().toastQueue[0].id
    useUIStore.getState().removeToast(toastId)
    expect(useUIStore.getState().toastQueue).toHaveLength(0)
  })

  it('opens and closes modal', () => {
    useUIStore.getState().openModal('search')
    expect(useUIStore.getState().activeModal).toBe('search')
    useUIStore.getState().closeModal()
    expect(useUIStore.getState().activeModal).toBeNull()
  })

  it('auto-removes toast after duration', () => {
    vi.useFakeTimers()
    useUIStore.getState().addToast('Auto remove', 'info', 1000)
    expect(useUIStore.getState().toastQueue).toHaveLength(1)

    vi.advanceTimersByTime(1000)
    expect(useUIStore.getState().toastQueue).toHaveLength(0)

    vi.useRealTimers()
  })
})