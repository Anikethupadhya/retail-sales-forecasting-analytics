// Development-only browser inspection. Run with Playwright on NODE_PATH and local Edge.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const url = process.env.DASHBOARD_URL || 'http://localhost:8501';
const screenshots = process.env.SCREENSHOT_DIR || 'docs/screenshots';
const evidence = process.env.BROWSER_EVIDENCE || 'outputs/verification/portfolio/browser.json';
fs.mkdirSync(screenshots,{recursive:true});
fs.mkdirSync(path.dirname(evidence),{recursive:true});
(async () => {
  const browser = await chromium.launch({headless: true, ...(process.env.PLAYWRIGHT_CHANNEL ? {channel:process.env.PLAYWRIGHT_CHANNEL} : {})});
  const errors = [];
  const checks = [];
  let page;
  try {
    page = await browser.newPage({viewport: {width: 1600, height: 1600}, deviceScaleFactor: 1});
    const stable = async () => {
      await page.getByRole('button', {name:'Stop', exact:true}).waitFor({state:'hidden',timeout:60000});
      await page.waitForFunction(() => document.querySelectorAll('[data-stale="true"]').length === 0);
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    };
    page.on('pageerror', e => errors.push(String(e)));
    await page.goto(url, {waitUntil: 'networkidle'});
    await page.getByRole('tab', {name: 'Sales Overview', exact: true}).waitFor();
    await page.locator('[data-testid="stPlotlyChart"]:visible').first().waitFor();
    if (!await page.getByText('All cleaned merchandise · all countries', {exact: true}).isVisible()) throw Error('Overview scope missing');
    checks.push('All-merchandise scope and source coverage');
    await stable();
    await page.screenshot({path:path.join(screenshots,'sales-overview.png'), fullPage:true});
    await page.setViewportSize({width:1600,height:2200});
    await page.getByRole('tab', {name:'Forecast Evaluation', exact:true}).click();
    await page.getByText('Historical fixed-origin backtests', {exact:true}).waitFor();
    await page.locator('[data-testid="stPlotlyChart"]:visible').first().waitFor();
    checks.push('Existing corrected benchmark charts and product/cohort scope');
    await stable();
    await page.screenshot({path:path.join(screenshots,'forecast-evaluation.png'), fullPage:true});
    await page.getByRole('combobox', {name:'Evaluation experiment'}).click();
    await page.getByRole('option', {name:'Retrospective robustness', exact:true}).click();
    await page.getByText(/Fixed cohort selected before January 1/).waitFor();
    await stable();
    await page.getByRole('combobox', {name:'Forecast start'}).waitFor();
    await page.getByRole('combobox', {name:'Forecast start'}).click();
    await page.getByRole('option', {name:'2011-11-01', exact:true}).click();
    await page.getByText(/Training cutoff: 2011-10-31/).waitFor({timeout:60000});
    await page.getByRole('combobox', {name:'Product', exact:true}).click();
    await page.getByRole('option').nth(1).click();
    await page.getByText('Selected product only', {exact:true}).waitFor();
    checks.push('Robustness experiment, November period and changed product');
    await stable();
    await page.screenshot({path:path.join(screenshots,'forecast-robustness.png'), fullPage:true});
    await page.getByRole('combobox', {name:'Evaluation experiment'}).click();
    await page.getByRole('option', {name:'Training-window experiment', exact:true}).click();
    await page.getByRole('combobox', {name:'Smoothing histories'}).click();
    await page.getByRole('option', {name:'Smoothing · 182 days', exact:true}).click();
    await page.getByRole('combobox', {name:'Smoothing histories'}).click();
    await page.getByRole('option', {name:'Smoothing · 365 days', exact:true}).click();
    await page.keyboard.press('Escape');
    await page.getByText(/182 or 365 calendar days/).waitFor();
    await stable();
    await page.screenshot({path:path.join(screenshots,'forecast-training-windows.png'),fullPage:true});
    checks.push('Training-window origin/product controls and all three saved smoothing curves');
    const walkthrough = JSON.parse(fs.readFileSync('outputs/portfolio/walkthrough_examples.json','utf8'));
    for (const example of walkthrough.examples) {
      const label = example.id[0].toUpperCase()+example.id.slice(1);
      await page.getByRole('combobox',{name:'Walkthrough example',exact:true}).click();
      await page.getByRole('option',{name:label,exact:true}).click();
      await page.getByText(new RegExp('Illustrative example selected after inspecting results: '+example.product_id)).waitFor({timeout:60000});
      await page.getByText(new RegExp('Forecast start: '+example.forecast_start)).waitFor();
      await stable();
      await page.screenshot({path:path.join(screenshots,'walkthrough-'+example.id+'.png'),fullPage:true});
      checks.push('Manifest-driven '+example.id+': '+example.product_id+', '+example.forecast_start);
    }
    await page.getByRole('tab', {name:'Model Performance', exact:true}).click();
    await page.setViewportSize({width:1600,height:2500});
    await page.getByText('Retrospective robustness · six periods pooled', {exact:true}).waitFor();
    await page.locator('[data-testid="stPlotlyChart"]:visible').first().waitFor();
    checks.push('Model comparison, period curves and signed product contributions');
    await stable();
    await page.screenshot({path:path.join(screenshots,'model-performance.png'), fullPage:true});
    await page.getByText('Training-window product contributions, bias, spikes and fit records', {exact:true}).click();
    await page.getByText(/Common spikes: actual units strictly above/).waitFor();
    await stable();
    await page.screenshot({path:path.join(screenshots,'training-window-diagnostics.png'),fullPage:true});
    checks.push('Rendered shared spike, product contribution and fit-record diagnostics');
    await page.getByText('Training-window product contributions, bias, spikes and fit records', {exact:true}).click();
    await page.getByText('Five largest improvements/deteriorations, bias and spike examples', {exact:true}).click();
    await page.getByRole('combobox', {name:'Spike example product'}).waitFor();
    checks.push('Rendered product error tables and spike chart');
    if (await page.getByText('Simulated inventory controls', {exact:true}).count()) throw Error('Old controls remain');
    const sourceChecksums = {};
    for(const name of ['app.py','scripts/capture_dashboard.cjs','package.json','outputs/portfolio/summary.json','outputs/portfolio/walkthrough_examples.json']) {
      sourceChecksums[name] = crypto.createHash('sha256').update(fs.readFileSync(name)).digest('hex');
    }
    fs.writeFileSync(evidence,JSON.stringify({status:errors.length?'failed':'passed', implementation_revision:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(), source_checksums:sourceChecksums, url, screenshots:6+walkthrough.examples.length, screenshot_paths:['sales-overview','forecast-evaluation','forecast-robustness','forecast-training-windows','model-performance','training-window-diagnostics',...walkthrough.examples.map(e=>'walkthrough-'+e.id)].map(n=>path.join(screenshots,n+'.png')), playwright_version:require('playwright/package.json').version, browser_channel:process.env.PLAYWRIGHT_CHANNEL || 'bundled chromium', checks, page_errors:errors},null,2));
    if(errors.length) process.exitCode=1;
  } catch(error) { await page.screenshot({path:path.join(screenshots,'browser-failure.png'),fullPage:true}); fs.writeFileSync(path.join(screenshots,'browser-failure.txt'),await page.locator('body').innerText()); throw error; } finally {await browser.close();}
})().catch(e => {console.error(e); process.exitCode=1;});
