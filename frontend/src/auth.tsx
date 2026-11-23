import {createContext,useContext,useState,type ReactNode} from 'react';

const AdminAuthContext=createContext<{token:string;setToken:(value:string)=>void}|null>(null);
export function AdminAuthProvider({children,initialToken=''}:{children:ReactNode;initialToken?:string}){
  const [token,setToken]=useState(initialToken);
  return <AdminAuthContext.Provider value={{token,setToken}}>{children}</AdminAuthContext.Provider>;
}
export function useAdminAuth(){
  const value=useContext(AdminAuthContext);
  if(!value)throw new Error('AdminAuthProvider required');
  return value;
}
