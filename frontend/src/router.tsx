import {createRootRoute,createRoute,createRouter} from '@tanstack/react-router';
import {Shell,Page} from './ui';
import {HumanPage,ExecutionReview} from './human';
import {VerificationPage} from './verification';
import {OverviewPage,KnowledgeOperationsPage} from './overview';
import {UserChat,OperatorConsole} from './assistant';
import {useAdminAuth} from './auth';
import {OperatorHome,TasksPage,BlockersPage,WorkspacePage,CostsPage,TechnicalPage} from './operator';
import {SettingsPage,RuntimeSettingsPage} from './settings';
import {TechnicalView} from './technical-view';
const root=createRootRoute({component:Shell});
function ChatPage(){const {token,setToken}=useAdminAuth();return <UserChat token={token} setToken={setToken}/>;}
const index=createRoute({getParentRoute:()=>root,path:'/',component:ChatPage});
const uiAlias=createRoute({getParentRoute:()=>root,path:'/ui',component:ChatPage});
const assistantAlias=createRoute({getParentRoute:()=>root,path:'/assistant',component:ChatPage});
const consoleRoute=createRoute({getParentRoute:()=>root,path:'/console',component:OperatorConsole});
const dashboard=createRoute({getParentRoute:()=>root,path:'/dashboard',component:OperatorHome});
const overview=createRoute({getParentRoute:()=>root,path:'/overview',component:()=> <TechnicalView><HumanPage stage="System"/></TechnicalView>});
const system=createRoute({getParentRoute:()=>root,path:'/system',component:()=> <TechnicalView><HumanPage stage="System"/></TechnicalView>});
const evidence=createRoute({getParentRoute:()=>root,path:'/evidence',component:()=> <TechnicalView><HumanPage stage="Evidence"/></TechnicalView>});
const humanTest=createRoute({getParentRoute:()=>root,path:'/test',component:()=> <TechnicalView><HumanPage stage="Test"/></TechnicalView>});
const executionReview=createRoute({getParentRoute:()=>root,path:'/review-execute',component:()=> <ExecutionReview title="Human Control"/>});
const review=createRoute({getParentRoute:()=>root,path:'/review',component:()=> <ExecutionReview title="Human Control"/>});
const decision=createRoute({getParentRoute:()=>root,path:'/decision',component:()=> <ExecutionReview title="Human Control"/>});
const engineeringOverview=createRoute({getParentRoute:()=>root,path:'/engineering-overview',component:()=> <TechnicalView><Page name="Overview"/></TechnicalView>});
const roadmap=createRoute({getParentRoute:()=>root,path:'/roadmap',component:()=> <TechnicalView><Page name="Roadmap"/></TechnicalView>});
const architecture=createRoute({getParentRoute:()=>root,path:'/architecture',component:()=> <TechnicalView><Page name="Architecture"/></TechnicalView>});
const engineering=createRoute({getParentRoute:()=>root,path:'/engineering',component:()=> <TechnicalView><Page name="Engineering"/></TechnicalView>});
const governance=createRoute({getParentRoute:()=>root,path:'/governance',component:()=> <TechnicalView><header><h1>Governance &amp; Permissions</h1></header><section className="panel"><p>Kebijakan dan batas kewenangan mengikuti evidence backend. Backend tetap menegakkan otorisasi. Inventaris izin tools per agent belum tersedia.</p></section><Page name="Governance"/></TechnicalView>});
const verification=createRoute({getParentRoute:()=>root,path:'/verification',component:()=> <TechnicalView><VerificationPage/></TechnicalView>});
const runtime=createRoute({getParentRoute:()=>root,path:'/runtime',component:()=> <TechnicalView><Page name="Runtime"/></TechnicalView>});
const knowledge=createRoute({getParentRoute:()=>root,path:'/knowledge',component:KnowledgeOperationsPage});
const operatorRoutes=[
 createRoute({getParentRoute:()=>root,path:'/workspace',component:ChatPage}),
 createRoute({getParentRoute:()=>root,path:'/tasks',component:TasksPage}),
 createRoute({getParentRoute:()=>root,path:'/blockers',component:BlockersPage}),
 createRoute({getParentRoute:()=>root,path:'/approvals',component:()=> <ExecutionReview title="Human Control"/>}),
 createRoute({getParentRoute:()=>root,path:'/costs',component:CostsPage}),
 createRoute({getParentRoute:()=>root,path:'/settings',component:SettingsPage}),
 createRoute({getParentRoute:()=>root,path:'/settings/models',component:RuntimeSettingsPage}),
 createRoute({getParentRoute:()=>root,path:'/settings/workspace',component:WorkspacePage}),
 createRoute({getParentRoute:()=>root,path:'/technical',component:()=> <TechnicalView><TechnicalPage/></TechnicalView>}),
];
export const router=createRouter({routeTree:root.addChildren([...operatorRoutes,executionReview,index,uiAlias,assistantAlias,consoleRoute,dashboard,overview,system,evidence,humanTest,review,decision,engineeringOverview,roadmap,architecture,engineering,governance,verification,runtime,knowledge])});
declare module '@tanstack/react-router'{interface Register{router:typeof router}}
