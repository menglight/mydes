import React, { useState } from 'react';

function DietaryPreferencesSettings() {
  const [cuisineTypes, setCuisineTypes] = useState(''); // Simple text input for comma-separated values
  const [preferredFlavors, setPreferredFlavors] = useState('');
  const [priceRange, setPriceRange] = useState('');
  const [dietaryRestrictions, setDietaryRestrictions] = useState('');

  const handleSubmit = (event) => {
    event.preventDefault();
    // TODO: Handle dietary preferences update logic
    console.log('Updating dietary preferences:', {
      cuisineTypes,
      preferredFlavors,
      priceRange,
      dietaryRestrictions,
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <h3>Dietary Preferences</h3>
      <div>
        <label htmlFor="cuisineTypes">Cuisine Types (comma-separated):</label>
        <input
          type="text"
          id="cuisineTypes"
          value={cuisineTypes}
          onChange={(e) => setCuisineTypes(e.target.value)}
        />
      </div>
      <div>
        <label htmlFor="preferredFlavors">Preferred Flavors (comma-separated):</label>
        <input
          type="text"
          id="preferredFlavors"
          value={preferredFlavors}
          onChange={(e) => setPreferredFlavors(e.target.value)}
        />
      </div>
      <div>
        <label htmlFor="priceRange">Price Range (e.g., $, $$, $$$):</label>
        <input
          type="text"
          id="priceRange"
          value={priceRange}
          onChange={(e) => setPriceRange(e.target.value)}
        />
      </div>
      <div>
        <label htmlFor="dietaryRestrictions">Dietary Restrictions (comma-separated):</label>
        <input
          type="text"
          id="dietaryRestrictions"
          value={dietaryRestrictions}
          onChange={(e) => setDietaryRestrictions(e.target.value)}
        />
      </div>
      <button type="submit">Save Dietary Preferences</button>
    </form>
  );
}

export default DietaryPreferencesSettings;
