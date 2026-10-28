import {render,screen,fireEvent} from '@testing-library/react';
import {expect,it,vi} from 'vitest';
import {SettingsNavigation} from '../src/settings';
import {TechnicalView} from '../src/technical-view';

vi.mock('@tanstack/react-router',()=>({Link:({to,children}:{to:string;children:React.ReactNode})=><a href={to}>{children}</a>}));

it('keeps engineering navigation behind an explicit technical-details action',()=>{
  render(<SettingsNavigation pathname="/dashboard"/>);
  expect(screen.getByRole('link',{name:'Dokumen'})).toHaveAttribute('href','/knowledge');
  expect(screen.getByRole('link',{name:'Persetujuan'})).toHaveAttribute('href','/approvals');
  expect(screen.queryByRole('link',{name:'Teknis'})).not.toBeInTheDocument();
  fireEvent.click(screen.getByText('Detail teknis'));
  expect(screen.getByRole('link',{name:'Teknis'})).toHaveAttribute('href','/technical');
});

it('shows engineering checks only on request and preserves their controls',()=>{
  const execute=vi.fn();
  render(<TechnicalView><h2>AC1 / R3.12</h2><button disabled onClick={execute}>Eksekusi terkunci</button></TechnicalView>);
  expect(screen.queryByText('AC1 / R3.12')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button',{name:'Buka detail teknis'}));
  expect(screen.getByRole('heading',{name:'AC1 / R3.12'})).toBeInTheDocument();
  expect(screen.getByRole('button',{name:'Eksekusi terkunci'})).toBeDisabled();
  expect(execute).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button',{name:'Tutup detail teknis'}));
  expect(screen.queryByText('AC1 / R3.12')).not.toBeInTheDocument();
});
