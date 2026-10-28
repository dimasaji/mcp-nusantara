import type {ReactNode} from 'react';
import {Link} from '@tanstack/react-router';

export function AppSidebar({children,onNewChat,pending=false,settingsActive=false}:{children?:ReactNode;onNewChat?:()=>void;pending?:boolean;settingsActive?:boolean}){
  return <aside className="app-sidebar">
    <Link className="app-brand" to="/">NUSANTARA<span>Asisten AI</span></Link>
    <nav aria-label="Navigasi utama">
      {onNewChat?<button type="button" disabled={pending} onClick={onNewChat}>+ New Chat</button>:<Link to="/">Kembali ke chat</Link>}
    </nav>
    <nav aria-label="Navigasi operator">
      <Link to="/dashboard">Beranda</Link>
      <Link to="/knowledge">Dokumen</Link>
      <Link to="/approvals">Persetujuan</Link>
      <Link to="/tasks">Riwayat aktivitas</Link>
    </nav>
    {children&&<div className="sidebar-history">{children}</div>}
    <Link className={`settings-entry${settingsActive?' active':''}`} to="/settings" aria-current={settingsActive?'page':undefined} activeProps={{className:'settings-entry active'}}>Pengaturan</Link>
  </aside>;
}

