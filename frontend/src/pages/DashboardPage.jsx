// import React, { useState, useEffect } from "react";
// import { useNavigate } from "react-router-dom";
// import {
//   LineChart,
//   Line,
//   XAxis,
//   YAxis,
//   Tooltip,
//   ResponsiveContainer,
// } from "recharts";
// import { useChatStore } from "../store/chatStore.js";

// const CFG = [
//   {
//     key: "heart_rate",
//     label: "Heart Rate",
//     unit: "bpm",
//     normal: [60, 100],
//     color: "#ef4444",
//     icon: "❤️",
//     desc: "Normal: 60–100 bpm",
//   },
//   {
//     key: "spo2",
//     label: "SpO2",
//     unit: "%",
//     normal: [95, 100],
//     color: "#3b82f6",
//     icon: "🫁",
//     desc: "Normal: 95–100%",
//   },
//   {
//     key: "temperature",
//     label: "Temperature",
//     unit: "°C",
//     normal: [36.1, 37.2],
//     color: "#f59e0b",
//     icon: "🌡️",
//     desc: "Normal: 36.1–37.2°C",
//   },
//   {
//     key: "systolic_bp",
//     label: "Systolic BP",
//     unit: "mmHg",
//     normal: [90, 120],
//     color: "#8b5cf6",
//     icon: "💉",
//     desc: "Normal: 90–120 mmHg",
//   },
//   {
//     key: "glucose",
//     label: "Glucose",
//     unit: "mg/dL",
//     normal: [70, 99],
//     color: "#10b981",
//     icon: "🩸",
//     desc: "Normal: 70–99 mg/dL (fasting)",
//   },
// ];

// function getRisk(key, val) {
//   const c = CFG.find((v) => v.key === key);
//   if (!c || val == null) return "normal";
//   return val < c.normal[0] || val > c.normal[1] ? "warning" : "normal";
// }

// const riskColor = (r) =>
//   ({ normal: "#10b981", warning: "#f59e0b", critical: "#ef4444" })[r] ||
//   "#10b981";

// function VCard({ c, value, hist }) {
//   const risk = getRisk(c.key, value);
//   const rc = riskColor(risk);
//   return (
//     <div
//       style={{
//         background: "var(--bg-card)",
//         border: `1px solid ${risk === "normal" ? "var(--border)" : rc + "40"}`,
//         borderRadius: "var(--radius)",
//         padding: "1.25rem",
//         display: "flex",
//         flexDirection: "column",
//         gap: "0.625rem",
//       }}
//     >
//       <div
//         style={{
//           display: "flex",
//           justifyContent: "space-between",
//           alignItems: "center",
//         }}
//       >
//         <div style={{ display: "flex", alignItems: "center", gap: "0.45rem" }}>
//           <span style={{ fontSize: "1.1rem" }}>{c.icon}</span>
//           <span
//             style={{
//               fontSize: "0.82rem",
//               color: "var(--text-secondary)",
//               fontWeight: 500,
//             }}
//           >
//             {c.label}
//           </span>
//         </div>
//         <span
//           style={{
//             fontSize: "0.7rem",
//             padding: "0.18rem 0.5rem",
//             background: `${rc}18`,
//             color: rc,
//             borderRadius: "20px",
//             fontWeight: 600,
//           }}
//         >
//           {risk === "normal" ? "✓ OK" : "⚠ Alert"}
//         </span>
//       </div>
//       <div style={{ display: "flex", alignItems: "baseline", gap: "0.25rem" }}>
//         <span
//           style={{
//             fontSize: "2rem",
//             fontWeight: 600,
//             color: c.color,
//             lineHeight: 1,
//           }}
//         >
//           {value != null
//             ? typeof value === "number"
//               ? +value.toFixed(1)
//               : value
//             : "—"}
//         </span>
//         <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
//           {c.unit}
//         </span>
//       </div>
//       <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
//         {c.desc}
//       </div>
//       {hist && hist.length > 2 && (
//         <ResponsiveContainer width="100%" height={52}>
//           <LineChart data={hist}>
//             <Line
//               type="monotone"
//               dataKey="v"
//               stroke={c.color}
//               strokeWidth={1.5}
//               dot={false}
//               isAnimationActive={false}
//             />
//           </LineChart>
//         </ResponsiveContainer>
//       )}
//     </div>
//   );
// }

// const randomDelta = (base, spread) =>
//   +(base + (Math.random() - 0.5) * spread).toFixed(1);

// export default function DashboardPage() {
//   const navigate = useNavigate();
//   const { vitals } = useChatStore();

//   const [live, setLive] = useState({
//     heart_rate: 72,
//     spo2: 98,
//     temperature: 36.8,
//     systolic_bp: 118,
//     glucose: 94,
//   });
//   const [hist, setHist] = useState(() =>
//     CFG.reduce(
//       (a, c) => ({
//         ...a,
//         [c.key]: Array.from({ length: 12 }, (_, i) => ({
//           t: i,
//           v: live[c.key] + (Math.random() - 0.5) * 4,
//         })),
//       }),
//       {},
//     ),
//   );

//   // Simulate live updates when no real IoMT
//   useEffect(() => {
//     if (vitals) return;
//     const id = setInterval(() => {
//       setLive((p) => {
//         const n = {
//           heart_rate: Math.round(randomDelta(p.heart_rate, 5)),
//           spo2: Math.min(100, Math.max(93, randomDelta(p.spo2, 0.8))),
//           temperature: randomDelta(p.temperature, 0.15),
//           systolic_bp: Math.round(randomDelta(p.systolic_bp, 4)),
//           glucose: Math.round(randomDelta(p.glucose, 3)),
//         };
//         setHist((h) => {
//           const updated = { ...h };
//           CFG.forEach((c) => {
//             const arr = [...h[c.key], { t: Date.now(), v: n[c.key] }];
//             updated[c.key] = arr.slice(-15);
//           });
//           return updated;
//         });
//         return n;
//       });
//     }, 3000);
//     return () => clearInterval(id);
//   }, [vitals]);

//   const display = vitals || live;

//   return (
//     <div
//       style={{
//         minHeight: "100vh",
//         background: "var(--bg-primary)",
//         padding: "1.5rem",
//       }}
//     >
//       <div style={{ maxWidth: "1000px", margin: "0 auto" }}>
//         {/* Header */}
//         <div
//           style={{
//             display: "flex",
//             justifyContent: "space-between",
//             alignItems: "flex-start",
//             marginBottom: "1.5rem",
//             flexWrap: "wrap",
//             gap: "1rem",
//           }}
//         >
//           <div>
//             <h1
//               style={{
//                 fontSize: "1.4rem",
//                 fontWeight: 600,
//                 marginBottom: "0.3rem",
//               }}
//             >
//               📡 Vitals Dashboard
//             </h1>
//             <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>
//               {vitals
//                 ? "🟢 Live IoMT data"
//                 : "🟡 Demo mode — connect IoMT device for live readings"}
//             </p>
//           </div>
//           <button
//             onClick={() => navigate("/chat")}
//             style={{
//               background: "var(--bg-card)",
//               border: "1px solid var(--border)",
//               color: "var(--text-secondary)",
//               padding: "0.5rem 1rem",
//               borderRadius: "var(--radius-sm)",
//               cursor: "pointer",
//               fontFamily: "var(--font-main)",
//               fontSize: "0.85rem",
//             }}
//           >
//             ← Back to Chat
//           </button>
//         </div>

//         {/* Vitals grid */}
//         <div
//           style={{
//             display: "grid",
//             gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))",
//             gap: "1rem",
//             marginBottom: "1.25rem",
//           }}
//         >
//           {CFG.map((c) => (
//             <VCard
//               key={c.key}
//               c={c}
//               value={display?.[c.key]}
//               hist={hist[c.key]}
//             />
//           ))}
//         </div>

//         {/* Ask AI CTA */}
//         <div
//           style={{
//             background: "var(--bg-card)",
//             border: "1px solid var(--border)",
//             borderRadius: "var(--radius)",
//             padding: "1.25rem",
//             display: "flex",
//             justifyContent: "space-between",
//             alignItems: "center",
//             flexWrap: "wrap",
//             gap: "1rem",
//             marginBottom: "1rem",
//           }}
//         >
//           <div>
//             <div style={{ fontWeight: 600, marginBottom: "0.2rem" }}>
//               Ask AI about your vitals
//             </div>
//             <div
//               style={{ fontSize: "0.83rem", color: "var(--text-secondary)" }}
//             >
//               Go to chat and ask "Analyse my current vitals" for a detailed
//               health assessment.
//             </div>
//           </div>
//           <button
//             onClick={() => navigate("/chat")}
//             style={{
//               background: "var(--accent)",
//               color: "#fff",
//               border: "none",
//               borderRadius: "var(--radius-sm)",
//               padding: "0.6rem 1.25rem",
//               cursor: "pointer",
//               fontFamily: "var(--font-main)",
//               fontWeight: 600,
//               fontSize: "0.875rem",
//             }}
//           >
//             Analyse Vitals →
//           </button>
//         </div>

//         {!vitals && (
//           <div
//             style={{
//               background: "rgba(245,158,11,0.05)",
//               border: "1px solid rgba(245,158,11,0.2)",
//               borderRadius: "var(--radius)",
//               padding: "0.875rem",
//               fontSize: "0.83rem",
//               color: "#f59e0b",
//             }}
//           >
//             📡 IoMT not connected. Add{" "}
//             <code
//               style={{
//                 background: "rgba(245,158,11,0.1)",
//                 padding: "1px 4px",
//                 borderRadius: "4px",
//               }}
//             >
//               IOMT_API_KEY
//             </code>{" "}
//             to backend{" "}
//             <code
//               style={{
//                 background: "rgba(245,158,11,0.1)",
//                 padding: "1px 4px",
//                 borderRadius: "4px",
//               }}
//             >
//               .env
//             </code>{" "}
//             to see live readings.
//           </div>
//         )}
//       </div>
//     </div>
//   );
// }
