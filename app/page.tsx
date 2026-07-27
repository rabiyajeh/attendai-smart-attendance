"use client";

import { useMemo, useState } from "react";
import {
  Activity, Bell, BookOpen, CalendarDays, Camera, ChevronDown, ChevronRight,
  CircleHelp, Clock3, Download, FileCheck2, Fingerprint, GraduationCap, LayoutDashboard,
  Menu, MoreHorizontal, Search, Settings, ShieldCheck, Sparkles, TrendingUp, UserCheck,
  UserRound, Users, X, Zap,
} from "lucide-react";
import {
  Area, AreaChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";

const trend = [
  { day: "Mon", rate: 88 }, { day: "Tue", rate: 91 }, { day: "Wed", rate: 89 },
  { day: "Thu", rate: 94 }, { day: "Fri", rate: 92 }, { day: "Sat", rate: 86 },
  { day: "Sun", rate: 90 },
];
const courses = [
  { name: "Computer Science", code: "CS-401", rate: 94, students: 42, color: "#18d7c0" },
  { name: "Data Structures", code: "CS-302", rate: 88, students: 38, color: "#5eead4" },
  { name: "Artificial Intelligence", code: "AI-501", rate: 91, students: 31, color: "#22d3ee" },
];
const activity = [
  { initials: "SA", name: "Sara Ahmed", text: "recognized in CS-401", time: "2 min ago", status: "Present", color: "#705CF6" },
  { initials: "MK", name: "Mustafa Khan", text: "marked late in AI-501", time: "8 min ago", status: "Late", color: "#F59E0B" },
  { initials: "AL", name: "Ayesha Latif", text: "correction approved", time: "16 min ago", status: "Updated", color: "#08A88A" },
  { initials: "HR", name: "Hamza Raza", text: "recognized in CS-302", time: "24 min ago", status: "Present", color: "#0284C7" },
];
const nav = [
  ["Dashboard", LayoutDashboard], ["Live Attendance", Camera], ["Students", Users],
  ["Courses & Classes", BookOpen], ["Timetable", CalendarDays], ["Face Enrollment", Fingerprint],
  ["Attendance Records", FileCheck2], ["Analytics & Reports", TrendingUp],
  ["Correction Requests", CircleHelp], ["Audit Log", ShieldCheck],
] as const;

export default function Home() {
  const [active, setActive] = useState("Dashboard");
  const [sidebar, setSidebar] = useState(false);
  const [session, setSession] = useState(false);
  const [notice, setNotice] = useState("");
  const [range, setRange] = useState("This week");
  const [search, setSearch] = useState("");
  const filteredActivity = useMemo(() => activity.filter(a => a.name.toLowerCase().includes(search.toLowerCase())), [search]);

  function toast(message: string) {
    setNotice(message);
    setTimeout(() => setNotice(""), 2600);
  }

  return (
    <main className="app-shell">
      {sidebar && <button className="scrim" aria-label="Close menu" onClick={() => setSidebar(false)} />}
      <aside className={`sidebar ${sidebar ? "open" : ""}`}>
        <div className="brand">
          <div className="brand-mark"><Sparkles size={19} /></div>
          <div><strong>Attend<span>AI</span></strong><small>SMART ATTENDANCE</small></div>
          <button className="mobile-close" onClick={() => setSidebar(false)}><X size={20}/></button>
        </div>
        <div className="org-card">
          <div className="org-icon"><GraduationCap size={20}/></div>
          <div><strong>Nexus University</strong><span>Academic portal</span></div>
          <ChevronDown size={16}/>
        </div>
        <nav>
          <p>WORKSPACE</p>
          {nav.slice(0, 6).map(([label, Icon]) => (
            <button key={label} className={active === label ? "active" : ""} onClick={() => { setActive(label); setSidebar(false); }}>
              <Icon size={18}/><span>{label}</span>{label === "Correction Requests" && <i>4</i>}
            </button>
          ))}
          <p>INSIGHTS & CONTROL</p>
          {nav.slice(6).map(([label, Icon]) => (
            <button key={label} className={active === label ? "active" : ""} onClick={() => { setActive(label); setSidebar(false); }}>
              <Icon size={18}/><span>{label}</span>{label === "Correction Requests" && <i>4</i>}
            </button>
          ))}
        </nav>
        <div className="privacy-note">
          <ShieldCheck size={19}/><div><strong>Privacy protected</strong><span>Biometric data encrypted</span></div>
        </div>
        <div className="user-card">
          <div className="avatar">FK</div><div><strong>Farrukh Khan</strong><span>Administrator</span></div><MoreHorizontal size={18}/>
        </div>
      </aside>

      <section className="workspace">
        <header>
          <button className="menu-btn" onClick={() => setSidebar(true)}><Menu size={22}/></button>
          <div className="search"><Search size={18}/><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search students, courses, records…" /><kbd>⌘ K</kbd></div>
          <div className="header-actions">
            <button className="icon-btn" aria-label="Notifications" onClick={() => toast("You have 3 unread notifications")}><Bell size={19}/><i /></button>
            <button className="icon-btn" aria-label="Settings" onClick={() => setActive("Settings")}><Settings size={19}/></button>
            <div className="header-user"><div className="avatar">FK</div><div><strong>Farrukh Khan</strong><span>Administrator</span></div><ChevronDown size={15}/></div>
          </div>
        </header>

        <div className="content">
          {active === "Dashboard" ? (
            <>
              <div className="hero-row">
                <div><p className="eyebrow"><span /><span>MONDAY, 27 JULY 2026</span></p><h1>Good evening, Farrukh <span>👋</span></h1><p>Here’s what’s happening across your institution today.</p></div>
                <div className="hero-actions">
                  <button className="secondary" onClick={() => toast("Report exported as CSV")}><Download size={17}/> Export report</button>
                  <button className="primary" onClick={() => { setActive("Live Attendance"); setSession(true); }}><Camera size={17}/> Start live session</button>
                </div>
              </div>
              <div className="status-strip"><div><Zap size={15}/> <strong>All systems operational</strong><span>•</span><span>Recognition service</span><b>Online</b></div><span>Last checked just now</span></div>
              <section className="stats-grid">
                <Stat icon={Users} label="Total students" value="1,248" detail="+32 this semester" tone="purple" />
                <Stat icon={BookOpen} label="Classes today" value="18" detail="12 completed · 6 active" tone="cyan" />
                <Stat icon={UserCheck} label="Present today" value="1,087" detail="87.1% attendance rate" tone="green" />
                <Stat icon={Clock3} label="Late arrivals" value="43" detail="3.4% of students" tone="amber" />
              </section>
              <section className="dashboard-grid">
                <article className="panel trend-panel">
                  <div className="panel-head"><div><h2>Attendance overview</h2><p>Daily attendance rate across all departments</p></div><select value={range} onChange={e => setRange(e.target.value)}><option>This week</option><option>This month</option><option>This semester</option></select></div>
                  <div className="chart-summary"><strong>90.4%</strong><span><TrendingUp size={14}/> 2.8%</span><small>vs previous period</small></div>
                  <div className="area-wrap"><ResponsiveContainer width="100%" height="100%"><AreaChart data={trend} margin={{ left: -28, right: 8, top: 10 }}><defs><linearGradient id="fillTeal" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#14b8a6" stopOpacity=".3"/><stop offset="100%" stopColor="#14b8a6" stopOpacity=".01"/></linearGradient></defs><CartesianGrid vertical={false} stroke="#e8eef2" strokeDasharray="4 4"/><XAxis dataKey="day" axisLine={false} tickLine={false} tick={{fill:"#81909c",fontSize:12}}/><YAxis domain={[70,100]} axisLine={false} tickLine={false} tick={{fill:"#81909c",fontSize:12}}/><Tooltip contentStyle={{borderRadius:12,border:"1px solid #dce7e9"}}/><Area type="monotone" dataKey="rate" stroke="#0d9f91" strokeWidth={3} fill="url(#fillTeal)"/></AreaChart></ResponsiveContainer></div>
                </article>
                <article className="panel distribution">
                  <div className="panel-head"><div><h2>Today’s distribution</h2><p>Live attendance breakdown</p></div><button><MoreHorizontal size={20}/></button></div>
                  <div className="donut"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={[{v:87.1,c:"#0d9f91"},{v:3.4,c:"#f2b34b"},{v:7.6,c:"#ef6d70"},{v:1.9,c:"#a59cf6"}]} dataKey="v" innerRadius={63} outerRadius={83} paddingAngle={2} stroke="none">{["#0d9f91","#f2b34b","#ef6d70","#a59cf6"].map(c=><Cell key={c} fill={c}/>)}</Pie></PieChart></ResponsiveContainer><div><strong>1,248</strong><span>Students</span></div></div>
                  <div className="legend"><Legend color="#0d9f91" label="Present" val="1,087"/><Legend color="#f2b34b" label="Late" val="43"/><Legend color="#ef6d70" label="Absent" val="95"/><Legend color="#a59cf6" label="Excused" val="23"/></div>
                </article>
                <article className="panel courses">
                  <div className="panel-head"><div><h2>Course performance</h2><p>Attendance rate by active course</p></div><button className="text-btn" onClick={() => setActive("Analytics & Reports")}>View all <ChevronRight size={15}/></button></div>
                  {courses.map(c => <div className="course" key={c.code}><div className="course-icon" style={{background:c.color+"24",color:c.color}}><BookOpen size={18}/></div><div className="course-main"><div><strong>{c.name}</strong><span>{c.code} · {c.students} students</span></div><b>{c.rate}%</b><div className="progress"><i style={{width:c.rate+"%",background:c.color}}/></div></div></div>)}
                </article>
                <article className="panel recent">
                  <div className="panel-head"><div><h2>Recent activity</h2><p>Latest attendance events</p></div><button className="text-btn" onClick={() => setActive("Attendance Records")}>View records <ChevronRight size={15}/></button></div>
                  {filteredActivity.length ? filteredActivity.map(a => <div className="activity-row" key={a.name}><div className="mini-avatar" style={{background:a.color}}>{a.initials}</div><div><strong>{a.name}</strong><span>{a.text}</span></div><time>{a.time}</time><em className={a.status.toLowerCase()}>{a.status}</em></div>) : <div className="empty">No activity matches “{search}”.</div>}
                </article>
              </section>
            </>
          ) : active === "Live Attendance" ? <LiveSession running={session} setRunning={setSession} toast={toast}/> : <ModulePage name={active} toast={toast}/>}
          <footer><span>AttendAI v1.0 · Privacy-first attendance intelligence</span><span><ShieldCheck size={14}/> AES-256 biometric encryption · Audit logging enabled</span></footer>
        </div>
      </section>
      {notice && <div className="toast"><FileCheck2 size={18}/>{notice}</div>}
    </main>
  );
}

function Stat({icon:Icon,label,value,detail,tone}:{icon:typeof Users,label:string,value:string,detail:string,tone:string}) {
  return <article className="stat-card"><div className={`stat-icon ${tone}`}><Icon size={21}/></div><div><span>{label}</span><strong>{value}</strong><small>{detail}</small></div><MoreHorizontal size={18}/></article>;
}
function Legend({color,label,val}:{color:string,label:string,val:string}) { return <div><i style={{background:color}}/><span>{label}</span><strong>{val}</strong></div>; }
function LiveSession({running,setRunning,toast}:{running:boolean,setRunning:(v:boolean)=>void,toast:(s:string)=>void}) {
  return <><div className="hero-row"><div><p className="eyebrow"><span/><span>FACIAL RECOGNITION</span></p><h1>Live attendance</h1><p>CS-401 · Advanced Computing · Room A-204</p></div><button className={running?"danger":"primary"} onClick={()=>{setRunning(!running);toast(running?"Session ended and absences calculated":"Camera session started securely")}}>{running?<><X size={17}/> End session</>:<><Camera size={17}/> Start camera</>}</button></div><div className="scanner-grid"><div className="camera-panel"><div className="camera-top"><span className={running?"live-dot":""}>{running?"LIVE":"READY"}</span><span>Camera 01 · 1080p</span></div><div className="camera-view"><Camera size={52}/><strong>{running?"Scanning for faces…":"Camera is paused"}</strong><span>{running?"Liveness checks and multi-frame confirmation active":"Start the session when your class is ready"}</span>{running&&<div className="face-box"><span>Sara Ahmed · 98.6%</span></div>}</div></div><div className="panel session-side"><h2>Session progress</h2><div className="session-count"><strong>{running?"29":"0"}</strong><span>of 42 recognized</span></div><div className="progress"><i style={{width:running?"69%":"0%"}}/></div><hr/><h3>Recognition policy</h3><p><ShieldCheck size={16}/> 3 consecutive frames required</p><p><Activity size={16}/> 88% confidence threshold</p><p><Fingerprint size={16}/> Active liveness detection</p><button className="secondary wide" onClick={()=>toast("Secure QR fallback opened")}>Open QR fallback</button></div></div></>;
}
function ModulePage({name,toast}:{name:string,toast:(s:string)=>void}) {
  const copy:Record<string,[string,string]> = {
    Students:["Student directory","Manage enrollment, identity, consent, and attendance standing."],
    "Courses & Classes":["Courses & classes","Organize departments, courses, enrollments, and class groups."],
    Timetable:["Academic timetable","Schedule classes, rooms, teachers, holidays, and attendance windows."],
    "Face Enrollment":["Facial enrollment","Capture consented, quality-checked samples and store encrypted embeddings."],
    "Attendance Records":["Attendance records","Review server-timestamped attendance with a complete correction trail."],
    "Analytics & Reports":["Analytics & reports","Explore attendance trends and generate CSV or PDF reports."],
    "Correction Requests":["Correction requests","Review student evidence and approve or reject attendance changes."],
    "Audit Log":["Audit log","Trace biometric enrollment, deletion, and attendance modifications."],
    Settings:["Settings","Configure attendance rules, retention, security, and notifications."],
  };
  const [title,desc]=copy[name]||[name,"Manage this area of your attendance workspace."];
  return <><div className="hero-row"><div><p className="eyebrow"><span/><span>WORKSPACE</span></p><h1>{title}</h1><p>{desc}</p></div><button className="primary" onClick={()=>toast(`${title} action created`)}><Sparkles size={17}/> New action</button></div><div className="module-grid"><article className="panel module-main"><div className="panel-head"><div><h2>{title}</h2><p>Connected to role-based APIs and protected audit logging</p></div><div className="search compact"><Search size={17}/><input placeholder={`Search ${title.toLowerCase()}…`}/></div></div>{activity.map((a,i)=><div className="data-row" key={a.name}><div className="mini-avatar" style={{background:a.color}}>{a.initials}</div><div><strong>{a.name}</strong><span>{i%2?"NU-2026-10"+i:"Computer Science · Semester 6"}</span></div><em className={i===1?"late":"present"}>{i===1?"Pending review":"Active"}</em><button><MoreHorizontal size={18}/></button></div>)}</article><article className="panel quick-panel"><div className="quick-icon"><ShieldCheck size={24}/></div><h2>Privacy by design</h2><p>Every sensitive action requires authorization and creates an immutable audit event. Facial embeddings never leave the secure service.</p><button className="secondary wide" onClick={()=>toast("Privacy controls opened")}>Review controls</button></article></div></>;
}
