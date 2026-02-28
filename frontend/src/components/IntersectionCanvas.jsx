import React, { useRef, useEffect, useCallback } from 'react';

// ── Geometrie (trebuie sa fie identica cu backend models/vehicle.py) ──
const CX = 400, CY = 400;   // centrul intersectiei
const LANE_W = 50;         // latimea unei benzi px
const ROAD_W = LANE_W * 2; // 100px — 2 benzi per directie
const HALF = ROAD_W / 2;   // 50px

// Culori vehicule
const STATE_COLOR = {
  moving: '#60A5FA',   // blue-400
  waiting: '#FBBF24',  // amber-400
  crossing: '#10B981', // emerald-500
  done: '#9CA3AF',     // gray-400
  braking: '#F87171',  // red-400 (glow)
  yielding: '#F87171', // red-400 (glow)
};

const INTENT_ICON = { straight: '↑', left: '↰', right: '↱' };
const PRIORITY_COLOR = { emergency: '#EF4444', normal: null };

// Heading (unghi radiani) per directie, pentru a roti vehiculul corect
// Folosit ca fallback daca backend-ul nu trimite heading
const HEADING = { N: Math.PI, S: 0, V: Math.PI / 2, E: -Math.PI / 2 };

// Returneaza unghiul de rotatie al vehiculului:
// - daca backend trimite 'heading' (dupa viraj), il folosim direct
// - altfel fallback la HEADING per directie de intrare
function getVehicleHeading(v) {
  if (v.heading !== undefined && v.heading !== null) return v.heading;
  return HEADING[v.direction] ?? 0;
}

// ── Risk zone constants ──
const TTC_CRITICAL = 1.5;  // secunde — rosu
const TTC_WARNING = 3.0;  // secunde — portocaliu
const RISK_CIRCLE_RADIUS = 80; // px

const IntersectionCanvas = ({
  vehicles = [],
  semaphore = {},
  risk = { risk: false, pair: null, ttc: 999, ttc_per_vehicle: {} },
  collisions = [],
  agentsMemory = {},
  cooperation = true,
  onGrantClearance = null,
  dimensions = { width: 800, height: 800 },
}) => {
  const canvasRef = useRef(null);
  const animFrameRef = useRef(null);

  // Hit-test: returns vehicle clicked (only waiting ones are clickable in manual mode)
  const getClickedVehicle = (canvas, clientX, clientY) => {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const mx = (clientX - rect.left) * scaleX;
    const my = (clientY - rect.top) * scaleY;
    for (const v of vehicles) {
      const dx = mx - v.x, dy = my - v.y;
      if (Math.abs(dx) < 22 && Math.abs(dy) < 28) return v;
    }
    return null;
  };

  const handleClick = (e) => {
    if (!onGrantClearance) return;
    const v = getClickedVehicle(canvasRef.current, e.clientX, e.clientY);
    if (v && v.state === 'waiting') {
      onGrantClearance(v.id);
    }
  };

  // ── Main draw function (called per frame when risk active) ──
  const draw = useCallback((now) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;

    ctx.clearRect(0, 0, W, H);

    // 1. Fundal (iarba/trotuar)
    ctx.fillStyle = '#1a2e1a';
    ctx.fillRect(0, 0, W, H);

    // 2. Drumuri
    drawRoads(ctx, W, H);

    // 3. Marcaje si benzi
    drawLaneMarkings(ctx, W, H);

    // 4. Linii de stop
    drawStopLines(ctx);

    // 5. Zona centrala a intersectiei
    drawIntersectionBox(ctx);

    // 6. Semafor (indicator luminos)
    drawSemaphore(ctx, semaphore);

    // 7. Vehicule
    vehicles.forEach(v => drawVehicle(ctx, v, !!onGrantClearance, now));

    // 8. Decision Arrows (A franeaza din cauza lui B)
    drawDecisionArrows(ctx, vehicles, agentsMemory, now);

    // 9. Risk zone (cerc + linie + label)
    if (risk && risk.risk && risk.pair) {
      drawRiskZone(ctx, risk, vehicles, now);
    }

    // 10. Coliziuni (explosii animate)
    if (collisions && collisions.length > 0) {
      drawCollisions(ctx, collisions, vehicles, now);
    }

  }, [vehicles, semaphore, cooperation, risk, collisions, agentsMemory, onGrantClearance]);

  useEffect(() => {
    // Animate at 60fps for smooth pulsing and arrows
    const animate = () => {
      draw(Date.now());
      animFrameRef.current = requestAnimationFrame(animate);
    };
    animate();
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [draw]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
      <canvas
        ref={canvasRef}
        width={dimensions.width}
        height={dimensions.height}
        onClick={handleClick}
        style={{
          maxWidth: '100%',
          maxHeight: '100%',
          border: '2px solid #374151', borderRadius: 8, display: 'block',
          cursor: onGrantClearance ? 'pointer' : 'default',
        }}
      />
      {onGrantClearance && (
        <div style={{
          position: 'absolute', top: 10, left: '50%', transform: 'translateX(-50%)',
          background: 'rgba(245, 158, 11, 0.15)', border: '1px solid #F59E0B', borderRadius: 8,
          padding: '6px 16px', color: '#FBBF24', fontSize: 13, fontWeight: 700,
          fontFamily: "'Inter', sans-serif", pointerEvents: 'none',
          backdropFilter: 'blur(4px)',
          boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
          display: 'flex', alignItems: 'center', gap: 8
        }}>
          <span style={{ fontSize: 18 }}>✋</span> Click pe un vehicul portocaliu pentru a-i da clearance
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────
// Functii de desenare
// ─────────────────────────────────────────────────────────────────────

function drawRoads(ctx, W, H) {
  // Drum vertical cu gradient
  const vGrad = ctx.createLinearGradient(CX - HALF, 0, CX + HALF, 0);
  vGrad.addColorStop(0, '#1F2937');
  vGrad.addColorStop(0.5, '#374151');
  vGrad.addColorStop(1, '#1F2937');
  ctx.fillStyle = vGrad;
  ctx.fillRect(CX - HALF, 0, ROAD_W, H);

  // Drum orizontal cu gradient
  const hGrad = ctx.createLinearGradient(0, CY - HALF, 0, CY + HALF);
  hGrad.addColorStop(0, '#1F2937');
  hGrad.addColorStop(0.5, '#374151');
  hGrad.addColorStop(1, '#1F2937');
  ctx.fillStyle = hGrad;
  ctx.fillRect(0, CY - HALF, W, ROAD_W);
}

function drawLaneMarkings(ctx, W, H) {
  // Linie centrala discontinua (separator benzi opuse) — verticala
  ctx.save();
  ctx.strokeStyle = '#FBBF24';
  ctx.lineWidth = 2;
  ctx.setLineDash([20, 12]);
  // Vertical — in afara intersectiei
  ctx.beginPath();
  ctx.moveTo(CX, 0); ctx.lineTo(CX, CY - HALF - 2);
  ctx.moveTo(CX, CY + HALF + 2); ctx.lineTo(CX, H);
  ctx.stroke();
  // Orizontal
  ctx.beginPath();
  ctx.moveTo(0, CY); ctx.lineTo(CX - HALF - 2, CY);
  ctx.moveTo(CX + HALF + 2, CY); ctx.lineTo(W, CY);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.restore();

  // Sageti directie banda (indica sensul de mers)
  ctx.save();
  ctx.fillStyle = 'rgba(255,255,255,0.25)';
  ctx.font = 'bold 18px Arial';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  // N → spre Sud (x=385, banda stanga)
  ctx.fillText('↓', CX - LANE_W / 2, 120);
  // S → spre Nord (x=415, banda stanga)
  ctx.fillText('↑', CX + LANE_W / 2, 680);
  // V → spre Est (y=415, banda stanga)
  ctx.fillText('→', 120, CY + LANE_W / 2);
  // E → spre Vest (y=385, banda stanga)
  ctx.fillText('←', 680, CY - LANE_W / 2);
  ctx.restore();
}

function drawStopLines(ctx) {
  ctx.save();
  ctx.strokeStyle = '#FFFFFF';
  ctx.lineWidth = 3;
  const STOP = 8; // pozitia liniei albe — nu se schimba

  // Nord — banda stanga (x=370..400)
  ctx.beginPath();
  ctx.moveTo(CX - HALF, CY - HALF - STOP);
  ctx.lineTo(CX, CY - HALF - STOP);
  ctx.stroke();

  // Sud — banda stanga (x=400..430)
  ctx.beginPath();
  ctx.moveTo(CX, CY + HALF + STOP);
  ctx.lineTo(CX + HALF, CY + HALF + STOP);
  ctx.stroke();

  // Vest — banda stanga (y=400..430)
  ctx.beginPath();
  ctx.moveTo(CX - HALF - STOP, CY);
  ctx.lineTo(CX - HALF - STOP, CY + HALF);
  ctx.stroke();

  // Est — banda stanga (y=370..400)
  ctx.beginPath();
  ctx.moveTo(CX + HALF + STOP, CY - HALF);
  ctx.lineTo(CX + HALF + STOP, CY);
  ctx.stroke();

  ctx.restore();
}

function drawIntersectionBox(ctx) {
  // Zona centrala — culoare usor diferita
  ctx.fillStyle = '#4B5563';
  ctx.fillRect(CX - HALF, CY - HALF, ROAD_W, ROAD_W);
  // Contur subtil
  ctx.strokeStyle = 'rgba(255,255,255,0.15)';
  ctx.lineWidth = 1;
  ctx.strokeRect(CX - HALF, CY - HALF, ROAD_W, ROAD_W);
}

// Pozitiile semafoarelor per directie
// Fiecare semafor e plasat pe banda de intrare, langa linia de stop
const LIGHT_POS = {
  N: { x: CX - HALF - 16, y: CY - HALF - 30 },
  S: { x: CX + HALF + 16, y: CY + HALF + 30 },
  E: { x: CX + HALF + 30, y: CY - HALF - 16 },
  V: { x: CX - HALF - 30, y: CY + HALF + 16 },
};

function drawSemaphore(ctx, semaphore) {
  const lightsPerDir = semaphore?.lights || {};
  const COLORS = { green: '#22C55E', yellow: '#FBBF24', red: '#EF4444' };
  const BODY_W = 18, BODY_H = 50;  // dimensiuni carcasa semafor (3 globuri)

  ['N', 'S', 'E', 'V'].forEach(dir => {
    const col = COLORS[lightsPerDir[dir] || 'red'];
    const pos = LIGHT_POS[dir];
    const bx = pos.x - BODY_W / 2;
    const by = pos.y - BODY_H / 2;

    ctx.save();

    // Carcasa semaforului
    ctx.fillStyle = '#1F2937';
    ctx.strokeStyle = '#374151';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(bx, by, BODY_W, BODY_H, 3);
    ctx.fill();
    ctx.stroke();

    // 3 globuri: rosu sus, galben mijloc, verde jos
    const globY = [by + 9, by + 25, by + 41];
    const globColors = ['#EF4444', '#FBBF24', '#22C55E'];
    const activeLight = lightsPerDir[dir] || 'red';
    const activeIdx = { red: 0, yellow: 1, green: 2 }[activeLight] ?? 0;

    globColors.forEach((gc, i) => {
      const lit = (i === activeIdx);
      ctx.beginPath();
      ctx.arc(pos.x, globY[i], 6, 0, Math.PI * 2);
      ctx.fillStyle = lit ? gc : '#374151';
      if (lit) {
        ctx.shadowColor = gc;
        ctx.shadowBlur = 10;
      }
      ctx.fill();
      ctx.shadowBlur = 0;
    });

    // Eticheta directie
    ctx.font = 'bold 8px monospace';
    ctx.fillStyle = '#9CA3AF';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(dir, pos.x, by + BODY_H + 7);

    ctx.restore();
  });
}

function drawVehicle(ctx, v, manualMode = false, now) {
  if (v.x < -60 || v.x > 860 || v.y < -60 || v.y > 860) return;

  const isNoV2X = v.v2x_enabled === false;
  const isEmergency = v.priority === 'emergency';
  const pulse = 0.5 + 0.5 * Math.sin(now / 150);

  // Culoarea: non-V2X = gri-închis, altfel normal
  let color;
  if (isNoV2X) {
    color = '#6B7280';  // gri închis
  } else {
    color = PRIORITY_COLOR[v.priority] || STATE_COLOR[v.state] || STATE_COLOR.moving;
  }

  ctx.save();
  ctx.translate(v.x, v.y);
  ctx.rotate(getVehicleHeading(v));

  // 1. Corp simplu (Dreptunghi rotunjit)
  ctx.fillStyle = color;
  // Adăugăm un efect de pulsare doar pentru mașinile de urgență (Cerința 12)
  if (isEmergency) ctx.globalAlpha = 0.7 + 0.3 * Math.sin(now / 100);
  // Non-V2X: contur roșu pulsant
  if (isNoV2X) {
    ctx.strokeStyle = '#EF4444';
    ctx.lineWidth = 2.5;
    ctx.globalAlpha = 0.8 + 0.2 * Math.sin(now / 200);
  }

  ctx.beginPath();
  ctx.roundRect(-12, -18, 24, 36, 4);
  ctx.fill();
  if (isNoV2X) ctx.stroke();

  // 2. Indicator direcție (un mic triunghi/vârf în față)
  ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
  ctx.beginPath();
  ctx.moveTo(-6, -14);
  ctx.lineTo(6, -14);
  ctx.lineTo(0, -22);
  ctx.closePath();
  ctx.fill();

  // 3. Indicator frână (linie discretă în spate dacă decelerază)
  if (v.state === 'braking' || v.state === 'yielding') {
    ctx.fillStyle = '#EF4444';
    ctx.fillRect(-10, 15, 20, 3);
  }

  // 4. X roșu suprapus pentru non-V2X
  if (isNoV2X) {
    ctx.globalAlpha = 0.9;
    ctx.strokeStyle = '#EF4444';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(-8, -10);
    ctx.lineTo(8, 10);
    ctx.moveTo(8, -10);
    ctx.lineTo(-8, 10);
    ctx.stroke();
  }

  ctx.restore();

  // 5. Etichetă minimalistă (ID-ul lângă mașină)
  ctx.font = "bold 11px Inter, sans-serif";
  ctx.fillStyle = isNoV2X ? '#F87171' : '#FFFFFF';
  ctx.textAlign = "center";
  ctx.fillText(v.id, v.x, v.y + 4);

  // 6. Badge "⛔" deasupra vehiculului fără V2X
  if (isNoV2X) {
    ctx.font = "bold 9px Inter, sans-serif";
    ctx.fillStyle = '#EF4444';
    ctx.textAlign = "center";
    ctx.fillText('⛔ FĂRĂ V2X', v.x, v.y - 26);
  }
}

// ─────────────────────────────────────────────────────────────────────
// Risk zone drawing — cerc pulsant + linie de pericol + label TTC
// ─────────────────────────────────────────────────────────────────────

// ─────────────────────────────────────────────────────────────────────
// Decision Arrows — Săgeți care arată cauzalitatea deciziilor
// ─────────────────────────────────────────────────────────────────────

function drawDecisionArrows(ctx, vehicles, agentsMemory, now) {
  Object.keys(agentsMemory).forEach(vid => {
    const memory = agentsMemory[vid];
    if (!memory || memory.length === 0) return;

    const last = memory[memory.length - 1];
    if (!last.target_id || last.action === 'GO') return;

    const vSource = vehicles.find(v => v.id === vid);
    const vTarget = vehicles.find(v => v.id === last.target_id);

    if (vSource && vTarget) {
      const pulse = 0.5 + 0.5 * Math.sin(now / 150);
      drawCurvedArrow(ctx, vSource.x, vSource.y, vTarget.x, vTarget.y, pulse, last.action);
    }
  });
}

function drawCurvedArrow(ctx, x1, y1, x2, y2, pulse, action) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const dist = Math.sqrt(dx * dx + dy * dy);

  // Offset-uri ca sa nu porneasca exact din centrul masinii
  const ox = (dx / dist) * 25;
  const oy = (dy / dist) * 25;

  ctx.save();
  ctx.strokeStyle = action === 'YIELDING' ? '#F87171' : '#FBBF24';
  ctx.lineWidth = 2;
  ctx.setLineDash([5, 3]);
  ctx.globalAlpha = 0.4 + pulse * 0.4;

  // Desenam un arc usor curbat
  const midX = (x1 + x2) / 2 + (dy / dist) * 30;
  const midY = (y1 + y2) / 2 - (dx / dist) * 30;

  ctx.beginPath();
  ctx.moveTo(x1 + ox, y1 + oy);
  ctx.quadraticCurveTo(midX, midY, x2 - ox, y2 - oy);
  ctx.stroke();

  // Capul săgeții
  const angle = Math.atan2(y2 - midY, x2 - midX);
  ctx.beginPath();
  ctx.translate(x2 - ox, y2 - oy);
  ctx.rotate(angle);
  ctx.moveTo(0, 0);
  ctx.lineTo(-10, -5);
  ctx.lineTo(-10, 5);
  ctx.closePath();
  ctx.fillStyle = ctx.strokeStyle;
  ctx.fill();

  ctx.restore();
}

function drawRiskZone(ctx, risk, vehicles, now) {
  const ttc = risk.ttc ?? 999;
  const isCritical = ttc < TTC_CRITICAL;
  const dangerColor = isCritical ? '#EF4444' : '#F59E0B';

  // Pulse corect: sin în [-1,1] → pulseAbs în [0,1]
  const rawSin = Math.sin(now / (isCritical ? 150 : 280));
  const pulseAbs = 0.5 + 0.5 * rawSin; // 0..1

  // ── 1. Cerc pulsant în jurul zonei de conflict (centrul intersecției)
  // Fill foarte transparent
  ctx.save();
  ctx.globalAlpha = 0.08 + pulseAbs * 0.14;
  ctx.fillStyle = dangerColor;
  ctx.beginPath();
  ctx.arc(CX, CY, RISK_CIRCLE_RADIUS, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  // Contur pulsant cu glow
  ctx.save();
  ctx.globalAlpha = 0.45 + pulseAbs * 0.45;
  ctx.strokeStyle = dangerColor;
  ctx.lineWidth = isCritical ? 4 : 2.5;
  ctx.setLineDash([14, 7]);
  ctx.shadowColor = dangerColor;
  ctx.shadowBlur = isCritical ? 32 : 18;
  ctx.beginPath();
  ctx.arc(CX, CY, RISK_CIRCLE_RADIUS, 0, Math.PI * 2);
  ctx.stroke();
  ctx.restore();

  // ── 2. Cercuri individuale (aura) în jurul fiecărui vehicul în risc
  const [id1, id2] = risk.pair || [];
  const v1 = vehicles.find(v => v.id === id1);
  const v2 = vehicles.find(v => v.id === id2);
  const ttcPerV = risk.ttc_per_vehicle || {};
  const VEHICLE_AURA_R = 34;

  [v1, v2].forEach((v, idx) => {
    if (!v) return;
    const vid = idx === 0 ? id1 : id2;
    const vttc = ttcPerV[vid] ?? ttc;
    const vCritical = vttc < TTC_CRITICAL;
    const vColor = vCritical ? '#EF4444' : '#F59E0B';

    // Fill aura
    ctx.save();
    ctx.globalAlpha = (0.12 + 0.22 * pulseAbs) * (vCritical ? 1 : 0.8);
    ctx.fillStyle = vColor;
    ctx.beginPath();
    ctx.arc(v.x, v.y, VEHICLE_AURA_R, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // Contur cerc vehicul
    ctx.save();
    ctx.globalAlpha = 0.65 + 0.35 * pulseAbs;
    ctx.strokeStyle = vColor;
    ctx.lineWidth = vCritical ? 2.5 : 1.8;
    ctx.setLineDash([6, 4]);
    ctx.shadowColor = vColor;
    ctx.shadowBlur = vCritical ? 18 : 10;
    ctx.beginPath();
    ctx.arc(v.x, v.y, VEHICLE_AURA_R, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();

    // Badge TTC individual deasupra vehiculului
    if (vttc < 999) {
      const bx = v.x;
      const by = v.y - VEHICLE_AURA_R - 10;
      const vtxt = `${vttc.toFixed(1)}s`;
      ctx.save();
      ctx.font = "bold 11px 'Inter', sans-serif";
      const vtw = ctx.measureText(vtxt).width;
      ctx.beginPath();
      ctx.roundRect(bx - vtw / 2 - 6, by - 10, vtw + 12, 20, 5);
      ctx.fillStyle = 'rgba(17,24,39,0.88)';
      ctx.fill();
      ctx.strokeStyle = vColor;
      ctx.lineWidth = 1.2;
      ctx.stroke();
      ctx.fillStyle = vColor;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(vtxt, bx, by);
      ctx.restore();
    }
  });

  // ── 3. Linie de pericol între cele două vehicule
  if (v1 && v2) {
    ctx.save();
    ctx.globalAlpha = 0.45 + 0.45 * pulseAbs;
    ctx.strokeStyle = dangerColor;
    ctx.lineWidth = 2.5;
    ctx.setLineDash([9, 6]);
    ctx.shadowColor = dangerColor;
    ctx.shadowBlur = 12;
    ctx.beginPath();
    ctx.moveTo(v1.x, v1.y);
    ctx.lineTo(v2.x, v2.y);
    ctx.stroke();
    ctx.restore();

    // ── 4. Badge TTC global la mijlocul liniei
    const mx = (v1.x + v2.x) / 2;
    const my = (v1.y + v2.y) / 2;
    ctx.save();
    ctx.font = "bold 13px 'Inter', sans-serif";
    const txt = `⚠ TTC: ${ttc.toFixed(1)}s`;
    const tw = ctx.measureText(txt).width;

    ctx.beginPath();
    ctx.roundRect(mx - tw / 2 - 10, my - 13, tw + 20, 26, 7);
    ctx.fillStyle = 'rgba(17,24,39,0.92)';
    ctx.fill();
    ctx.strokeStyle = dangerColor;
    ctx.lineWidth = 1.5;
    ctx.stroke();

    ctx.fillStyle = dangerColor;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.shadowColor = dangerColor;
    ctx.shadowBlur = 6;
    ctx.fillText(txt, mx, my);
    ctx.restore();
  }
}

// ─────────────────────────────────────────────────────────────────────
// Collision Explosion Animation
// ─────────────────────────────────────────────────────────────────────

function drawCollisions(ctx, collisions, vehicles, now) {
  collisions.forEach(col => {
    const [id1, id2] = col.vehicles || [];
    const v1 = vehicles.find(v => v.id === id1);
    const v2 = vehicles.find(v => v.id === id2);
    if (!v1 || !v2) return;

    const cx = (v1.x + v2.x) / 2;
    const cy = (v1.y + v2.y) / 2;
    const pulse = 0.5 + 0.5 * Math.sin(now / 100);

    // Cerc de explozie exterior
    ctx.save();
    ctx.globalAlpha = 0.15 + 0.25 * pulse;
    ctx.fillStyle = '#EF4444';
    ctx.beginPath();
    ctx.arc(cx, cy, 55 + 15 * pulse, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // Cerc de explozie interior
    ctx.save();
    ctx.globalAlpha = 0.3 + 0.4 * pulse;
    ctx.fillStyle = '#F97316';
    ctx.beginPath();
    ctx.arc(cx, cy, 30 + 10 * pulse, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // Contur pulsant
    ctx.save();
    ctx.globalAlpha = 0.6 + 0.4 * pulse;
    ctx.strokeStyle = '#EF4444';
    ctx.lineWidth = 3;
    ctx.setLineDash([8, 4]);
    ctx.shadowColor = '#EF4444';
    ctx.shadowBlur = 25;
    ctx.beginPath();
    ctx.arc(cx, cy, 55 + 15 * pulse, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();

    // Text "💥 COLIZIUNE!"
    ctx.save();
    ctx.font = "bold 14px 'Inter', sans-serif";
    const txt = '💥 COLIZIUNE!';
    const tw = ctx.measureText(txt).width;
    ctx.beginPath();
    ctx.roundRect(cx - tw / 2 - 10, cy - 42, tw + 20, 26, 7);
    ctx.fillStyle = 'rgba(153,27,27,0.95)';
    ctx.fill();
    ctx.strokeStyle = '#FCA5A5';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.fillStyle = '#FCA5A5';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.shadowColor = '#EF4444';
    ctx.shadowBlur = 8;
    ctx.fillText(txt, cx, cy - 29);
    ctx.restore();
  });
}


export default IntersectionCanvas;
