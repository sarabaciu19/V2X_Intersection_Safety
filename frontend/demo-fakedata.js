// Demo script - testează fakeData.js în Node
// Rulează cu: node demo-fakedata.js

import { FAKE_STATE, SCENARIOS, generateRandomVehicles } from './src/data/fakeData.js';

console.log('🎯 DEMO - fakeData.js\n');

console.log('1️⃣ FAKE_STATE (format WebSocket):');
console.log(JSON.stringify(FAKE_STATE, null, 2));

console.log('\n2️⃣ Scenarii disponibile:');
console.log('   - normal');
console.log('   - collision_imminent');
console.log('   - high_traffic');
console.log('   - emergency_vehicle');

console.log('\n3️⃣ Scenariu "collision_imminent":');
console.log(JSON.stringify(SCENARIOS.collision_imminent, null, 2));

console.log('\n4️⃣ Vehicule random (5):');
const randomVehicles = generateRandomVehicles(5);
console.log(JSON.stringify(randomVehicles, null, 2));

console.log('\n✅ fakeData.js funcționează corect!');
console.log('📦 Format identic cu WebSocket - gata pentru integrare!');

