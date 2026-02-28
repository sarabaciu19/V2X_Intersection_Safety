import React, { useRef, useEffect, useCallback } from 'react';

// ── Geometrie (trebuie sa fie identica cu backend models/vehicle.py) ──
const CX = 400, CY = 400;   // centrul intersectiei
const LANE_W = 30;         // latimea unei benzi px
const ROAD_W = LANE_W * 2; // 60px — 2 benzi per directie
const HALF = ROAD_W / 2; // 30px

// Culori vehicule
const STATE_COLOR = {
  moving: '#3B82F6',   // albastru
  waiting: '#F59E0B',   // portocaliu — asteapta la linia de stop
  crossing: '#22C55E',   // verde — a primit clearance, traverseaza
  done: '#6B7280',   // gri
};

const INTENT_ICON = { straight: '↑', left: '←', right: '→' };
const PRIORITY_COLOR = { emergency: '#EF4444', normal: null };

// Heading (unghi radiani) per directie, pentru a roti vehiculul corect
const HEADING = { N: Math.PI, S: 0, V: Math.PI / 2, E: -Math.PI / 2 };

// ── Risk zone constants ──
const TTC_CRITICAL = 1.5;  // secunde — rosu
const TTC_WARNING = 3.0;  // secunde — portocaliu
const RISK_CIRCLE_RADIUS = 80; // px

const IntersectionCanvas = ({
  vehicles = [],
  semaphore = {},
  risk = { risk: false, pair: null, ttc: 999, ttc_per_vehicle: {} },
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
    vehicles.forEach(v => drawVehicle(ctx, v, !!onGrantClearance));

    // 8. Risk zone (cerc + linie + label)
    if (risk && risk.risk && risk.pair) {
      drawRiskZone(ctx, risk, vehicles, now);
    }

    // 9. Legenda cooperation
    drawLegend(ctx, cooperation, risk, W);
  }, [vehicles, semaphore, cooperation, risk, onGrantClearance]);

  useEffect(() => {
    // If risk is active, animate at 60fps for smooth pulsing
    if (risk && risk.risk) {
      const animate = () => {
        draw(Date.now());
        animFrameRef.current = requestAnimationFrame(animate);
      };
      animate();
      return () => {
        if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      };
    } else {
      // No risk — draw once
      draw(Date.now());
    }
  }, [draw, risk]);

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
          background: '#F59E0B22', border: '1px solid #F59E0B', borderRadius: 6,
          padding: '4px 14px', color: '#FBBF24', fontSize: 12, fontWeight: 700,
          fontFamily: 'monospace', pointerEvents: 'none',
        }}>
          ✋ Click pe un vehicul portocaliu pentru a-i da clearance
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────
// Functii de desenare
// ─────────────────────────────────────────────────────────────────────

function drawRoads(ctx, W, H) {
  ctx.fillStyle = '#374151';
  // Drum vertical
  ctx.fillRect(CX - HALF, 0, ROAD_W, H);
  // Drum orizontal
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
  // N → spre Sud (x=415)
  ctx.fillText('↓', CX + LANE_W / 2, 120);
  // S → spre Nord (x=385)
  ctx.fillText('↑', CX - LANE_W / 2, 680);
  // V → spre Est (y=385)
  ctx.fillText('→', 120, CY - LANE_W / 2);
  // E → spre Vest (y=415)
  ctx.fillText('←', 680, CY + LANE_W / 2);
  ctx.restore();
}

function drawStopLines(ctx) {
  ctx.save();
  ctx.strokeStyle = '#FFFFFF';
  ctx.lineWidth = 3;
  const STOP = 8; // distanta extra inainte de intersectie

  // Nord — linie orizontala la y = CY - HALF - STOP
  ctx.beginPath();
  ctx.moveTo(CX, CY - HALF - STOP);
  ctx.lineTo(CX + HALF, CY - HALF - STOP);
  ctx.stroke();

  // Sud
  ctx.beginPath();
  ctx.moveTo(CX - HALF, CY + HALF + STOP);
  ctx.lineTo(CX, CY + HALF + STOP);
  ctx.stroke();

  // Vest
  ctx.beginPath();
  ctx.moveTo(CX - HALF - STOP, CY - HALF);
  ctx.lineTo(CX - HALF - STOP, CY);
  ctx.stroke();

  // Est
  ctx.beginPath();
  ctx.moveTo(CX + HALF + STOP, CY);
  ctx.lineTo(CX + HALF + STOP, CY + HALF);
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
  N: { x: CX + HALF + 16, y: CY - HALF - 30 },  // banda N (x=430+), deasupra liniei de stop
  S: { x: CX - HALF - 16, y: CY + HALF + 30 },  // banda S (x=370-), sub linia de stop
  E: { x: CX + HALF + 30, y: CY + HALF + 16 },  // banda E (y=430+), dreapta liniei de stop
  V: { x: CX - HALF - 30, y: CY - HALF - 16 },  // banda V (y=370-), stanga liniei de stop
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

function drawVehicle(ctx, v, manualMode = false) {
  // Nu desena vehiculul daca a iesit complet din canvas (margine 60px)
  if (v.x < -60 || v.x > 860 || v.y < -60 || v.y > 860) return;
  const color = PRIORITY_COLOR[v.priority] || STATE_COLOR[v.state] || STATE_COLOR.moving;
  const isClickable = manualMode && v.state === 'waiting';

  // Pulsing ring per vehiculele clickabile (manual mode + waiting)
  if (isClickable) {
    ctx.save();
    ctx.strokeStyle = '#F59E0B';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    ctx.arc(v.x, v.y, 28, 0, Math.PI * 2);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();
  }

  ctx.save();
  ctx.translate(v.x, v.y);
  ctx.rotate(HEADING[v.direction] ?? 0);

  // Corp masina (18×30px, centrat)
  const W2 = 14, H2 = 22;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.roundRect(-W2, -H2, W2 * 2, H2 * 2, 4);
  ctx.fill();

  // Contur
  ctx.strokeStyle = 'rgba(0,0,0,0.6)';
  ctx.lineWidth = 1.5;
  ctx.stroke();

  // Fata masinii (bara alba)
  ctx.fillStyle = 'rgba(255,255,255,0.9)';
  ctx.fillRect(-W2 + 2, -H2, W2 * 2 - 4, 4);

  // Clearance glow daca traverseaza
  if (v.state === 'crossing' || v.clearance) {
    ctx.shadowColor = '#22C55E';
    ctx.shadowBlur = 14;
    ctx.strokeStyle = '#22C55E';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.shadowBlur = 0;
  }

  ctx.restore();

  // ── Labels (in spatiul lumii, nu rotit) ──
  ctx.save();
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  // ID + intent icon deasupra
  const icon = INTENT_ICON[v.intent] || '?';
  ctx.font = 'bold 11px monospace';
  ctx.fillStyle = '#FFFFFF';
  ctx.fillText(`${v.id} ${icon}`, v.x, v.y - 30);

  // Stare sub masina
  ctx.font = '9px monospace';
  ctx.fillStyle = color;
  ctx.fillText(v.state.toUpperCase(), v.x, v.y + 30);

  ctx.restore();
}

// ─────────────────────────────────────────────────────────────────────
// Risk zone drawing — cerc pulsant + linie de pericol + label TTC
// ─────────────────────────────────────────────────────────────────────

function drawRiskZone(ctx, risk, vehicles, now) {
  const ttc = risk.ttc ?? 999;
  const isCritical = ttc < TTC_CRITICAL;
  const dangerColor = isCritical ? '#EF4444' : '#F97316'; // rosu / portocaliu

  // Pulsing opacity (breathing effect 0.3 — 0.9)
  const pulse = 0.3 + 0.3 * (1 + Math.sin(now / (isCritical ? 150 : 250)));

  // ── 1. Cerc pulsant in jurul centrului intersectiei ──
  ctx.save();
  ctx.globalAlpha = pulse;
  ctx.strokeStyle = dangerColor;
  ctx.lineWidth = isCritical ? 4 : 3;
  ctx.setLineDash([12, 6]);
  ctx.shadowColor = dangerColor;
  ctx.shadowBlur = isCritical ? 25 : 15;
  ctx.beginPath();
  ctx.arc(CX, CY, RISK_CIRCLE_RADIUS, 0, Math.PI * 2);
  ctx.stroke();
  ctx.shadowBlur = 0;

  // Cerc interior mai subtil (fill transparent)
  ctx.fillStyle = dangerColor;
  ctx.globalAlpha = pulse * 0.08;
  ctx.beginPath();
  ctx.arc(CX, CY, RISK_CIRCLE_RADIUS, 0, Math.PI * 2);
  ctx.fill();

  ctx.setLineDash([]);
  ctx.globalAlpha = 1;
  ctx.restore();

  // ── 2. Linie de pericol între vehiculele aflate în risc ──
  const [id1, id2] = risk.pair || [];
  const v1 = vehicles.find(v => v.id === id1);
  const v2 = vehicles.find(v => v.id === id2);

  if (v1 && v2) {
    ctx.save();
    ctx.globalAlpha = pulse;
    ctx.strokeStyle = dangerColor;
    ctx.lineWidth = isCritical ? 3 : 2;
    ctx.setLineDash([8, 5]);
    ctx.shadowColor = dangerColor;
    ctx.shadowBlur = 10;

    ctx.beginPath();
    ctx.moveTo(v1.x, v1.y);
    ctx.lineTo(v2.x, v2.y);
    ctx.stroke();

    ctx.shadowBlur = 0;
    ctx.setLineDash([]);
    ctx.globalAlpha = 1;
    ctx.restore();

    // ── 3. Label TTC la mijlocul liniei ──
    const mx = (v1.x + v2.x) / 2;
    const my = (v1.y + v2.y) / 2;

    ctx.save();
    // Fundal label
    const labelText = `⚠ TTC: ${ttc.toFixed(2)}s`;
    ctx.font = 'bold 13px monospace';
    const tw = ctx.measureText(labelText).width;
    const pad = 6;
    ctx.fillStyle = 'rgba(0,0,0,0.8)';
    ctx.beginPath();
    ctx.roundRect(mx - tw / 2 - pad, my - 10 - pad, tw + pad * 2, 20 + pad, 6);
    ctx.fill();

    // Border
    ctx.strokeStyle = dangerColor;
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Text
    ctx.fillStyle = dangerColor;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(labelText, mx, my);
    ctx.restore();

    // ── 4. Marker ring pe fiecare vehicul aflat in risc ──
    [v1, v2].forEach(v => {
      ctx.save();
      ctx.globalAlpha = pulse;
      ctx.strokeStyle = dangerColor;
      ctx.lineWidth = 2.5;
      ctx.shadowColor = dangerColor;
      ctx.shadowBlur = 12;
      ctx.beginPath();
      ctx.arc(v.x, v.y, 32, 0, Math.PI * 2);
      ctx.stroke();
      ctx.shadowBlur = 0;
      ctx.globalAlpha = 1;
      ctx.restore();
    });
  }
}

function drawLegend(ctx, cooperation, risk, W) {
  ctx.save();
  const hasRisk = risk && risk.risk;
  const legendH = hasRisk ? 125 : 100;

  // Fundal legenda
  ctx.fillStyle = 'rgba(17,24,39,0.85)';
  ctx.fillRect(W - 180, 8, 172, legendH);
  ctx.strokeStyle = '#374151';
  ctx.lineWidth = 1;
  ctx.strokeRect(W - 180, 8, 172, legendH);

  ctx.font = 'bold 11px monospace';
  ctx.textAlign = 'left';
  const entries = [
    { color: '#3B82F6', label: 'moving — se apropie' },
    { color: '#F59E0B', label: 'waiting — asteapta' },
    { color: '#22C55E', label: 'crossing — traverseaza' },
    { color: '#EF4444', label: 'urgenta' },
  ];
  entries.forEach((e, i) => {
    ctx.fillStyle = e.color;
    ctx.fillRect(W - 172, 18 + i * 21, 12, 12);
    ctx.fillStyle = '#D1D5DB';
    ctx.fillText(e.label, W - 155, 28 + i * 21);
  });

  // Cooperation status
  ctx.font = 'bold 10px monospace';
  ctx.fillStyle = cooperation ? '#22C55E' : '#EF4444';
  ctx.fillText(`V2X: ${cooperation ? 'ON ✓' : 'OFF ✗'}`, W - 172, 106);

  // Risk status in legend
  if (hasRisk) {
    const ttc = risk.ttc ?? 999;
    const isCritical = ttc < TTC_CRITICAL;
    const col = isCritical ? '#EF4444' : '#F97316';
    ctx.fillStyle = col;
    ctx.font = 'bold 10px monospace';
    ctx.fillText(`⚠ RISC TTC:${ttc.toFixed(1)}s`, W - 172, 121);
  }

  ctx.restore();
}

export default IntersectionCanvas;

