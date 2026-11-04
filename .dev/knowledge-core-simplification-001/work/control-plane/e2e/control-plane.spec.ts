import {test,expect} from '@playwright/test';
import fs from 'node:fs';
test('critical engineering navigation and evidence trace',async({page})=>{
  const snapshot=JSON.parse(fs.readFileSync(process.env.CPLANE_SNAPSHOT_FILE!, 'utf8'));
  await page.route('**/v1/control-plane/snapshot',route=>route.fulfill({json:snapshot}));
  await page.goto('/engineering-overview');await expect(page.getByRole('heading',{name:'Engineering Console',exact:true})).toBeVisible();
  await page.getByText('Engineering views',{exact:true}).first().click();
  // Engineering Console renders its own frozen historical evidence fixture (V1 HOLD / V2 DEFERRED),
  // not the live snapshot; assert the values that fixture actually carries.
  await expect(page.getByText(/PARTIAL \/ REVIEW_REQUIRED/).first()).toBeVisible();
  await expect(page.getByRole('heading',{name:'Blocker V1 dari laporan historis',exact:true})).toBeVisible();
  await expect(page.getByText(/CC05 consent/).first()).toBeVisible();
  await expect(page.getByText('REVIEW_REQUIRED',{exact:true}).first()).toBeVisible();
  if(process.env.CPLANE_SCREENSHOT_FILE)await page.screenshot({path:process.env.CPLANE_SCREENSHOT_FILE.replace('.png','-overview.png'),fullPage:true});
  const pages:{group:string|null;link:string;name:string;heading:string}[]=[
    {group:'Engineering views',link:'Roadmap',name:'Roadmap',heading:'Roadmap'},
    {group:'Engineering views',link:'Architecture',name:'Architecture',heading:'Architecture'},
    {group:'Engineering views',link:'Engineering',name:'Engineering',heading:'Engineering'},
    {group:'Engineering views',link:'Runtime',name:'Runtime',heading:'Runtime'},
    {group:'Lintas proses',link:'Knowledge',name:'Knowledge',heading:'Knowledge'},
    {group:'Lintas proses',link:'Governance',name:'Governance',heading:'Governance'},
    {group:null,link:'05 Test & Verification',name:'Verification',heading:'Verifikasi dan keputusan'}];
  let openGroup='Engineering views';
  for(const {group,link,name,heading} of pages){
    if(group&&group!==openGroup){await page.getByText(group,{exact:true}).first().click();openGroup=group;}
    await page.getByRole('link',{name:link,exact:true}).click();await expect(page.getByRole('heading',{name:heading,exact:true})).toBeVisible();
    if(name==='Architecture'){
      await expect(page.getByTestId('engineering-graph')).toBeVisible();
      await expect(page.locator('.react-flow__node')).toHaveCount(6);
      await page.locator('.react-flow__node').first().click();await expect(page.getByText('Trace to source',{exact:true})).toBeVisible();
      const before=await page.locator('.react-flow__viewport').getAttribute('style');
      await page.getByRole('button',{name:'Zoom In',exact:true}).click();
      await expect(page.locator('.react-flow__viewport')).not.toHaveAttribute('style',before!);
      await page.getByRole('button',{name:'Collapse control layer'}).click();await expect(page.locator('.react-flow__node')).toHaveCount(5);
      await page.getByRole('button',{name:'Expand control layer'}).click();await expect(page.locator('.react-flow__node')).toHaveCount(6);
    }
    if(name==='Runtime')await expect(page.getByText('HISTORICAL_CONTROLLED_RUNTIME',{exact:true})).toBeVisible();
    if(name==='Knowledge')await expect(page.getByText('FIXTURE_EVIDENCE',{exact:true})).toBeVisible();
  }
  await page.screenshot({path:process.env.CPLANE_SCREENSHOT_FILE??'test-results/control-plane.png',fullPage:true});
});
test('missing and invalid evidence fails closed',async({page})=>{
  await page.route('**/v1/control-plane/snapshot',route=>route.fulfill({status:503,json:{error:'unavailable'}}));await page.goto('/overview');await expect(page.getByRole('alert')).toContainText('UNKNOWN');
  await page.unroute('**/v1/control-plane/snapshot');await page.route('**/v1/control-plane/snapshot',route=>route.fulfill({json:{status:'PASS'}}));await page.getByRole('button',{name:/Refresh evidence/}).click();await expect(page.getByRole('alert')).toBeVisible();
  await expect(page.getByText('CLOSED_PASS',{exact:true})).toHaveCount(0);
  await expect(page.getByText('R3_IMPLEMENTATION_PASS_WITH_CONDITIONS',{exact:true})).toHaveCount(0);
});
