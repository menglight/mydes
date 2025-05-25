import React, { useState } from 'react';

function UserProfileSettings() {
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const [bodyType, setBodyType] = useState('');

  const handleSubmit = (event) => {
    event.preventDefault();
    // TODO: Handle profile update logic
    console.log('Updating profile:', { age, gender, bodyType });
  };

  return (
    <form onSubmit={handleSubmit}>
      <h3>User Profile</h3>
      <div>
        <label htmlFor="age">Age:</label>
        <input
          type="number"
          id="age"
          value={age}
          onChange={(e) => setAge(e.target.value)}
        />
      </div>
      <div>
        <label htmlFor="gender">Gender:</label>
        <input
          type="text"
          id="gender"
          value={gender}
          onChange={(e) => setGender(e.target.value)}
        />
      </div>
      <div>
        <label htmlFor="bodyType">Body Type:</label>
        <input
          type="text"
          id="bodyType"
          value={bodyType}
          onChange={(e) => setBodyType(e.target.value)}
        />
      </div>
      <button type="submit">Save Profile</button>
    </form>
  );
}

export default UserProfileSettings;
