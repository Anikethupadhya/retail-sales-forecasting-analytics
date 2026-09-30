// Development-only browser inspection. Run with Playwright on NODE_PATH and local Edge.
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const browser = await chromium.launch({headless: true, channel: 'msedge'});
  const errors = [];
  const checks = [];
  try {
    const page = await browser.newPage({viewport: {width: 1600, height: 1600}, deviceScaleFactor: 1});
    const stable = async () => {
      await page.getByRole('button', {name:'Stop', exact:true}).waitFor({state:'hidden',timeout:60000});
      await page.waitForFunction(() => document.querySelectorAll('[data-stale="true"]').length === 0);
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    };
    page.on('pageerror', e => errors.push(String(e)));
    await page.goto('http://localhost:8501', {waitUntil: 'networkidle'});
    await page.getByRole('tab', {name: 'Sales Overview', exact: true}).waitFor();
    await page.locator('[data-testid="stPlotlyChart"]:visible').first().waitFor();
    if (!await page.getByText('All cleaned merchandise · all countries', {exact: true}).isVisible()) throw Error('Overview scope missing');
    checks.push('All-merchandise scope and source coverage');
    await stable();
    await page.screenshot({path:'docs/screenshots/sales-overview.png', fullPage:true});
    await page.getByRole('tab', {name:'Forecast Evaluation', exact:true}).click();
    await page.getByText('Historical fixed-origin backtests', {exact:true}).waitFor();
    await page.locator('[data-testid="stPlotlyChart"]:visible').first().waitFor();
    checks.push('Existing corrected benchmark charts and product/cohort scope');
    await stable();
    await page.screenshot({path:'docs/screenshots/forecast-evaluation.png', fullPage:true});
    await page.getByRole('combobox', {name:'Evaluation experiment'}).click();
    await page.getByRole('option', {name:'Retrospective robustness', exact:true}).click();
    await page.getByRole('combobox', {name:'Forecast start'}).waitFor();
    await page.getByRole('combobox', {name:'Forecast start'}).click();
    await page.getByRole('option', {name:'2011-11-01', exact:true}).click();
    await page.getByText(/Training cutoff: 2011-10-31/).waitFor();
    await page.getByRole('combobox', {name:'Product', exact:true}).click();
    await page.getByRole('option').nth(1).click();
    await page.getByText('Selected product only', {exact:true}).waitFor();
    checks.push('Robustness experiment, November period and changed product');
    await stable();
    await page.screenshot({path:'docs/screenshots/forecast-robustness.png', fullPage:true});
    await page.getByRole('tab', {name:'Model Performance', exact:true}).click();
    await page.setViewportSize({width:1600,height:2500});
    await page.getByText('Retrospective robustness · six periods pooled', {exact:true}).waitFor();
    await page.locator('[data-testid="stPlotlyChart"]:visible').first().waitFor();
    checks.push('Model comparison, period curves and signed product contributions');
    await stable();
    await page.screenshot({path:'docs/screenshots/model-performance.png', fullPage:true});
    await page.getByText('Five largest improvements/deteriorations, bias and spike examples', {exact:true}).click();
    await page.getByRole('combobox', {name:'Spike example product'}).waitFor();
    checks.push('Rendered product error tables and spike chart');
    if (await page.getByText('Simulated inventory controls', {exact:true}).count()) throw Error('Old controls remain');
    fs.writeFileSync('outputs/verification/browser.json',JSON.stringify({url:'http://localhost:8501', screenshots:4, checks, page_errors:errors},null,2));
    if(errors.length) process.exitCode=1;
  } finally {await browser.close();}
})().catch(e => {console.error(e); process.exitCode=1;});
