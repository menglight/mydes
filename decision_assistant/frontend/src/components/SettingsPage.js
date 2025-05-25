import React from 'react';
import UserProfileSettings from './UserProfileSettings';
import DietaryPreferencesSettings from './DietaryPreferencesSettings';
import ClothingPreferencesSettings from './ClothingPreferencesSettings';

function SettingsPage() {
  return (
    <div>
      <h2>Settings</h2>
      <UserProfileSettings />
      <hr />
      <DietaryPreferencesSettings />
      <hr />
      <ClothingPreferencesSettings />
    </div>
  );
}

export default SettingsPage;
