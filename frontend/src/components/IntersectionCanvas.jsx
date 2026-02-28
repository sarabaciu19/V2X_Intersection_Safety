import React, { useRef, useEffect } from 'react';

/**
 * IntersectionCanvas - Canvas 2D pentru desenarea intersecției
 * Specificații:
 * - Canvas: 800x800px
 * - Intersecție centrată la (400, 400)
 * - Vehicule: 30x50px, colorate după state
 * - Zonă de risc: cerc roșu semi-transparent când danger=true
 */
const IntersectionCanvas = ({ vehicles = [], risk = { danger: false }, dimensions = { width: 800, height: 800 } }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Desenează fundalul
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Desenează intersecția (drumuri + marcaje)
    drawIntersection(ctx, 400, 400);

    // Desenează zona de risc (ÎNAINTE de vehicule pentru a fi în spate)
    if (risk && risk.danger) {
      drawRiskZone(ctx, 400, 400);
    }

    // Desenează vehiculele
    drawVehicles(ctx, vehicles);

  }, [vehicles, risk, dimensions]);

  /**
   * Desenează intersecția: 2 drumuri (gri) + marcaje (albe)
   * Centrat la (centerX, centerY)
   */
  const drawIntersection = (ctx, centerX, centerY) => {
    const roadWidth = 120; // Lățime drum

    // === DRUMURI (dreptunghiure gri) ===
    ctx.fillStyle = '#4B5563'; // Gri drum

    // Drum vertical
    ctx.fillRect(
      centerX - roadWidth / 2,  // x
      0,                         // y (de sus până jos)
      roadWidth,                 // width
      800                        // height (întreg canvas-ul)
    );

    // Drum orizontal
    ctx.fillRect(
      0,                         // x (de la stânga la dreapta)
      centerY - roadWidth / 2,   // y
      800,                       // width (întreg canvas-ul)
      roadWidth                  // height
    );

    // === MARCAJE DE STRADĂ (linii albe întrerupte) ===
    ctx.strokeStyle = '#FFFFFF';
    ctx.lineWidth = 2;
    ctx.setLineDash([20, 15]); // Linie întreruptă

    // Linie centrală verticală
    ctx.beginPath();
    ctx.moveTo(centerX, 0);
    ctx.lineTo(centerX, 800);
    ctx.stroke();

    // Linie centrală orizontală
    ctx.beginPath();
    ctx.moveTo(0, centerY);
    ctx.lineTo(800, centerY);
    ctx.stroke();

    ctx.setLineDash([]); // Reset dash

    // === MARCAJE OPRIRE (linii continue la intrarea în intersecție) ===
    ctx.lineWidth = 3;

    // Nord (sus)
    ctx.beginPath();
    ctx.moveTo(centerX - roadWidth / 2, centerY - roadWidth / 2);
    ctx.lineTo(centerX + roadWidth / 2, centerY - roadWidth / 2);
    ctx.stroke();

    // Sud (jos)
    ctx.beginPath();
    ctx.moveTo(centerX - roadWidth / 2, centerY + roadWidth / 2);
    ctx.lineTo(centerX + roadWidth / 2, centerY + roadWidth / 2);
    ctx.stroke();

    // Vest (stânga)
    ctx.beginPath();
    ctx.moveTo(centerX - roadWidth / 2, centerY - roadWidth / 2);
    ctx.lineTo(centerX - roadWidth / 2, centerY + roadWidth / 2);
    ctx.stroke();

    // Est (dreapta)
    ctx.beginPath();
    ctx.moveTo(centerX + roadWidth / 2, centerY - roadWidth / 2);
    ctx.lineTo(centerX + roadWidth / 2, centerY + roadWidth / 2);
    ctx.stroke();
  };

  /**
   * Desenează zona de risc: cerc roșu semi-transparent la intersecție
   */
  const drawRiskZone = (ctx, centerX, centerY) => {
    ctx.fillStyle = 'rgba(239, 68, 68, 0.25)'; // Roșu semi-transparent
    ctx.beginPath();
    ctx.arc(centerX, centerY, 80, 0, 2 * Math.PI);
    ctx.fill();
  };

  /**
   * Desenează vehiculele: dreptunghiuri 30x50px colorate după state
   * State colors:
   * - 'normal' → #3B82F6 (albastru)
   * - 'braking' → #F59E0B (portocaliu)
   * - 'yielding' → #EF4444 (roșu)
   * - 'danger' → #DC2626 (roșu închis)
   * - 'warning' → #FBBF24 (galben)
   * - 'emergency' → #8B5CF6 (violet)
   */
  const drawVehicles = (ctx, vehicles) => {
    vehicles.forEach(vehicle => {
      ctx.save();

      // Transformare pentru rotație (dacă există heading)
      ctx.translate(vehicle.x, vehicle.y);
      if (vehicle.heading !== undefined) {
        ctx.rotate(vehicle.heading);
      }

      // Culoare în funcție de state/status
      const state = vehicle.state || vehicle.status || 'normal';
      ctx.fillStyle = getVehicleColor(state);

      // Desenează vehicul (dreptunghi 30x50px, centrat)
      ctx.fillRect(-15, -25, 30, 50);

      // Border pentru contur
      ctx.strokeStyle = '#000000';
      ctx.lineWidth = 1;
      ctx.strokeRect(-15, -25, 30, 50);

      // Indicator față vehicul (linie albă în față)
      ctx.fillStyle = '#FFFFFF';
      ctx.fillRect(-10, -25, 20, 5);

      // ID vehicul (text deasupra)
      ctx.fillStyle = '#FFFFFF';
      ctx.font = 'bold 12px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(vehicle.id, 0, -35);

      // Viteză (text jos)
      if (vehicle.speed !== undefined) {
        ctx.font = '10px Arial';
        ctx.fillText(`${Math.round(vehicle.speed)} km/h`, 0, 40);
      }

      ctx.restore();
    });
  };

  /**
   * Returnează culoarea vehiculului în funcție de state
   */
  const getVehicleColor = (state) => {
    switch (state) {
      case 'braking':
        return '#F59E0B'; // Portocaliu
      case 'yielding':
        return '#EF4444'; // Roșu
      case 'danger':
        return '#DC2626'; // Roșu închis
      case 'warning':
        return '#FBBF24'; // Galben
      case 'emergency':
        return '#8B5CF6'; // Violet
      case 'normal':
      default:
        return '#3B82F6'; // Albastru (default)
    }
  };

  return (
    <div className="intersection-canvas-container">
      <canvas
        ref={canvasRef}
        width={dimensions.width}
        height={dimensions.height}
        style={{
          border: '2px solid #444',
          borderRadius: '8px',
          backgroundColor: '#1a1a1a',
          display: 'block',
        }}
      />
    </div>
  );
};

export default IntersectionCanvas;

