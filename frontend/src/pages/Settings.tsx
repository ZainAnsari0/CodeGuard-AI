import { useState } from 'react'
import { useAuthStore } from '../store/authStore'
import { Settings as SettingsIcon, User, Shield, Bell } from 'lucide-react'

export function Settings() {
  const { user } = useAuthStore()
  const [activeTab, setActiveTab] = useState('profile')

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-text-primary">Settings</h1>
        <p className="text-text-secondary mt-1">Manage your account and preferences.</p>
      </div>

      <div className="flex flex-col md:flex-row gap-6">
        {/* Sidebar */}
        <div className="w-full md:w-64 shrink-0 space-y-1">
          <button
            onClick={() => setActiveTab('profile')}
            className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'profile'
                ? 'bg-brand-500/10 text-brand-400'
                : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary'
            }`}
          >
            <User className="w-4 h-4" />
            Profile
          </button>
          <button
            onClick={() => setActiveTab('security')}
            className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'security'
                ? 'bg-brand-500/10 text-brand-400'
                : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary'
            }`}
          >
            <Shield className="w-4 h-4" />
            Security
          </button>
          <button
            onClick={() => setActiveTab('notifications')}
            className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'notifications'
                ? 'bg-brand-500/10 text-brand-400'
                : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary'
            }`}
          >
            <Bell className="w-4 h-4" />
            Notifications
          </button>
          <button
            onClick={() => setActiveTab('preferences')}
            className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'preferences'
                ? 'bg-brand-500/10 text-brand-400'
                : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary'
            }`}
          >
            <SettingsIcon className="w-4 h-4" />
            Preferences
          </button>
        </div>

        {/* Content */}
        <div className="flex-1">
          <div className="glass-card p-6">
            {activeTab === 'profile' && (
              <div className="space-y-4">
                <h2 className="text-lg font-semibold text-text-primary border-b border-border-default pb-4">Profile Information</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">Full Name</label>
                    <input type="text" className="w-full bg-bg-tertiary border border-border-default rounded-lg px-4 py-2 text-text-primary outline-none focus:border-brand-500" defaultValue={user?.full_name || ''} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">Email Address</label>
                    <input type="email" className="w-full bg-bg-tertiary border border-border-default rounded-lg px-4 py-2 text-text-primary outline-none focus:border-brand-500 opacity-50" defaultValue={user?.email || ''} readOnly />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">Role</label>
                    <input type="text" className="w-full bg-bg-tertiary border border-border-default rounded-lg px-4 py-2 text-text-primary outline-none focus:border-brand-500 opacity-50 capitalize" defaultValue={user?.role || ''} readOnly />
                  </div>
                </div>
                <div className="pt-4">
                  <button className="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-lg text-sm font-medium transition-colors">Save Changes</button>
                </div>
              </div>
            )}
            {activeTab === 'security' && (
              <div className="space-y-4">
                <h2 className="text-lg font-semibold text-text-primary border-b border-border-default pb-4">Security Settings</h2>
                <p className="text-sm text-text-secondary">Manage your password and security preferences.</p>
                <div>
                  <button className="px-4 py-2 border border-border-default hover:bg-bg-tertiary text-text-primary rounded-lg text-sm font-medium transition-colors">Change Password</button>
                </div>
              </div>
            )}
            {activeTab === 'notifications' && (
              <div className="space-y-4">
                <h2 className="text-lg font-semibold text-text-primary border-b border-border-default pb-4">Notification Preferences</h2>
                <div className="space-y-3">
                  <label className="flex items-center gap-3">
                    <input type="checkbox" className="rounded text-brand-500 bg-bg-tertiary border-border-default" defaultChecked />
                    <span className="text-sm text-text-primary">Email me when a scan completes</span>
                  </label>
                  <label className="flex items-center gap-3">
                    <input type="checkbox" className="rounded text-brand-500 bg-bg-tertiary border-border-default" defaultChecked />
                    <span className="text-sm text-text-primary">Email me about new critical vulnerabilities</span>
                  </label>
                </div>
              </div>
            )}
            {activeTab === 'preferences' && (
              <div className="space-y-4">
                <h2 className="text-lg font-semibold text-text-primary border-b border-border-default pb-4">System Preferences</h2>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">Default Scan Language</label>
                    <select className="w-full max-w-xs bg-bg-tertiary border border-border-default rounded-lg px-4 py-2 text-text-primary outline-none focus:border-brand-500">
                      <option value="auto">Auto-detect</option>
                      <option value="python">Python</option>
                      <option value="javascript">JavaScript</option>
                    </select>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
