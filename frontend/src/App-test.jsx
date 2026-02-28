import React from 'react';

function App() {
  return (
    <div style={{
      padding: '20px',
      backgroundColor: '#1a1a1a',
      color: 'white',
      minHeight: '100vh',
      fontFamily: 'Arial'
    }}>
      <h1>🚗 V2X Intersection Safety System - TEST</h1>
      <p>✅ React funcționează!</p>
      <p>✅ App.jsx se încarcă corect!</p>

      <div style={{ marginTop: '20px', padding: '20px', backgroundColor: '#2a2a2a', borderRadius: '8px' }}>
        <h2>🔧 Diagnostic</h2>
        <ul>
          <li>✅ JavaScript rulează</li>
          <li>✅ React render OK</li>
          <li>✅ Styling funcționează</li>
        </ul>
      </div>

      <div style={{ marginTop: '20px', padding: '20px', backgroundColor: '#059669', borderRadius: '8px' }}>
        <h2>✅ SUCCESS!</h2>
        <p>Dacă vezi asta, aplicația funcționează!</p>
        <p>Problema era probabil în imports sau componente.</p>
      </div>
    </div>
  );
}

export default App;

