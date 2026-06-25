import { useState, useRef } from 'react'
import { useAuthStore } from '../store/authStore'
import { useUIStore } from '../store/uiStore'
import { apiFetch } from '../lib/api'
import { Settings as SettingsIcon, User, Shield, Bell, Camera, Save, Lock, Loader2 } from 'lucide-react'

type TabId = 'profile' | 'security' | 'notifications' | 'preferences'

const tabs: { id: TabId; label: string; icon: typeof User }[] = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'preferences', label: 'Preferences', icon: SettingsIcon },
]

function getInitials(name: string): string {
  return name
    .split(' ')
    .map(part => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export function Settings() {
  const { user, setUser } = useAuthStore()
  const { addToast } = useUIStore()
  const [activeTab, setActiveTab] = useState<TabId>('profile')

  // Profile state
  const [fullName, setFullName] = useState(user?.full_name || '')
  const [saving, setSaving] = useState(false)

  // Password state
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordSaving, setPasswordSaving] = useState(false)
  const [passwordError, setPasswordError] = useState<string | null>(null)

  // Notification state
  const [notifyScanComplete, setNotifyScanComplete] = useState(true)
  const [notifyCriticalVuln, setNotifyCriticalVuln] = useState(true)
  const [notifyWeeklyDigest, setNotifyWeeklyDigest] = useState(false)

  // Preferences state
  const [defaultLanguage, setDefaultLanguage] = useState('auto')
  const [preferencesSaving, setPreferencesSaving] = useState(false)

  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleSaveProfile = async () => {
    if (!fullName.trim()) {
      addToast('Name cannot be empty', 'error')
      return
    }
    setSaving(true)
    try {
      const result = await apiFetch<{ message: string; data: { user: any } }>(
        '/api/v1/auth/me',
        {
          method: 'PATCH',
          body: JSON.stringify({ full_name: fullName.trim() }),
        }
      )
      setUser(result.data.user)
      addToast('Profile updated successfully', 'success')
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Failed to update profile', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleChangePassword = async () => {
    setPasswordError(null)
    if (!currentPassword || !newPassword) {
      setPasswordError('Please fill in all password fields')
      return
    }
    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match')
      return
    }
    if (newPassword.length < 8) {
      setPasswordError('Password must be at least 8 characters')
      return
    }
    setPasswordSaving(true)
    try {
      await apiFetch('/api/v1/auth/me', {
        method: 'PATCH',
        body: JSON.stringify({ password: newPassword }),
      })
      addToast('Password changed successfully', 'success')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Failed to change password', 'error')
    } finally {
      setPasswordSaving(false)
    }
  }

  const handleSavePreferences = async () => {
    setPreferencesSaving(true)
    try {
      await apiFetch('/api/v1/auth/me', {
        method: 'PATCH',
        body: JSON.stringify({
          preferences: {
            default_language: defaultLanguage,
            notifications: {
              scan_complete: notifyScanComplete,
              critical_vuln: notifyCriticalVuln,
              weekly_digest: notifyWeeklyDigest,
            },
          },
        }),
      })
      addToast('Preferences saved successfully', 'success')
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Failed to save preferences', 'error')
    } finally {
      setPreferencesSaving(false)
    }
  }

  return (
    <div className="animate-fade-in">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-headline-md font-semibold text-on-surface tracking-tight">
          Settings
        </h1>
        <p className="text-body-sm text-on-surface-variant mt-1">
          Manage your account and preferences.
        </p>
      </div>

      <div className="max-w-4xl mx-auto">
        {/* Tab Navigation */}
        <div className="flex border-b border-outline-variant mb-6">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 px-5 py-3 text-label-md uppercase tracking-label transition-colors relative
                  ${isActive
                    ? 'text-primary'
                    : 'text-on-surface-variant hover:text-on-surface'
                  }
                `}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
                {isActive && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-primary to-secondary rounded-full" />
                )}
              </button>
            )
          })}
        </div>

        {/* Tab Content */}
        <div className="glass-panel p-6 md:p-8">
          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <div className="space-y-8 animate-fade-in">
              {/* Avatar Section */}
              <div className="flex items-center gap-6 pb-6 border-b border-outline-variant">
                <div className="relative group">
                  {/* Gradient border ring */}
                  <div className="w-20 h-20 rounded-full p-[2px] bg-gradient-to-br from-primary to-secondary">
                    <div className="w-full h-full rounded-full bg-surface-lowest flex items-center justify-center text-headline-md font-semibold text-primary">
                      {user?.full_name ? getInitials(user.full_name) : '??'}
                    </div>
                  </div>
                  {/* Camera overlay */}
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="absolute inset-0 rounded-full bg-surface-lowest/60 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                    aria-label="Change avatar"
                  >
                    <Camera className="w-5 h-5 text-on-surface" />
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    aria-hidden="true"
                  />
                </div>
                <div>
                  <h2 className="text-headline-sm font-semibold text-on-surface">
                    {user?.full_name || 'User'}
                  </h2>
                  <p className="text-body-sm text-on-surface-variant mt-0.5">
                    {user?.email || ''}
                  </p>
                  <span className="inline-block mt-1.5 text-label-sm uppercase tracking-label text-primary bg-primary/10 px-2 py-0.5 rounded-md">
                    {user?.role || 'member'}
                  </span>
                </div>
              </div>

              {/* Profile Form */}
              <div className="space-y-5">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label className="block text-label-sm uppercase tracking-label text-on-surface-variant mb-2">
                      Full Name
                    </label>
                    <input
                      type="text"
                      className="input-glow w-full rounded-lg px-4 py-2.5 text-on-surface text-body-md"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-label-sm uppercase tracking-label text-on-surface-variant mb-2">
                      Email Address
                    </label>
                    <input
                      type="email"
                      className="input-glow w-full rounded-lg px-4 py-2.5 text-on-surface-variant text-body-md opacity-60 cursor-not-allowed"
                      defaultValue={user?.email || ''}
                      readOnly
                    />
                  </div>
                  <div>
                    <label className="block text-label-sm uppercase tracking-label text-on-surface-variant mb-2">
                      Role
                    </label>
                    <input
                      type="text"
                      className="input-glow w-full rounded-lg px-4 py-2.5 text-on-surface-variant text-body-md opacity-60 cursor-not-allowed capitalize"
                      defaultValue={user?.role || ''}
                      readOnly
                    />
                  </div>
                </div>

                <div className="pt-3 flex justify-end">
                  <button
                    onClick={handleSaveProfile}
                    disabled={saving}
                    className="btn-gradient rounded-lg px-6 py-2.5 text-label-md uppercase tracking-label flex items-center gap-2"
                  >
                    {saving ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Save className="w-4 h-4" />
                    )}
                    {saving ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Security Tab */}
          {activeTab === 'security' && (
            <div className="space-y-8 animate-fade-in">
              <div className="pb-6 border-b border-outline-variant">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Lock className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <h2 className="text-headline-sm font-semibold text-on-surface">
                      Security Settings
                    </h2>
                    <p className="text-body-sm text-on-surface-variant mt-0.5">
                      Manage your password and security preferences.
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-5 max-w-lg">
                <div>
                  <label className="block text-label-sm uppercase tracking-label text-on-surface-variant mb-2">
                    Current Password
                  </label>
                  <input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    className="input-glow w-full rounded-lg px-4 py-2.5 text-on-surface text-body-md"
                    placeholder="Enter current password"
                  />
                </div>
                <div>
                  <label className="block text-label-sm uppercase tracking-label text-on-surface-variant mb-2">
                    New Password
                  </label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="input-glow w-full rounded-lg px-4 py-2.5 text-on-surface text-body-md"
                    placeholder="Enter new password"
                  />
                </div>
                <div>
                  <label className="block text-label-sm uppercase tracking-label text-on-surface-variant mb-2">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="input-glow w-full rounded-lg px-4 py-2.5 text-on-surface text-body-md"
                    placeholder="Confirm new password"
                  />
                </div>

                {passwordError && (
                  <div className="flex items-center gap-2 text-label-sm text-severity-critical bg-severity-critical-bg px-4 py-2.5 rounded-lg border border-severity-critical/20">
                    <span>{passwordError}</span>
                  </div>
                )}

                <div className="pt-3 flex justify-end">
                  <button
                    onClick={handleChangePassword}
                    disabled={passwordSaving}
                    className="btn-gradient rounded-lg px-6 py-2.5 text-label-md uppercase tracking-label flex items-center gap-2"
                  >
                    {passwordSaving ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Shield className="w-4 h-4" />
                    )}
                    {passwordSaving ? 'Changing...' : 'Change Password'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Notifications Tab */}
          {activeTab === 'notifications' && (
            <div className="space-y-8 animate-fade-in">
              <div className="pb-6 border-b border-outline-variant">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Bell className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <h2 className="text-headline-sm font-semibold text-on-surface">
                      Notification Preferences
                    </h2>
                    <p className="text-body-sm text-on-surface-variant mt-0.5">
                      Choose what notifications you receive.
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                {/* Scan Complete Toggle */}
                <label className="glass-card flex items-center justify-between p-4 cursor-pointer group hover:border-primary/30 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center">
                      <Bell className="w-4 h-4 text-primary" />
                    </div>
                    <div>
                      <span className="text-body-md text-on-surface block">Scan Completion</span>
                      <span className="text-label-sm text-on-surface-variant block mt-0.5">
                        Get notified when a scan finishes
                      </span>
                    </div>
                  </div>
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={notifyScanComplete}
                      onChange={(e) => setNotifyScanComplete(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-10 h-5 bg-surface-highest rounded-full peer-checked:bg-primary/40 transition-colors" />
                    <div className="absolute left-0.5 top-0.5 w-4 h-4 bg-on-surface-variant rounded-full transition-all peer-checked:translate-x-5 peer-checked:bg-primary" />
                  </div>
                </label>

                {/* Critical Vuln Toggle */}
                <label className="glass-card flex items-center justify-between p-4 cursor-pointer group hover:border-primary/30 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-md bg-severity-critical/10 flex items-center justify-center">
                      <Bell className="w-4 h-4 text-severity-critical" />
                    </div>
                    <div>
                      <span className="text-body-md text-on-surface block">Critical Vulnerabilities</span>
                      <span className="text-label-sm text-on-surface-variant block mt-0.5">
                        Get alerted about critical severity findings
                      </span>
                    </div>
                  </div>
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={notifyCriticalVuln}
                      onChange={(e) => setNotifyCriticalVuln(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-10 h-5 bg-surface-highest rounded-full peer-checked:bg-primary/40 transition-colors" />
                    <div className="absolute left-0.5 top-0.5 w-4 h-4 bg-on-surface-variant rounded-full transition-all peer-checked:translate-x-5 peer-checked:bg-primary" />
                  </div>
                </label>

                {/* Weekly Digest Toggle */}
                <label className="glass-card flex items-center justify-between p-4 cursor-pointer group hover:border-primary/30 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-md bg-accent-500/10 flex items-center justify-center">
                      <Bell className="w-4 h-4 text-accent-500" />
                    </div>
                    <div>
                      <span className="text-body-md text-on-surface block">Weekly Digest</span>
                      <span className="text-label-sm text-on-surface-variant block mt-0.5">
                        Receive a weekly summary of your project activity
                      </span>
                    </div>
                  </div>
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={notifyWeeklyDigest}
                      onChange={(e) => setNotifyWeeklyDigest(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-10 h-5 bg-surface-highest rounded-full peer-checked:bg-primary/40 transition-colors" />
                    <div className="absolute left-0.5 top-0.5 w-4 h-4 bg-on-surface-variant rounded-full transition-all peer-checked:translate-x-5 peer-checked:bg-primary" />
                  </div>
                </label>
              </div>

              <div className="pt-3 flex justify-end">
                <button
                  onClick={handleSavePreferences}
                  disabled={preferencesSaving}
                  className="btn-gradient rounded-lg px-6 py-2.5 text-label-md uppercase tracking-label flex items-center gap-2"
                >
                  {preferencesSaving ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  {preferencesSaving ? 'Saving...' : 'Save Preferences'}
                </button>
              </div>
            </div>
          )}

          {/* Preferences Tab */}
          {activeTab === 'preferences' && (
            <div className="space-y-8 animate-fade-in">
              <div className="pb-6 border-b border-outline-variant">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <SettingsIcon className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <h2 className="text-headline-sm font-semibold text-on-surface">
                      System Preferences
                    </h2>
                    <p className="text-body-sm text-on-surface-variant mt-0.5">
                      Configure default behaviors and display options.
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-5 max-w-lg">
                <div>
                  <label className="block text-label-sm uppercase tracking-label text-on-surface-variant mb-2">
                    Default Scan Language
                  </label>
                  <select
                    value={defaultLanguage}
                    onChange={(e) => setDefaultLanguage(e.target.value)}
                    className="input-glow w-full rounded-lg px-4 py-2.5 text-on-surface text-body-md appearance-none cursor-pointer"
                  >
                    <option value="auto">Auto-detect</option>
                    <option value="python">Python</option>
                    <option value="javascript">JavaScript</option>
                    <option value="typescript">TypeScript</option>
                    <option value="java">Java</option>
                    <option value="go">Go</option>
                  </select>
                  <p className="text-label-sm text-on-surface-variant mt-1.5">
                    Language used when no explicit language is specified for a scan.
                  </p>
                </div>

                <div>
                  <label className="block text-label-sm uppercase tracking-label text-on-surface-variant mb-2">
                    Report Theme
                  </label>
                  <select
                    className="input-glow w-full rounded-lg px-4 py-2.5 text-on-surface text-body-md appearance-none cursor-pointer"
                    defaultValue="dark"
                  >
                    <option value="dark">Dark (Cyber-Sec Glass)</option>
                    <option value="light">Light</option>
                    <option value="system">System</option>
                  </select>
                  <p className="text-label-sm text-on-surface-variant mt-1.5">
                    Visual theme for exported reports and shared links.
                  </p>
                </div>
              </div>

              <div className="pt-3 flex justify-end">
                <button
                  onClick={handleSavePreferences}
                  disabled={preferencesSaving}
                  className="btn-gradient rounded-lg px-6 py-2.5 text-label-md uppercase tracking-label flex items-center gap-2"
                >
                  {preferencesSaving ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  {preferencesSaving ? 'Saving...' : 'Save Preferences'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}