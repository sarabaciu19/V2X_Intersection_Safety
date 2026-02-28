import React, { useRef, useEffect } from 'react';

// ── Geometrie (trebuie sa fie identica cu backend models/vehicle.py) ──
const CX = 400, CY = 400;   // centrul intersectiei
const LANE_W   = 30;         // latimea unei benzi px
const ROAD_W   = LANE_W * 2; // 60px — 2 benzi per directie
const HALF     = ROAD_W / 2; // 30px

// Culori vehicule
const STATE_COLOR = {
  moving:   '#3B82F6',   // albastru
  waiting:  '#F59E0B',   // portocaliu — asteapta la linia de stop
  crossing: '#22C55E',   // verde — a primit clearance, traverseaza
  done:     '#6B7280',   // gri
};

const INTENT_ICON = { straight: '↑', left: '←', right: '→' };
const PRIORITY_COLOR = { emergency: '#EF4444', normal: null };

// Heading (unghi radiani) per directie, pentru a roti vehiculul corect
// Fata masinii (bara alba) este la -H2 (sus) la unghi=0 → masina priveste in sus
// N vine din Nord → merge spre Sud (jos)    → Math.PI
// S vine din Sud  → merge spre Nord (sus)   → 0
// V vine din Vest → merge spre Est (dreapta) → Math.PI / 2
// E vine din Est  → merge spre Vest (stanga) → -Math.PI / 2
const HEADING = { N: Math.PI, S: 0, V: Math.PI / 2, E: -Math.PI / 2 };

const IntersectionCanvas = ({
  vehicles     = [],
  semaphore    = {},
  cooperation  = true,
  onGrantClearance = null,
  dimensions   = { width: 800, height: 800 },
}) => {
  const canvasRef = useRef(null);

  // Hit-test: returns vehicle clicked (only waiting ones are clickable in manual mode)
  const getClickedVehicle = (canvas, clientX, clientY) => {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width  / rect.width;
    const scaleY = canvas.height / rect.height;
    const mx = (clientX - rect.left) * scaleX;
    const my = (clientY - rect.top)  * scaleY;
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

  useEffect(() => {
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

    // 8. Legenda cooperation
    drawLegend(ctx, cooperation, W);

  }, [vehicles, semaphore, cooperation]);

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
  ctx.moveTo(CX, 0);           ctx.lineTo(CX, CY - HALF - 2);
  ctx.moveTo(CX, CY + HALF + 2); ctx.lineTo(CX, H);
  ctx.stroke();
  // Orizontal
  ctx.beginPath();
  ctx.moveTo(0, CY);            ctx.lineTo(CX - HALF - 2, CY);
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
  ctx.moveTo(CX,        CY - HALF - STOP);
  ctx.lineTo(CX + HALF, CY - HALF - STOP);
  ctx.stroke();

  // Sud
  ctx.beginPath();
  ctx.moveTo(CX - HALF, CY + HALF + STOP);
  ctx.lineTo(CX,        CY + HALF + STOP);
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

function drawSemaphore(ctx, semaphore) {
  const light = semaphore?.light || 'green';
  const colors = { green: '#22C55E', yellow: '#FBBF24', red: '#EF4444' };
  const col = colors[light] || '#22C55E';

  // Indicator mic in coltul stanga-sus al intersectiei
  ctx.save();
  ctx.fillStyle = '#111827';
  ctx.fillRect(CX - HALF - 28, CY - HALF - 28, 24, 24);
  ctx.fillStyle = col;
  ctx.beginPath();
  ctx.arc(CX - HALF - 16, CY - HALF - 16, 9, 0, Math.PI * 2);
  ctx.fill();

  // Glow
  ctx.shadowColor = col;
  ctx.shadowBlur = 12;
  ctx.fill();
  ctx.shadowBlur = 0;
  ctx.restore();
}

function drawVehicle(ctx, v, manualMode = false) {
  // Nu desena vehiculul daca a iesit complet din canvas (margine 60px)
  if (v.x < -60 || v.x > 860 || v.y < -60 || v.y > 860) return;
  const color   = PRIORITY_COLOR[v.priority] || STATE_COLOR[v.state] || STATE_COLOR.moving;
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
    ctx.shadowBlur  = 14;
    ctx.strokeStyle = '#22C55E';
    ctx.lineWidth   = 2;
    ctx.stroke();
    ctx.shadowBlur  = 0;
  }

  ctx.restore();

  // ── Labels (in spatiul lumii, nu rotit) ──
  ctx.save();
  ctx.textAlign    = 'center';
  ctx.textBaseline = 'middle';

  // ID + intent icon deasupra
  const icon = INTENT_ICON[v.intent] || '?';
  ctx.font      = 'bold 11px monospace';
  ctx.fillStyle = '#FFFFFF';
  ctx.fillText(`${v.id} ${icon}`, v.x, v.y - 30);

  // Stare sub masina
  ctx.font      = '9px monospace';
  ctx.fillStyle = color;
  ctx.fillText(v.state.toUpperCase(), v.x, v.y + 30);

  ctx.restore();
}

function drawLegend(ctx, cooperation, W) {
  ctx.save();
  // Fundal legenda
  ctx.fillStyle = 'rgba(17,24,39,0.85)';
  ctx.fillRect(W - 180, 8, 172, 100);
  ctx.strokeStyle = '#374151';
  ctx.lineWidth = 1;
  ctx.strokeRect(W - 180, 8, 172, 100);

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
  ctx.font      = 'bold 10px monospace';
  ctx.fillStyle = cooperation ? '#22C55E' : '#EF4444';
  ctx.fillText(`V2X: ${cooperation ? 'ON ✓' : 'OFF ✗'}`, W - 172, 106);

  ctx.restore();
}

export default IntersectionCanvas;

