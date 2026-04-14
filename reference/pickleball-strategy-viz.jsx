import { useState, useRef, useCallback, useEffect } from "react";

const COURT_W = 20;
const COURT_L = 44;
const KITCHEN = 7;
const NET_Y = COURT_L / 2;

// ── Wide flat perspective matching reference photo ──
const SVG_W = 800;
const SVG_H = 440;

// Court trapezoid — wide near baseline, narrower far baseline
// Matches the uploaded court photo proportions
const NEAR_LEFT_X = 30;
const NEAR_RIGHT_X = SVG_W - 30;
const NEAR_Y = SVG_H - 25;

const FAR_LEFT_X = 185;
const FAR_RIGHT_X = SVG_W - 185;
const FAR_Y = 65;

function courtToScreen(ftX, ftY) {
  const t = 1 - ftY / COURT_L;
  const depth = Math.pow(t, 1.12);
  const screenY = NEAR_Y - depth * (NEAR_Y - FAR_Y);
  const leftX = NEAR_LEFT_X + depth * (FAR_LEFT_X - NEAR_LEFT_X);
  const rightX = NEAR_RIGHT_X + depth * (FAR_RIGHT_X - NEAR_RIGHT_X);
  return [leftX + (ftX / COURT_W) * (rightX - leftX), screenY];
}

function screenToCourt(sx, sy) {
  const depth = Math.max(0, Math.min(1, (NEAR_Y - sy) / (NEAR_Y - FAR_Y)));
  const t = Math.pow(depth, 1 / 1.12);
  const ftY = (1 - t) * COURT_L;
  const leftX = NEAR_LEFT_X + depth * (FAR_LEFT_X - NEAR_LEFT_X);
  const rightX = NEAR_RIGHT_X + depth * (FAR_RIGHT_X - NEAR_RIGHT_X);
  return [
    Math.max(0, Math.min(COURT_W, ((sx - leftX) / (rightX - leftX)) * COURT_W)),
    Math.max(0, Math.min(COURT_L, ftY)),
  ];
}

function quad(x1, y1, x2, y2) {
  const [ax, ay] = courtToScreen(x1, y1);
  const [bx, by] = courtToScreen(x2, y1);
  const [cx, cy] = courtToScreen(x2, y2);
  const [dx, dy] = courtToScreen(x1, y2);
  return `M${ax},${ay} L${bx},${by} L${cx},${cy} L${dx},${dy} Z`;
}

function cLine(x1, y1, x2, y2) {
  const [a, b] = courtToScreen(x1, y1);
  const [c, d] = courtToScreen(x2, y2);
  return { x1: a, y1: b, x2: c, y2: d };
}

function describePosition(ftX, ftY, side) {
  const lr = ftX < COURT_W / 3 ? "left sideline" : ftX > COURT_W * 2 / 3 ? "right sideline" : "center";
  const dist = side === "my" ? ftY - NET_Y : NET_Y - ftY;
  const depth = dist <= KITCHEN ? "kitchen line" : dist <= KITCHEN + 5 ? "transition zone" : "baseline";
  return `${depth}, ${lr}`;
}

function describeBallZone(ftY) {
  if (ftY >= NET_Y + KITCHEN) return "baseline";
  if (ftY >= NET_Y) return "your kitchen";
  if (ftY >= NET_Y - KITCHEN) return "opponent kitchen";
  return "opponent baseline";
}

// ── Stick Figure ──
function StickFigure({ cx, cy, facingForward, color, label, isSelected, isMe, scale }) {
  const s = (scale || 1) * 0.55;
  const headR = 4.2 * s, bodyLen = 12 * s, limbLen = 8.5 * s, armSpread = 7.5 * s;
  const bodyTopY = cy - bodyLen;

  return (
    <g style={{ cursor: "grab" }}>
      {isSelected && (
        <ellipse cx={cx} cy={cy + 2 * s} rx={13 * s} ry={5 * s}
          fill="none" stroke={color} strokeWidth={1.5} strokeDasharray="4,3" opacity={0.7}>
          <animate attributeName="stroke-dashoffset" from="0" to="14" dur="1s" repeatCount="indefinite" />
        </ellipse>
      )}
      {isMe && (
        <>
          <rect x={cx + 7 * s} y={bodyTopY - headR * 2.2} width={19 * s} height={11 * s} rx={2.5 * s}
            fill="#f59e0b" stroke="#b45309" strokeWidth={0.8} />
          <text x={cx + 16.5 * s} y={bodyTopY - headR * 2.2 + 8 * s} textAnchor="middle"
            fontSize={6.5 * s} fontWeight="800" fill="#1a1a1a" fontFamily="'DM Mono', monospace">ME</text>
        </>
      )}
      <ellipse cx={cx} cy={cy + 3 * s} rx={5.5 * s} ry={2 * s} fill="rgba(0,0,0,0.2)" />
      <circle cx={cx} cy={bodyTopY - headR} r={headR}
        fill={color} stroke="rgba(0,0,0,0.2)" strokeWidth={0.8 * s} />
      {facingForward && s > 0.4 && <>
        <circle cx={cx - 1.3 * s} cy={bodyTopY - headR - 0.5 * s} r={0.7 * s} fill="rgba(0,0,0,0.3)" />
        <circle cx={cx + 1.3 * s} cy={bodyTopY - headR - 0.5 * s} r={0.7 * s} fill="rgba(0,0,0,0.3)" />
      </>}
      <line x1={cx} y1={bodyTopY} x2={cx} y2={cy}
        stroke="rgba(255,255,255,0.7)" strokeWidth={1.6 * s} strokeLinecap="round" />
      <line x1={cx - armSpread} y1={bodyTopY + bodyLen * 0.3}
        x2={cx + armSpread} y2={bodyTopY + bodyLen * 0.33}
        stroke="rgba(255,255,255,0.6)" strokeWidth={1.4 * s} strokeLinecap="round" />
      <line x1={cx + armSpread} y1={bodyTopY + bodyLen * 0.33}
        x2={cx + armSpread + 3 * s} y2={bodyTopY + bodyLen * 0.15}
        stroke="#c4a86a" strokeWidth={1.8 * s} strokeLinecap="round" />
      <line x1={cx} y1={cy} x2={cx - 3.5 * s} y2={cy + limbLen * 0.65}
        stroke="rgba(255,255,255,0.6)" strokeWidth={1.4 * s} strokeLinecap="round" />
      <line x1={cx} y1={cy} x2={cx + 3.5 * s} y2={cy + limbLen * 0.65}
        stroke="rgba(255,255,255,0.6)" strokeWidth={1.4 * s} strokeLinecap="round" />
      <text x={cx} y={cy + limbLen * 0.65 + 9 * s} textAnchor="middle"
        fontSize={8 * s} fontWeight="700" fill={color}
        fontFamily="'DM Mono', monospace" letterSpacing="0.3px"
        stroke="rgba(0,0,0,0.7)" strokeWidth={2.5 * s} paintOrder="stroke">
        {label}
      </text>
    </g>
  );
}

function BallIcon({ cx, cy, isSelected, scale }) {
  const s = (scale || 1) * 0.55;
  const r = 4.5 * s;
  return (
    <g style={{ cursor: "grab" }}>
      {isSelected && (
        <circle cx={cx} cy={cy} r={r + 5 * s} fill="none" stroke="#f59e0b"
          strokeWidth={1.5} strokeDasharray="4,3" opacity={0.8}>
          <animate attributeName="stroke-dashoffset" from="0" to="14" dur="0.8s" repeatCount="indefinite" />
        </circle>
      )}
      <ellipse cx={cx} cy={cy + r + 1.5 * s} rx={r * 0.5} ry={1.2 * s} fill="rgba(0,0,0,0.15)" />
      <circle cx={cx} cy={cy} r={r} fill="#c8e64a" stroke="#5a6e1a" strokeWidth={0.9 * s} />
      <circle cx={cx - 1 * s} cy={cy - 1 * s} r={0.9 * s} fill="#b0d63a" />
      <circle cx={cx + 1.8 * s} cy={cy + 0.5 * s} r={0.7 * s} fill="#b0d63a" />
    </g>
  );
}

// ── Court SVG ──
function Court3D({ players, ball, mySide, dragging, onPointerDown }) {
  const getScale = (ftY) => 1.15 - (1 - ftY / COURT_L) * 0.5;

  const entities = [
    ...Object.entries(players).map(([k, p]) => ({ type: "player", key: k, ...p })),
    { type: "ball", key: "ball", ...ball },
  ].sort((a, b) => b.y - a.y);

  return (
    <svg width={SVG_W} height={SVG_H} viewBox={`0 0 ${SVG_W} ${SVG_H}`}
      style={{ display: "block", maxWidth: "100%", height: "auto", touchAction: "none", background: "#0a0a0a" }}>

      {/* Court surface */}
      <path d={quad(0, 0, COURT_W, COURT_L)} fill="#2e8ab8" />

      {/* Kitchen zones — slightly darker */}
      <path d={quad(0, NET_Y - KITCHEN, COURT_W, NET_Y)} fill="#2980aa" />
      <path d={quad(0, NET_Y, COURT_W, NET_Y + KITCHEN)} fill="#2b84b0" />

      {/* Court lines — crisp white */}
      {[
        [0, 0, COURT_W, 0], [COURT_W, 0, COURT_W, COURT_L],
        [0, COURT_L, COURT_W, COURT_L], [0, 0, 0, COURT_L],
        [0, NET_Y - KITCHEN, COURT_W, NET_Y - KITCHEN],
        [0, NET_Y + KITCHEN, COURT_W, NET_Y + KITCHEN],
        [COURT_W / 2, 0, COURT_W / 2, NET_Y - KITCHEN],
        [COURT_W / 2, NET_Y + KITCHEN, COURT_W / 2, COURT_L],
      ].map((c, i) => {
        const l = cLine(...c);
        return <line key={i} {...l} stroke="rgba(255,255,255,0.92)" strokeWidth={2.2} />;
      })}

      {/* Net */}
      {(() => {
        const [lx, ly] = courtToScreen(-0.3, NET_Y);
        const [rx] = courtToScreen(COURT_W + 0.3, NET_Y);
        const netH = 18;
        return (
          <>
            {/* Net shadow on court */}
            <line x1={lx} y1={ly + 2} x2={rx} y2={ly + 2}
              stroke="rgba(0,0,0,0.15)" strokeWidth={netH} />
            {/* Net body */}
            <rect x={lx} y={ly - netH} width={rx - lx} height={netH}
              fill="rgba(0,0,0,0.18)" />
            {/* Top cable */}
            <line x1={lx} y1={ly - netH} x2={rx} y2={ly - netH}
              stroke="rgba(255,255,255,0.7)" strokeWidth={2} />
            {/* Vertical threads */}
            {Array.from({ length: 16 }).map((_, i) => {
              const f = (i + 1) / 17;
              const mx = lx + (rx - lx) * f;
              return <line key={i} x1={mx} y1={ly - netH + 2} x2={mx} y2={ly}
                stroke="rgba(255,255,255,0.08)" strokeWidth={0.5} />;
            })}
            {/* Horizontal threads */}
            {Array.from({ length: 3 }).map((_, i) => {
              const f = (i + 1) / 4;
              const my = (ly - netH + 2) + (netH - 3) * f;
              return <line key={`h${i}`} x1={lx + 3} y1={my} x2={rx - 3} y2={my}
                stroke="rgba(255,255,255,0.05)" strokeWidth={0.4} />;
            })}
          </>
        );
      })()}

      {/* NVZ labels */}
      {(() => {
        const [kx1, ky1] = courtToScreen(COURT_W / 2, NET_Y - KITCHEN / 2);
        const [kx2, ky2] = courtToScreen(COURT_W / 2, NET_Y + KITCHEN / 2);
        return (
          <>
            <text x={kx1} y={ky1} textAnchor="middle" dominantBaseline="middle"
              fontSize="9" fill="rgba(255,255,255,0.09)" fontFamily="'DM Mono', monospace"
              fontWeight="600" letterSpacing="2px">NVZ</text>
            <text x={kx2} y={ky2} textAnchor="middle" dominantBaseline="middle"
              fontSize="12" fill="rgba(255,255,255,0.07)" fontFamily="'DM Mono', monospace"
              fontWeight="600" letterSpacing="3px">NVZ</text>
          </>
        );
      })()}

      {/* Entities */}
      {entities.map((ent) => {
        const [sx, sy] = courtToScreen(ent.x, ent.y);
        const scale = getScale(ent.y);
        if (ent.type === "ball") {
          return <g key="ball" onPointerDown={(e) => onPointerDown(e, "ball")}>
            <BallIcon cx={sx} cy={sy} isSelected={dragging === "ball"} scale={scale} />
          </g>;
        }
        const isOpp = ent.key.startsWith("opp");
        const isLeft = ent.key.includes("left");
        const color = isOpp ? "#ef6461" : "#48bfe3";
        const label = isOpp ? (isLeft ? "OPP L" : "OPP R") : (isLeft ? "YOU L" : "YOU R");
        const isMe = (mySide === "left" && ent.key === "my_left") || (mySide === "right" && ent.key === "my_right");
        return <g key={ent.key} onPointerDown={(e) => onPointerDown(e, ent.key)}>
          <StickFigure cx={sx} cy={sy} facingForward={!isOpp} color={color} label={label}
            isSelected={dragging === ent.key} isMe={isMe} scale={scale} />
        </g>;
      })}
    </svg>
  );
}

// ── Rally Generator (Mock) ──
function generateRally(players, ball, mySide) {
  const meKey = mySide === "left" ? "my_left" : "my_right";
  const partnerKey = mySide === "left" ? "my_right" : "my_left";
  const me = players[meKey], partner = players[partnerKey];
  const oppL = players.opp_left, oppR = players.opp_right;
  const myPos = describePosition(me.x, me.y, "my");
  const partnerPos = describePosition(partner.x, partner.y, "my");
  const oppLPos = describePosition(oppL.x, oppL.y, "opp");
  const oppRPos = describePosition(oppR.x, oppR.y, "opp");
  const ballInKitchen = ball.y >= NET_Y && ball.y <= NET_Y + KITCHEN;
  const bothOppsK = oppL.y >= NET_Y - KITCHEN - 2 && oppR.y >= NET_Y - KITCHEN - 2;
  const oppLWide = oppL.x < COURT_W / 4, oppRWide = oppR.x > COURT_W * 3 / 4;
  const middleOpen = Math.abs(oppL.x - oppR.x) > 8;
  const meAtBaseline = me.y > NET_Y + KITCHEN + 5;

  if (ballInKitchen && ball.height === "low") {
    return [
      { name: "Cross-Court Dink", why: `Ball low in kitchen. Opponents ${bothOppsK ? "both at kitchen" : "mixed"}.`,
        rally: [
          { shot: 1, who: "You", action: "Soft cross-court dink to backhand side", result: "Lands in opponent kitchen, unattackable" },
          { shot: 2, who: "Opponent", action: `${oppLWide ? "OPP L stretches" : "OPP L"} dinks back down the line`, result: "Returns to your side mid-height" },
          { shot: 3, who: "You", action: middleOpen ? "Speed up through middle gap" : "Reset with cross-court dink", result: middleOpen ? "Splits defenders — winner" : "Maintain kitchen position" },
        ] },
      { name: "Erne Attack", why: `You at ${myPos}. Opponent at ${mySide === "left" ? oppLPos : oppRPos}.`,
        rally: [
          { shot: 1, who: "You", action: "Jump around post for erne volley", result: "Sharp angle surprises opponent" },
          { shot: 2, who: "Opponent", action: "Scramble return — weak pop-up", result: "Ball floats high" },
          { shot: 3, who: "Your Partner", action: `Partner at ${partnerPos} puts away overhead`, result: "Winner" },
        ] },
    ];
  } else if (ball.height === "high" && ball.speed === "slow") {
    return [
      { name: "Overhead to Feet", why: `High slow ball. ${bothOppsK ? "Both at kitchen — target feet." : "Target closer opponent."}`,
        rally: [
          { shot: 1, who: "You", action: `Smash at ${bothOppsK ? "gap between opponents" : "closer opponent's feet"}`, result: "Hard and low" },
          { shot: 2, who: "Opponent", action: "Defensive block — soft float back", result: "Pop-up mid-court" },
          { shot: 3, who: "You", action: "Step in, angled volley putaway", result: "Winner to open court" },
        ] },
      { name: "Deep Placement", why: `Less risky. ${oppRWide || oppLWide ? "Sideline exposed." : "Target weaker player."}`,
        rally: [
          { shot: 1, who: "You", action: `Controlled overhead deep to ${oppRWide ? "right" : "left"} sideline`, result: "Pushes opponent behind baseline" },
          { shot: 2, who: "Opponent", action: "Defensive lob or drive from deep", result: "Returns deep but you hold" },
          { shot: 3, who: "You", action: "Drop into kitchen while they're deep", result: "Forces sprint — you control point" },
        ] },
    ];
  } else if (meAtBaseline && ball.speed === "fast") {
    return [
      { name: "Deep Block + Transition", why: `You're deep at ${myPos}. Fast ball incoming.`,
        rally: [
          { shot: 1, who: "You", action: "Block-return deep, sprint forward", result: "Buys transition time" },
          { shot: 2, who: "Opponent", action: `Opponent at ${oppLPos} drives or drops`, result: "You're now in transition zone" },
          { shot: 3, who: "You", action: "Volley drop into kitchen", result: "Complete advance to kitchen" },
        ] },
      { name: "Counter-Drive Down Line", why: `Opponent at ${mySide === "left" ? oppLPos : oppRPos} may be out of position.`,
        rally: [
          { shot: 1, who: "You", action: "Redirect pace down the line", result: "Uses their power against them" },
          { shot: 2, who: "Opponent", action: "Partner scrambles — weak return", result: "Short ball" },
          { shot: 3, who: "Your Partner", action: `Partner at ${partnerPos} attacks`, result: "Put-away at kitchen" },
        ] },
    ];
  }
  return [
    { name: "Third-Shot Drop", why: `You at ${myPos}, ball in ${describeBallZone(ball.y)}.`,
      rally: [
        { shot: 1, who: "You", action: "Soft drop into opponent kitchen", result: "Lands softly, unattackable" },
        { shot: 2, who: "Opponent", action: `Opponent at ${oppLPos} dinks back`, result: "Dink to your side" },
        { shot: 3, who: "You", action: "Advance to kitchen, engage dink rally", result: "Positioning equalized" },
      ] },
    { name: "Drive + Crash", why: `Aggressive. ${middleOpen ? "Middle gap open." : "Apply pressure."}`,
      rally: [
        { shot: 1, who: "You", action: `Drive ${middleOpen ? "through middle" : "at weaker opponent"}`, result: "Forces quick reaction" },
        { shot: 2, who: "Opponent", action: "Block return — soft ball", result: "You advance" },
        { shot: 3, who: "You", action: "Volley drop from transition", result: "Crash to kitchen line" },
      ] },
    { name: "Lob Over Backhand", why: `${bothOppsK ? "Both pressed to net." : "Creates depth."}`,
      rally: [
        { shot: 1, who: "You", action: "Topspin lob over backhand side", result: "Sails over net player" },
        { shot: 2, who: "Opponent", action: "Chases — running overhead or reset", result: "Off-balance" },
        { shot: 3, who: "You", action: "Attack weak return while advancing", result: "Gain court advantage" },
      ] },
  ];
}

// ── Storage ──
async function loadScenarios() {
  try { const r = await window.storage.get("pickle-scenarios"); return r ? JSON.parse(r.value) : []; }
  catch { return []; }
}
async function saveScenarios(s) {
  try { await window.storage.set("pickle-scenarios", JSON.stringify(s)); } catch {}
}

// ── Control Panel ──
function ControlPanel({ mySide, setMySide, ball, setBall, onAnalyze, isAnalyzing, onSave, scenarioCount }) {
  const inK = ball.y >= NET_Y - KITCHEN && ball.y <= NET_Y + KITCHEN;
  return (
    <div style={panelStyle}>
      <div>
        <label style={st.label}>I AM</label>
        <div style={{ display: "flex", gap: 8 }}>
          {["left", "right"].map(s => <button key={s} onClick={() => setMySide(s)}
            style={{ ...st.btn, ...(mySide === s ? st.active : {}) }}>{s === "left" ? "Left Side" : "Right Side"}</button>)}
        </div>
      </div>
      <div>
        <label style={st.label}>BALL HEIGHT</label>
        <div style={{ display: "flex", gap: 8 }}>
          {["low", "mid", "high"].map(h => <button key={h} onClick={() => setBall(b => ({ ...b, height: h }))}
            style={{ ...st.btn, ...(ball.height === h ? st.active : {}) }}>{h.charAt(0).toUpperCase() + h.slice(1)}</button>)}
        </div>
      </div>
      <div>
        <label style={st.label}>BALL SPEED</label>
        <div style={{ display: "flex", gap: 8 }}>
          {["slow", "fast"].map(s => <button key={s} onClick={() => setBall(b => ({ ...b, speed: s }))}
            style={{ ...st.btn, ...(ball.speed === s ? st.active : {}) }}>{s.charAt(0).toUpperCase() + s.slice(1)}</button>)}
        </div>
      </div>
      {inK && <div>
        <label style={st.label}>SPIN <span style={{ color: "#f59e0b", fontWeight: 400 }}>(kitchen)</span></label>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {["topspin", "flat", "slice"].map(sp => <button key={sp} onClick={() => setBall(b => ({ ...b, spin: sp }))}
            style={{ ...st.btn, ...(ball.spin === sp ? st.active : {}) }}>{sp.charAt(0).toUpperCase() + sp.slice(1)}</button>)}
        </div>
      </div>}
      <div style={{ background: "rgba(0,0,0,0.3)", borderRadius: 8, padding: "10px 14px", fontSize: 11, fontFamily: "'DM Mono', monospace", color: "rgba(255,255,255,0.4)", lineHeight: 1.7 }}>
        Ball: ({ball.x.toFixed(1)}ft, {ball.y.toFixed(1)}ft) · {ball.height} · {ball.speed}{inK && ball.spin ? ` · ${ball.spin}` : ""}<br />
        Zone: {describeBallZone(ball.y)}
      </div>
      <button onClick={onAnalyze} disabled={isAnalyzing} style={{ ...st.analyze, opacity: isAnalyzing ? 0.6 : 1 }}>
        {isAnalyzing ? "Analyzing..." : "What Shot Should I Hit?"}
      </button>
      <button onClick={onSave} style={st.save}>Save Scenario {scenarioCount > 0 ? `(${scenarioCount})` : ""}</button>
    </div>
  );
}

// ── Results ──
function ResultsPanel({ result }) {
  if (!result) return null;
  return (
    <div style={{ ...panelStyle, marginTop: 14 }}>
      <h3 style={{ margin: "0 0 14px 0", fontFamily: "'DM Mono', monospace", fontSize: 12, fontWeight: 700, color: "#f59e0b", letterSpacing: "1.5px", textTransform: "uppercase" }}>Shot Recommendations</h3>
      {result.map((shot, i) => (
        <div key={i} style={{ padding: "14px 16px", marginBottom: 12, background: i === 0 ? "rgba(245,158,11,0.06)" : "rgba(255,255,255,0.015)", borderRadius: 10, borderLeft: `3px solid ${i === 0 ? "#f59e0b" : "rgba(255,255,255,0.06)"}` }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, fontWeight: 800, color: i === 0 ? "#f59e0b" : "rgba(255,255,255,0.25)", minWidth: 22 }}>#{i + 1}</span>
            <span style={{ fontFamily: "'Outfit', sans-serif", fontSize: 15, fontWeight: 700, color: "#e8e4dd" }}>{shot.name}</span>
          </div>
          <p style={{ margin: "0 0 10px 30px", fontSize: 12, color: "rgba(255,255,255,0.4)", lineHeight: 1.5, fontFamily: "'DM Mono', monospace", fontStyle: "italic" }}>{shot.why}</p>
          <div style={{ marginLeft: 30 }}>
            {shot.rally.map((step, j) => {
              const isYou = step.who === "You" || step.who === "Your Partner";
              return (
                <div key={j} style={{ display: "flex", gap: 10 }}>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", minWidth: 24 }}>
                    <div style={{ width: 20, height: 20, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9.5, fontWeight: 800, fontFamily: "'DM Mono', monospace", background: isYou ? "rgba(72,191,227,0.2)" : "rgba(239,100,97,0.2)", color: isYou ? "#48bfe3" : "#ef6461", border: `1.5px solid ${isYou ? "rgba(72,191,227,0.4)" : "rgba(239,100,97,0.4)"}`, flexShrink: 0 }}>{step.shot}</div>
                    {j < shot.rally.length - 1 && <div style={{ width: 1.5, height: 22, background: "rgba(255,255,255,0.08)" }} />}
                  </div>
                  <div style={{ paddingBottom: j < shot.rally.length - 1 ? 5 : 0, flex: 1 }}>
                    <div style={{ fontSize: 10, fontWeight: 700, fontFamily: "'DM Mono', monospace", color: isYou ? "#48bfe3" : "#ef6461", textTransform: "uppercase", letterSpacing: "1px", marginBottom: 2 }}>{step.who}</div>
                    <div style={{ fontSize: 12.5, color: "rgba(255,255,255,0.6)", lineHeight: 1.5, fontFamily: "'Outfit', sans-serif" }}>{step.action}</div>
                    <div style={{ fontSize: 11, color: "rgba(255,255,255,0.3)", lineHeight: 1.4, fontFamily: "'DM Mono', monospace", marginTop: 2 }}>→ {step.result}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Scenarios ──
function ScenarioList({ scenarios, onLoad, onDelete }) {
  const [open, setOpen] = useState(false);
  if (!scenarios.length) return null;
  return (
    <div style={{ ...panelStyle, marginTop: 14 }}>
      <button onClick={() => setOpen(!open)} style={{ background: "none", border: "none", color: "rgba(255,255,255,0.5)", fontFamily: "'DM Mono', monospace", fontSize: 12, fontWeight: 600, cursor: "pointer", padding: 0, width: "100%", textAlign: "left", display: "flex", justifyContent: "space-between" }}>
        <span>SAVED SCENARIOS ({scenarios.length})</span><span style={{ fontSize: 16 }}>{open ? "−" : "+"}</span>
      </button>
      {open && <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
        {scenarios.map(sc => (
          <div key={sc.id} style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 10px", borderRadius: 6, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: "#e8e4dd", fontFamily: "'Outfit', sans-serif", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{sc.name}</div>
              <div style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", fontFamily: "'DM Mono', monospace" }}>{new Date(sc.timestamp).toLocaleDateString()}</div>
            </div>
            <button onClick={() => onLoad(sc)} style={{ padding: "4px 10px", borderRadius: 4, border: "1px solid rgba(72,191,227,0.3)", background: "rgba(72,191,227,0.1)", color: "#48bfe3", fontSize: 10, fontFamily: "'DM Mono', monospace", fontWeight: 600, cursor: "pointer" }}>Load</button>
            <button onClick={() => onDelete(sc.id)} style={{ padding: "4px 8px", borderRadius: 4, border: "1px solid rgba(239,100,97,0.3)", background: "rgba(239,100,97,0.1)", color: "#ef6461", fontSize: 10, fontFamily: "'DM Mono', monospace", fontWeight: 600, cursor: "pointer" }}>×</button>
          </div>
        ))}
      </div>}
    </div>
  );
}

// ── App ──
export default function PickleballStrategyViz() {
  const svgRef = useRef(null);
  const [mySide, setMySide] = useState("left");
  const [dragging, setDragging] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [toast, setToast] = useState(false);
  const [players, setPlayers] = useState({ opp_left: { x: 5, y: 7 }, opp_right: { x: 15, y: 7 }, my_left: { x: 5, y: 37 }, my_right: { x: 15, y: 37 } });
  const [ball, setBall] = useState({ x: 10, y: 33, height: "mid", speed: "slow", spin: null });

  useEffect(() => { loadScenarios().then(setScenarios); }, []);

  const getSvgPt = useCallback((e) => {
    const svg = svgRef.current?.querySelector("svg");
    if (!svg) return null;
    const r = svg.getBoundingClientRect();
    return { x: (e.clientX - r.left) * (SVG_W / r.width), y: (e.clientY - r.top) * (SVG_H / r.height) };
  }, []);

  const handlePointerDown = useCallback((e, id) => { e.preventDefault(); e.stopPropagation(); setDragging(id); }, []);

  useEffect(() => {
    if (!dragging) return;
    const move = (e) => {
      e.preventDefault();
      const ce = e.touches ? e.touches[0] : e;
      const pt = getSvgPt(ce);
      if (!pt) return;
      const [ftX, ftY] = screenToCourt(pt.x, pt.y);
      if (dragging === "ball") {
        setBall(b => ({ ...b, x: Math.max(0, Math.min(COURT_W, ftX)), y: Math.max(NET_Y, Math.min(COURT_L, ftY)) }));
      } else {
        const isOpp = dragging.startsWith("opp"), isLeft = dragging.includes("left");
        let cy = isOpp ? Math.max(0, Math.min(NET_Y, ftY)) : Math.max(NET_Y, Math.min(COURT_L, ftY));
        let cx = Math.max(0, Math.min(COURT_W, ftX));
        setPlayers(p => {
          const u = { ...p, [dragging]: { x: cx, y: cy } };
          const pfx = isOpp ? "opp" : "my";
          if (isLeft && u[`${pfx}_left`].x > u[`${pfx}_right`].x - 1) u[`${pfx}_left`] = { ...u[`${pfx}_left`], x: u[`${pfx}_right`].x - 1 };
          if (!isLeft && u[`${pfx}_right`].x < u[`${pfx}_left`].x + 1) u[`${pfx}_right`] = { ...u[`${pfx}_right`], x: u[`${pfx}_left`].x + 1 };
          return u;
        });
      }
    };
    const up = () => setDragging(null);
    window.addEventListener("pointermove", move, { passive: false });
    window.addEventListener("pointerup", up);
    window.addEventListener("touchmove", move, { passive: false });
    window.addEventListener("touchend", up);
    return () => { window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up); window.removeEventListener("touchmove", move); window.removeEventListener("touchend", up); };
  }, [dragging, getSvgPt]);

  useEffect(() => {
    const inK = ball.y >= NET_Y - KITCHEN && ball.y <= NET_Y + KITCHEN;
    if (!inK && ball.spin) setBall(b => ({ ...b, spin: null }));
  }, [ball.y, ball.spin]);

  const analyze = async () => {
    setIsAnalyzing(true); setResult(null);
    await new Promise(r => setTimeout(r, 1200));
    setResult(generateRally(players, ball, mySide));
    setIsAnalyzing(false);
  };

  const save = async () => {
    const nm = `${describeBallZone(ball.y)} · ${ball.height} ${ball.speed}${ball.spin ? ` · ${ball.spin}` : ""}`;
    const sc = { id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6), name: nm, timestamp: new Date().toISOString(), state: { players: { ...players }, ball: { ...ball }, mySide, result } };
    const u = [sc, ...scenarios].slice(0, 50);
    setScenarios(u); await saveScenarios(u);
    setToast(true); setTimeout(() => setToast(false), 2000);
  };

  return (
    <div style={{ minHeight: "100vh", background: "#0e1117", color: "#e8e4dd", fontFamily: "'Outfit', sans-serif", padding: "20px 12px" }}>
      <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet" />
      {toast && <div style={{ position: "fixed", top: 20, left: "50%", transform: "translateX(-50%)", background: "#f59e0b", color: "#1a1a1a", padding: "10px 24px", borderRadius: 8, fontFamily: "'DM Mono', monospace", fontSize: 13, fontWeight: 700, zIndex: 100, boxShadow: "0 4px 20px rgba(0,0,0,0.3)" }}>Scenario saved!</div>}
      <div style={{ maxWidth: 1150, margin: "0 auto 16px", textAlign: "center" }}>
        <h1 style={{ fontFamily: "'DM Mono', monospace", fontSize: 20, fontWeight: 800, letterSpacing: "2px", margin: 0, color: "#f59e0b", textTransform: "uppercase" }}>Pickle Playbook</h1>
        <p style={{ fontSize: 12, color: "rgba(255,255,255,0.3)", margin: "5px 0 0", fontFamily: "'DM Mono', monospace" }}>Drag players & ball → set parameters → get 3-shot rally analysis</p>
      </div>
      <div style={{ maxWidth: 1150, margin: "0 auto", display: "flex", gap: 18, flexWrap: "wrap", justifyContent: "center", alignItems: "flex-start" }}>
        <div ref={svgRef} style={{ borderRadius: 10, overflow: "hidden", flexShrink: 0, boxShadow: "0 8px 40px rgba(0,0,0,0.6)" }}>
          <Court3D players={players} ball={ball} mySide={mySide} dragging={dragging} onPointerDown={handlePointerDown} />
        </div>
        <div style={{ flex: "1 1 280px", minWidth: 280, maxWidth: 340 }}>
          <ControlPanel mySide={mySide} setMySide={setMySide} ball={ball} setBall={setBall} onAnalyze={analyze} isAnalyzing={isAnalyzing} onSave={save} scenarioCount={scenarios.length} />
          <ResultsPanel result={result} />
          <ScenarioList scenarios={scenarios} onLoad={(sc) => { setPlayers(sc.state.players); setBall(sc.state.ball); setMySide(sc.state.mySide); setResult(sc.state.result || null); }} onDelete={async (id) => { const u = scenarios.filter(s => s.id !== id); setScenarios(u); await saveScenarios(u); }} />
        </div>
      </div>
    </div>
  );
}

const panelStyle = { background: "#1c2530", borderRadius: 12, padding: "18px 20px", display: "flex", flexDirection: "column", gap: 16, border: "1px solid rgba(255,255,255,0.06)" };
const st = {
  label: { display: "block", fontFamily: "'DM Mono', monospace", fontSize: 10, fontWeight: 600, letterSpacing: "1.5px", color: "rgba(255,255,255,0.4)", textTransform: "uppercase", marginBottom: 7 },
  btn: { flex: 1, padding: "8px 10px", borderRadius: 6, border: "1px solid rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.03)", color: "rgba(255,255,255,0.45)", fontFamily: "'DM Mono', monospace", fontSize: 12, fontWeight: 500, cursor: "pointer", transition: "all 0.15s" },
  active: { background: "rgba(245,158,11,0.15)", borderColor: "#f59e0b", color: "#f59e0b", fontWeight: 700 },
  analyze: { width: "100%", padding: "13px 18px", borderRadius: 8, border: "none", background: "linear-gradient(135deg, #f59e0b, #d97706)", color: "#1a1a1a", fontFamily: "'DM Mono', monospace", fontSize: 13, fontWeight: 800, letterSpacing: "0.5px", cursor: "pointer", textTransform: "uppercase" },
  save: { width: "100%", padding: "10px 18px", borderRadius: 8, border: "1px solid rgba(72,191,227,0.3)", background: "rgba(72,191,227,0.08)", color: "#48bfe3", fontFamily: "'DM Mono', monospace", fontSize: 12, fontWeight: 600, cursor: "pointer", textTransform: "uppercase", letterSpacing: "0.5px" },
};
