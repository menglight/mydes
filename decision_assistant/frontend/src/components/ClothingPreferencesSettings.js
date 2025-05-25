import React, { useState } from 'react';

function ClothingPreferencesSettings() {
  const [styles, setStyles] = useState(''); // Simple text input for comma-separated values
  const [preferredColors, setPreferredColors] = useState('');
  const [preferredBrands, setPreferredBrands] = useState('');

  const handleSubmit = (event) => {
    event.preventDefault();
    // TODO: Handle clothing preferences update logic
    console.log('Updating clothing preferences:', {
      styles,
      preferredColors,
      preferredBrands,
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <h3>Clothing Preferences</h3>
      <div>
        <label htmlFor="styles">Styles (comma-separated):</label>
        <input
          type="text"
          id="styles"
          value={styles}
          onChange={(e) => setStyles(e.target.value)}
        />
      </div>
      <div>
        <label htmlFor="preferredColors">Preferred Colors (comma-separated):</label>
        <input
          type="text"
          id="preferredColors"
          value={preferredColors}
          onChange={(e) => setPreferredColors(e.target.value)}
        />
      </div>
      <div>
        <label htmlFor="preferredBrands">Preferred Brands (comma-separated):</label>
        <input
          type="text"
          id="preferredBrands"
          value={preferredBrands}
          onChange={(e) => setPreferredBrands(e.target.value)}
        />
      </div>
      <button type="submit">Save Clothing Preferences</button>
    </form>
  );
}

export default ClothingPreferencesSettings;
