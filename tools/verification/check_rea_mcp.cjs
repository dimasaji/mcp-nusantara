// Explicit standalone MCP probe; does not imply the current Codex session reconnected.
const fs=require('node:fs');
const path=require('node:path');
const base='C:/Users/dmaza/AppData/Local/npm-cache/_npx/af752b90495482d7/node_modules';
const {Client}=require(base+'/@modelcontextprotocol/client/dist/index.cjs');
const {StdioClientTransport}=require(base+'/@modelcontextprotocol/client/dist/stdio.cjs');
(async()=>{
 const out=path.resolve('artifacts/v1-verification/rea');fs.mkdirSync(out,{recursive:true});
 const client=new Client({name:'nusantara-local-verification',version:'1.0.0'});
 const transport=new StdioClientTransport({command:'cmd.exe',args:['/d','/c','npx','-y','rea-agents@6.5.0','mcp'],stderr:'pipe'});
 try{
  await client.connect(transport);
  const catalog=await client.listTools();
  fs.writeFileSync(path.join(out,'tools.json'),JSON.stringify(catalog,null,2));
  const tool=catalog.tools.find(t=>t.name==='binary_session');
  if(!tool)throw Error('binary_session missing');
  console.log(JSON.stringify({server:client.getServerVersion(),tool_count:catalog.tools.length}));
  const result=await client.callTool({name:tool.name,arguments:{}});
  fs.writeFileSync(path.join(out,'binary-session.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify({tool:tool.name,isError:result.isError??false,saved:'binary-session.json'}));
  if(result.isError)throw Error('REA session probe failed');
  const capture=await client.callTool({name:'capture_browser_scenario',arguments:{
   browser:{mode:'launch',executable_path:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true},
   start_url:{url:'http://127.0.0.1:5180/verification'},
   actions:[{step_id:'wait_review',action:'wait_for',locator:{kind:'css',selector:'h1'},state:'visible',timeout_ms:30000},
            {step_id:'wait_evidence',action:'wait_for',locator:{kind:'css',selector:'textarea'},state:'visible',timeout_ms:30000}],
   capture:{at_end:['url','dom','accessibility'],events:['page-errors','network']}
  }},{timeout:60000});
  fs.writeFileSync(path.join(out,'verification-browser.json'),JSON.stringify(capture,null,2));
  console.log(JSON.stringify({tool:'capture_browser_scenario',isError:capture.isError??false,saved:'verification-browser.json',human_decision_clicked:false}));
  if(capture.isError)throw Error('REA browser capture failed');
 }finally{await client.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
