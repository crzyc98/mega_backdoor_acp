/**
 * MappingProfileSelector Component
 *
 * T042: Component for managing saved mapping profiles in the import wizard.
 * Allows users to select, create, update, and delete mapping profiles.
 */

import { useState, useEffect } from "react";
import type { MappingProfile } from "../types/importWizard";
import {
  listMappingProfiles,
  createMappingProfile,
  deleteMappingProfile,
} from "../services/importWizardService";
import styles from "./MappingProfileSelector.module.css";

interface MappingProfileSelectorProps {
  workspaceId: string;
  currentMapping: Record<string, string>;
  dateFormat?: string;
  onApplyProfile: (profile: MappingProfile) => void;
  onSaveProfile?: (name: string, description?: string) => void;
}

export function MappingProfileSelector({
  workspaceId,
  currentMapping,
  dateFormat,
  onApplyProfile,
  onSaveProfile,
}: MappingProfileSelectorProps) {
  const [profiles, setProfiles] = useState<MappingProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [saveName, setSaveName] = useState("");
  const [saveDescription, setSaveDescription] = useState("");
  const [saving, setSaving] = useState(false);

  // Load profiles on mount
  useEffect(() => {
    loadProfiles();
  }, [workspaceId]);

  const loadProfiles = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await listMappingProfiles(workspaceId);
      setProfiles(result.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load profiles");
    } finally {
      setLoading(false);
    }
  };

  const handleApply = (profile: MappingProfile) => {
    onApplyProfile(profile);
  };

  const handleDelete = async (profileId: string) => {
    if (!confirm("Are you sure you want to delete this profile?")) {
      return;
    }

    try {
      await deleteMappingProfile(workspaceId, profileId);
      setProfiles(profiles.filter((p) => p.id !== profileId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete profile");
    }
  };

  const handleSave = async () => {
    if (!saveName.trim()) {
      setError("Profile name is required");
      return;
    }

    try {
      setSaving(true);
      setError(null);

      const newProfile = await createMappingProfile(workspaceId, {
        name: saveName.trim(),
        description: saveDescription.trim() || undefined,
        column_mapping: currentMapping,
        date_format: dateFormat,
      });

      setProfiles([...profiles, newProfile]);
      setShowSaveDialog(false);
      setSaveName("");
      setSaveDescription("");
      onSaveProfile?.(saveName.trim(), saveDescription.trim() || undefined);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save profile");
    } finally {
      setSaving(false);
    }
  };

  const hasCurrentMapping = Object.keys(currentMapping).length > 0;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h4 className={styles.title}>Saved Mapping Profiles</h4>
        {hasCurrentMapping && (
          <button
            className={styles.saveButton}
            onClick={() => setShowSaveDialog(true)}
            type="button"
          >
            Save Current Mapping
          </button>
        )}
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {loading ? (
        <div className={styles.loading}>Loading profiles...</div>
      ) : profiles.length === 0 ? (
        <div className={styles.empty}>
          <p>No saved profiles yet.</p>
          <p className={styles.hint}>
            Save your column mappings to reuse them in future imports.
          </p>
        </div>
      ) : (
        <ul className={styles.profileList}>
          {profiles.map((profile) => (
            <li key={profile.id} className={styles.profileItem}>
              <div className={styles.profileInfo}>
                <span className={styles.profileName}>
                  {profile.name}
                  {profile.is_default && (
                    <span className={styles.defaultBadge}>Default</span>
                  )}
                </span>
                {profile.description && (
                  <span className={styles.profileDescription}>
                    {profile.description}
                  </span>
                )}
              </div>
              <div className={styles.profileActions}>
                <button
                  className={styles.applyButton}
                  onClick={() => handleApply(profile)}
                  type="button"
                >
                  Apply
                </button>
                <button
                  className={styles.deleteButton}
                  onClick={() => handleDelete(profile.id)}
                  type="button"
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {showSaveDialog && (
        <div className={styles.dialogOverlay}>
          <div className={styles.dialog}>
            <h4 className={styles.dialogTitle}>Save Mapping Profile</h4>
            <div className={styles.formGroup}>
              <label htmlFor="profileName">Name *</label>
              <input
                id="profileName"
                type="text"
                value={saveName}
                onChange={(e) => setSaveName(e.target.value)}
                placeholder="e.g., Payroll System Export"
                className={styles.input}
                autoFocus
              />
            </div>
            <div className={styles.formGroup}>
              <label htmlFor="profileDescription">Description</label>
              <textarea
                id="profileDescription"
                value={saveDescription}
                onChange={(e) => setSaveDescription(e.target.value)}
                placeholder="Optional description..."
                className={styles.textarea}
                rows={2}
              />
            </div>
            <div className={styles.dialogActions}>
              <button
                className={styles.cancelButton}
                onClick={() => {
                  setShowSaveDialog(false);
                  setSaveName("");
                  setSaveDescription("");
                }}
                type="button"
                disabled={saving}
              >
                Cancel
              </button>
              <button
                className={styles.confirmButton}
                onClick={handleSave}
                type="button"
                disabled={saving || !saveName.trim()}
              >
                {saving ? "Saving..." : "Save Profile"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
