const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
  });
  // const browser = await puppeteer.launch();
  const page = await browser.newPage();

  // 1. Fill login form
  await page.goto('https://acceso.alfyinversiones.com.ar/');
  // TODO: read from env
  await page.type('[name="Dni"]', '');
  await page.type('[name="Usuario"]', '');
  await page.type('[name="Password"]', '');
  await page.click('#loginButton');
  await page.waitForNavigation();

  // 2. Check account balance
  await page.waitForSelector('#result-portafolioOnline', { visible: true });
  const totalText = await page.$eval('.first-row .text-bold', (el => el.innerText));
  const totalAccountValue = parseFloat(
    totalText.split(' ')[1] // removes undesired $ sign
      .split('.').join('')    // removes undesired dot symbols
      .replace(',', '.')      // proper float format
  );

  // 3. Portfolio updates
  const portfolio = JSON.parse(fs.readFileSync('portfolio.json'));
  await page.goto('https://acceso.alfyinversiones.com.ar/Prices/Stocks');

  for (let stock in portfolio) {
    if (portfolio.hasOwnProperty(stock)) {
      portfolio[stock] = Math.round(portfolio[stock] * totalAccountValue * 100) / 100; // round 2 decimals
      await page.type('#nombre_especie_footer', stock);
      await page.type('#importe_footer', portfolio[stock].toString());
      await page.click('.hidden-md .btn-compra');
      await page.waitForSelector('.modal-content #formCargar-orden', { visible: true });
      await page.click('#btnVerificacion-Confirmar_footer');
      await page.waitForSelector('.callout-success', { visible: true });
      await page.click('#btnVerificacion-Cancelar');
      // add 2 sec sleep, otherwise the buy button is not actionable
    }
  }

  // Cleanup
  await browser.close();
})();
