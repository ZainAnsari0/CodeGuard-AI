import { Fragment, useState } from 'react'
import { Dialog, DialogPanel, Transition, TransitionChild } from '@headlessui/react'
import { Search, X } from 'lucide-react'
import { useUIStore } from '../../store/uiStore'

export function SearchModal() {
  const { activeModal, closeModal } = useUIStore()
  const isOpen = activeModal === 'search'
  const [query, setQuery] = useState('')

  return (
    <Transition show={isOpen} as={Fragment}>
      <Dialog onClose={closeModal} className="relative z-50">
        <TransitionChild
          as={Fragment}
          enter="ease-out duration-200"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-150"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-bg-overlay/60 backdrop-blur-sm" />
        </TransitionChild>

        <div className="fixed inset-0 flex items-start justify-center pt-[20vh]">
          <TransitionChild
            as={Fragment}
            enter="ease-out duration-200"
            enterFrom="opacity-0 scale-95"
            enterTo="opacity-100 scale-100"
            leave="ease-in duration-150"
            leaveFrom="opacity-100 scale-100"
            leaveTo="opacity-0 scale-95"
          >
            <DialogPanel className="glass-card w-full max-w-lg mx-4 p-0 shadow-modal overflow-hidden">
              <div className="flex items-center gap-3 px-4 py-3 border-b border-border-default">
                <Search className="w-5 h-5 text-text-muted shrink-0" />
                <input
                  type="text"
                  placeholder="Search projects, scans, settings..."
                  className="flex-1 bg-transparent text-text-primary text-sm outline-none placeholder:text-text-muted"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  autoFocus
                />
                <button
                  onClick={closeModal}
                  className="text-text-muted hover:text-text-primary transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="px-4 py-6 text-center">
                {query.trim() === '' ? (
                  <p className="text-sm text-text-muted">Start typing to search...</p>
                ) : (
                  <p className="text-sm text-text-muted">No results for &ldquo;{query}&rdquo;</p>
                )}
              </div>

              <div className="border-t border-border-default px-4 py-2">
                <div className="flex items-center gap-2 text-xs text-text-muted">
                  <kbd className="px-1.5 py-0.5 rounded bg-bg-tertiary text-text-muted text-[11px]">Esc</kbd>
                  <span>to close</span>
                </div>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </Dialog>
    </Transition>
  )
}