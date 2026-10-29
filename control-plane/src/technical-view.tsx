import type {ReactNode} from 'react';
import {Link} from '@tanstack/react-router';

/** Keep engineering detail reachable from the existing settings navigation. */
export function TechnicalView({children}:{children:ReactNode}){
  return <div className="technical-view">
    <nav aria-label="Kembali ke pengaturan"><Link to="/settings">Pengaturan</Link></nav>
    {children}
  </div>;
}
